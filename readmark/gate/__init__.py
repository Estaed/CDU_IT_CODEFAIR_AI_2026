"""Gate: which passages the officer must open before signing, most decisive first.

Three sources of flags, in this order:

1. every passage cited by a claim whose check failed (contradicted by another passage, quote not
   found, checker disagrees), and both passages of every disagreeing or updated pair;
2. then the passages the relevance scan rates at or above the threshold that no claim cites
   ("possibly missed"), strongest first.

A page is one task however many passages are flagged: it carries all their reasons and claims.
At most ``CAP`` pages are required; the rest are listed as suggested, so the gate never grows
into "read everything" (Buçinca 2021: forcing every passage is the weakest design).
"""

from readmark.ingest import passage_key

CAP = 8
REASONS = ("contradicted", "quote_not_found", "checker_disagrees", "possibly_missed", "cited")
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
                     contradictions: list[dict] = (), possibly_missed: list[dict] = (),
                     passages: dict[str, dict] | None = None) -> dict:
    """Order the flagged passages and split them into required (at most ``cap``) and suggested.

    ``claims`` carry ``claim_id, clause_id, status, citations``, and optionally ``reasons`` (all
    failed checks) and ``checker``. ``contradictions`` are
    ``{clause_id, a, b, relation, probability}``;
    ``possibly_missed`` are ``{clause_id, passage_id, score}``.

    Order: flagged claims and contradicting pairs by severity, then the probability of the
    disagreement (the checker's for a verdict other than "supports", the pair's for a
    contradiction), then the clause's place in the checklist, then the order given; after them
    the possibly-missed passages by scan score. The sort key is total, so the order is
    deterministic. Connected updated pairs under a clause share a page-level record chain.
    Its most confident pair retains priority; other chain pages are suggested unless another
    flag independently requires them. This keeps a clear before/after comparison without
    spending the cap on every intermediate record. Cited case pages fill otherwise unused
    slots after flags, with pages used by more claims first; they are evidence, not new errors.
    ``passages`` enables that fallback and retains each page's complete reading surface."""
    order = {cid: i for i, cid in enumerate(clause_order)}

    def place(clause_id: str) -> int:
        return order.get(clause_id, len(order))

    def page_key(pid: str) -> str:
        # The document prefix is essential: page 1 of two uploaded documents is not one page.
        return pid.rsplit(":", 1)[0]

    primary_updates = set()
    for cid in clause_order:
        remaining = [p for p in contradictions if p["clause_id"] == cid
                     and p.get("relation") == "updated"]
        while remaining:
            component = [remaining.pop(0)]
            pages = {page_key(pid) for p in component for pid in (p["a"], p["b"])}
            while True:
                linked = [p for p in remaining if pages & {page_key(p["a"]), page_key(p["b"])}]
                if not linked:
                    break
                for p in linked:
                    remaining.remove(p)
                    component.append(p)
                    pages.update((page_key(p["a"]), page_key(p["b"])))
            strongest = min(component, key=lambda p: (-(p.get("probability") or 0),
                                                      passage_key(p["a"]), passage_key(p["b"])))
            primary_updates.update((cid, page_key(pid)) for pid in (strongest["a"], strongest["b"]))

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
            priority = key
            if pair.get("relation") == "updated" and (
                pair["clause_id"], page_key(pid)
            ) not in primary_updates:
                priority = (3, *key[1:])
            flags.append(((*priority, m), pid, ["contradicted"], None, pair["clause_id"]))
    for n, item in enumerate(possibly_missed):
        key = (1, -item["score"], 0, place(item["clause_id"]), 2, n, 0)
        flags.append((key, item["passage_id"], ["possibly_missed"], None, item["clause_id"]))

    if passages is not None:
        uses: dict[str, set[str]] = {}
        for claim in claims:
            for cite in claim["citations"]:
                pid = cite["passage_id"]
                if passages.get(pid, {}).get("source") == "case":
                    uses.setdefault(page_key(pid), set()).add(claim["claim_id"])
        for n, claim in enumerate(claims):
            for m, cite in enumerate(claim["citations"]):
                pid = cite["passage_id"]
                if passages.get(pid, {}).get("source") == "case":
                    key = (2, -len(uses[page_key(pid)]), 0, place(claim["clause_id"]), 0, n, m)
                    flags.append((key, pid, ["cited"], claim["claim_id"], claim["clause_id"]))

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
    pages = {}
    for item in items.values():
        page = pages.setdefault(page_key(item["passage_id"]), {
            "passage_id": item["passage_id"], "passage_ids": [], "passages": [],
            "claim_ids": [], "clause_ids": [], "reasons": [], "_key": item["_key"],
        })
        page["passage_ids"].append(item["passage_id"])
        page["passages"].append({k: v for k, v in item.items() if k != "_key"})
        for field in ("claim_ids", "clause_ids", "reasons"):
            page[field] = list(dict.fromkeys([*page[field], *item[field]]))
    ranked = sorted(pages.values(), key=lambda i: (i["_key"], i["passage_id"]))
    for rank, item in enumerate(ranked, start=1):
        item.pop("_key")
        item["rank"] = rank
    return {"cap": cap, "required": ranked[:cap], "suggested": ranked[cap:]}
