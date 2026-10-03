"""Code checks and the reading gate."""

from conftest import fact

from readmark.checks import check_fact, claim_reasons, claim_status, values_missing
from readmark.checks.cross import contradicted_by
from readmark.gate import CAP, required_reading
from readmark.ingest import case_passages

PASSAGES = {p["passage_id"]: p for p in case_passages("stub")[1]}


def test_fabricated_quote_fails_the_code_check():
    f = fact("elig-debts", "The applicant still owes rent.",
             ("stub:p3:2", "Arrears remain outstanding at $2,400."))
    result = check_fact(f, PASSAGES)
    assert result["passed"] is False
    assert result["citations"][0]["quote_found"] is False


def test_citation_to_missing_passage_fails():
    f = fact("elig-debts", "Arrears were cleared.", ("stub:p99:1", "Arrears cleared in full."))
    result = check_fact(f, PASSAGES)
    assert result["passed"] is False and result["citations"][0]["passage_exists"] is False


def test_stale_claim_citing_only_the_january_ledger_is_caught_by_the_pair_not_the_code_check():
    """The gap Task-00 measured, now closed: the stub's January ledger (the scenario's p.8)
    still says $2,400, so 'arrears $2,400' citing only it is a real quote with a matching number
    and passes the code check. The contradiction pair with the March ledger (p.23) flags it."""
    f = fact("elig-debts", "The applicant has rent arrears of $2,400.",
             ("stub:p2:2", "Arrears balance $2,400.00."))
    result = check_fact(f, PASSAGES)
    assert result["passed"] is True  # code checks alone still cannot see it

    pairs = [{"a": "stub:p2:2", "b": "stub:p3:2", "probability": 0.69}]
    by = contradicted_by(result["citations"], pairs)
    assert by == ["stub:p3:2"]
    reasons = claim_reasons(result, {"verdict": "supports", "probability": 0.9}, by)
    assert claim_status(reasons) == "contradicted"


def test_number_or_date_absent_from_the_quotes_fails():
    f = fact("elig-debts", "Arrears of $3,400 were cleared in March 2026.",
             ("stub:p3:2", "Arrears cleared in full. Balance $0.00."))
    result = check_fact(f, PASSAGES)
    assert result["passed"] is False
    assert set(result["values_missing"]) == {"3,400", "March", "2026"}


def test_values_compare_by_value_and_ignore_page_references():
    quotes = ["Statement date 15 Jan 2026.", "Arrears balance $2,400.00."]
    assert values_missing("Arrears of $2,400 in January 2026 (p. 2, §3.4).", quotes) == []
    assert values_missing("The delegate may use discretion.", []) == []


def _claim(i, status, clause="elig-debts", verdict=None, prob=None):
    return {
        "claim_id": f"c{i:02d}",
        "clause_id": clause,
        "status": status,
        "checker": {"verdict": verdict, "probability": prob} if verdict else None,
        "citations": [{"passage_id": f"stub:p{i}:1"}],
    }


def test_required_reading_is_capped_at_eight_and_ordered():
    claims = [_claim(i, "checker_disagrees", verdict="not_enough_information", prob=0.5)
              for i in range(1, 11)]
    claims.append(_claim(11, "quote_not_found"))
    claims.append(_claim(12, "checker_disagrees", verdict="contradicts", prob=0.99))
    claims.append(_claim(13, "supported", verdict="supports", prob=0.99))
    gate = required_reading(claims, ["elig-debts"])

    assert CAP == 8
    assert len(gate["required"]) == 8
    assert len(gate["suggested"]) == 4  # 12 flagged passages in total; supported ones never
    order = [i["passage_id"] for i in gate["required"]]
    assert order[:2] == ["stub:p12:1", "stub:p11:1"]  # contradiction, then quote not found
    assert [i["rank"] for i in gate["required"]] == list(range(1, 9))
    assert "stub:p13:1" not in order + [i["passage_id"] for i in gate["suggested"]]


def test_clause_order_breaks_ties():
    claims = [_claim(1, "quote_not_found", clause="prio-category"),
              _claim(2, "quote_not_found", clause="elig-residency")]
    gate = required_reading(claims, ["elig-residency", "prio-category"])
    assert [i["passage_id"] for i in gate["required"]] == ["stub:p2:1", "stub:p1:1"]
