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
    from conftest import FixedChecker

    f['claim_id'] = 'c01'
    by = contradicted_by([f], {'c01': result}, pairs, PASSAGES,
                         FixedChecker(verdicts={'c01@stub:p3:2': ('contradicts', 0.9)}))['c01']
    assert by == ["stub:p3:2"]
    reasons = claim_reasons(result, {"verdict": "supports", "probability": 0.9}, by)
    assert claim_status(reasons) == "contradicted"


def test_number_or_date_absent_from_all_cited_evidence_fails():
    f = fact("elig-debts", "Arrears of $3,400 were cleared in April 2026.",
             ("stub:p3:2", "Arrears cleared in full. Balance $0.00."))
    result = check_fact(f, PASSAGES)
    assert result["passed"] is False
    assert set(result["values_missing"]) == {"3,400", "April 2026"}


def test_date_in_the_document_header_and_amount_elsewhere_in_the_passage_pass():
    passages = {'case:p1:1': {'text': 'Charge $615.40. The account remains under review.',
                            'doc_title': 'Account review, 1 October 2026',
                            'doc_date': '2026-10-01'}}
    claim = fact('elig-debts', 'The $615.40 charge is under review on 1 October 2026.',
                 ('case:p1:1', 'The account remains under review.'))
    assert check_fact(claim, passages)['passed']
    passages['case:p1:1']['doc_title'] = 'Account review'
    assert check_fact(claim, passages)['passed']  # date only in the header's date field
    passages['case:p1:1']['doc_date'] = None
    assert check_fact(claim, passages)['values_missing'] == ['1 October 2026']
    claim['claim'] = 'The $616.40 charge is under review.'
    assert check_fact(claim, passages)['values_missing'] == ['616.40']
    passages['uncited:p2:1'] = {'text': 'Charge $616.40.', 'doc_date': '2026-10-01'}
    assert not check_fact(claim, passages)['passed']  # uncited evidence cannot rescue it
    claim['citations'][0]['quote'] = 'Invented quote.'
    claim['claim'] = 'The $615.40 charge is under review on 1 October 2026.'
    assert set(check_fact(claim, passages)['values_missing']) == {'615.40', '1 October 2026'}


def test_date_ranges_match_as_connected_dates_not_independent_digits():
    forms = ['21–27 February 2026', '21-27 Feb 2026',
             '21 February to 27 February 2026',
             '21 February 2026 to 27 February 2026', '2026-02-21 to 2026-02-27']
    for claim in forms:
        for source in forms:
            assert values_missing(claim, [source]) == []
    for wrong in ['20–27 February 2026', '21–28 February 2026', '21–27 March 2026',
                  '21–27 February 2025', '2026-02-21 to 2026-03-27', '27–21 February 2026']:
        assert values_missing(wrong, [forms[0]])
    assert values_missing(forms[0], ['21 February 2026', '27 February 2026']) == []
    assert values_missing(forms[0], ['Commenced 21 February 2026 and ended 27 February 2026.']) == []
    assert values_missing(forms[0], ['21 January 2026', '27 February 2025'])
    assert values_missing('31–32 February 2026', [forms[0]])


def test_values_compare_by_value_and_ignore_page_references():
    quotes = ["Statement date 15 Jan 2026.", "Arrears balance $2,400.00."]
    assert values_missing("Arrears of $2,400 in January 2026 (p. 2, §3.4).", quotes) == []
    assert values_missing("The delegate may use discretion.", []) == []


def test_equivalent_dates_and_identifiers_match_without_losing_absent_values():
    quotes = ['Reference A-0142. Consultation 2026-03-15.']
    for claim in ['15 Mar', '15 March 2026', 'March 2026', 'A0142', 'A-0142']:
        assert values_missing(claim, quotes) == []
    assert values_missing('January 2026', ['Recorded 2026-01-31.']) == []
    assert values_missing('2026-03-15', ['Consultation 15 Mar 2026.']) == []
    for claim in ['16 Mar', '15 March 2025', 'January 2026', 'A0143', '$3400']:
        assert values_missing(claim, quotes)
    # Date components cannot be borrowed across dates, amounts, or separate quotes.
    assert values_missing('15 March 2026', ['15 January 2026; 16 March 2026.'])
    assert values_missing('15 Mar', ['$15. March 2026.'])
    assert values_missing('15 March 2026', ['15 March', 'Year 2026'])
    assert values_missing('A0142', ['Reference B-0142.'])
    assert values_missing('2026-03-15', ['15 Mar'])
    assert values_missing('$2026', ['Reference A2026.'])


def test_pair_context_uses_case_records_when_a_claim_also_cites_policy():
    from conftest import FixedChecker

    january, march = 'stub:p2:2', 'stub:p3:2'
    passages = {**PASSAGES, 'policy:p1:1': {'source': 'policy', 'text': 'Policy text.'}}
    checks = {'c01': {'citations': [{'passage_id': pid, 'quote_found': True}
                                   for pid in (january, 'policy:p1:1')]}}
    checker = FixedChecker()
    jobs = []
    original = checker.check

    def record(items):
        jobs.extend(items)
        return original(items)

    checker.check = record
    result = contradicted_by([{'claim_id': 'c01', 'claim': 'The January ledger showed arrears.'}],
                             checks, [{'a': january, 'b': march}], passages, checker)
    assert result == {'c01': []}
    assert [p['passage_id'] for p in jobs[0]['context']] == [january]


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


def test_supports_score_rescues_only_nei_and_never_bypasses_other_checks():
    from readmark.checks.supports import SUPPORTS_THRESHOLD, checker_backs

    above = {'verdict': 'not_enough_information', 'supports': SUPPORTS_THRESHOLD + 0.01}
    below = {'verdict': 'not_enough_information', 'supports': SUPPORTS_THRESHOLD - 0.01,
             'probability': 0.99}
    assert checker_backs(above)
    assert checker_backs({**above, 'supports': SUPPORTS_THRESHOLD})
    assert not checker_backs(below)
    assert not checker_backs({'verdict': 'contradicts', 'supports': 1.0})
    assert not checker_backs({'verdict': None, 'supports': 1.0})
    assert checker_backs({'verdict': 'supports', 'supports': 0.0})
    for score in (None, True, '0.9', float('nan'), float('inf'), -0.1, 1.1):
        assert not checker_backs({**above, 'supports': score})
    assert claim_reasons({'passed': True}, above, []) == []
    assert claim_reasons({'passed': True}, below, []) == ['checker_disagrees']
    assert claim_reasons({'passed': False}, above, []) == ['quote_not_found']
    assert claim_reasons({'passed': True}, above, ['another:p1:1']) == ['contradicted']
