"""Checklist: the approved decisive clauses, each anchored to its verbatim policy sentence."""

from pathlib import Path

import yaml

from readmark.ingest import IngestError, normalise

CLAUSES_FILE = Path(__file__).resolve().parent / "clauses.yaml"
CLAUSE_IDS = (
    "elig-residency",
    "elig-property",
    "elig-income",
    "elig-debts",
    "elig-former-tenancy",
    "prio-category",
    "prio-documentation",
    "prio-discretion",
)


def load_clauses(path: Path = CLAUSES_FILE) -> list[dict]:
    clauses = yaml.safe_load(path.read_text(encoding="utf-8"))
    ids = tuple(c["clause_id"] for c in clauses)
    if sorted(ids) != sorted(CLAUSE_IDS):
        raise IngestError(f"{path.name} must hold exactly the contract clause ids, got {ids}")
    return clauses


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
