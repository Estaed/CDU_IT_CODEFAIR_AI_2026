"""Cross-passage checks on the demo file A-0142: contradiction pairs, possibly missed, a reading
list that stays capped with one task per passage, and the scan threshold's recorded method."""

import json

from conftest import FixedChecker, FixedWriter, fact, needs_pdfs

from readmark import CASES_DIR, ROOT
from readmark.checks.cross import SCAN_THRESHOLD, THRESHOLD_CASE, choose_threshold, page_of
from readmark.gate import CAP, required_reading
from readmark.ingest import case_passages
from readmark.pipeline import run, validate_view

A_RUN = ROOT / "runs" / "A-0142"
JANUARY, MARCH = "A-0142:p8:3", "A-0142:p23:3"  # the two ledger balances, p.8 and p.23
STALE = fact("elig-debts", "The applicant has rent arrears of $2,400.",
             (JANUARY, "Arrears balance $2,400.00."))
HIGH = SCAN_THRESHOLD + 1.0


def clause(view: dict, clause_id: str) -> dict:
    return next(c for c in view["clauses"] if c["clause_id"] == clause_id)


@needs_pdfs
def test_claim_citing_only_the_january_ledger_is_contradicted_by_march(tmp_path):
    both = fact("elig-debts", "The arrears of $2,400 were later cleared in full.",
                (JANUARY, "Arrears balance $2,400.00."), (MARCH, "Arrears cleared in full."))
    checker = FixedChecker(scores={"elig-debts": {JANUARY: HIGH, MARCH: HIGH}},
                           contradict=[(JANUARY, MARCH)])
    view = run("A-0142", writer=FixedWriter([STALE, both]), checker_impl=checker,
               out_dir=tmp_path)

    stale, weighed = view["claims"]
    assert stale["status"] == "contradicted"
    assert stale["contradicted_by"] == [MARCH]
    # A claim that already cites both sides has weighed them; the pair names nothing for it.
    assert weighed["contradicted_by"] == [] and weighed["status"] == "supported"
    assert clause(view, "elig-debts")["contradictions"] == [
        {"a": JANUARY, "b": MARCH, "probability": 0.9}]

    required = {i["passage_id"]: i for i in view["required_reading"]}
    assert {JANUARY, MARCH} <= set(required)
    assert "contradicted" in required[JANUARY]["reasons"]
    assert stale["claim_id"] in required[JANUARY]["claim_ids"]
    assert "contradicted" in required[MARCH]["reasons"]
    assert "elig-debts" in required[MARCH]["clause_ids"]
    assert view["sources"][MARCH]["kind"] == "case"
    validate_view(view)


@needs_pdfs
def test_uncited_passage_at_or_above_the_threshold_is_possibly_missed(tmp_path):
    above, at, below = "A-0142:p51:4", "A-0142:p51:3", "A-0142:p44:1"
    checker = FixedChecker(scores={
        "prio-documentation": {above: SCAN_THRESHOLD + 0.5, at: SCAN_THRESHOLD,
                               below: SCAN_THRESHOLD - 0.5},
        "elig-debts": {JANUARY: HIGH},  # cited by a claim, so never "possibly missed"
    })
    view = run("A-0142", writer=FixedWriter([STALE]), checker_impl=checker, out_dir=tmp_path)

    docs = clause(view, "prio-documentation")
    assert docs["possibly_missed"] == [{"passage_id": above, "score": SCAN_THRESHOLD + 0.5},
                                       {"passage_id": at, "score": SCAN_THRESHOLD}]
    assert docs["coverage"] == "possibly_missed"
    assert clause(view, "elig-debts")["possibly_missed"] == []

    reading = {i["passage_id"]: i for i in view["required_reading"]}
    assert reading[above]["reasons"] == ["possibly_missed"]
    assert reading[above]["claim_ids"] == [] and reading[above]["clause_ids"] == [
        "prio-documentation"]
    listed = reading.keys() | {i["passage_id"] for i in view["suggested_reading"]}
    assert below not in listed
    validate_view(view)


def test_flags_beyond_the_cap_stay_capped_and_each_passage_is_one_task():
    claims = [
        {"claim_id": f"c{i:02d}", "clause_id": "elig-debts", "status": "checker_disagrees",
         "reasons": ["checker_disagrees"],
         "checker": {"verdict": "not_enough_information", "probability": 0.5},
         "citations": [{"passage_id": f"X:p{i}:1"}, {"passage_id": f"X:p{i + 1}:1"}]}
        for i in range(1, 9)
    ]
    pairs = [{"clause_id": "elig-debts", "a": "X:p1:1", "b": "X:p20:1", "probability": 0.8}]
    missed = [{"clause_id": "prio-category", "passage_id": f"X:p{i}:1", "score": 3.0}
              for i in [20, *range(30, 40)]]
    gate = required_reading(claims, ["elig-debts", "prio-category"], contradictions=pairs,
                            possibly_missed=missed)

    everything = gate["required"] + gate["suggested"]
    assert len(gate["required"]) == CAP
    ids = [i["passage_id"] for i in everything]
    assert len(ids) == len(set(ids)) == 9 + 1 + 10  # each passage once, however often flagged
    # The pair ranks first; p1 carries both its reasons and its claim, p20 its two clauses.
    assert ids[:2] == ["X:p1:1", "X:p20:1"]
    assert everything[0]["reasons"] == ["contradicted", "checker_disagrees"]
    assert everything[0]["claim_ids"] == ["c01"]
    assert everything[1]["reasons"] == ["contradicted", "possibly_missed"]
    assert everything[1]["claim_ids"] == [] and everything[1]["clause_ids"] == [
        "elig-debts", "prio-category"]
    # Possibly missed alone comes after every flagged claim and pair.
    only_missed = [i["reasons"] == ["possibly_missed"] for i in everything]
    assert only_missed == sorted(only_missed)
    assert [i["rank"] for i in everything] == list(range(1, len(everything) + 1))


def test_scan_threshold_is_its_recorded_method_applied_to_a0142():
    """The threshold was set on A-0142 with its own gold.json, before any evaluation; the
    committed scan reproduces it, and scan.json says how it was chosen."""
    scan = json.loads((A_RUN / "scan.json").read_text(encoding="utf-8"))
    gold = json.loads((CASES_DIR / THRESHOLD_CASE / "gold.json").read_text(encoding="utf-8"))
    assert scan["threshold"] == SCAN_THRESHOLD
    assert scan["threshold_set_on"] == THRESHOLD_CASE and "gold.json" in scan["threshold_how"]
    assert scan["passages_scanned"] == len(case_passages("A-0142")[1])
    assert choose_threshold(scan["scores"], gold["required_reading"]) == SCAN_THRESHOLD


def test_a0142_debts_clause_holds_the_ledger_contradiction():
    """The replayed demo run: Jev itself called the January and March ledgers contradictory
    under the Debts clause (nothing in the code names that pair)."""
    view = json.loads((A_RUN / "view.json").read_text(encoding="utf-8"))
    pairs = clause(view, "elig-debts")["contradictions"]
    assert ("p8", "p23") in {(page_of(p["a"]), page_of(p["b"])) for p in pairs}
    assert len(view["required_reading"]) <= CAP
    listed = [i["passage_id"] for i in view["required_reading"] + view["suggested_reading"]]
    assert len(listed) == len(set(listed))
    validate_view(view)
