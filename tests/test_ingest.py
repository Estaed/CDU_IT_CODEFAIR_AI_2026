"""Ingest: pinned PDFs, contract-format case files, and clause sentences found verbatim."""

import csv
import json
import shutil

import pytest
from conftest import needs_pdfs

from readmark import CASES_DIR, POLICIES_DIR
from readmark.checklist import CLAUSE_IDS, anchor, load_clauses
from readmark.ingest import IngestError, case_passages, normalise, policy_passages


@needs_pdfs
def test_changed_policy_pdf_stops_ingest_naming_file_and_expected_sha(tmp_path):
    for pdf in POLICIES_DIR.glob("*.pdf"):
        shutil.copy(pdf, tmp_path / pdf.name)
    shutil.copy(POLICIES_DIR / "policies.lock.json", tmp_path / "policies.lock.json")
    target = tmp_path / "priority-housing-policy.pdf"
    data = bytearray(target.read_bytes())
    data[len(data) // 2] ^= 0x01  # one byte changed
    target.write_bytes(bytes(data))
    expected = json.loads((tmp_path / "policies.lock.json").read_text())[target.name]["sha256"]

    with pytest.raises(IngestError) as err:
        policy_passages(tmp_path)
    assert "priority-housing-policy.pdf" in str(err.value)
    assert expected in str(err.value)


def test_missing_policy_pdf_stops_ingest(tmp_path):
    shutil.copy(POLICIES_DIR / "policies.lock.json", tmp_path / "policies.lock.json")
    with pytest.raises(IngestError, match="missing"):
        policy_passages(tmp_path)


def test_stub_case_passage_ids_follow_the_contract():
    meta, passages = case_passages("stub")
    assert meta["pages"] == 6
    ids = [p["passage_id"] for p in passages]
    assert ids[:2] == ["stub:p1:1", "stub:p1:2"]
    assert "stub:p2:2" in ids and "stub:p3:2" in ids
    ledger = next(p for p in passages if p["passage_id"] == "stub:p2:2")
    assert "Former tenancy debt owed to the CEO (Housing)." in ledger["text"]
    assert ledger["doc_type"] == "ledger"


def test_case_pages_must_be_consecutive(tmp_path):
    bad = tmp_path / "case.md"
    bad.write_text("<!-- page 1 -->\nA.\n\n<!-- page 3 -->\nB.\n", encoding="utf-8")
    with pytest.raises(IngestError, match="out of order"):
        case_passages("x", bad)


def test_stub_case_files_match_the_contract():
    """Task-01's validator walks data/cases/, so the stub must be exact."""
    folder = CASES_DIR / "stub"
    text = (folder / "case.md").read_text(encoding="utf-8")
    pages = {}
    for chunk in text.split("<!-- page ")[1:]:
        number, _, body = chunk.partition(" -->")
        pages[int(number)] = normalise(body)
    assert sorted(pages) == list(range(1, len(pages) + 1))
    assert "income statement" not in text.lower()

    with (folder / "facts.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert list(rows[0]) == ["fact_id", "clause_id", "statement", "value", "page", "quote",
                             "role", "trap", "decisive"]
    for row in rows:
        assert row["clause_id"] in CLAUSE_IDS
        assert row["role"] in {"supports", "against", "contradicts", "stale", "missing"}
        assert row["trap"] in {"none", "stale_value", "contradiction", "omission",
                               "policy_misread", "exclusion_2yr", "missing_doc", "discretion"}
        assert row["decisive"] in {"yes", "no"}
        if row["role"] == "missing":
            assert row["page"] == "" and row["quote"] == ""
        else:
            assert normalise(row["quote"]) in pages[int(row["page"])], row["fact_id"]

    gold = json.loads((folder / "gold.json").read_text(encoding="utf-8"))
    assert set(gold) == {"case_id", "outcomes", "correct_decision", "required_reading",
                         "rationale"}
    assert gold["case_id"] == "stub"
    assert set(gold["outcomes"]) == set(CLAUSE_IDS) == set(gold["rationale"])
    assert set(gold["outcomes"].values()) <= {"met", "not_met", "cannot_decide",
                                              "not_applicable"}
    assert gold["correct_decision"] in {"approve", "decline", "request_information"}
    assert all(p.startswith("p") and int(p[1:]) in pages for p in gold["required_reading"])


@needs_pdfs
def test_every_clause_sentence_is_verbatim_in_its_policy():
    clauses = anchor(load_clauses(), policy_passages())
    assert [c["clause_id"] for c in clauses] == list(CLAUSE_IDS)
    assert {c["clause_id"]: c["passage_id"] for c in clauses}["elig-debts"] == "eligibility:p6:9"
