"""The SummEdits sample for the checker evaluation (Task-08).

Source: the official SummEdits release on Hugging Face, ``Salesforce/summedits`` (CC BY 4.0),
pinned to one revision and checked by SHA-256. Run once to write the committed sample:

    uv run python -m readmark.eval.summedits <path to the downloaded summedits.json>

The full release (28.6 MB) is not committed; only the sample is, with its source, licence,
citation and sampling rule in ``data/benchmark/summedits/README.md``.
"""

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

from readmark import DATA

SAMPLE_DIR = DATA / "benchmark" / "summedits"
SAMPLE_FILE = SAMPLE_DIR / "sample.jsonl"

SOURCE_URL = ("https://huggingface.co/datasets/Salesforce/summedits/resolve/"
              "ce0c479aaf59259abb6b67e42248b2f49004b7d5/summedits.json")
SOURCE_SHA256 = "21e34593330020d02b7d92f4651fdcc550f7d79a2f899392f106fd816c215a89"

SEED = 20261003
PER_DOMAIN_PER_LABEL = 15  # 10 domains x 2 labels x 15 = 300 pairs

# Jev's context is 32K tokens. A document longer than this many words is skipped with a count
# rather than truncated; the longest SummEdits document is about 2,100 words, so none is.
MAX_DOC_WORDS = 15_000


def sample_pairs(rows: list[dict]) -> tuple[list[dict], int]:
    """Stratified random sample: for every domain and both labels, PER_DOMAIN_PER_LABEL pairs.

    One seeded generator walks the strata in a fixed order (domain, then label), so the sample is
    the same on every machine. The sample is then shuffled with the same generator and numbered
    s001..s300 in that order: the ids carry no domain or label (the release ids end in ``_og``
    for unedited seed summaries, which would leak the label to a model)."""
    rng = random.Random(SEED)
    usable = [r for r in rows if len(r["doc"].split()) <= MAX_DOC_WORDS]
    skipped = len(rows) - len(usable)
    picked = []
    for domain in sorted({r["domain"] for r in usable}):
        for label in (0, 1):
            stratum = sorted((r for r in usable if r["domain"] == domain and int(r["label"]) == label),
                             key=lambda r: r["id"])
            picked.extend(rng.sample(stratum, PER_DOMAIN_PER_LABEL))
    rng.shuffle(picked)
    sample = [
        {
            "sample_id": f"s{i:03d}",
            "source_id": r["id"],
            "domain": r["domain"],
            "label": int(r["label"]),  # 1 = consistent with the document, 0 = inconsistent
            "edit_types": list(r["edit_types"] or []),
            "doc": r["doc"],
            "summary": r["summary"],
        }
        for i, r in enumerate(picked, start=1)
    ]
    return sample, skipped


def load_sample(path: Path = SAMPLE_FILE) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="readmark.eval.summedits")
    parser.add_argument("source", type=Path, help="the downloaded summedits.json")
    args = parser.parse_args(argv)
    raw = args.source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SOURCE_SHA256:
        print(f"{args.source}: SHA-256 {digest} is not the pinned release {SOURCE_SHA256}",
              file=sys.stderr)
        return 1
    sample, skipped = sample_pairs(json.loads(raw))
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLE_FILE.write_text(
        "".join(json.dumps(s, ensure_ascii=False, sort_keys=True) + "\n" for s in sample),
        encoding="utf-8", newline="\n",
    )
    print(f"{len(sample)} pairs ({skipped} documents over {MAX_DOC_WORDS} words skipped) -> "
          f"{SAMPLE_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
