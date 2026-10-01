"""Build the cross-vendor challenge set: reports written by a different model family.

The main set is written by Claude Opus and read by Claude Sonnet, so a judge can fairly ask
whether the extractor only reads its own family's prose. This set answers that: the same
generation prompt (same NT class definitions, same rules), but the text is written by an
OpenAI model through the Codex CLI, then read by the unchanged Sonnet extractor and scored
separately by ``run_eval.py``.

Run from the repo root with a logged-in ``codex`` and ``claude`` (spends both windows):
    venv/Scripts/python scripts/build_challenge_set.py
Writes data/build/challenge.json (labels, text, writer) and
data/build/challenge_extraction.json (rows shaped like extraction.json). Resumable: a step
whose artefact exists is skipped; delete the file to redo it.
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]  # package from source; sibling scripts

import extract  # noqa: E402
import generate_text  # noqa: E402

from fair_turn.data import synth  # noqa: E402
from fair_turn.llm import claude_cli, codex_cli, prompts  # noqa: E402

BUILD = ROOT / "data" / "build"
SIZE = 36  # 12 per safety class
WRITER_MODEL = "gpt-6-luna"
WRITER_EFFORT = "medium"
BATCH = 12


def tuples(personas: list[dict], communities: list[dict]) -> list[dict]:
    """``SIZE`` label tuples, deterministic: classes balanced, each class cycling through the
    fault types the synthetic mix makes plausible for it (probability at least 5 %), town and
    remote alternating. Health risk is the persona's own factors."""
    classes = list(synth.SAFETY_ORDER)
    plausible = {
        cls: [
            str(fault)
            for fault, mix in synth.SAFETY_MIX_BY_FAULT.items()
            if mix[classes.index(cls)] >= 0.05
        ]
        for cls in classes
    }
    town = [c for c in communities if not c["is_remote"]]
    remote = [c for c in communities if c["is_remote"]]
    items = []
    for i in range(SIZE):
        persona = personas[(i * 7) % len(personas)]
        community = (remote if i % 2 else town)[(i * 5) % len(remote if i % 2 else town)]
        cls = classes[i % len(classes)]
        faults = plausible[cls]
        items.append(
            {
                "job_id": f"CH-{i + 1:03d}",
                "community_id": community["community_id"],
                "fault_type": faults[(i // len(classes)) % len(faults)],
                "safety_class": str(cls),
                "health_risk": list(persona["household_factors"]),
                "persona_id": persona["persona_id"],
                "reported_on": "2025-12-15",
                "setting": generate_text.setting_for(community),
            }
        )
    return items


def write_texts(items: list[dict], personas: dict[str, dict]) -> list[dict]:
    """Ask the other-vendor writer for the text, validate it as the main set is validated."""
    names = generate_text.real_names()
    out = []
    for start in range(0, len(items), BATCH):
        batch = items[start : start + BATCH]
        result = codex_cli.extract(
            prompts.GENERATION_SYSTEM + "\n\n" + prompts.generation_prompt(batch, personas),
            prompts.GENERATION_SCHEMA,
            timeout=900,
            model=WRITER_MODEL,
            effort=WRITER_EFFORT,
        )
        wanted = {item["job_id"] for item in batch}
        texts = {}
        for report in result.get("reports", []):
            reason = generate_text.validate(report, wanted - set(texts), names)
            if reason:
                print(f"challenge: {report.get('job_id')} rejected: {reason}", file=sys.stderr)
                continue
            texts[report["job_id"]] = report["text"]
        for item in batch:
            if item["job_id"] in texts:
                out.append({**item, "text": texts[item["job_id"]], "writer": WRITER_MODEL})
    return out


def extract_rows(challenge: list[dict]) -> list[dict]:
    """The unchanged Sonnet extractor over the challenge texts, one call."""
    reports = [{"job_id": c["job_id"], "text": c["text"]} for c in challenge]
    result = claude_cli.generate(
        prompts.EXTRACTION_SYSTEM + "\n\n" + prompts.extraction_prompt(reports),
        prompts.extraction_batch_schema(),
        model="sonnet",
    )
    texts = {c["job_id"]: c["text"] for c in challenge}
    rows = [
        extract.row_for(item, texts[item["job_id"]], None)
        for item in result.get("items", [])
        if item.get("job_id") in texts
    ]
    return sorted(rows, key=lambda r: r["job_id"])


def _write(path: Path, rows: list[dict]) -> None:
    path.write_bytes((json.dumps(rows, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))


def main() -> int:
    personas = json.loads((BUILD / "personas.json").read_text("utf-8"))
    with (BUILD / "communities.csv").open(encoding="utf-8", newline="") as f:
        communities = [{**r, "is_remote": r["is_remote"] == "True"} for r in csv.DictReader(f)]
    challenge_path = BUILD / "challenge.json"
    if not challenge_path.exists():
        items = tuples(personas, communities)
        challenge = write_texts(items, {p["persona_id"]: p for p in personas})
        for item in challenge:
            item.pop("setting")
        _write(challenge_path, challenge)
        print(f"challenge: {len(challenge)} of {len(items)} texts written", file=sys.stderr)
    challenge = json.loads(challenge_path.read_text("utf-8"))
    rows_path = BUILD / "challenge_extraction.json"
    if not rows_path.exists():
        _write(rows_path, extract_rows(challenge))
    print(f"challenge: {len(json.loads(rows_path.read_text('utf-8')))} rows", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
