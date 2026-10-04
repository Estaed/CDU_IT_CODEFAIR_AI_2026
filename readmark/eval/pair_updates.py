"""Task-30 measurement: frozen controls, response-only caches and before/after evidence.

Run with ``python -m readmark.eval.pair_updates snapshot|controls``. External W-01 pages
are read only at call time; neither their text nor a request is written into this repository.
"""

import argparse
import json
import shutil
from unittest.mock import patch
from pathlib import Path

from readmark import ROOT, dumps
from readmark.cache import Cache
from readmark.ingest import case_path
from readmark.jev import JevChecker

CASES = ("A-0142", "E-01", "E-02", "E-03", "H-01", "stub")
EVIDENCE = ROOT / "runs/eval/pair_updates"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(data), encoding="utf-8", newline="\n")


ORIGINAL_CACHE_CALL = Cache.call


def cached_claude(cache, kind, request, live):
    """Every Claude stage must replay; only missing Jev requests may reach the network."""
    if not kind.startswith("jev"):
        return ORIGINAL_CACHE_CALL(Cache(cache.directory, replay=True), kind, request, live)
    return ORIGINAL_CACHE_CALL(cache, kind, request, live)


def snapshot():
    if (EVIDENCE / "before").exists():
        raise RuntimeError("The before snapshot is already frozen.")
    for cid in (*CASES, "eval"):
        for path in (ROOT / "runs" / cid).glob("*.json"):
            dest = EVIDENCE / "before" / cid / path.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)
    controls = []
    for cid in CASES:
        view = load(EVIDENCE / "before" / cid / "view.json")
        for cl in view["clauses"]:
            for pair in cl["contradictions"]:
                if cid in ("E-01", "E-02", "E-03", "H-01") or cl["clause_id"] == "elig-debts":
                    controls.append({"case": cid, "clause_id": cl["clause_id"],
                                     "a": pair["a"], "b": pair["b"],
                                     "expected": "updated" if cid in ("A-0142", "stub")
                                     else "contradict"})
    agrees = []
    for cid in CASES:
        for pair in load(EVIDENCE / "before" / cid / "pairs.json")["verdicts"]:
            if pair["verdict"] == "agree":
                agrees.append({"case": cid, "clause_id": pair["clause_id"],
                               "a": pair["a"], "b": pair["b"], "expected": "agree"})
    # Spread the fallback across cases and topics rather than taking one case's first dozen.
    chosen = []
    while len(chosen) < 12:
        for cid in CASES:
            candidates = [p for p in agrees if p["case"] == cid and p not in chosen]
            if candidates and len(chosen) < 12:
                chosen.append(candidates[0])
    controls.extend(chosen)
    save(EVIDENCE / "controls.json", controls)
    print("Frozen controls:")
    for p in controls:
        print(f"{p['case']} {p['clause_id']} {p['a']} <-> {p['b']} expected={p['expected']}")
    for cid in ("E-01", "E-02", "E-03", "H-01"):
        print(f"\n{cid} gold rationales:")
        print(dumps(load(case_path(cid).with_name("gold.json"))["rationale"]))


def jobs(external: Path):
    for p in load(EVIDENCE / "controls.json"):
        view = load(EVIDENCE / "before" / p["case"] / "view.json")
        passages = {x["passage_id"]: x for x in
                    load(EVIDENCE / "before" / p["case"] / "passages.json")["case_passages"]}
        cl = next(c for c in view["clauses"] if c["clause_id"] == p["clause_id"])
        yield p, {"clause": cl, "a": passages[p["a"]], "b": passages[p["b"]]}
    definitions = [
        ("T1", "Child's exposure to the domestic incident", "Whether the child was present",
         ("03-candidate-personal-statement.txt", 4, "2026-09-28", "statement"),
         ("10-police-dv-incident-narrative.txt", 1, "2021-03-16", "police narrative")),
        ("T2", "Program completion", "The date the program was completed",
         ("12-program-completion-certificate.txt", 1, "2022-04-04", "certificate"),
         ("13-facilitator-exit-report.txt", 1, "2022-04-08", "facilitator report")),
    ]
    for trap, title, decides, *docs in definitions:
        passages = []
        for filename, page, date, kind in docs:
            text = (external / filename).read_text(encoding="utf-8").split("\f")[page - 1]
            passages.append({"passage_id": f"W-01:{filename[:2]}-p{page}", "page": page,
                             "k": 1, "doc_date": date, "doc_type": kind,
                             "doc_title": text.splitlines()[0], "text": text})
        p = {"case": "W-01", "clause_id": trap, "a": passages[0]["passage_id"],
             "b": passages[1]["passage_id"], "expected": "contradict"}
        yield p, {"clause": {"clause_id": trap, "title": title, "decides": decides},
                  "a": passages[0], "b": passages[1]}


def controls(external: Path, attempt: str):
    from readmark.jev import PAIR_QUESTION

    rows = []
    for p, job in jobs(external):
        # Same caches as the production pipeline, so selected controls are not called twice.
        directory = (ROOT / "runs" / p["case"] / "cache" if p["case"] != "W-01"
                     else EVIDENCE / "cache")
        result = JevChecker(Cache(directory, replay=False)).compare([job])[0]
        rows.append({**p, **result})
        print(f"{p['case']} {p['a']} <-> {p['b']}: {result['verdict']} "
              f"expected={p['expected']} {result['probabilities']}", flush=True)
    save(EVIDENCE / f"{attempt}.json", {"wording": PAIR_QUESTION, "results": rows})
    for expected in ("updated", "contradict", "agree"):
        subset = [p for p in rows if p["expected"] == expected]
        print(f"{expected}: {sum(p['verdict'] == expected for p in subset)}/{len(subset)}")


def numeric_changes(before, after, path="", before_n=None, after_n=None):
    """Every numeric leaf, with its nearest explicit denominator; do not omit unchanged n."""
    if isinstance(before, dict) or isinstance(after, dict):
        old = before if isinstance(before, dict) else {}
        new = after if isinstance(after, dict) else {}
        for key in sorted(old.keys() | new.keys()):
            yield from numeric_changes(old.get(key), new.get(key), f"{path}.{key}",
                                       old.get("n", before_n), new.get("n", after_n))
    elif isinstance(before, list) or isinstance(after, list):
        old = before if isinstance(before, list) else []
        new = after if isinstance(after, list) else []
        for i in range(max(len(old), len(new))):
            yield from numeric_changes(old[i] if i < len(old) else None,
                                       new[i] if i < len(new) else None, f"{path}[{i}]",
                                       before_n, after_n)
    elif before != after and any(isinstance(x, (int, float)) and not isinstance(x, bool)
                                 for x in (before, after)):
        yield {"path": path.lstrip("."), "before": before, "after": after,
               "before_n": before_n, "after_n": after_n}


def report():
    attempts = [load(p) for p in sorted(EVIDENCE.glob("wording-*.json"))]
    lines = ["# Task-30: record updates and disagreements — 4 October 2026", "",
             "## Result", "",
             "Selected wording 3. Both ledger controls are `updated` (2/2, n=2); all "
             "planted incompatible accounts stay `contradict` (4/4, n=4, comprising two "
             "H-01 pairs and W-01 T1/T2); agree controls stay `agree` (12/12, n=12). "
             "No planted contradiction is lost. The old `contradict` label covered genuine "
             "disagreements, updates and false alarms; retaining every old label would "
             "defeat this distinction.", "",
             "All six case pipelines were rebuilt with live Jev pair requests and cached "
             "writer/auditor responses (n=6 cases). Missing non-Jev requests explicitly "
             "raise ReplayMiss. New pair leads introduced new opposing-passage checks; "
             "these were measured live with Jev, including mutation rechecks. No Claude "
             "calls occurred (n=0). Older response files are retained unchanged.", "",
             "H-01 remains **after changes, not held-out**. Its original evaluation marker, "
             "first-run view digest, implementation pin and first-run numbers remain frozen. "
             "All wordings were tested on the same controls across cases, including W-01; "
             "none was tuned on H-01 alone. New code and the new view digest are disclosed "
             "by `heldout_discipline`.", "",
             "## Control provenance and interpretation", "",
             "The original wave-2 control identities were not found in "
             "`reports/otopilot-2026-10-03-wave2-report.md`, `tests/` or `readmark/`. "
             "The permitted fallback uses 12 committed agree pairs, spread across all "
             "six cases (n=12). Identities and probabilities are listed below.", "",
             "The 13 committed E/H contradiction pairs were read against their actual "
             "passages and each case's gold rationale (n=13):", "",
             "- E-01 p2:1–p10:4: a closed tenancy without a specified end reason and an "
             "archive response without a later closure agreement can both be true. "
             "The planted breach is on p7, per gold; this pair is an existing false alarm.",
             "- E-02 p2:1/p1:1/p1:3–p9:1 (n=3): an expected tenancy end and an unconfirmed "
             "possible extension do not assert incompatible facts or an actual extension. "
             "Gold leaves urgent need undecided. These are existing false alarms.",
             "- E-03 p7:1–p1:3, p7:4–p4:2 and p7:1–p4:2 (n=3): ownership and unsafe "
             "access can coexist; gold explicitly requires weighing both. These are false "
             "alarms. Wording 3 still calls p7:4–p4:2 contradictory (0.39; n=1 pair); "
             "this residual false alarm is reported, not silently corrected.",
             "- E-03 p8:1–p12:1: a short booking was extended from 12 July through 24 July. "
             "This is an actual update, consistent with gold (n=1 pair).",
             "- H-01 p5:2–p3:2, p5:1–p17:4 and p5:2–p17:4 (n=3): February pay records "
             "precede the July end of that employment and irregular current work. Gold "
             "names the stale income evidence; these are updates, not incompatible histories.",
             "- H-01 p2:3–p17:3 and p12:1–p2:3 (n=2): the application denies any previous "
             "social tenancy while the declaration and closure record establish one. "
             "These are incompatible accounts of the same past fact.", "",
             "W-01 T1 (`03-p4`–`10-p1`) and T2 (`12-p1`–`13-p1`) come from the external "
             "answer key and full relevant pages (n=2). T1 disagrees about the child's "
             "presence at the same incident; T2 gives incompatible completion/attendance "
             "dates without a recorded correction. Document dates are the source dates, "
             "not the later copy date. Source text is never copied into this repo; only "
             "response caches and control results are stored.", "",
             "## Wordings measured", ""]
    planted = {frozenset(("H-01:p2:3", "H-01:p17:3")),
               frozenset(("H-01:p12:1", "H-01:p2:3")),
               frozenset(("W-01:03-p4", "W-01:10-p1")),
               frozenset(("W-01:12-p1", "W-01:13-p1"))}
    for i, attempt in enumerate(attempts, 1):
        rows = attempt["results"]
        subset = [r for r in rows if frozenset((r["a"], r["b"])) in planted]
        lines += [f"### Wording {i}{' — selected' if i == 3 else ''}", "",
                  "```json", json.dumps(attempt["wording"], indent=2), "```", "",
                  f"Planted contradict hits: {sum(r['verdict'] == 'contradict' for r in subset)}"
                  f"/{len(subset)} (n={len(subset)})."]
        for expected in ("updated", "contradict", "agree"):
            subset = [r for r in rows if r["expected"] == expected]
            label = "Contradict controls (13 committed labels plus 2 W-01 key pairs)" if expected == "contradict" else expected
            lines.append(f"{label}: {sum(r['verdict'] == expected for r in subset)}/{len(subset)} "
                         f"(n={len(subset)}).")
        lines += ["", "| Control | Baseline expectation | Answer | Probabilities (n=1 pair) |",
                  "|---|---|---|---|"]
        lines += [f"| {r['case']} {r['a']} ↔ {r['b']} | {r['expected']} | {r['verdict']} | "
                  f"`{json.dumps(r['probabilities'], sort_keys=True)}` |" for r in rows]
        lines.append("")
    lines += ["Wording 1 lost H-01 p12:1–p2:3 (`agree`, 0.56; n=1). Wording 2 recovered it "
              "by explicitly checking categorical statements about past events across all "
              "cases. Wording 3 additionally clarifies that uncertainty and missing "
              "confirmation are not actual changes; it retains all four planted conflicts "
              "and removes several legacy false alarms. E-01's false alarm remains "
              "(`contradict`, 0.62; n=1). These residual errors remain visible to the officer.", "",
              "W-01 final: T1 `contradict` (1.00), T2 `contradict` (0.63), n=2 pairs.", "",
              "## Every production pair whose verdict changed", "",
              "Probability maps list every class; the old question had no `updated` class. "
              "Each row has n=1 compared pair.", "",
              "| Case / clause / pair | Before → after | Before probabilities | After probabilities |",
              "|---|---|---|---|"]
    changes = []
    for cid in CASES:
        old = load(EVIDENCE / "before" / cid / "pairs.json")["verdicts"]
        new = load(ROOT / "runs" / cid / "pairs.json")["verdicts"]
        index = {(p["clause_id"], p["a"], p["b"]): p for p in old}
        for p in new:
            prior = index[(p["clause_id"], p["a"], p["b"])]
            if prior["verdict"] != p["verdict"]:
                changes.append({"case": cid, "before": prior, "after": p})
                lines.append(f"| {cid} / {p['clause_id']} / {p['a']} ↔ {p['b']} | "
                             f"{prior['verdict']} → {p['verdict']} | "
                             f"`{json.dumps(prior['probabilities'], sort_keys=True)}` | "
                             f"`{json.dumps(p['probabilities'], sort_keys=True)}` |")
    lines += ["", f"Changed verdicts: {len(changes)} (n={sum(len(load(ROOT / 'runs' / cid / 'pairs.json')['verdicts']) for cid in CASES)} compared production pairs).", "",
              "## Every changed evaluation number", "",
              "The table mechanically walks every numeric leaf in `runs/eval/summary.json`. "
              "Frozen historical numbers are unchanged. Denominators shown are the nearest "
              "explicit n in each metric; `absent` denotes a field not previously present.", "",
              "| Summary path | Before → after | n before → after | Why |", "|---|---|---|---|"]
    numeric = list(numeric_changes(load(EVIDENCE / "before/eval/summary.json"),
                                   load(ROOT / "runs/eval/summary.json")))
    for row in numeric:
        path = row["path"]
        why = ("New successful Jev pair/control/recheck response files; original responses unchanged."
               if any(term in path for term in ("live_responses", "response_cache")) else
               "New A-0142 update pairs add p30 and extra ledger passages at pair severity, "
               "displacing p51/p58 from the capped gate (both remain suggested)."
               if "A-0142" in path else
               "E-02's three false contradiction pairs become agree, removing p1/p2 pair "
               "flags; the scan still flags p9/p10, so fewer gold/trap pages are flagged."
               if "E-02" in path else
               "E-03's two false property contradictions become agree/unrelated, reducing "
               "pair-only reading; p7:1's access fact loses its clause-matched flag."
               if "E-03" in path else
               "E-02 loses the false pair leads for mutations m11/m13: contradicted becomes "
               "checker_disagrees, but the direct checker still catches both; rates are unchanged.")
        lines.append(f"| `{path}` | {row['before']} → {row['after']} | "
                     f"{row['before_n']} → {row['after_n']} | {why} |")
    save(EVIDENCE / "changes.json", {"pair_changes": changes, "evaluation_number_changes": numeric})
    lines += ["", "### Reading and mutation effects", "",
              "A-0142's full required gold coverage falls 4/5 → 3/5 (n=5): the newly "
              "identified historical debt updates require p30:2 and additional p23/p24 "
              "passages. These higher-priority pair leads displace p51:5 and p58:3 from "
              "required to suggested reading. Required reading remains 8/8 (n=8 cap); "
              "all five gold pages remain flagged across required/suggested (5/5, n=5). "
              "The pair-only ablation adds p30, giving 2/5 → 3/5 gold pages (n=5). "
              "This cost follows the contract's equal priority for updates and disagreements; "
              "the gate was not retuned to improve a score.", "",
              "E-02 loses false pair flags on p1/p2; scan leads on p9/p10 remain. Required "
              "reading 8 → 6 (n=8 cap); gold coverage 3/4 → 2/4 (n=4); trap touches "
              "2/4 → 1/4 (n=4). The p2 gold lead had been supplied by a false contradiction, "
              "not independent confirmation of the applicant's expectation. Pair-only "
              "ablation required reading falls 4 → 0 (n=8 cap), and its gold coverage "
              "2/4 → 0/4 (n=4).", "",
              "E-03's property false alarms reduce pair-only reading 8 → 7 (n=8 cap); "
              "the p7:1 access-assessment trap loses its clause-matched flag, so trap "
              "touches fall 4/6 → 3/6 (n=6). E-02 mutations m11 and m13 change from "
              "contradicted to checker_disagrees after false pair flags disappear; the "
              "direct checker still catches both. Overall mutations "
              "remain caught 20/21 (n=21 errors), false alarms 1/24 (n=24 correct controls). "
              "The numerical checker fields newly included in jev_supports.mutation_changes "
              "are existing direct-check results attached to these new status-change rows.", "",
              "## Screen and verification", "",
              "Schema 3 requires `relation` on each entry of the unchanged `contradictions` "
              "list; its probability belongs to the named relation. Both relation classes "
              "enter the same gate and opposing-passage recheck path. No outcome is prefilled. "
              "The record does not name record pairs, so its format needs no change.", "",
              "The date/type classifier is removed. Warnings and comparison headings use "
              "the model's relation. Known dates only order the displayed update; missing "
              "or equal dates use 'record a change over time' and never claim a newer page. "
              "Mixed updates/disagreements preserve each comparison's own relation.", "",
              "Screenshots: `reports/screens/2026-10-04-pair-updates/debts-warning-1280.png`, "
              "`debts-comparison-1280.png`, `debts-warning-1440.png`, `debts-comparison-1440.png` "
              "(n=4 images). Tarık's eye acceptance remains pending; screenshots and browser "
              "checks do not stand in for his reading of the screen.", "",
              "### Assertions changed", "",
              "- `test_cross.py`: the January-only stale-claim test is expanded to both "
              "`contradict` and `updated`; its exact pair assertion adds `relation`. "
              "Existing required-reading and claim-recheck assertions remain.",
              "- `test_cross.py`: the committed ledger test now explicitly requires Jev's "
              "`updated` relation and both ledger passages in required reading; renamed to update.",
              "- `test_eval_cases.py`: the Task-14 whole-cache equality and zero-new-responses "
              "assertions are replaced by byte-level equality of every original response "
              "and an exact count of added responses. Live Task-30 measurements necessarily "
              "add responses; frozen baselines must remain untouched.",
              "- `test_screen.py`: the existing comparison click selects the strongest first "
              "pair, since a real run may now expose several update pairs. Its assertions "
              "that both source texts appear and viewing does not silently mark them opened remain.",
              "- `test_screen.py`: E-02's priority warning layout checks now run only when "
              "Jev supplies pairs. When the three former false alarms become agree, new "
              "assertions require no comparison links or disagreement warning. A separate "
              "mixed-relation fixture preserves multiple-comparison checks.",
              "- `test_screen.py`: the all-page-tabs flow now explicitly opens each required "
              "passage row, since two required paragraphs share page 23. Its original "
              "assertion that all eight required passages were opened remains unchanged; "
              "one page tab must not silently count both paragraphs as opened.",
              "- `test_screen.py`: the plain-notes flow's page-only row assertion now "
              "requires the paragraph when several required passages share a page, before "
              "and after opening. The existing paragraph-row test also checks after a "
              "timed opening/progress refresh. This caught a real refresh bug: the counter "
              "redrew rows without their paragraph labels. Both initial drawing and "
              "progress refresh now use the same required-row renderer.",
              "- No acceptance assertion is deleted. New fake-Jev tests cover both relations, "
              "claim rechecks, required reading, differing record types, different/equal/missing "
              "dates, unselected outcomes and comparison text. Stub replay forbids any key "
              "lookup/live model and compares every stage twice (n=2 replays).", ""]
    (ROOT / "reports/2026-10-04-pair-updates.md").write_text("\n".join(lines),
                                                           encoding="utf-8", newline="\n")
    print(f"Report: {len(changes)} pair changes, {len(numeric)} numeric changes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("snapshot", "controls", "rerun", "evaluate", "report"))
    parser.add_argument("--external", type=Path)
    parser.add_argument("--attempt", default="wording-1")
    args = parser.parse_args()
    if args.action == "snapshot":
        snapshot()
    elif args.action == "report":
        report()
    elif args.action == "rerun":
        from readmark.audit.claude import ClaudeAuditor
        from readmark.eval.discipline import EvaluationWriter
        from readmark.pipeline import run
        from readmark.writer import ClaudeWriter

        with patch.object(Cache, "call", cached_claude):
            for cid in CASES:
                cache = Cache(ROOT / "runs" / cid / "cache", replay=True)
                writer = (EvaluationWriter(cache) if cid.startswith(("E-", "H-"))
                          else ClaudeWriter(cache))
                run(cid, writer=writer, auditor=ClaudeAuditor(cache),
                    audit=cid in ("A-0142", "H-01"))
                print(f"{cid}: rebuilt with cached writer/auditor and live Jev pairs", flush=True)
    elif args.action == "evaluate":
        from readmark.eval import assemble_summary
        from readmark.eval.cases import evaluate_ablation, evaluate_cases, evaluate_mutations

        evaluate_cases(replay=True)
        # New pair leads can introduce opposing-passage checks not in the old cache.
        with patch.object(Cache, "call", cached_claude):
            evaluate_mutations(replay=False)
        evaluate_ablation()
        print(assemble_summary())
    elif args.external is None:
        parser.error("controls needs --external pointing to W-01's application folder")
    else:
        controls(args.external, args.attempt)
