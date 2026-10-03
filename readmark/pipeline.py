"""``run --case <id>``: every v1 layer once, each writing ``runs/<case>/<stage>.json``.

ingest -> checklist -> writer -> code checks -> checker -> gate -> view.

Stage files hold case text (synthetic) and policy offsets and hashes, never policy text beyond
the clause sentences and the quotes the screen shows (contract, Run outputs).
"""

import json
import re
from pathlib import Path

import jsonschema

from readmark import SCHEMAS_DIR, case_run_dir, dumps
from readmark.cache import Cache
from readmark.checklist import anchor, load_clauses
from readmark.checks import check_fact
from readmark.gate import required_reading
from readmark.ingest import POLICIES, case_passages, load_lock, policy_passages, stage_record
from readmark.jev import make_checker
from readmark.writer import OTHER, ClaudeWriter

VIEW_SCHEMA = SCHEMAS_DIR / "view.schema.json"
SCHEMA_VERSION = 1


def section_label(heading: str | None) -> str | None:
    """'3.4. Debts' -> '§3.4 Debts'."""
    if not heading:
        return None
    return "§" + re.sub(r"^(\d+(?:\.\d+)*)\.?\s+", r"\1 ", heading)


def claim_status(check: dict, verdict: dict | None) -> str:
    """One claim-check word (the first of the three status lists). Contradiction pairs arrive in
    wave 2; until then a checker verdict of 'contradicts' counts as the checker disagreeing."""
    if not check["passed"]:
        return "quote_not_found"
    if not verdict or verdict.get("verdict") != "supports":
        return "checker_disagrees"
    return "supported"


def build_view(case_meta: dict, case: list[dict], policy: list[dict], clauses: list[dict],
               lock: dict, facts: list[dict], checks: dict, verdicts: dict, gate: dict,
               models: dict) -> dict:
    passages = {p["passage_id"]: p for p in [*case, *policy]}
    claims, missing = [], {}
    for fact in facts:
        if not fact["found"]:
            missing.setdefault(fact["clause_id"], []).append(
                {"claim_id": fact["claim_id"], "statement": fact["claim"]}
            )
            continue
        check = checks[fact["claim_id"]]
        verdict = verdicts.get(fact["claim_id"])
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
                "checker": verdict,
                "status": claim_status(check, verdict),
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
        # Clause coverage says "no evidence in file" only when no claim cites the file for this
        # clause. A sub-fact the writer could not find stays in "missing" and shows on its own
        # row, so a clause with supported claims is never labelled empty.
        coverage = None
        if g["clause_id"] != OTHER and not own:
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
            }
        )

    cited = {c["passage_id"] for claim in claims for c in claim["citations"]}
    cited |= {g["passage_id"] for g in groups if g["passage_id"]}
    sources = {}
    for pid in sorted(cited):
        p = passages.get(pid)
        if p is None:
            sources[pid] = {"passage_id": pid, "exists": False, "kind": None}
        elif p["source"] == "case":
            sources[pid] = {
                "passage_id": pid, "exists": True, "kind": "case", "page": p["page"],
                "doc_type": p["doc_type"], "doc_title": p["doc_title"], "doc_date": p["doc_date"],
                "text": p["text"],
            }
        else:
            # Policy text is not stored: the server reads it from the pinned PDF on demand.
            sources[pid] = {
                "passage_id": pid, "exists": True, "kind": "policy", "page": p["page"],
                "doc_title": p["doc_title"], "version": p["version"],
                "section": section_label(p["section"]), "text": None,
            }

    titles = {f: t for f, t in POLICIES.values()}
    return {
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
        "sources": sources,
        "required_reading": gate["required"],
        "suggested_reading": gate["suggested"],
        "cap": gate["cap"],
    }


def validate_view(view: dict) -> None:
    schema = json.loads(VIEW_SCHEMA.read_text(encoding="utf-8"))
    jsonschema.validate(view, schema)


def run(case_id: str, replay: bool = False, checker: str = "jev", writer=None,
        checker_impl=None, out_dir: Path | None = None) -> dict:
    """Run every layer once and write the stage files. ``writer`` and ``checker_impl`` replace
    the live models (tests use fixed ones); ``replay`` reads every response from the cache."""
    out = out_dir or case_run_dir(case_id)
    cache = Cache(out / "cache", replay=replay)

    # 1. Ingest: pins first, then passages.
    lock = load_lock()
    policy = policy_passages()
    case_meta, case = case_passages(case_id)
    # 2. Checklist: each clause anchored to the passage that holds its sentence.
    clauses = anchor(load_clauses(), policy)
    policy_by_id = {p["passage_id"]: p for p in policy}
    passages = {p["passage_id"]: p for p in [*case, *policy]}

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

    # 6. Gate.
    models = {
        "writer": {"name": writer.name, "model": getattr(writer, "model_id", None)},
        "checker": {"name": checker_impl.name, "model": getattr(checker_impl, "model_id", None)},
    }
    prelim = [
        {"claim_id": f["claim_id"], "clause_id": f["clause_id"],
         "citations": [{"passage_id": c["passage_id"]} for c in f["citations"]],
         "checker": verdicts.get(f["claim_id"]),
         "status": claim_status(checks[f["claim_id"]], verdicts.get(f["claim_id"]))}
        for f in found
    ]
    gate = required_reading(prelim, [c["clause_id"] for c in clauses])

    # 7. View.
    view = build_view(case_meta, case, policy, clauses, lock, facts, checks, verdicts, gate,
                      models)
    validate_view(view)

    out.mkdir(parents=True, exist_ok=True)
    stages = {
        "passages": stage_record(case_meta, case, policy, lock),
        "checklist": [{"clause_id": c["clause_id"], "passage_id": c["passage_id"],
                       "item_passage_ids": c["item_passage_ids"]} for c in clauses],
        "writer": {**models["writer"], "facts": facts},
        "checks": checks,
        checker_impl.name if checker_impl.name == "jev" else f"{checker_impl.name}-check": {
            **models["checker"], "verdicts": [verdicts[k] for k in sorted(verdicts)]},
        "gate": gate,
        "view": view,
    }
    for name, data in stages.items():
        # LF on every platform, so a replay matches the committed files byte for byte.
        (out / f"{name}.json").write_text(dumps(data), encoding="utf-8", newline="\n")
    return view
