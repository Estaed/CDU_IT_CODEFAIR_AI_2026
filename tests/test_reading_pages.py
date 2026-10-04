"""The capped reading surface is pages; a record chain cannot consume the whole cap."""

import json

import pytest

from readmark import ROOT
from readmark.eval.pair_retry import measurements
from readmark.gate import required_reading
from readmark.record import RecordError, validate


def test_one_page_preserves_each_passages_own_reasons_and_clauses():
    claims = [{"claim_id": "c1", "clause_id": "income", "status": "quote_not_found",
               "citations": [{"passage_id": "X-d1:p2:1"}]}]
    missed = [{"clause_id": "residency", "passage_id": "X-d1:p2:4", "score": 4},
              {"clause_id": "income", "passage_id": "X-d2:p2:1", "score": 3}]
    gate = required_reading(claims, ["income", "residency"], cap=1, possibly_missed=missed)
    page = gate["required"][0]
    assert page["passage_ids"] == ["X-d1:p2:1", "X-d1:p2:4"]
    assert page["clause_ids"] == ["income", "residency"]
    assert page["reasons"] == ["quote_not_found", "possibly_missed"]
    assert page["passages"][1]["clause_ids"] == ["residency"]
    assert page["passages"][1]["reasons"] == ["possibly_missed"]
    assert gate["suggested"][0]["passage_id"] == "X-d2:p2:1"


def test_transitive_updates_share_pages_and_keep_strongest_pair_without_hiding_conflicts():
    pairs = [
        {"clause_id": "record", "a": "X:p1:1", "b": "X:p2:1",
         "relation": "updated", "probability": 1},
        # Connect through a different paragraph of the same page.
        {"clause_id": "record", "a": "X:p2:3", "b": "X:p3:1",
         "relation": "updated", "probability": 0.9},
        {"clause_id": "record", "a": "X:p3:1", "b": "X:p4:1",
         "relation": "updated", "probability": 0.8},
        {"clause_id": "other", "a": "X:p5:1", "b": "X:p6:1",
         "relation": "contradict", "probability": 0.7},
    ]
    gate = required_reading([], ["record", "other"], cap=5, contradictions=pairs,
                            possibly_missed=[{"clause_id": "other", "passage_id": "X:p7:1",
                                              "score": 4}])
    assert [i["passage_id"] for i in gate["required"]] == [
        "X:p1:1", "X:p2:1", "X:p5:1", "X:p6:1", "X:p7:1"]
    assert [i["passage_id"] for i in gate["suggested"]] == ["X:p3:1", "X:p4:1"]
    assert gate["required"][1]["passage_ids"] == ["X:p2:1", "X:p2:3"]


def test_cited_evidence_fills_unused_slots_without_changing_a_claim_check():
    claims = [{"claim_id": f"c{n}", "clause_id": "question", "status": "supported",
               "citations": [{"passage_id": pid}]} for n, pid in enumerate(
                   ["X:p1:1", "X:p2:1", "X:p2:2", "policy:p1:1"])]
    passages = {c["citations"][0]["passage_id"]: {"source": "case"} for c in claims[:-1]}
    gate = required_reading(claims, ["question"], cap=1, passages=passages)
    assert gate["required"][0]["passage_id"] == "X:p2:1"
    assert gate["required"][0]["reasons"] == ["cited"]
    assert all(c["status"] == "supported" for c in claims)
    assert [i["passage_id"] for i in gate["suggested"]] == ["X:p1:1"]


def test_record_accepts_another_known_paragraph_on_the_required_page():
    view = json.loads((ROOT / "runs/A-0142/view.json").read_text(encoding="utf-8"))
    chosen = next(r for r in view["required_reading"] if len(r["passage_ids"]) > 1)
    alternate = next(pid for pid in chosen["passage_ids"] if pid != chosen["passage_id"])
    opened = [{"passage_id": alternate if r is chosen else r["passage_id"],
               "seconds_in_view": 3, "opened_at": "2026-10-04T00:00:00Z"}
              for r in view["required_reading"]]
    payload = {"decision": "request_information", "reason": "Need further evidence.",
               "clause_outcomes": {c["clause_id"]: "cannot_decide" for c in view["clauses"]
                                   if c["clause_id"] != "other"}, "passages_opened": opened}
    validate(payload, view)
    opened[0]["seconds_in_view"] = 0
    with pytest.raises(RecordError, match="at least 3 seconds"):
        validate(payload, view)


def test_every_case_retains_its_baseline_gold_coverage_and_trap_touches():
    measurements()  # checks page coverage and passage/quote-specific traps, without live models
