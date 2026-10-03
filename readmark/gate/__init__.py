"""Gate: which passages the officer must open before signing, most decisive first.

Three sources of flags, in this order:

1. every passage cited by a claim whose check failed (contradicted by another passage, quote not
   found, checker disagrees), and both passages of every contradicting pair;
2. then the passages the relevance scan rates at or above the threshold that no claim cites
   ("possibly missed"), strongest first.

A passage is one task however many flags it has: it carries all its reasons, claims and clauses.
At most ``CAP`` passages are required; the rest are listed as suggested, so the gate never grows
into "read everything" (Buçinca 2021: forcing every passage is the weakest design).
"""

CAP = 8
REASONS = ("contradicted", "quote_not_found", "checker_disagrees", "possibly_missed")
FLAGGED = REASONS[:3]  # the reasons a claim can carry


def severity(claim: dict) -> int:
    """How strongly a claim's own checks speak against it: a contradiction first (another
    passage, or the checker calling the claim contradicted), then a quote that is not in its
    passage, then a checker that cannot confirm it."""
    reasons = claim.get("reasons") or [claim["status"]]
    checker = claim.get("checker") or {}
    if "contradicted" in reasons or (
        "checker_disagrees" in reasons and checker.get("verdict") == "contradicts"
    ):
        return 3
    if "quote_not_found" in reasons:
        return 2
    if "checker_disagrees" in reasons:
        return 1
    return 0


def required_reading(claims: list[dict], clause_order: list[str], cap: int = CAP,
                     contradictions: list[dict] = (), possibly_missed: list[dict] = ()) -> dict:
    """Order the flagged passages and split them into required (at most ``cap``) and suggested.

    ``claims`` carry ``claim_id, clause_id, status, citations``, and optionally ``reasons`` (all
    failed checks) and ``checker``. ``contradictions`` are ``{clause_id, a, b, probability}``;
    ``possibly_missed`` are ``{clause_id, passage_id, score}``.

    Order: flagged claims and contradicting pairs by severity, then the probability of the
    disagreement (the checker's for a verdict other than "supports", the pair's for a
    contradiction), then the clause's place in the checklist, then the order given; after them
    the possibly-missed passages by scan score. The sort key is total, so the order is
    deterministic."""
    order = {cid: i for i, cid in enumerate(clause_order)}

    def place(clause_id: str) -> int:
        return order.get(clause_id, len(order))

    # Each flag: (key, passage_id, reasons, claim_id or None, clause_id).
    flags = []
    for n, claim in enumerate(claims):
        reasons = [r for r in claim.get("reasons") or [claim["status"]] if r in FLAGGED]
        if not reasons:
            continue
        # A checker that supports the claim lends it no weight here: its probability is
        # confidence in the claim, not in a problem with it.
        checker = claim.get("checker") or {}
        prob = 0.0 if checker.get("verdict") == "supports" else checker.get("probability") or 0.0
        key = (0, -severity(claim), -prob, place(claim["clause_id"]), 0, n)
        for m, citation in enumerate(claim["citations"]):
            flags.append(((*key, m), citation["passage_id"], reasons, claim["claim_id"],
                          claim["clause_id"]))
    for n, pair in enumerate(contradictions):
        key = (0, -3, -(pair.get("probability") or 0.0), place(pair["clause_id"]), 1, n)
        for m, pid in enumerate((pair["a"], pair["b"])):
            flags.append(((*key, m), pid, ["contradicted"], None, pair["clause_id"]))
    for n, item in enumerate(possibly_missed):
        key = (1, -item["score"], 0, place(item["clause_id"]), 2, n, 0)
        flags.append((key, item["passage_id"], ["possibly_missed"], None, item["clause_id"]))

    # One entry per passage. Flags are merged strongest first, so each passage keeps its most
    # decisive key and lists its claims and clauses in that order.
    items: dict[str, dict] = {}
    for key, pid, reasons, claim_id, clause_id in sorted(flags, key=lambda f: (f[0], f[1])):
        item = items.setdefault(pid, {"passage_id": pid, "claim_ids": [], "clause_ids": [],
                                      "reasons": [], "_key": key})
        if claim_id and claim_id not in item["claim_ids"]:
            item["claim_ids"].append(claim_id)
        if clause_id not in item["clause_ids"]:
            item["clause_ids"].append(clause_id)
        item["reasons"] = sorted(set(item["reasons"]) | set(reasons), key=REASONS.index)
    ranked = sorted(items.values(), key=lambda i: (i["_key"], i["passage_id"]))
    for rank, item in enumerate(ranked, start=1):
        item.pop("_key")
        item["rank"] = rank
    return {"cap": cap, "required": ranked[:cap], "suggested": ranked[cap:]}
