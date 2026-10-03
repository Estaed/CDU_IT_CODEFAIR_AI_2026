"""Checklist: the approved decisive clauses, each anchored to its verbatim policy sentence."""

from pathlib import Path

from readmark.ingest import IngestError, normalise
from readmark.checklist.lists import (
    DEFAULT_LIST_ID,
    QUESTION_LISTS_DIR,
    case_question_list,
    list_question_lists,
    load_question_list,
    read_yaml,
    set_case_question_list,
    validate_clauses,
)

__all__ = ["DEFAULT_LIST_ID", "QUESTION_LISTS_DIR", "case_question_list", "list_question_lists",
           "load_question_list", "set_case_question_list", "load_clauses", "anchor",
           "CLAUSES_FILE", "CLAUSE_IDS"]

CLAUSES_FILE = QUESTION_LISTS_DIR / DEFAULT_LIST_ID / "clauses.yaml"
# Compatibility for the frozen housing writer, audit and evaluation contracts.
CLAUSE_IDS = tuple(c["clause_id"] for c in load_question_list()["clauses"])


def load_clauses(path: Path | None = None, *, question_list: dict | None = None) -> list[dict]:
    if path is not None:
        return validate_clauses(read_yaml(path), path)
    spec = question_list if question_list is not None else load_question_list()
    return spec["clauses"]


def anchor(clauses: list[dict], policy_passages: list[dict]) -> list[dict]:
    """Attach the policy passage id that holds each clause sentence (and each list item).

    Stops if a sentence is not in its policy word for word: a clause must never rest on a
    paraphrase."""
    out = []
    for clause in clauses:
        own = [p for p in policy_passages if p["policy"] == clause["policy"]]

        def find(text: str, _own: list[dict] = own, _clause: dict = clause) -> str:
            hits = [p["passage_id"] for p in _own if normalise(text) in p["text"]]
            if not hits:
                raise IngestError(
                    f"{_clause['clause_id']}: sentence not found verbatim in the "
                    f"{_clause['policy']} policy: {text[:80]}"
                )
            return hits[0]

        out.append(
            {
                **clause,
                "passage_id": find(clause["sentence"]),
                "item_passage_ids": [find(i) for i in clause.get("items", [])],
            }
        )
    return out
