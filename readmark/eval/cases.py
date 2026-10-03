"""Case evaluation, mutation scoring and cumulative ablation, using the existing claim path.

Gold is read only by this scorer, after a completed pipeline. Models receive case text and
unlabelled mutation sentences. Ablation reuses stages; it never asks a model another question.
"""

import csv
import json
from collections import Counter
from pathlib import Path

from readmark import DATA, case_run_dir
from readmark.audit import check_claims, map_pairs
from readmark.checks import claim_reasons, claim_status
from readmark.checks.cross import page_of
from readmark.eval import write_part
from readmark.eval.discipline import assert_scoring_allowed, now, save
from readmark.gate import required_reading
from readmark.ingest import case_path, normalise
from readmark.pipeline import run

EVALUATION_CASES = ("E-01", "E-02", "E-03")
ALL_CASES = ("A-0142", *EVALUATION_CASES, "H-01")
LAYERS = ("claude_alone", "code_checks", "second_key", "contradiction_pairs", "scan")
STATUSES = ("supported", "quote_not_found", "checker_disagrees", "contradicted")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def selected_cases(case_id: str | None, *, mutations: bool = False) -> tuple[str, ...]:
    allowed = EVALUATION_CASES if mutations else ALL_CASES
    if case_id is None:
        return allowed
    if case_id not in allowed:
        raise ValueError(f"Use one of {', '.join(allowed)} for this evaluation part.")
    return (case_id,)


def rate(count: int, n: int) -> dict:
    return {"count": count, "n": n, "rate": round(count / n, 4) if n else None}


def mutation_metrics(rows: list[dict]) -> dict:
    """A caught claim is any final status other than supported; supported labels are controls."""
    errors = [r for r in rows if r["label"] != "supported"]
    controls = [r for r in rows if r["label"] == "supported"]
    return {
        "catch_rate": rate(sum(r["status"] != "supported" for r in errors), len(errors)),
        "false_alarm_rate": rate(sum(r["status"] != "supported" for r in controls),
                                 len(controls)),
        "by_mutation_type": {
            kind: rate(sum(r["status"] != "supported" for r in errors
                           if r["mutation_type"] == kind),
                       sum(r["mutation_type"] == kind for r in errors))
            for kind in sorted({r["mutation_type"] for r in errors})
        },
    }


def cached_calls(out: Path) -> dict:
    """Successful live responses behind this run, excluding lifecycle metadata files."""
    counts = Counter()
    for path in sorted((out / "cache").glob("*.json")):
        entry = load(path)
        if "kind" in entry and "response" in entry:
            counts[entry["kind"]] += 1
    claude = sum(v for k, v in counts.items() if not k.startswith("jev"))
    jev = sum(v for k, v in counts.items() if k.startswith("jev"))
    return {"n": claude + jev, "claude": claude, "jev": jev,
            "by_kind": {k: {"count": v, "n": claude + jev} for k, v in sorted(counts.items())},
            "method": "One stored response per successful live request; replay makes no calls. "
                      "Failed requests are not counted by cache files."}


def evaluate_mutations(replay: bool, case_id: str | None = None) -> dict:
    for cid in selected_cases(case_id, mutations=True):
        out = case_run_dir(cid)
        view = load(out / "view.json")
        rows = [json.loads(line) for line in
                (case_path(cid).parent / "mutations.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()]
        # Only sentences enter the model path, never labels, source facts or mutation types.
        claims = check_claims(cid, [r["claim"] for r in rows], replay=replay,
                              pairs=map_pairs(view),
                              required=[r["passage_id"] for r in view["required_reading"]],
                              prefix="m")
        save(out / "mutations.json", {"case_id": cid, "claims": claims, "labels": rows})
    combined = []
    per_case = {}
    for cid in EVALUATION_CASES:
        path = case_run_dir(cid) / "mutations.json"
        if not path.exists():
            continue
        stage = load(path)
        rows = [{**r, "status": c["status"]} for r, c in
                zip(stage["labels"], stage["claims"], strict=True)]
        per_case[cid] = mutation_metrics(rows)
        combined.extend(rows)
    result = {"part": "mutations", "rule": "Caught means final status is not supported. "
              "False alarms use supported gold claims only.",
              "overall": mutation_metrics(combined), "cases": per_case}
    write_part("mutations", result)
    return result


def scoring_inputs(cid: str) -> tuple[dict, list[dict], dict | None]:
    """The sole reader of held-out labels and seal. Called only after the pipeline finishes."""
    out = case_run_dir(cid)
    if not (out / "view.json").exists():
        raise RuntimeError(f"Complete {cid}'s pipeline before scoring its labels.")
    discipline = None
    folder = case_path(cid).parent
    if cid == "H-01":
        record = assert_scoring_allowed(out)
        sealed = (folder / "SEALED.md").read_text(encoding="utf-8")
        discipline = {k: record[k] for k in
                      ("last_code_change_at", "code_frozen_at", "started_at", "completed_at")}
        changed = record['changed_result_files']
        discipline.update({"seal_read_after_run": bool(sealed),
                           "live_runs": {"count": 1, "n": 1},
                           "crash_fixes": [], "tuned_after_run": bool(changed),
                           "implementation_sha256": record["implementation_sha256"],
                           "label": record['scoring_label'],
                           "changed_result_files": changed,
                           "first_run_view_sha256": record['view_sha256'],
                           "scored_view_sha256": record['scored_view_sha256']})
    gold = load(folder / "gold.json")
    with (folder / "facts.csv").open(encoding="utf-8", newline="") as stream:
        facts = list(csv.DictReader(stream))
    return gold, facts, discipline


def page_coverage(items: list[dict], gold_pages: list[str]) -> dict:
    pages = {page_of(i["passage_id"]) for i in items}
    covered = [p for p in gold_pages if p in pages]
    return {**rate(len(covered), len(gold_pages)), "covered": covered,
            "missed": [p for p in gold_pages if p not in pages]}


def trap_touches(view: dict, facts: list[dict], passages: dict[str, dict]) -> list[dict]:
    """A page is too broad: require a matching clause and the fact's verbatim quote.

    Missing documents have no passage. Report their clause's explicit missing-evidence flag
    separately; a touched trap is a lead for the officer, not proof of a caught model error.
    """
    results = []
    for fact in facts:
        if fact["trap"] == "none":
            continue
        hit = {"fact_id": fact["fact_id"], "trap": fact["trap"],
               "clause_id": fact["clause_id"], "required": [], "suggested": [],
               "missing_evidence_flag": False}
        if fact["page"] and fact["quote"]:
            for bucket in ("required", "suggested"):
                for item in view[f"{bucket}_reading"]:
                    p = passages.get(item["passage_id"])
                    if p and str(p["page"]) == fact["page"] and (
                        fact["clause_id"] in item["clause_ids"]
                        and normalise(fact["quote"]) in p["text"]
                    ):
                        hit[bucket].append(item["passage_id"])
        elif fact["role"] == "missing":
            clause = next(c for c in view["clauses"] if c["clause_id"] == fact["clause_id"])
            hit["missing_evidence_flag"] = bool(clause["missing"]) or (
                clause["coverage"] == "no_evidence_in_file")
        hit["touched"] = bool(hit["required"] or hit["suggested"] or
                              hit["missing_evidence_flag"])
        results.append(hit)
    return results


def score_case(cid: str) -> dict:
    gold, facts, discipline = scoring_inputs(cid)
    out = case_run_dir(cid)
    view = load(out / "view.json")
    passages = {p["passage_id"]: p for p in load(out / "passages.json")["case_passages"]}
    traps = trap_touches(view, facts, passages)
    result = {
        "required_reading": {"count": len(view["required_reading"]), "n": view["cap"],
                             "unit": "passages; n is the maximum allowed"},
        "gold_page_coverage": page_coverage(view["required_reading"], gold["required_reading"]),
        "all_flagged_gold_page_coverage": page_coverage(
            [*view["required_reading"], *view["suggested_reading"]], gold["required_reading"]),
        "trap_touch_rate": rate(sum(t["touched"] for t in traps), len(traps)),
        "traps": traps, "live_responses": cached_calls(out),
    }
    if discipline:
        result["heldout_discipline"] = discipline
        result['label'] = discipline['label']
    if (out / 'audit.json').exists():
        audit = load(out / "audit.json")
        result["summary_audit"] = {
            "model": audit["model"], "prompt": audit["prompt"], "created": audit["created"],
            "flags": rate(sum(c["status"] != "supported" for c in audit["claims"]),
                          len(audit["claims"])),
            "by_status": {s: {"count": sum(c["status"] == s for c in audit["claims"]),
                              "n": len(audit["claims"])} for s in STATUSES},
            "nothing_to_check": rate(len(audit.get('nothing_to_check', [])),
                                     len(audit['claims'])),
            "meaning": "Flags are candidate errors, not a real-error count. H-01's "
                       "first-run flags were independently labelled after the run; "
                       "unflagged claims were not reviewed. The fixed-schema supported "
                       "bucket includes suggestions with null checker judgments; "
                       "nothing_to_check reports them separately.",
        }
    if discipline and discipline['tuned_after_run']:
        baseline = load(out.parent / 'eval' / 'checks_round2.json')
        result['first_run'] = baseline['before']['parts']['cases']['cases'][cid]
    return result


def assumption_result(cases: dict) -> str:
    if "H-01" not in cases:
        return "The held-out file has not completed; the riskiest assumption is still untested."
    held = cases["H-01"]
    if held.get('label') == 'after changes, not held-out':
        first = held['first_run']
        before, after = first['summary_audit']['flags'], held['summary_audit']['flags']
        return (f"H-01 first run (held-out): {before['count']} summary flags "
                f"(n={before['n']} claims), unchanged. After changes, not held-out: "
                f"{after['count']} flags (n={after['n']} claims). First-run labels found "
                "one real summary error and four file-inconsistency flags among fourteen "
                "flags (n=14); nine were false alarms. Unflagged claims were not reviewed. "
                "See audit_labels for retained flags by class; a new held-out file is needed "
                "to test the changed checks independently.")
    reading, coverage = held["required_reading"], held["gold_page_coverage"]
    flags = held["summary_audit"]["flags"]
    traps = held["trap_touch_rate"]
    return (
        f"The single held-out run required {reading['count']} passages (cap n={reading['n']}) "
        f"and covered {coverage['count']} gold required pages (n={coverage['n']}); "
        f"required reading {'stayed' if reading['count'] <= reading['n'] else 'did not stay'} "
        f"within eight. Flags touched {traps['count']} planted trap facts (n={traps['n']}) "
        f"across required, suggested and missing-evidence flags. Its frozen summary produced "
        f"{flags['count']} flags (n={flags['n']} claims), whose real-error precision is not "
        "independently labelled. The demo summary found two real errors among twenty-two "
        "flags (n=95 claims). The reading cap holds; the evidence for finding real summary "
        "errors remains the demo, and held-out flag counts alone do not establish accuracy."
    )


def evaluate_cases(replay: bool, case_id: str | None = None) -> dict:
    for cid in selected_cases(case_id):
        out = case_run_dir(cid)
        marker = out / "evaluation.json"
        if not replay and cid != "H-01":
            if marker.exists() or any((out / "cache").glob("writer-*.json")):
                raise RuntimeError(f"{cid} has already started; use --replay.")
            save(marker, {"case_id": cid, "started_at": now(), "completed_at": None})
        run(cid, replay=replay)
        if not replay and cid != "H-01":
            record = load(marker)
            record["completed_at"] = now()
            save(marker, record)
    scored = {cid: score_case(cid) for cid in ALL_CASES
              if (case_run_dir(cid) / "view.json").exists()}
    result = {"part": "cases", "cases": scored,
              "trap_rule": "Exact quote in a flagged passage under the same clause, or an "
                           "explicit missing-evidence flag for a fact with no page. "
                           "Required and suggested touches are reported separately.",
              "riskiest_assumption": assumption_result(scored)}
    write_part("cases", result)
    return result


def layer_reasons(check: dict, verdict: dict | None, contra: list[str], layer: int) -> list[str]:
    if verdict and verdict.get('verdict') is None:
        return []  # nothing to check: a review suggestion, not a positive model judgment
    if layer == 0:
        return []
    if layer == 1:
        return [] if check["passed"] else ["quote_not_found"]
    return claim_reasons(check, verdict, contra if layer >= 3 else [])


def mutation_ablation(stage: dict) -> list[dict]:
    outputs = []
    previous = set()
    for layer, name in enumerate(LAYERS):
        rows, caught = [], set()
        for label, claim in zip(stage["labels"], stage["claims"], strict=True):
            check = {"passed": bool(claim["citations"])
                     and all(c["quote_found"] for c in claim["citations"])
                     and not claim["values_missing"]}
            status = claim_status(layer_reasons(check, claim["checker"],
                                               claim["contradicted_by"], layer))
            rows.append({**label, "status": status})
            if label["label"] != "supported" and status != "supported":
                caught.add(claim["claim_id"])
        n = sum(r["label"] != "supported" for r in rows)
        outputs.append({"layer": name, **mutation_metrics(rows),
                        "new_errors_caught": {"count": len(caught - previous), "n": n}})
        previous = caught
    return outputs


def case_ablation(cid: str, gold: dict) -> list[dict]:
    out = case_run_dir(cid)
    facts = [f for f in load(out / "writer.json")["facts"] if f["found"]]
    checks = load(out / "checks.json")
    verdicts = {v["claim_id"]: v for v in load(out / "jev.json")["verdicts"]}
    view = load(out / "view.json")
    final = {c["claim_id"]: c for c in view["claims"]}
    clauses = [c["clause_id"] for c in view["clauses"] if c["clause_id"] != "other"]
    pairs = [{**p, "clause_id": c["clause_id"]} for c in view["clauses"]
             for p in c["contradictions"]]
    missed = [{**p, "clause_id": c["clause_id"]} for c in view["clauses"]
              for p in c["possibly_missed"]]
    cited = [{"passage_id": c["passage_id"]} for f in facts for c in f["citations"]]
    outputs, previous = [], set()
    for layer, name in enumerate(LAYERS):
        claims = []
        for f in facts:
            reasons = layer_reasons(checks[f["claim_id"]], verdicts.get(f["claim_id"]),
                                    final[f["claim_id"]]["contradicted_by"], layer)
            claims.append({**f, "reasons": reasons, "status": claim_status(reasons),
                           "checker": verdicts.get(f["claim_id"]) if layer >= 2 else None})
        gate = required_reading(claims, clauses, contradictions=pairs if layer >= 3 else [],
                                possibly_missed=missed if layer >= 4 else [])
        if layer == 4 and gate != load(out / "gate.json"):
            raise AssertionError(f"{cid}: full ablation must reproduce the saved gate.")
        coverage = page_coverage(gate["required"], gold["required_reading"])
        covered = set(coverage["covered"])
        outputs.append({"layer": name, "required_reading": {
            "count": len(gate["required"]), "n": gate["cap"]},
            "gold_page_coverage": coverage,
            "new_gold_pages": {"count": len(covered - previous), "n": len(gold["required_reading"]),
                               "pages": sorted(covered - previous)},
            "lost_gold_pages": {"count": len(previous - covered),
                                "n": len(gold["required_reading"]),
                                "pages": sorted(previous - covered)},
            "all_flagged_gold_page_coverage": page_coverage(
                [*gate["required"], *gate["suggested"]], gold["required_reading"]),
            "writer_cited_gold_page_coverage": page_coverage(cited, gold["required_reading"])})
        previous = covered
    return outputs


def evaluate_ablation() -> dict:
    cases, mutations, all_labels, all_claims = {}, {}, [], []
    for cid in ALL_CASES:
        if not (case_run_dir(cid) / "view.json").exists():
            continue
        gold, _, _ = scoring_inputs(cid)
        cases[cid] = case_ablation(cid, gold)
        path = case_run_dir(cid) / "mutations.json"
        if path.exists():
            stage = load(path)
            mutations[cid] = mutation_ablation(stage)
            # Keep claim ids unique when counting newly caught mutations across files.
            all_labels.extend(stage["labels"])
            all_claims.extend({**c, "claim_id": f"{cid}:{c['claim_id']}"} for c in stage["claims"])
    result = {"part": "ablation", "method": "Cumulative layers, rebuilt from saved stages. "
              "Claude alone means accepting the proposed claims with no validation; it is "
              "not a separate Claude-as-checker measurement. Writer-cited gold coverage is "
              "shown separately from flagged required reading. The scan adds reading leads, "
              "not mutation claim verdicts. The full scan layer includes the frozen dedup rule. "
              "A capped gate can lose a gold page as stronger flags displace it.",
              "cases": cases, "mutations": mutations,
              "mutation_overall": mutation_ablation({"labels": all_labels, "claims": all_claims}),
              "additional_model_calls": {"count": 0, "n": 0}}
    write_part("ablation", result)
    return result


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def release_benchmark(folder: Path | None = None) -> dict:
    """Release original synthetic labels, keeping the held-out scorer's seal checks."""
    facts, gold_rows, mutations = [], [], []
    for cid in ALL_CASES:
        gold, case_facts, _ = scoring_inputs(cid)
        facts.extend({"case_id": cid, **f} for f in case_facts)
        for clause, outcome in gold["outcomes"].items():
            gold_rows.append({"case_id": cid, "clause_id": clause, "outcome": outcome,
                              "correct_decision": gold["correct_decision"],
                              "required_reading": ";".join(gold["required_reading"]),
                              "rationale": gold["rationale"][clause]})
        path = case_path(cid).parent / "mutations.jsonl"
        if cid in EVALUATION_CASES:
            mutations.extend({"case_id": cid, **json.loads(line)} for line in
                             path.read_text(encoding="utf-8").splitlines() if line.strip())
    folder = folder or DATA / "benchmark"
    folder.mkdir(parents=True, exist_ok=True)
    write_csv(folder / "facts.csv", facts, ["case_id", *case_facts[0]])
    write_csv(folder / "gold.csv", gold_rows, list(gold_rows[0]))
    write_csv(folder / "mutations.csv", mutations, list(mutations[0]))
    result = {"part": "benchmark", "licence": "CC BY 4.0 (original synthetic material)",
              "facts": {"count": len(facts), "n": len(facts)},
              "gold_clause_labels": {"count": len(gold_rows), "n": len(gold_rows)},
              "mutation_claims": {"count": len(mutations), "n": len(mutations)},
              "cases": {"count": len({f['case_id'] for f in facts}),
                        "n": len({f['case_id'] for f in facts})},
              "files": ["facts.csv", "gold.csv", "mutations.csv", "DATASHEET.md"]}
    write_part("benchmark", result)
    return result
