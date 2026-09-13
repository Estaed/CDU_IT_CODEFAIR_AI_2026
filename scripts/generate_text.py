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
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # the package is not installed into venv; scripts run from source

from fair_turn.core.wording import READING_LEVEL, check  # noqa: E402
from fair_turn.llm import claude_cli, prompts  # noqa: E402

BUILD = ROOT / "data" / "build"
RAW_DETAIL = ROOT / "data" / "raw" / "bushtel_community_detail_2026-09-12.json"
BATCH_SIZE = 20
MAX_ROUNDS = 3  # passes over the still-missing labels before giving up
WORKERS = 4  # concurrent CLI calls; each is a separate `claude -p` process


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
    # Reading level is a ceiling for text the tool writes to tenants (PRD section 7), not
    # for the tenant's own words; only the deficit terms are rejected here.
    if problems := [t for t in check(text) if t != READING_LEVEL]:
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
    workers: int = WORKERS,
    timeout: float = 600,
) -> dict:
    """Generate every missing report; returns
    ``{"calls", "failed_calls", "written", "rejected", "missing"}``. A failed or timed-out
    call is logged and counted, and its labels stay missing for the next round."""
    # Step 1: load the labels to write text for, plus the personas and community rows a
    # prompt needs to describe the setting without naming the real place.
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

    # Step 2: resume from whatever reports.json already has, so an interrupted run
    # continues instead of re-spending calls on labels that already have text.
    out_path = build_dir / "reports.json"
    reports = json.loads(out_path.read_text("utf-8")) if out_path.exists() else []
    have = {r["job_id"] for r in reports}
    calls, failed_calls, written, rejected = 0, 0, 0, []
    started = time.monotonic()

    def call(batch: list[dict]) -> dict | None:
        try:
            return claude_cli.generate(
                prompts.GENERATION_SYSTEM + "\n\n" + prompts.generation_prompt(batch, personas),
                prompts.GENERATION_SCHEMA,
                model=model,
                executable=executable,
                timeout=timeout,
            )
        except Exception as exc:
            reason = " ".join(str(exc).split())[:200]
            print(
                f"generate_text: batch from {batch[0]['job_id']} failed: {reason}",
                file=sys.stderr,
            )
            return None

    # Step 3: batch and call, for up to MAX_ROUNDS passes — a later round only retries the
    # labels a prior round's rejections or failures left missing.
    for _ in range(MAX_ROUNDS):
        missing = [label for label in labels if label["job_id"] not in have]
        if not missing:
            break
        batches = [missing[i : i + batch_size] for i in range(0, len(missing), batch_size)]
        if limit is not None:
            batches = batches[: max(limit - calls, 0)]
        if not batches:
            break
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(call, batch): batch for batch in batches}
            for future in as_completed(futures):  # a slow call never holds back finished ones
                batch, result = futures[future], future.result()
                calls += 1
                if result is None:
                    failed_calls += 1
                    continue
                # Step 4: validate each returned item (length, wording, no real names) and
                # keep only what passes; a rejected item's job_id stays missing and is
                # retried next round.
                wanted = {label["job_id"] for label in batch}
                for item in result.get("reports", []):
                    reason = validate(item, wanted - have, names)
                    if reason:
                        rejected.append({"job_id": item.get("job_id"), "reason": reason})
                        continue
                    reports.append({"job_id": item["job_id"], "text": item["text"]})
                    have.add(item["job_id"])
                    written += 1
                # Step 5: write the artefact after every batch so an interrupted run loses
                # at most one batch of work, not the whole call.
                reports.sort(key=lambda r: r["job_id"])
                out_path.write_bytes(
                    (json.dumps(reports, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
                )
                left = len(labels) - len(have)
                elapsed = time.monotonic() - started
                print(
                    f"generate_text: call {calls}, {written} written, {left} missing, "
                    f"{elapsed:.0f}s",
                    file=sys.stderr,
                )
    return {
        "calls": calls,
        "failed_calls": failed_calls,
        "written": written,
        "rejected": rejected,
        "missing": len(labels) - len(have),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", default="opus")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--limit", type=int, help="stop after this many CLI calls")
    parser.add_argument("--workers", type=int, default=WORKERS)
    args = parser.parse_args()
    # Step 6: run the batched generation, then report the summary and exit non-zero only if
    # labels are still missing after MAX_ROUNDS — a caller (otopilot, a human) can retry.
    summary = run(
        model=args.model, batch_size=args.batch_size, limit=args.limit, workers=args.workers
    )
    print(json.dumps({k: v for k, v in summary.items() if k != "rejected"}), file=sys.stderr)
    if summary["rejected"]:
        print(f"rejected {len(summary['rejected'])}: {summary['rejected'][:10]}", file=sys.stderr)
    return 0 if summary["missing"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
