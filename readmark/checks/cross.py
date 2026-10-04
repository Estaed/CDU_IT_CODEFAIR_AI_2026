"""Cross-passage checks: what no claim's own passage can show.

1. **Contradiction pairs.** For each decisive clause, the case passages that matter most to it
   (cited by one of its claims, or at or above the scan threshold; the top ``PAIR_TOP`` by scan
   score) are compared pair by pair, and so are the pages any one claim cites together. A claim that rests on one side of a contradicting pair and
   not the other is checked against the other passage before being marked contradicted.
   This is what catches "arrears $2,400"
   citing only the January ledger, which passes every check against its own passage.
2. **Possibly missed.** A case passage at or above the threshold for a clause that no claim
   cites at all is "possibly missed" under that clause: the omission map.
3. **The threshold** is set once, on the demo file A-0142 with its own ``gold.json`` and no other
   file's gold, before any evaluation (``choose_threshold``). A test recomputes it from the
   committed A-0142 scan, so the constant cannot drift from its recorded method.

Everything here is pure: the Jev calls live in ``readmark.jev`` and the results arrive as data.
"""

from itertools import combinations

from readmark.ingest import passage_key

PAIR_TOP = 5  # "up to about five" passages per clause: 10 pairs, plus pages a claim cites together

# 1.76 on the recorded A-0142 scan: the best scores of the five gold pages were p8 1.91,
# p23 1.76, p30 3.47, p51 3.96 and p58 3.81 (n=5), so p23 sets it.
SCAN_THRESHOLD = 1.76
THRESHOLD_CASE = "A-0142"
THRESHOLD_HOW = (
    "Set on A-0142 with its gold.json only, before any evaluation: the highest threshold at "
    "which every page in gold required_reading (p8, p23, p30, p51, p58; n=5) still has a passage "
    "scoring at or above it under at least one decisive clause, i.e. the lowest of those pages' "
    "best scan scores (readmark.checks.cross.choose_threshold)."
)


def page_of(passage_id: str) -> str:
    """'A-0142:p8:3' -> 'p8', the page form gold.json uses."""
    return passage_id.rsplit(":", 2)[1]


def choose_threshold(scores: dict[str, dict[str, float]], gold_pages: list[str]) -> float:
    """The highest threshold that keeps every gold required page within reach of the scan.

    For each gold page take its best score over all its passages and all clauses; the threshold
    is the lowest of those. Any higher value would leave a page the gold file calls required
    unable to surface as "possibly missed" if the writer skipped it."""
    best: dict[str, float] = {}
    for per_clause in scores.values():
        for pid, score in per_clause.items():
            page = page_of(pid)
            best[page] = max(best.get(page, score), score)
    absent = [p for p in gold_pages if p not in best]
    if absent:
        raise ValueError(f"gold pages with no scanned passage: {absent}")
    return min(best[p] for p in gold_pages)


def pair_candidates(cited: list[str], scores: dict[str, float], threshold: float,
                    top: int = PAIR_TOP) -> list[str]:
    """The case passages that matter most to one clause, at most ``top``: first those its claims
    cite (a contradiction there changes a claim's status), then those the scan puts at or above
    the threshold; by scan score within each group.

    Cited passages come first because the scan can rate a claim's own passage below uncited
    neighbours: on A-0142 the Debts clause scores stay under 2 of 4 (a debt does not withhold
    housing), and ranking by score alone pushed the March ledger the claims cite out of the top
    five."""
    cited_set = {pid for pid in cited if pid in scores}
    pool = cited_set | {pid for pid, s in scores.items() if s >= threshold}
    # Paragraphs, not pages: Task-32 tried one slot per page and H-01 lost its planted p2:3-p12:1
    # contradiction, because a page's best-scoring paragraph is not always the conflicting one.
    return sorted(pool, key=lambda pid: (pid not in cited_set, -scores[pid],
                                         passage_key(pid)))[:top]


def pairs_of(candidates: list[str]) -> list[tuple[str, str]]:
    return list(combinations(candidates, 2))


def co_cited_pairs(citations: list[list[str]], already: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Pages one claim cites together, compared even outside the top candidates.

    ``citations`` holds each claim's cited passage ids under one clause. The writer put these
    pages side by side, so the officer should learn whether they agree; on W-01 the child-presence
    claim cites the statement and the police report, which the top five never paired. One
    passage per page (the first cited), ordered by file position; pairs already asked are skipped.
    """
    seen = {frozenset((page_of(a), page_of(b))) for a, b in already}
    out = []
    for cited in citations:
        first: dict[str, str] = {}
        for pid in cited:
            first.setdefault(page_of(pid), pid)
        for a, b in combinations(sorted(first.values(), key=passage_key), 2):
            key = frozenset((page_of(a), page_of(b)))
            if key not in seen:
                seen.add(key)
                out.append((a, b))
    return out


def contradicting(verdicts: list[dict]) -> list[dict]:
    """Disagreements and updates both require reading and one-sided claim rechecks.

    Keep the legacy list name; relation names Jev's answer and probability is for that answer.
    """
    hits = [
        {"a": v["a"], "b": v["b"], "relation": v["verdict"],
         "probability": (v.get("probabilities") or {}).get(v["verdict"])}
        for v in verdicts if v["verdict"] in ("contradict", "updated")
    ]
    return sorted(hits, key=lambda p: (-(p["probability"] or 0.0), passage_key(p["a"]),
                                       passage_key(p["b"])))


def opposing_passages(citations: list[dict], pairs: list[dict]) -> list[str]:
    """Candidate opposing passages, before checking whether they contradict the claim.

    ``citations`` are the code-check results (``passage_id``, ``quote_found``). A claim rests on
    a passage only where its quote was found there, so a fabricated quote keeps its own status
    ("quote not found") instead of borrowing the passage's contradiction. A claim that already
    cites both sides of a pair has weighed them, so that pair names nothing for it."""
    rests_on = {c["passage_id"] for c in citations if c.get("quote_found")}
    others = set()
    for pair in pairs:
        if pair["a"] in rests_on and pair["b"] not in rests_on:
            others.add(pair["b"])
        if pair["b"] in rests_on and pair["a"] not in rests_on:
            others.add(pair["a"])
    return sorted(others, key=passage_key)


def contradicted_by(facts: list[dict], checks: dict, pairs: list[dict],
                    passages: dict[str, dict], checker) -> dict[str, list[str]]:
    """Check the claim itself against each opposing passage through the checker seam.

    Chosen after the demo audit; the held-out file is the honest test. A passage pair can
    disagree while a historical claim or the later balance remains true. Only an explicit
    'contradicts' verdict flags the claim. Pair display and required reading are independent.
    """
    jobs = [{"claim_id": f"{f['claim_id']}@{pid}", "claim": f['claim'],
             "passages": [passages[pid]],
             "context": [passages[c['passage_id']] for c in checks[f['claim_id']]['citations']
                         if c.get('quote_found') and c['passage_id'] in passages
                         and passages[c['passage_id']].get('source') != 'policy']}
            for f in facts for pid in opposing_passages(checks[f['claim_id']]['citations'], pairs)
            if pid in passages]
    verdicts = {v['claim_id']: v for v in checker.check(jobs)} if jobs else {}
    result = {f['claim_id']: [] for f in facts}
    for job in jobs:
        if verdicts.get(job['claim_id'], {}).get('verdict') == 'contradicts':
            cid, pid = job['claim_id'].split('@', 1)
            result[cid].append(pid)
    return result


def possibly_missed(scores: dict[str, float], cited: set[str], threshold: float) -> list[dict]:
    """Passages at or above the threshold for one clause that no claim cites, most relevant
    first."""
    hits = [(pid, s) for pid, s in scores.items() if s >= threshold and pid not in cited]
    return [{"passage_id": pid, "score": s}
            for pid, s in sorted(hits, key=lambda h: (-h[1], passage_key(h[0])))]


def distinct_missed(hits: list[dict], cited: set[str], passages: dict[str, dict],
                    duplicates: dict[str, str] | None = None) -> list[dict]:
    """Keep the strongest passage for each fact, including facts already cited by the map.

    Chosen after the demo audit; the held-out evaluation is its honest test. Jev supplies
    semantic duplicates (each must refer to a cited or earlier, stronger passage); exact text
    repetitions are also duplicates. Same-topic or conflicting facts must remain distinct.
    """
    from readmark.ingest import normalise

    seen = {normalise(passages[pid]['text']) for pid in cited if pid in passages}
    prior = set(cited)
    kept = []
    for hit in hits:
        pid = hit['passage_id']
        text = normalise(passages[pid]['text'])
        representative = (duplicates or {}).get(pid)
        if text not in seen and representative not in prior:
            kept.append(hit)
        seen.add(text)
        prior.add(pid)
    return kept
