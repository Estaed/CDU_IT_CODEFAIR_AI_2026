"""Cross-passage checks: what no claim's own passage can show.

1. **Contradiction pairs.** For each decisive clause, the case passages that matter most to it
   (cited by one of its claims, or at or above the scan threshold; the top ``PAIR_TOP`` by scan
   score) are compared pair by pair. A claim that rests on one side of a contradicting pair and
   not the other is "contradicted by another passage". This is what catches "arrears $2,400"
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

PAIR_TOP = 5  # "up to about five" passages per clause: at most 10 pairs per clause

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
    return sorted(pool, key=lambda pid: (pid not in cited_set, -scores[pid],
                                         passage_key(pid)))[:top]


def pairs_of(candidates: list[str]) -> list[tuple[str, str]]:
    return list(combinations(candidates, 2))


def contradicting(verdicts: list[dict]) -> list[dict]:
    """The pairs a checker called contradictory, as the view shows them under their clause:
    ``{a, b, probability}`` with the checker's probability for "contradict", strongest first."""
    hits = [
        {"a": v["a"], "b": v["b"], "probability": (v.get("probabilities") or {}).get("contradict")}
        for v in verdicts if v["verdict"] == "contradict"
    ]
    return sorted(hits, key=lambda p: (-(p["probability"] or 0.0), passage_key(p["a"]),
                                       passage_key(p["b"])))


def contradicted_by(citations: list[dict], pairs: list[dict]) -> list[str]:
    """The passages that contradict what a claim rests on.

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


def possibly_missed(scores: dict[str, float], cited: set[str], threshold: float) -> list[dict]:
    """Passages at or above the threshold for one clause that no claim cites, most relevant
    first."""
    hits = [(pid, s) for pid, s in scores.items() if s >= threshold and pid not in cited]
    return [{"passage_id": pid, "score": s}
            for pid, s in sorted(hits, key=lambda h: (-h[1], passage_key(h[0])))]
