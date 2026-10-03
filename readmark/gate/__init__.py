"""Gate: which passages the officer must open before signing, most decisive first.

Required reading is every passage cited by a claim whose check failed: quote not found, checker
disagrees, or contradicted by another passage. At most ``CAP`` passages are required; the rest
are listed as suggested, so the gate never grows into "read everything" (Buçinca 2021: forcing
every passage is the weakest design).
"""

CAP = 8
FLAGGED = ("contradicted", "quote_not_found", "checker_disagrees")


def severity(claim: dict) -> int:
    """How strongly a claim's own checks speak against it: an explicit contradiction first,
    then a quote that is not in its passage, then a checker that cannot confirm it."""
    checker = claim.get("checker") or {}
    if claim["status"] == "contradicted" or (
        claim["status"] == "checker_disagrees" and checker.get("verdict") == "contradicts"
    ):
        return 3
    if claim["status"] == "quote_not_found":
        return 2
    if claim["status"] == "checker_disagrees":
        return 1
    return 0


def required_reading(claims: list[dict], clause_order: list[str], cap: int = CAP) -> dict:
    """Order the flagged passages and split them into required (at most ``cap``) and suggested.

    Order: severity, then the checker's probability for its verdict, then the clause's place in
    the checklist, then the order the writer gave. The sort key is total, so the order is
    deterministic."""
    order = {cid: i for i, cid in enumerate(clause_order)}
    items: dict[str, dict] = {}
    for n, claim in enumerate(claims):
        if claim["status"] not in FLAGGED:
            continue
        prob = (claim.get("checker") or {}).get("probability") or 0.0
        key = (-severity(claim), -prob, order.get(claim["clause_id"], len(order)), n)
        for m, citation in enumerate(claim["citations"]):
            pid = citation["passage_id"]
            item = items.setdefault(pid, {"passage_id": pid, "claim_ids": [], "reasons": [],
                                          "_key": (*key, m)})
            item["_key"] = min(item["_key"], (*key, m))
            if claim["claim_id"] not in item["claim_ids"]:
                item["claim_ids"].append(claim["claim_id"])
            if claim["status"] not in item["reasons"]:
                item["reasons"].append(claim["status"])
    ranked = sorted(items.values(), key=lambda i: (i["_key"], i["passage_id"]))
    for rank, item in enumerate(ranked, start=1):
        item.pop("_key")
        item["rank"] = rank
    return {"cap": cap, "required": ranked[:cap], "suggested": ranked[cap:]}
