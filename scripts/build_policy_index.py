"""Build the frozen FS17 policy-passage index (PRD section 5)."""

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from collections.abc import Callable
from datetime import date
from pathlib import Path

import numpy as np
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # scripts run from source, not an installed package

from fair_turn.core.constants import SAFETY_CLASSES  # noqa: E402
from fair_turn.core.types import FaultType  # noqa: E402
from fair_turn.core.verify_spans import normalise  # noqa: E402
from fair_turn.data.policy import key_for  # noqa: E402
from fair_turn.llm.ollama import embed as ollama_embed  # noqa: E402

FS17_URL = "https://dhlgcd.nt.gov.au/media/documents/fact-sheets/repairs-and-maintenance-fs17.pdf"
DEFAULT_PDF = ROOT / "data" / "raw" / "nt_fs17_repairs_and_maintenance_2025-10.pdf"
DEFAULT_OUT = ROOT / "data" / "build" / "policy_passages.json"
PROVENANCE = ROOT / "data" / "raw" / "PROVENANCE.md"
THRESHOLD = 0.55
FAKE_DIMENSIONS = 64
WITH_FAULT_QUERY = (
    "How quickly a {safety_class} repair for a {fault} fault in a {place} must be done, "
    "and what counts as urgent"
)
WITHOUT_FAULT_QUERY = (
    "How quickly a {safety_class} repair in a {place} must be done, and what counts as urgent"
)


def fake_embed(texts: list[str]) -> list[list[float]]:
    """Return deterministic, L2-normalised hashing bag-of-words vectors for CI."""
    vectors = []
    for text in texts:
        vector = np.zeros(FAKE_DIMENSIONS, dtype=float)
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            bucket = (
                int.from_bytes(hashlib.sha256(token.encode("utf-8")).digest()[:4]) % FAKE_DIMENSIONS
            )
            vector[bucket] += 1.0
        magnitude = np.linalg.norm(vector)
        vectors.append((vector / magnitude if magnitude else vector).tolist())
    return vectors


def _is_heading(paragraph: str) -> bool:
    return len(paragraph.split()) <= 8 and not paragraph.rstrip().endswith((".", "!", "?"))


def _split_long_paragraph(paragraph: str) -> list[str]:
    """Split an overlong paragraph at sentence boundaries while preserving its words."""
    if len(paragraph.split()) <= 120:
        return [paragraph]
    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    pieces: list[str] = []
    current: list[str] = []
    words = 0
    for sentence in sentences:
        sentence_words = sentence.split()
        while sentence_words:
            room = 120 - words
            if room == 0:
                pieces.append(" ".join(current))
                current, words, room = [], 0, 120
            take = sentence_words[:room]
            current.extend(take)
            words += len(take)
            sentence_words = sentence_words[room:]
            if words == 120:
                pieces.append(" ".join(current))
                current, words = [], 0
    if current:
        pieces.append(" ".join(current))
    return pieces


def chunk_document(text: str) -> list[tuple[str, str]]:
    """Chunk FS17 paragraphs by heading into 60--120-word passages."""
    chunks: list[tuple[str, str]] = []
    section = "FS17"
    current: list[str] = []
    word_count = 0

    def flush() -> None:
        nonlocal current, word_count
        if current:
            chunks.append((section, " ".join(current)))
        current, word_count = [], 0

    for raw_paragraph in re.split(r"\n\s*\n", text):
        paragraph = normalise(raw_paragraph)
        if not paragraph:
            continue
        if _is_heading(paragraph):
            flush()
            section = paragraph
            continue
        for piece in _split_long_paragraph(paragraph):
            piece_words = len(piece.split())
            if current and word_count + piece_words > 120:
                flush()
            current.append(piece)
            word_count += piece_words
            if word_count >= 60:
                flush()
    flush()
    return chunks


def _query(safety_class: str, is_remote: bool, fault_type: FaultType | None) -> str:
    place = "remote community" if is_remote else "town home"
    if fault_type is None:
        return WITHOUT_FAULT_QUERY.format(safety_class=safety_class, place=place)
    return WITH_FAULT_QUERY.format(
        safety_class=safety_class,
        fault=fault_type.value.replace("_", " "),
        place=place,
    )


def build(
    text: str,
    embed_fn: Callable[[list[str]], list[list[float]]],
    threshold: float,
    *,
    embed_model: str = "bge-m3",
    fetched: str | None = None,
) -> dict:
    """Build the complete typed-key index from source text and an embedding seam."""
    chunks = chunk_document(text)
    chunk_vectors = np.asarray(embed_fn([chunk[1] for chunk in chunks]), dtype=float)
    keys: dict[str, list[dict]] = {}
    for safety_class in SAFETY_CLASSES:
        for is_remote in (False, True):
            for fault_type in (*FaultType, None):
                key = key_for(safety_class, is_remote, fault_type)
                query_vector = np.asarray(
                    embed_fn([_query(safety_class, is_remote, fault_type)])[0], dtype=float
                )
                if not len(chunks):
                    keys[key] = []
                    continue
                denominator = np.linalg.norm(chunk_vectors, axis=1) * np.linalg.norm(query_vector)
                scores = np.divide(
                    chunk_vectors @ query_vector,
                    denominator,
                    out=np.zeros(len(chunks)),
                    where=denominator != 0,
                )
                ranked = sorted(enumerate(scores), key=lambda pair: (-pair[1], pair[0]))
                keys[key] = [
                    {
                        "section": chunks[index][0],
                        "text": chunks[index][1],
                        "score": round(float(score), 6),
                    }
                    for index, score in ranked[:3]
                    if score >= threshold
                ]
    return {
        "source": {
            "title": "NT DHLGCD fact sheet FS17 Repairs and maintenance (10/2025)",
            "url": FS17_URL,
            "effective_date": "2025-10",
            "fetched": fetched or date.today().isoformat(),
        },
        "threshold": threshold,
        "embed_model": embed_model,
        "keys": keys,
    }


def write_artefact(path: Path, artefact: dict) -> None:
    """Write stable, judge-readable JSON with a final newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        json.dump(artefact, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _fetch_pdf(path: Path) -> None:
    with urllib.request.urlopen(FS17_URL, timeout=120) as response:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(response.read())
    provenance = PROVENANCE.read_text(encoding="utf-8")
    if FS17_URL not in provenance:
        row = (
            f"| `nt_fs17_repairs_and_maintenance_2025-10.pdf` | "
            f"NT DHLGCD fact sheet FS17 Repairs and maintenance (10/2025) â€” {FS17_URL} | "
            "Repairs and maintenance policy passages | Â© Northern Territory Government; "
            "licence: PRD open question 6 |\n"
        )
        with PROVENANCE.open("a", encoding="utf-8", newline="") as f:
            f.write(row)


def _pdf_text(path: Path) -> str:
    return "\n\n".join(page.extract_text() or "" for page in PdfReader(path).pages)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fake", action="store_true", help="use the deterministic CI embedder")
    parser.add_argument("--text", type=Path, help="plain-text source instead of the FS17 PDF")
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF, help="path to the frozen FS17 PDF")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output index path")
    parser.add_argument("--threshold", type=float, default=THRESHOLD, help="minimum cosine score")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.text:
        text = args.text.read_text(encoding="utf-8")
    else:
        if not args.pdf.exists():
            _fetch_pdf(args.pdf)
        text = _pdf_text(args.pdf)
    embedder = fake_embed if args.fake else ollama_embed
    model = "fake-hash-64" if args.fake else "bge-m3"
    artefact = build(text, embedder, args.threshold, embed_model=model)
    write_artefact(args.out, artefact)
    print(f"wrote {args.out.relative_to(ROOT) if args.out.is_relative_to(ROOT) else args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
