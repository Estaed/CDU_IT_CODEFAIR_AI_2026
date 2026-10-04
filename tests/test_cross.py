"""Cross-passage checks on the demo file A-0142: contradiction pairs, possibly missed, a reading
list that stays capped with one task per passage, and the scan threshold's recorded method."""

import json

from conftest import FixedChecker, FixedWriter, fact, needs_pdfs

from readmark import CASES_DIR, ROOT
from readmark.checks.cross import (
    SCAN_THRESHOLD, THRESHOLD_CASE, choose_threshold, distinct_missed, page_of,
)
from readmark.gate import CAP, required_reading
from readmark.ingest import case_passages
from readmark.cache import Cache
from readmark.jev import CheckerError, JevChecker
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
                           verdicts={f'c01@{MARCH}': ('contradicts', 0.9)},
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
def test_true_claim_on_one_side_of_a_pair_is_not_contradicted(tmp_path):
    cleared = fact('elig-debts', 'The March ledger shows the arrears cleared.',
                   (MARCH, 'Arrears cleared in full.'))
    historical = fact('elig-debts', 'The January ledger showed $2,400 arrears.',
                      (JANUARY, 'Arrears balance $2,400.00.'))
    checker = FixedChecker(scores={'elig-debts': {JANUARY: HIGH, MARCH: HIGH}},
                           contradict=[(JANUARY, MARCH)])
    checked = []
    original = checker.check

    def record(items):
        checked.extend(items)
        return original(items)

    checker.check = record
    view = run('A-0142', writer=FixedWriter([cleared, historical]), checker_impl=checker,
               out_dir=tmp_path)
    assert all(c['status'] == 'supported' and c['contradicted_by'] == [] for c in view['claims'])
    opposing = [i for i in checked if 'context' in i]
    assert len(opposing) == 2
    assert opposing[0]['claim'] == cleared['claim']
    assert opposing[0]['passages'][0]['passage_id'] == JANUARY
    assert opposing[1]['passages'][0]['passage_id'] == MARCH
    assert {JANUARY, MARCH} <= {i['passage_id'] for i in view['required_reading']}
    assert clause(view, 'elig-debts')['contradictions']


def test_possibly_missed_repetitions_keep_the_strongest_fact_and_distinct_values():
    passages = {f'X:p{n}:1': {'text': text} for n, text in enumerate([
        'Income evidence is outstanding.', 'No current income statement has arrived.',
        'Income statement received on 2 March.', 'Income evidence is outstanding.',
    ], start=1)}
    hits = [{'passage_id': pid, 'score': 4 - n / 10}
            for n, pid in enumerate(passages)]
    duplicate = {'X:p2:1': 'X:p1:1'}
    assert distinct_missed(hits, set(), passages, duplicate) == [hits[0], hits[2]]
    assert distinct_missed(hits[1:], {'X:p1:1'}, passages, duplicate) == [hits[2]]
    # A bad model pointer to a later/lower-scored passage cannot hide the strongest fact.
    assert distinct_missed(hits, set(), passages, {'X:p1:1': 'X:p2:1'})[0] == hits[0]


def test_semantic_dedup_uses_confirmed_facts_and_replays_without_network(tmp_path):
    clause = {'clause_id': 'income', 'title': 'Income', 'decides': 'Current income evidence'}
    passages = [{'passage_id': f'X:p{n}:1', 'text': text, 'doc_type': 'letter',
                 'doc_title': 'Income request', 'doc_date': '2026-03-20'}
                for n, text in enumerate([
                    'No current income statement is in the file.',
                    'Current income evidence remains outstanding.',
                    'The officer asked for a statement on 20 March.',
                ], start=1)]
    checker = JevChecker(Cache(tmp_path / 'cache', replay=False))
    bodies = []

    def post(body):
        bodies.append(body)
        if body['questions']['P001']['type'] == 'choice':
            return {'model': 'fixed-jev', 'answers': {
                'P001': {'choice': 'P000', 'confidence': 0.6},
                'P002': {'choice': 'P000', 'confidence': 0.6}}}
        return {'model': 'fixed-jev', 'answers': {'P001': {'noul': 0.99},
                                                'P002': {'noul': 0.3}}}

    checker._post = post
    jobs = [{'clause': clause, 'anchors': [], 'candidates': passages}]
    result = checker.deduplicate(jobs)
    assert result == {'income': {'X:p2:1': 'X:p1:1'}}
    assert len(bodies) == 2  # source selection and binary confirmation
    hits = [{'passage_id': p['passage_id'], 'score': 4 - n / 10}
            for n, p in enumerate(passages)]
    assert distinct_missed(hits, set(), {p['passage_id']: p for p in passages},
                           result['income']) == [hits[0], hits[2]]
    checker.cache.replay = True
    assert checker.deduplicate(jobs) == result
    assert len(bodies) == 2


def test_large_dedup_is_batched_and_an_oversized_batch_keeps_its_passages(tmp_path, monkeypatch):
    # A 104-page upload hit Jev's max_tokens_exceeded; calls now stay under a choice budget.
    monkeypatch.setattr('readmark.jev.DEDUP_CHOICES', 10)
    clause = {'clause_id': 'risk', 'title': 'Risk', 'decides': 'Risk to children'}
    passages = [{'passage_id': f'X:p{n}:1', 'text': f'Fact {n}.', 'doc_type': 'letter',
                 'doc_title': 'Record', 'doc_date': '2026-03-20'} for n in range(8)]
    checker = JevChecker(Cache(tmp_path / 'cache', replay=False))
    bodies = []

    def post(body):
        bodies.append(body)
        if len(bodies) == 1:
            raise CheckerError('Jev returned HTTP 400: max_tokens_exceeded')
        if body['questions'][next(iter(body['questions']))]['type'] == 'choice':
            return {'model': 'fixed-jev', 'answers': {
                k: {'choice': 'P000'} for k in body['questions']}}
        return {'model': 'fixed-jev', 'answers': {k: {'noul': 0.99} for k in body['questions']}}

    checker._post = post
    result = checker.deduplicate([{'clause': clause, 'anchors': passages[:2],
                                   'candidates': passages[2:]}])
    choices = [sum(len(q['criteria']) - 1 for q in b['questions'].values())
               for b in bodies if 'criteria' in next(iter(b['questions'].values()))]
    assert choices == [2 + 3 + 4, 5, 6, 7]  # earlier passages offered per batch, budget 10
    # The oversized first batch (P002-P004) stays visible; later batches still merge.
    assert set(result['risk']) == {'X:p5:1', 'X:p6:1', 'X:p7:1'}


@needs_pdfs
def test_pipeline_only_distinct_missed_facts_compete_for_reading(tmp_path):
    strongest, duplicate = 'A-0142:p19:3', 'A-0142:p19:4'

    class DeduplicatingChecker(FixedChecker):
        def deduplicate(self, jobs):
            assert any([p['passage_id'] for p in j['candidates']] == [strongest, duplicate]
                       for j in jobs)
            return {'elig-property': {duplicate: strongest}}

    checker = DeduplicatingChecker(scores={'elig-property': {strongest: 4, duplicate: 3}})
    view = run('A-0142', writer=FixedWriter([]), checker_impl=checker, out_dir=tmp_path)
    assert clause(view, 'elig-property')['possibly_missed'] == [
        {'passage_id': strongest, 'score': 4}]
    assert [i['passage_id'] for i in view['required_reading']] == [strongest]
    assert duplicate not in view['sources']


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
