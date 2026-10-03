"""The reusable claim path: claim sentences about one case in, view-shaped claims out.

The summary under audit runs through it, and the evaluation wave runs the mutation set and the
held-out file through it, so it needs no summary. Each claim gets exactly the checks the evidence
map gives its own claims:

1. a locator (Claude) finds the case passages that bear on it, with verbatim quotes;
2. code: each quote is in its passage; values may also be in that passage or its header;
3. Jev's second key on the claim against its cited passages;
4. Check each claim against the other side of any contradicting pair it rests on.

Nothing is hidden: a factual claim no passage supports keeps the status "quote not found".
Pure summary suggestions stay visible as nothing to check in evaluation, with null judgments.
"""

import re
from pathlib import Path

from readmark import case_run_dir
from readmark.cache import Cache
from readmark.checklist import load_clauses
from readmark.checks import check_fact, claim_reasons, claim_status
from readmark.checks.cross import contradicted_by
from readmark.ingest import case_passages
from readmark.jev import make_checker
from readmark.writer import OTHER


def nothing_to_check(claim: str) -> bool:
    """Only a review suggestion, never a hedged factual statement or a quoted file rule.

    'The applicant should have received $50' remains a factual claim. Keep this conservative:
    a suggestion that also asserts a reason ('because income is missing') is checked whole.
    The fixed view schema has no exempt status: use its non-flagged 'supported' bucket with
    an explicitly null verdict, probability and support, and report 'nothing to check' in eval.
    """
    text = claim.strip().rstrip('.!?')
    # Ignore connectors inside the quoted answer being proposed for review.
    unquoted = re.sub(r'"[^"\n]*"|“[^”\n]*”', 'quoted answer', text)
    if re.search(r'\b(?:because|since|although|whereas|which|but|and|as)\b', unquoted,
                 re.IGNORECASE):
        return False
    return bool(re.fullmatch(
        r'(?:It (?:may|might|could) be worth (?:checking|clarifying|reviewing|confirming) .+'
        r'|(?:The |This )?(?:answer|wording|statement|entry|issue) .+ '
        r'(?:may|might|could) (?:also )?need (?:checking|clarifying|reviewing|confirmation)'
        r'|(?:The )?(?:officer|delegate|reviewer|assessor|We|You) '
        r'(?:should|could|may|might) (?:check|clarify|review|confirm|request|seek) .+)',
        text, re.IGNORECASE))


def map_pairs(view: dict) -> list[dict]:
    """The contradicting pairs of an evidence-map view, every clause together."""
    return [p for clause in view["clauses"] for p in clause["contradictions"]]


def check_claims(case_id: str, claims: list[str], *, locator=None, checker=None,
                 pairs: list[dict] = (), required=(), cache: Cache | None = None,
                 replay: bool = False, case_file: Path | None = None,
                 prefix: str = "a") -> list[dict]:
    """Check claim sentences about one case the way the evidence map checks its own claims.

    Takes:
    - ``case_id``: the case, read from ``data/cases/<case_id>/case.md``, or from ``case_file``
      (the held-out file lives elsewhere);
    - ``claims``: claim sentences, one claim each, in order (a mutation-set claim, or one claim
      split from a summary sentence);
    - ``locator``: finds the passages bearing on each claim (default ``ClaudeAuditor``);
    - ``checker``: the second key, behind the checker seam (default Jev);
    - ``pairs``: the case's contradicting passage pairs ``{a, b, probability}`` from its
      evidence map (``map_pairs(view)``). Without them no claim can be "contradicted";
    - ``required``: the passage ids in the map's required reading, which set each claim's
      ``required``; the claim path never adds to them;
    - ``cache``/``replay``: where model responses are kept, by default ``runs/<case_id>/cache``.

    Returns one claim per sentence, in order, with ids ``a01, a02, ...``, in the view's claim
    shape: ``{claim_id, clause_id, claim, citations: [{passage_id, quote, quote_found,
    passage_exists}], values_missing, checker, contradicted_by, status, required}``. ``status``
    is ``contradicted``, ``quote_not_found``, ``checker_disagrees`` or ``supported``; a claim
    with no passage shows ``quote_not_found`` and is never dropped. Pure suggestions in the
    summary (prefix ``a``) instead have a null judgment in the non-flagged schema bucket.
    """
    case_meta, case = case_passages(case_id, case_file)
    passages = {p["passage_id"]: p for p in case}
    cache = cache or Cache(case_run_dir(case_id) / "cache", replay=replay)
    if locator is None:
        from readmark.audit.claude import ClaudeAuditor

        locator = ClaudeAuditor(cache)
    checker = checker or make_checker("jev", cache)
    required = set(required)

    # 1. Locate: one call for every claim. A claim the locator skipped has no citations.
    ids = [f"{prefix}{n:02d}" for n in range(1, len(claims) + 1)]
    asked = [{"claim_id": i, "claim": c} for i, c in zip(ids, claims, strict=True)]
    located = locator.locate(case_meta, case, load_clauses(), asked) if asked else {}
    facts = [{**a, **located.get(a["claim_id"], {"clause_id": OTHER, "citations": []})}
             for a in asked]

    # Preserve every locator request, including suggestions, so frozen Claude calls replay.
    exempt = {f['claim_id'] for f in facts if prefix == 'a' and nothing_to_check(f['claim'])}

    # 2. Code checks: verified quotes, then values in their passages and document headers.
    checks = {f["claim_id"]: check_fact(f, passages) for f in facts}

    # 3. Second key on each claim against its cited passages that exist.
    items = []
    for f in facts:
        if f['claim_id'] in exempt:
            continue
        cited = []
        for c in f["citations"]:
            if c["passage_id"] in passages and passages[c["passage_id"]] not in cited:
                cited.append(passages[c["passage_id"]])
        if cited:
            items.append({"claim_id": f["claim_id"], "claim": f["claim"], "passages": cited})
    verdicts = {v["claim_id"]: v for v in checker.check(items)} if items else {}

    # 4. Contradiction pairs, then one status per claim, ranked as the map ranks them.
    pair_checker = make_checker('jev', cache) if checker.name == 'claude' else checker
    contradictions = contradicted_by([f for f in facts if f['claim_id'] not in exempt],
                                    checks, list(pairs), passages, pair_checker)
    out = []
    for f in facts:
        check, verdict = checks[f["claim_id"]], verdicts.get(f["claim_id"])
        contra = contradictions.get(f['claim_id'], [])
        if f['claim_id'] in exempt:
            # A null judgment explicitly says no checker assessed this suggestion as a fact.
            verdict = {'claim_id': f['claim_id'], 'verdict': None,
                       'probability': None, 'supports': None}
        out.append({
            "claim_id": f["claim_id"],
            "clause_id": f["clause_id"],
            "claim": f["claim"],
            "citations": [{**r, "quote": c["quote"]}
                          for c, r in zip(f["citations"], check["citations"], strict=True)],
            "values_missing": [] if f['claim_id'] in exempt else check["values_missing"],
            "checker": verdict,
            "contradicted_by": contra,
            "status": 'supported' if f['claim_id'] in exempt else
                      claim_status(claim_reasons(check, verdict, contra)),
            "required": any(c["passage_id"] in required for c in f["citations"]),
        })
    return out
