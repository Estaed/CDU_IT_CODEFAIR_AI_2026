"""Write the tenant's words for every label: data/build/reports.json.

Run from the repo root with a logged-in ``claude`` (spends the Claude subscription window;
check ``limit`` first). Resumable: labels that already have a report are skipped and the
file is written after every batch, so an interrupted run continues where it stopped.

    venv/Scripts/python scripts/generate_text.py              # everything still missing
    venv/Scripts/python scripts/generate_text.py --limit 1    # one batch, to read the output

Third step of the build pipeline (after build_labels.py). Needs no network beyond the CLI.
"""

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # the package is not installed into venv; scripts run from source

from fair_turn.core.wording import check  # noqa: E402
from fair_turn.llm import claude_cli, prompts  # noqa: E402

BUILD = ROOT / "data" / "build"
RAW_DETAIL = ROOT / "data" / "raw" / "bushtel_community_detail_2026-09-12.json"
BATCH_SIZE = 20
MAX_ROUNDS = 3  # passes over the still-missing labels before giving up


def real_names(detail_path: Path = RAW_DETAIL) -> list[str]:
    names: set[str] = set()
    for r in json.loads(detail_path.read_text("utf-8")):
        if r["CommunityTypeName"] in ("Major", "Minor"):
            names.add(r["Name"])
            names.add(r["DefaultName"])
            names.update(a for a in r.get("AliasNamesString", "").split(",") if a.strip())
    return sorted(n for n in names if n)


def setting_for(community: dict) -> str:
    """What the tenant may say about where they are, without naming it."""
    if not community["is_remote"]:
        return "a town house, sealed roads, crews based nearby"
    access = {
        "sealed": "sealed road to the regional centre",
        "unsealed": "unsealed road that can close in the wet season",
        "barge_or_air": "no road; supplies and crews come by barge or plane",
    }[community["road_access"]]
    return (
        f"a remote community, {access}, about {round(float(community['km_to_base']))} km "
        "from the crew base"
    )


def validate(item: dict, wanted: set[str], names: list[str]) -> str | None:
    """Reason the item is rejected, or None."""
    text = item.get("text", "")
    if item.get("job_id") not in wanted:
        return "unknown or repeated job_id"
    if not prompts.REPORT_MIN_CHARS <= len(text) <= prompts.REPORT_MAX_CHARS:
        return f"length {len(text)}"
    if problems := check(text):
        return "wording: " + ", ".join(problems)
    for name in names:
        if re.search(rf"(?<![A-Za-z]){re.escape(name)}(?![A-Za-z])", text, re.I):
            return "real community name"
    return None


def run(
    build_dir: Path = BUILD,
    executable: list[str] | None = None,
    model: str = "opus",
    batch_size: int = BATCH_SIZE,
    limit: int | None = None,
    names: list[str] | None = None,
) -> dict:
    """Generate every missing report; returns ``{"calls": n, "written": n, "rejected": [...]}``."""
    labels = json.loads((build_dir / "labels.json").read_text("utf-8"))
    personas = {
        p["persona_id"]: p for p in json.loads((build_dir / "personas.json").read_text("utf-8"))
    }
    communities = {}
    with (build_dir / "communities.csv").open(encoding="utf-8", newline="") as f:
        for record in csv.DictReader(f):
            record["is_remote"] = record["is_remote"] == "True"
            communities[record["community_id"]] = record
    for label in labels:
        label["setting"] = setting_for(communities[label["community_id"]])
    names = real_names() if names is None else names

    out_path = build_dir / "reports.json"
    reports = json.loads(out_path.read_text("utf-8")) if out_path.exists() else []
    have = {r["job_id"] for r in reports}
    calls, written, rejected = 0, 0, []
    started = time.monotonic()
    for _ in range(MAX_ROUNDS):
        missing = [label for label in labels if label["job_id"] not in have]
        if not missing:
            break
        for start in range(0, len(missing), batch_size):
            if limit is not None and calls >= limit:
                break
            batch = missing[start : start + batch_size]
            wanted = {label["job_id"] for label in batch}
            result = claude_cli.generate(
                prompts.GENERATION_SYSTEM + "\n\n" + prompts.generation_prompt(batch, personas),
                prompts.GENERATION_SCHEMA,
                model=model,
                executable=executable,
            )
            calls += 1
            for item in result.get("reports", []):
                reason = validate(item, wanted - have, names)
                if reason:
                    rejected.append({"job_id": item.get("job_id"), "reason": reason})
                    continue
                reports.append({"job_id": item["job_id"], "text": item["text"]})
                have.add(item["job_id"])
                written += 1
            reports.sort(key=lambda r: r["job_id"])
            out_path.write_bytes(
                (json.dumps(reports, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
            )
            left = len(labels) - len(have)
            elapsed = time.monotonic() - started
            print(
                f"generate_text: call {calls}, {written} written, {left} missing, {elapsed:.0f}s",
                file=sys.stderr,
            )
        if limit is not None and calls >= limit:
            break
    return {
        "calls": calls,
        "written": written,
        "rejected": rejected,
        "missing": len(labels) - len(have),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", default="opus")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--limit", type=int, help="stop after this many CLI calls")
    args = parser.parse_args()
    summary = run(model=args.model, batch_size=args.batch_size, limit=args.limit)
    print(json.dumps({k: v for k, v in summary.items() if k != "rejected"}), file=sys.stderr)
    if summary["rejected"]:
        print(f"rejected {len(summary['rejected'])}: {summary['rejected'][:10]}", file=sys.stderr)
    return 0 if summary["missing"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
