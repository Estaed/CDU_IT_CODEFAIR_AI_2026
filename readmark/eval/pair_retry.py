"""Reproducible Task-30 retry measurements, without model calls or case-specific gate rules."""

import json
import hashlib
import struct
import subprocess
from pathlib import Path

from readmark import ROOT
from readmark.eval.cases import ALL_CASES, page_coverage, rate, trap_touches
from readmark.eval.pair_updates import CASES, EVIDENCE, load, numeric_changes, save
from readmark.ingest import case_path


def working_inventory() -> dict:
    """Content hashes without invoking a Git command; rg observes the repository ignores."""
    paths = subprocess.check_output(["rg", "--files", "--hidden"], cwd=ROOT, text=True).splitlines()
    return {Path(p).as_posix(): hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
            for p in paths if p != ".git" and not p.startswith((".git/", ".git\\"))}


def index_blobs() -> dict:
    """Read the unchanged baseline index to check ownership and snapshot provenance."""
    marker = (ROOT / ".git").read_text(encoding="utf-8").strip()
    gitdir = Path(marker.removeprefix("gitdir: "))
    data = (gitdir / "index").read_bytes()
    magic, version, count = struct.unpack_from(">4sII", data)
    assert magic == b"DIRC" and version in (2, 3), "Unsupported index; report instead of guessing."
    offset, entries = 12, {}
    for _ in range(count):
        start = offset
        blob = data[offset + 40:offset + 60].hex()
        flags = struct.unpack_from(">H", data, offset + 60)[0]
        offset += 62 + (2 if flags & 0x4000 else 0)
        end = data.index(b"\0", offset)
        name = data[offset:end].decode("utf-8")
        entries[name] = blob
        offset = start + ((end + 1 - start + 7) // 8) * 8
    return entries


def verify_baseline() -> None:
    entries = index_blobs()
    checked = 0
    for folder in (EVIDENCE / "before").iterdir():
        for snapshot in folder.glob("*.json"):
            name = f"runs/{folder.name}/{snapshot.name}"
            if name not in entries:
                continue
            raw = snapshot.read_bytes()
            digest = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
            assert digest == entries[name], f"Baseline snapshot differs from index: {name}"
            checked += 1
    print(f"BASE_SHA snapshot provenance: {checked} indexed JSON stages match byte for byte.")


def reading_measurement(cid: str, folder: Path) -> dict:
    view = load(folder / "view.json")
    if cid == "stub":
        gold, facts = [], []
    else:
        import csv

        gold = load(case_path(cid).with_name("gold.json"))["required_reading"]
        with case_path(cid).with_name("facts.csv").open(encoding="utf-8", newline="") as stream:
            facts = list(csv.DictReader(stream))
    passages = {p["passage_id"]: p for p in load(folder / "passages.json")["case_passages"]}
    traps = trap_touches(view, facts, passages)
    return {"pages": list(dict.fromkeys(i["passage_id"].split(":")[-2]
                                       for i in view["required_reading"])),
            "gold": gold, "coverage": page_coverage(view["required_reading"], gold),
            "traps": rate(sum(t["touched"] for t in traps), len(traps))}


def measurements() -> dict:
    rows = {}
    for cid in CASES:
        rows[cid] = {label: reading_measurement(cid, folder / cid) for label, folder in (
            ("base", EVIDENCE / "before"), ("first_attempt", EVIDENCE / "first-attempt"),
            ("retry", ROOT / "runs"))}
        if cid in ALL_CASES:
            before, after = rows[cid]["base"], rows[cid]["retry"]
            assert after["coverage"]["count"] >= before["coverage"]["count"], cid
            assert after["traps"]["count"] >= before["traps"]["count"], cid
    return rows


def report() -> None:
    verify_baseline()
    rows = measurements()
    old = load(EVIDENCE / "before/eval/summary.json")
    first = load(EVIDENCE / "first-attempt/eval/summary.json")
    final = load(ROOT / "runs/eval/summary.json")
    changes = list(numeric_changes(old, final))
    save(EVIDENCE / "retry.json", {"cases": rows, "evaluation_number_changes": changes,
                                 "first_attempt_to_retry": list(numeric_changes(first, final))})
    lines = ["## Retry", "",
             "The first attempt was rejected for reading coverage. The sections above record "
             "that attempt; this section supersedes its gate, reading and verification results.", "",
             "### Rule", "",
             "A document page takes one slot, regardless of flagged paragraph count. Its "
             "navigation target remains passage_id; passage_ids and passages preserve every "
             "flagged/cited paragraph and its own reasons, claims and clauses. Grouping never "
             "borrows another paragraph's clause for trap scoring. Page 1 in two documents "
             "takes two slots. Schema version 4 binds this shape.", "",
             "Updated pairs form a connected component under one clause when they share a "
             "page, including different paragraphs on that page. The most confident pair "
             "supplies the two primary pages; ties use numeric page/paragraph order. Other "
             "pages of that record chain rank after independent failures and scan leads. "
             "An independently failed claim or contradiction retains its existing priority. "
             "This preserves a strong before/after comparison without filling the cap with "
             "intermediate records. All pairs remain on screen and still recheck claims.", "",
             "Unused slots after flags and scan leads retain cited case evidence, ordered by "
             "the number of distinct claims using the page, then checklist and citation order. "
             "A neutral cited reading reason preserves the sources of supported claims even "
             "when a former false contradiction becomes agree. It creates no new claim or "
             "question warning, changes no outcome and adds no screen section. Policy-only "
             "citations do not fill these slots. This is why E-02's notice remains required "
             "without pretending the uncertain extension contradicts it. No case id, page "
             "number, document title, gold label or new threshold enters the gate rule.", "",
             "The screen and server accept a timed opening of any known paragraph on the "
             "required page. The receipt retains only the passage actually viewed and its "
             "actual duration; it does not claim all paragraphs were read. Hidden/comparison "
             "windows retain the existing pause rule.", "",
             "PAIR_QUESTION, PAIR_VERDICTS and CAP are unchanged in the retry. The measured "
             "controls remain updated 2/2 (n=2), planted contradict 4/4 (n=4) and agree "
             "12/12 (n=12). No new model responses were requested.", "",
             "### Required page lists", "",
             "Bold marks gold pages. Baseline is BASE_SHA "
             "52d250dd5b4d9d0b3558e727bcb1fdb23f6b6831; the frozen before stages are preserved. "
             "First attempt and retry snapshots are separate. Duplicate page entries are "
             "collapsed here; first-attempt A-0142 had two paragraphs on page 23.", "",
             "| Case | BASE_SHA → first attempt → retry | Gold coverage | Trap touches |",
             "|---|---|---|---|"]
    for cid, stages in rows.items():
        lists = []
        coverage, traps = [], []
        for stage in stages.values():
            lists.append(", ".join(f"**{p}**" if p in stage["gold"] else p for p in stage["pages"]))
            coverage.append(str(stage["coverage"]["count"]))
            traps.append(str(stage["traps"]["count"]))
        n = stages["base"]["coverage"]["n"]
        tn = stages["base"]["traps"]["n"]
        lines.append(f"| {cid} | {' → '.join(lists)} | {' → '.join(coverage)} (n={n}) | "
                     f"{' → '.join(traps)} (n={tn}) |")
    lines += ["", "Every case meets or exceeds its baseline gold coverage and trap-touch "
              "count (n=5 scored cases). A-0142 still requires pages 8 and 23 and retains "
              "gold pages 51 and 58. H-01 retains the baseline count but page 14 replaces "
              "page 3 in required reading; page 3's historical payslip remains suggested "
              "with its income update comparisons and citations. H-01 remains after changes, "
              "not held-out; its original evaluation marker is untouched.", "",
              "### Every evaluation number changed from BASE_SHA to retry", "",
              "Each row is one numeric leaf; n is the nearest explicit denominator. "
              "Historical baselines remain unchanged. Machine-readable first-attempt → retry "
              "changes are also in runs/eval/pair_updates/retry.json.", "",
              "| Summary path | BASE_SHA → retry | n before → after | Cause |",
              "|---|---|---|---|"]
    for row in changes:
        path = row["path"]
        cause = ("First-attempt Jev response additions; retry made no model calls."
                 if any(s in path for s in ("live_responses", "response_cache")) else
                 "Page grouping, shared update chains and neutral cited evidence; no verdict change."
                 if any(s in path for s in ("gold_page", "required_reading", "trap", "new_gold", "lost_gold")) else
                 "First-attempt pair classification and opposing-claim rechecks retained; no retry wording change.")
        lines.append(f"| `{path}` | {row['before']} → {row['after']} | "
                     f"{row['before_n']} → {row['after_n']} | {cause} |")
    lines += ["", "### Retry assertions and verification", "",
              "- test_pipeline.py replaces the assumption that only a failed claim's source "
              "is required: that source must rank first, and all added entries must carry "
              "only the neutral cited reason. Failed-check and verified-quote assertions remain.",
              "- test_screen.py expects the server's required-page wording instead of "
              "required-passage wording; navigation order, timed openings and record coverage "
              "are asserted by page while every individual highlight remains checked. The "
              "supported-claim fixture ignores the neutral cited reason when identifying its "
              "sole checker flag. Existing timing, highlight and lock assertions remain.",
              "- test_generate_list.py supplies timed required-page openings when signing "
              "the supported uploaded case; unused slots now retain its cited page. The "
              "actual signature endpoint and both export assertions remain.",
              "- test_reading_pages.py adds page membership/reason preservation, distinct "
              "documents, transitive update-chain pressure, neutral fallback, server opening "
              "another paragraph and per-case baseline coverage/trap regression checks.",
              "- No acceptance assertion was removed. Gate results, screenshot inspection "
              "and commit hand-off are recorded below after the final checks.", ""]
    destination = ROOT / "reports/2026-10-04-pair-updates.md"
    previous = destination.read_text(encoding="utf-8").split("\n## Retry\n", 1)[0]
    destination.write_text(previous.rstrip() + "\n\n" + "\n".join(lines),
                           encoding="utf-8", newline="\n")
    print(json.dumps({cid: {k: {"coverage": s["coverage"], "traps": s["traps"]}
                           for k, s in stages.items()} for cid, stages in rows.items()}, indent=2))
    print(f"Retry report: {len(changes)} changed numerical leaves.")


if __name__ == "__main__":
    report()
