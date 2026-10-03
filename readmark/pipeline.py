"""``run --case <id>``: every v1 layer once, each writing ``runs/<case>/<stage>.json``.

ingest -> checklist -> writer -> code checks -> checker -> scan -> pairs -> gate -> view.

Stage files hold case text (synthetic) and policy offsets and hashes, never policy text beyond
the clause sentences and the quotes the screen shows (contract, Run outputs).
"""

import json
import math
import re
from pathlib import Path

import jsonschema

from readmark import SCHEMAS_DIR, case_run_dir, dumps
from readmark.cache import Cache
from readmark.checklist import anchor, load_clauses
from readmark.checks import check_fact, claim_reasons, claim_status
from readmark.checks.cross import (
    PAIR_TOP,
    SCAN_THRESHOLD,
    THRESHOLD_CASE,
    THRESHOLD_HOW,
    contradicted_by,
    contradicting,
    pair_candidates,
    pairs_of,
    possibly_missed,
)
from readmark.gate import required_reading
from readmark.ingest import (
    POLICIES,
    case_passages,
    load_lock,
    passage_key,
    policy_passages,
    stage_record,
)
from readmark.jev import SCAN_BATCH, make_checker
from readmark.writer import OTHER, ClaudeWriter

VIEW_SCHEMA = SCHEMAS_DIR / "view.schema.json"
SCHEMA_VERSION = 2


def section_label(heading: str | None) -> str | None:
    """'3.4. Debts' -> '§3.4 Debts'."""
    if not heading:
        return None
    return "§" + re.sub(r"^(\d+(?:\.\d+)*)\.?\s+", r"\1 ", heading)


def source_entry(pid: str, passages: dict[str, dict]) -> dict:
    p = passages.get(pid)
    if p is None:
        return {"passage_id": pid, "exists": False, "kind": None}
    if p["source"] == "case":
        return {
            "passage_id": pid, "exists": True, "kind": "case", "page": p["page"],
            "doc_type": p["doc_type"], "doc_title": p["doc_title"], "doc_date": p["doc_date"],
            "text": p["text"],
        }
    # Policy text is not stored: the server reads it from the pinned PDF on demand.
    return {
        "passage_id": pid, "exists": True, "kind": "policy", "page": p["page"],
        "doc_title": p["doc_title"], "version": p["version"],
        "section": section_label(p["section"]), "text": None,
    }


def named_passage_ids(view: dict) -> set[str]:
    """Every passage id the view names outside ``sources``: each must have a source entry."""
    ids = set()
    for claim in view["claims"]:
        ids |= {c["passage_id"] for c in claim["citations"]}
        ids |= set(claim["contradicted_by"])
    for clause in view["clauses"]:
        if clause["policy_passage_id"]:
            ids.add(clause["policy_passage_id"])
        for pair in clause["contradictions"]:
            ids |= {pair["a"], pair["b"]}
        ids |= {m["passage_id"] for m in clause["possibly_missed"]}
    for item in [*view["required_reading"], *view["suggested_reading"]]:
        ids.add(item["passage_id"])
    return ids


def build_view(case_meta: dict, case: list[dict], policy: list[dict], clauses: list[dict],
               lock: dict, facts: list[dict], checks: dict, verdicts: dict, gate: dict,
               models: dict, cross: dict) -> dict:
    """``cross`` holds the cross-passage results: ``contradictions`` and ``possibly_missed``
    per clause, and ``contradicted_by`` and ``reasons`` per claim."""
    passages = {p["passage_id"]: p for p in [*case, *policy]}
    claims, missing = [], {}
    for fact in facts:
        if not fact["found"]:
            missing.setdefault(fact["clause_id"], []).append(
                {"claim_id": fact["claim_id"], "statement": fact["claim"]}
            )
            continue
        check = checks[fact["claim_id"]]
        claims.append(
            {
                "claim_id": fact["claim_id"],
                "clause_id": fact["clause_id"],
                "claim": fact["claim"],
                "citations": [
                    {**r, "quote": c["quote"]}
                    for c, r in zip(fact["citations"], check["citations"], strict=True)
                ],
                "values_missing": check["values_missing"],
                "checker": verdicts.get(fact["claim_id"]),
                "contradicted_by": cross["contradicted_by"][fact["claim_id"]],
                "status": claim_status(cross["reasons"][fact["claim_id"]]),
            }
        )
    required = {i["passage_id"] for i in gate["required"]}
    for claim in claims:
        claim["required"] = any(c["passage_id"] in required for c in claim["citations"])

    groups = [*clauses]
    if any(c["clause_id"] == OTHER for c in claims) or OTHER in missing:
        groups.append({"clause_id": OTHER, "title": "Not on the checklist", "source": None,
                       "decides": "Facts the writer found important that no clause names.",
                       "sentence": None, "items": [], "policy": None, "passage_id": None,
                       "item_passage_ids": []})
    view_clauses = []
    for g in groups:
        own = [c["claim_id"] for c in claims if c["clause_id"] == g["clause_id"]]
        missed = cross["possibly_missed"].get(g["clause_id"], [])
        # Clause coverage: "possibly missed" when the scan found a relevant passage no claim
        # cites (there may be evidence the writer skipped); otherwise "no evidence in file" only
        # when no claim cites the file for this clause. A sub-fact the writer could not find
        # stays in "missing" on its own row, so a clause with supported claims is never empty.
        coverage = None
        if missed:
            coverage = "possibly_missed"
        elif g["clause_id"] != OTHER and not own:
            coverage = "no_evidence_in_file"
        view_clauses.append(
            {
                "clause_id": g["clause_id"],
                "title": g["title"],
                "source": g["source"],
                "decides": g["decides"],
                "policy_sentence": g["sentence"],
                "policy_items": g.get("items", []),
                "policy_passage_id": g["passage_id"],
                "claim_ids": own,
                "coverage": coverage,
                "missing": missing.get(g["clause_id"], []),
                "contradictions": cross["contradictions"].get(g["clause_id"], []),
                "possibly_missed": missed,
            }
        )

    titles = {f: t for f, t in POLICIES.values()}
    view = {
        "schema_version": SCHEMA_VERSION,
        "case": {**case_meta, "synthetic": True},
        "policies": [
            {"file": f, "title": titles.get(f, f), **{k: pin[k] for k in
                                                       ("version", "approved", "sha256")}}
            for f, pin in sorted(lock.items())
        ],
        "models": models,
        "clauses": view_clauses,
        "claims": claims,
        "sources": {},
        "required_reading": gate["required"],
        "suggested_reading": gate["suggested"],
        "cap": gate["cap"],
    }
    # Sources last, from everything the view names, so no passage id is ever left without one.
    view["sources"] = {pid: source_entry(pid, passages)
                       for pid in sorted(named_passage_ids(view))}
    return view


def validate_view(view: dict) -> None:
    schema = json.loads(VIEW_SCHEMA.read_text(encoding="utf-8"))
    jsonschema.validate(view, schema)
    unsourced = named_passage_ids(view) - set(view["sources"])
    if unsourced:
        raise jsonschema.ValidationError(f"passage ids with no sources entry: {sorted(unsourced)}")


def run(case_id: str, replay: bool = False, checker: str = "jev", writer=None,
        checker_impl=None, out_dir: Path | None = None) -> dict:
    """Run every layer once and write the stage files. ``writer`` and ``checker_impl`` replace
    the live models (tests use fixed ones); ``replay`` reads every response from the cache.

    The scan and the contradiction pairs are Jev's jobs: they run on ``checker_impl`` when it
    offers ``scan`` and ``compare`` (Jev, or a test's fixed checker), else on Jev."""
    out = out_dir or case_run_dir(case_id)
    cache = Cache(out / "cache", replay=replay)

    # 1. Ingest: pins first, then passages.
    lock = load_lock()
    policy = policy_passages()
    case_meta, case = case_passages(case_id)
    # 2. Checklist: each clause anchored to the passage that holds its sentence.
    clauses = anchor(load_clauses(), policy)
    clause_ids = [c["clause_id"] for c in clauses]
    policy_by_id = {p["passage_id"]: p for p in policy}
    passages = {p["passage_id"]: p for p in [*case, *policy]}
    case_by_id = {p["passage_id"]: p for p in case}

    # 3. Writer.
    writer = writer or ClaudeWriter(cache)
    raw = writer.write(case_meta, case, clauses, policy_by_id)
    facts = [{**f, "claim_id": f"c{n:02d}"} for n, f in enumerate(raw["facts"], start=1)]

    # 4. Code checks on every fact with citations; nothing is dropped.
    found = [f for f in facts if f["found"]]
    checks = {f["claim_id"]: check_fact(f, passages) for f in found}

    # 5. Checker: second key on each claim against its cited passages that exist.
    checker_impl = checker_impl or make_checker(checker, cache)
    items = []
    for f in found:
        cited = []
        for c in f["citations"]:
            if c["passage_id"] in passages and passages[c["passage_id"]] not in cited:
                cited.append(passages[c["passage_id"]])
        if cited:
            items.append({"claim_id": f["claim_id"], "claim": f["claim"], "passages": cited})
    verdicts = {v["claim_id"]: v for v in checker_impl.check(items)}
    models = {
        "writer": {"name": writer.name, "model": getattr(writer, "model_id", None)},
        "checker": {"name": checker_impl.name, "model": getattr(checker_impl, "model_id", None)},
    }

    # 6. Relevance scan: every case passage scored against each decisive clause.
    cross_impl = checker_impl if hasattr(checker_impl, "scan") else make_checker("jev", cache)
    scores = cross_impl.scan(clauses, case)

    # 7. Contradiction pairs: per clause, the passages that matter most to it, pair by pair.
    cited_by_clause: dict[str, list[str]] = {}
    for f in found:
        for c in f["citations"]:
            if c["passage_id"] in case_by_id:
                cited_by_clause.setdefault(f["clause_id"], []).append(c["passage_id"])
    candidates = {cid: pair_candidates(cited_by_clause.get(cid, []), scores[cid], SCAN_THRESHOLD)
                  for cid in clause_ids}
    jobs = [{"clause": c, "a": case_by_id[a], "b": case_by_id[b]}
            for c in clauses for a, b in pairs_of(candidates[c["clause_id"]])]
    pair_verdicts = cross_impl.compare(jobs) if jobs else []
    contradictions = {cid: contradicting([v for v in pair_verdicts if v["clause_id"] == cid])
                      for cid in clause_ids}

    # Cross-passage results per claim and per clause. "Possibly missed" means cited by no
    # claim at all, under any clause.
    all_pairs = [p for cid in clause_ids for p in contradictions[cid]]
    cited_anywhere = {c["passage_id"] for f in found for c in f["citations"]}
    contra = {f["claim_id"]: contradicted_by(checks[f["claim_id"]]["citations"], all_pairs)
              for f in found}
    reasons = {f["claim_id"]: claim_reasons(checks[f["claim_id"]], verdicts.get(f["claim_id"]),
                                            contra[f["claim_id"]]) for f in found}
    missed = {cid: possibly_missed(scores[cid], cited_anywhere, SCAN_THRESHOLD)
              for cid in clause_ids}
    cross = {"contradictions": contradictions, "possibly_missed": missed,
             "contradicted_by": contra, "reasons": reasons}

    # 8. Gate.
    prelim = [
        {"claim_id": f["claim_id"], "clause_id": f["clause_id"],
         "citations": [{"passage_id": c["passage_id"]} for c in f["citations"]],
         "checker": verdicts.get(f["claim_id"]),
         "reasons": reasons[f["claim_id"]], "status": claim_status(reasons[f["claim_id"]])}
        for f in found
    ]
    gate = required_reading(
        prelim, clause_ids,
        contradictions=[{**p, "clause_id": cid} for cid in clause_ids
                        for p in contradictions[cid]],
        possibly_missed=[{**m, "clause_id": cid} for cid in clause_ids for m in missed[cid]],
    )

    # 9. View.
    view = build_view(case_meta, case, policy, clauses, lock, facts, checks, verdicts, gate,
                      models, cross)
    validate_view(view)

    job_models = getattr(cross_impl, "job_models", {})
    cross_model = getattr(cross_impl, "model_id", None)
    out.mkdir(parents=True, exist_ok=True)
    stages = {
        "passages": stage_record(case_meta, case, policy, lock),
        "checklist": [{"clause_id": c["clause_id"], "passage_id": c["passage_id"],
                       "item_passage_ids": c["item_passage_ids"]} for c in clauses],
        "writer": {**models["writer"], "facts": facts},
        "checks": checks,
        checker_impl.name if checker_impl.name == "jev" else f"{checker_impl.name}-check": {
            **models["checker"], "verdicts": [verdicts[k] for k in sorted(verdicts)]},
        "scan": {
            "case_id": case_id,
            "model": job_models.get("scan", cross_model),
            "threshold": SCAN_THRESHOLD,
            "threshold_set_on": THRESHOLD_CASE,
            "threshold_how": THRESHOLD_HOW,
            "passages_scanned": len(case),
            "clauses_scanned": len(clauses),
            "batch": SCAN_BATCH,
            "calls": math.ceil(len(case) / SCAN_BATCH) * len(clauses),
            "at_or_above_threshold": {cid: sum(s >= SCAN_THRESHOLD for s in scores[cid].values())
                                      for cid in clause_ids},
            "scores": scores,
        },
        "pairs": {
            "model": job_models.get("pairs", cross_model),
            "top": PAIR_TOP,
            "candidates": candidates,
            "verdicts": sorted(pair_verdicts, key=lambda v: (
                clause_ids.index(v["clause_id"]), passage_key(v["a"]), passage_key(v["b"]))),
        },
        "gate": gate,
        "view": view,
    }
    for name, data in stages.items():
        # LF on every platform, so a replay matches the committed files byte for byte.
        (out / f"{name}.json").write_text(dumps(data), encoding="utf-8", newline="\n")
    return view
