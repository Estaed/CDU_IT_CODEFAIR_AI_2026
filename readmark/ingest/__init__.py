"""Ingest: the five policy PDFs and one case file become numbered passages.

Policy passages are ``<policy>:p<N>:<k>`` and case passages ``<case_id>:p<N>:<k>`` (contract),
where N is the page and k the 1-based paragraph on that page. Every PDF is checked against its
SHA-256 pin in ``policies.lock.json`` first, so a changed policy fails loudly instead of being
read silently.
"""

import hashlib
import json
import logging
import re
from collections import Counter
from pathlib import Path

from pypdf import PdfReader

from readmark import CASES_DIR, POLICIES_DIR

# pypdf warns about a symbol font it cannot fully decode; the text it extracts is still exact.
logging.getLogger("pypdf").setLevel(logging.ERROR)

# Short key (used in passage ids), file name and display title for each bundled policy.
POLICIES = {
    "eligibility": ("eligibility-for-social-housing-policy.pdf", "Eligibility for Social Housing"),
    "priority": ("priority-housing-policy.pdf", "Priority Housing"),
    "identification": (
        "identification-and-documentation-policy.pdf",
        "Identification and Documentation",
    ),
    "dfv": ("domestic-family-violence-policy.pdf", "Domestic and Family Violence"),
    "discretion": ("discretionary-decision-making-policy.pdf", "Discretionary Decision Making"),
}


class IngestError(RuntimeError):
    """Raised when an input cannot be trusted: a missing or changed PDF, a malformed case."""


def normalise(text: str) -> str:
    """Whitespace collapsed, case kept: a phrase may wrap across a line and still match."""
    return " ".join(text.split())


def passage_key(passage_id: str) -> tuple:
    """File order for a passage id: 'A-0142:p8:3' sorts before 'A-0142:p23:1'. An id that does
    not parse (a writer's invented one) sorts after the real ones, by its text."""
    source, _, rest = passage_id.partition(":")
    page, _, k = rest.partition(":")
    if page[1:].isdigit() and k.isdigit():
        return (source, 0, int(page[1:]), int(k), "")
    return (source, 1, 0, 0, passage_id)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------------------------
# Policies
# ---------------------------------------------------------------------------------------------


def load_lock(policies_dir: Path = POLICIES_DIR) -> dict:
    return json.loads((policies_dir / "policies.lock.json").read_text(encoding="utf-8"))


def verify_pins(policies_dir: Path = POLICIES_DIR, lock: dict | None = None) -> dict:
    """Stop unless every pinned PDF is present and byte-identical to its pin."""
    lock = lock if lock is not None else load_lock(policies_dir)
    for file_name, pin in sorted(lock.items()):
        path = policies_dir / file_name
        if not path.exists():
            raise IngestError(
                f"Policy PDF missing: {path}. Download it by hand from {pin['url']} "
                f"(expected SHA-256 {pin['sha256']}); see README."
            )
        actual = sha256_file(path)
        if actual != pin["sha256"]:
            raise IngestError(
                f"Policy PDF changed: {file_name} has SHA-256 {actual}, expected SHA-256 "
                f"{pin['sha256']} (version {pin['version']}). Re-download it from {pin['url']} "
                "or re-pin it on purpose."
            )
    return lock


_HEADING = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+([A-Z][^.]{1,80})$")
_PAGE_FOOTER = re.compile(r"^Page \d+ of \d+$")
_BULLET = re.compile(r"^[•\-–]\s*")


def _page_lines(reader: PdfReader) -> list[list[str]]:
    """Lines per page with running headers, footers and table-of-contents lines removed."""
    pages = [[ln.strip() for ln in (p.extract_text() or "").splitlines()] for p in reader.pages]
    # A line repeated on three or more pages is a running header or footer, not content.
    seen = Counter(ln for lines in pages for ln in set(lines) if ln)
    return [
        [
            ln
            for ln in lines
            if ln and seen[ln] < 3 and not _PAGE_FOOTER.match(ln) and "......" not in ln
        ]
        for lines in pages
    ]


def _paragraphs(lines: list[str]) -> list[tuple[str, str | None]]:
    """Join PDF lines into paragraphs. Returns (text, heading) pairs, where heading is the
    section line itself when the paragraph is one.

    A paragraph ends at a heading, a bullet, or a line that ends a sentence and stops short of
    the page's full line width (the PDF gives lines, not paragraphs).
    """
    width = max((len(ln) for ln in lines), default=0)
    paras: list[list[str]] = []
    kinds: list[bool] = []  # True when the paragraph is a heading
    prev_ends = True
    for ln in lines:
        heading = bool(_HEADING.match(ln)) and len(ln) < 90
        bullet = bool(_BULLET.match(ln))
        if not paras or heading or bullet or kinds[-1] or prev_ends:
            paras.append([])
            kinds.append(heading)
        paras[-1].append(_BULLET.sub("", ln) if bullet else ln)
        prev_ends = heading or (ln.endswith((".", ":", ";", "?")) and len(ln) < 0.85 * width)
    return [(normalise(" ".join(p)), normalise(" ".join(p)) if h else None) for p, h in
            zip(paras, kinds, strict=True)]


def policy_passages(policies_dir: Path = POLICIES_DIR) -> list[dict]:
    """All policy passages, text included. The text stays in memory: stage files keep only ids,
    offsets and hashes (contract, Run outputs)."""
    lock = verify_pins(policies_dir)
    out: list[dict] = []
    for key, (file_name, title) in POLICIES.items():
        if file_name not in lock:
            raise IngestError(f"{file_name} is not pinned in policies.lock.json")
        reader = PdfReader(str(policies_dir / file_name))
        section = None
        for page_no, lines in enumerate(_page_lines(reader), start=1):
            for k, (text, heading) in enumerate(_paragraphs(lines), start=1):
                if heading:
                    section = heading
                out.append(
                    {
                        "passage_id": f"{key}:p{page_no}:{k}",
                        "source": "policy",
                        "policy": key,
                        "doc_title": f"{title} policy",
                        "version": lock[file_name]["version"],
                        "page": page_no,
                        "k": k,
                        "section": section,
                        "text": text,
                    }
                )
    return out


# ---------------------------------------------------------------------------------------------
# Case files
# ---------------------------------------------------------------------------------------------

_PAGE_MARK = re.compile(r"^<!--\s*page\s+(\d+)\s*-->\s*$")
_DOC_HEAD = re.compile(r"^## Document:\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*$")


def case_path(case_id: str) -> Path:
    return CASES_DIR / case_id / "case.md"


def case_passages(case_id: str, path: Path | None = None) -> tuple[dict, list[dict]]:
    """Parse a contract-format case file into (meta, passages).

    The page marker and the ``## Document:`` line are structure, not paragraphs, so k counts
    only the text paragraphs on a page.
    """
    path = path or case_path(case_id)
    if not path.exists():
        raise IngestError(f"Case file not found: {path}")
    pages: list[list[str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = _PAGE_MARK.match(line)
        if m:
            if int(m.group(1)) != len(pages) + 1:
                raise IngestError(
                    f"{path}: page marker {m.group(1)} out of order (expected {len(pages) + 1})"
                )
            pages.append([])
        elif pages:
            pages[-1].append(line)
        elif line.strip():
            raise IngestError(f"{path}: text before the first page marker")
    if not pages:
        raise IngestError(f"{path}: no page markers")

    doc = {"doc_type": None, "doc_title": None, "doc_date": None}
    documents: list[dict] = []
    passages: list[dict] = []
    for page_no, lines in enumerate(pages, start=1):
        k = 0
        block: list[str] = []
        for line in [*lines, ""]:
            head = _DOC_HEAD.match(line)
            if head:
                doc = dict(zip(("doc_type", "doc_title", "doc_date"), head.groups(), strict=True))
                documents.append({**doc, "page": page_no})
                continue
            if line.strip():
                block.append(line)
                continue
            if block:
                k += 1
                passages.append(
                    {
                        "passage_id": f"{case_id}:p{page_no}:{k}",
                        "source": "case",
                        "page": page_no,
                        "k": k,
                        **doc,
                        "text": normalise(" ".join(block)),
                    }
                )
                block = []
    meta = {
        "case_id": case_id,
        "pages": len(pages),
        "documents": documents,
        "sha256": sha256_file(path),
    }
    return meta, passages


def stage_record(meta: dict, case: list[dict], policy: list[dict], lock: dict) -> dict:
    """The ``passages`` stage file: case text in full (synthetic), policy passages as ids,
    lengths and hashes only."""
    return {
        "case": meta,
        "case_passages": case,
        "policies": {
            name: {k: pin[k] for k in ("version", "approved", "sha256", "pages")}
            for name, pin in sorted(lock.items())
        },
        "policy_passages": [
            {
                "passage_id": p["passage_id"],
                "page": p["page"],
                "chars": len(p["text"]),
                "sha256": sha256_text(p["text"]),
            }
            for p in policy
        ],
    }
