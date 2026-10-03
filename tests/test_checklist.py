"""List discovery, validation and case selection without PDFs or model calls."""

import hashlib
import json

import pytest
import yaml

from readmark import POLICIES_DIR
from readmark.checklist import (
    CLAUSE_IDS,
    DEFAULT_LIST_ID,
    case_question_list,
    list_question_lists,
    load_question_list,
    set_case_question_list,
)
from readmark.ingest import IngestError, load_lock


def make_tiny_list(tmp_path):
    lists_dir = tmp_path / "lists"
    folder = lists_dir / "tiny-review"
    policies_dir = folder / "policies"
    policies_dir.mkdir(parents=True)
    policy_file = policies_dir / "rules.txt"
    policy_file.write_text("Applicants must supply proof of enrolment.\n\n"
                           "Applicants must explain their request.\n", encoding="utf-8")
    spec = {
        "id": "tiny-review", "title": "Tiny application review",
        "policies": [{"key": "tiny", "file": "rules.txt", "title": "Application rules",
                      "pin": {"sha256": hashlib.sha256(policy_file.read_bytes()).hexdigest(),
                              "version": "1", "approved": "2026-10-03", "pages": 1,
                              "url": "https://example.test/rules.txt"}}],
    }
    questions = [
        {"clause_id": "enrolment", "policy": "tiny", "title": "Enrolment",
         "source": "Application rules section 1", "decides": "Enrolment evidence is present.",
         "sentence": "Applicants must supply proof of enrolment."},
        {"clause_id": "explanation", "policy": "tiny", "title": "Explanation",
         "source": "Application rules section 2", "decides": "The request is explained.",
         "sentence": "Applicants must explain their request."},
    ]
    (folder / "list.yaml").write_text(yaml.safe_dump(spec), encoding="utf-8")
    (folder / "clauses.yaml").write_text(yaml.safe_dump(questions), encoding="utf-8")
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    (case_dir / "case.md").write_text(
        "<!-- page 1 -->\n## Document: letter | Synthetic application | 2026-10-03\n\n"
        "The student is enrolled.\n", encoding="utf-8"
    )
    set_case_question_list("tiny", "tiny-review", case_dir=case_dir, lists_dir=lists_dir)
    return lists_dir, case_dir, policy_file


def test_default_list_preserves_the_housing_contract():
    spec = load_question_list()
    assert list_question_lists() == [{"id": DEFAULT_LIST_ID, "title": "NT priority housing, urban"}]
    assert tuple(c["clause_id"] for c in spec["clauses"]) == CLAUSE_IDS == (
        "elig-residency", "elig-property", "elig-income", "elig-debts", "elig-former-tenancy",
        "prio-category", "prio-documentation", "prio-discretion",
    )
    assert load_lock(question_list=spec) == json.loads(
        (POLICIES_DIR / "policies.lock.json").read_text(encoding="utf-8")
    )
    assert spec["policies_dir"] == POLICIES_DIR


def test_absent_case_selection_defaults_without_creating_a_file(tmp_path):
    assert case_question_list("new", case_dir=tmp_path) == DEFAULT_LIST_ID
    assert list(tmp_path.iterdir()) == []


def test_second_list_is_discovered_and_case_selection_round_trips(tmp_path):
    lists_dir, case_dir, _ = make_tiny_list(tmp_path)
    assert list_question_lists(lists_dir) == [
        {"id": "tiny-review", "title": "Tiny application review"}
    ]
    assert case_question_list("tiny", case_dir=case_dir, lists_dir=lists_dir) == "tiny-review"
    assert len(load_question_list("tiny-review", lists_dir)["clauses"]) == 2
    before = (case_dir / "question-list.json").read_bytes()
    with pytest.raises(IngestError, match="Cannot load"):
        set_case_question_list("tiny", "unknown", case_dir=case_dir, lists_dir=lists_dir)
    assert (case_dir / "question-list.json").read_bytes() == before


@pytest.mark.parametrize("selection", ["broken json", "[]", '{}',
                                        '{"question_list": "unknown"}',
                                        '{"question_list": "../tiny-review"}'])
def test_bad_selection_never_silently_defaults(tmp_path, selection):
    (tmp_path / "question-list.json").write_text(selection, encoding="utf-8")
    with pytest.raises(IngestError):
        case_question_list("tiny", case_dir=tmp_path)


@pytest.mark.parametrize("defect", ["duplicate_question", "unknown_policy", "missing_sentence",
                                    "duplicate_policy", "bad_hash", "unsafe_filename"])
def test_invalid_list_stops_before_use(tmp_path, defect):
    lists_dir, _, _ = make_tiny_list(tmp_path)
    folder = lists_dir / "tiny-review"
    spec = yaml.safe_load((folder / "list.yaml").read_text(encoding="utf-8"))
    clauses = yaml.safe_load((folder / "clauses.yaml").read_text(encoding="utf-8"))
    if defect == "duplicate_question":
        clauses[1]["clause_id"] = clauses[0]["clause_id"]
    elif defect == "unknown_policy":
        clauses[1]["policy"] = "housing"
    elif defect == "missing_sentence":
        del clauses[0]["sentence"]
    elif defect == "duplicate_policy":
        spec["policies"].append(spec["policies"][0])
    elif defect == "bad_hash":
        spec["policies"][0]["pin"]["sha256"] = "not a hash"
    else:
        spec["policies"][0]["file"] = "../rules.txt"
    (folder / "list.yaml").write_text(yaml.safe_dump(spec), encoding="utf-8")
    (folder / "clauses.yaml").write_text(yaml.safe_dump(clauses), encoding="utf-8")
    with pytest.raises(IngestError):
        load_question_list("tiny-review", lists_dir)
