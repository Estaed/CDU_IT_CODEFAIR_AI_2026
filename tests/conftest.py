"""Shared test seams: a fixed writer and a fixed checker stand in for Claude and Jev."""

import pytest

from readmark import POLICIES_DIR
from readmark.jev import date_order

PDFS_PRESENT = all(
    (POLICIES_DIR / f).exists()
    for f in (
        "eligibility-for-social-housing-policy.pdf",
        "priority-housing-policy.pdf",
        "identification-and-documentation-policy.pdf",
        "domestic-family-violence-policy.pdf",
        "discretionary-decision-making-policy.pdf",
    )
)
needs_pdfs = pytest.mark.skipif(not PDFS_PRESENT, reason="policy PDFs not downloaded (README)")


class FixedWriter:
    name = "fixed"
    model_id = "fixed-writer"

    def __init__(self, facts: list[dict]):
        self.facts = facts

    def write(self, case_meta, case_passages, clauses, policy_by_id):
        return {"facts": self.facts}


class FixedChecker:
    """Says 'supports' unless a claim id is listed with another verdict.

    It also fills Jev's two cross-passage jobs, so a test never reaches the network: the scan
    gives every passage 0 unless ``scores`` lists it (``{clause_id: {passage_id: score}}``), and
    a pair is 'agree' unless ``contradict`` lists it (passage-id pairs, either order)."""

    name = "fixed"
    model_id = "fixed-checker"

    def __init__(self, verdicts: dict[str, tuple[str, float]] | None = None,
                 scores: dict[str, dict[str, float]] | None = None,
                 contradict: list[tuple[str, str]] = ()):
        self.verdicts = verdicts or {}
        self.scores = scores or {}
        self.contradict = {frozenset(p) for p in contradict}
        self.compared: list[tuple[str, str, str]] = []

    def scan(self, clauses, passages):
        return {
            c["clause_id"]: {p["passage_id"]: self.scores.get(c["clause_id"], {})
                             .get(p["passage_id"], 0.0) for p in passages}
            for c in clauses
        }

    def compare(self, jobs):
        out = []
        for job in jobs:
            a, b = sorted([job["a"], job["b"]], key=date_order)
            hit = frozenset((a["passage_id"], b["passage_id"])) in self.contradict
            self.compared.append((job["clause"]["clause_id"], a["passage_id"], b["passage_id"]))
            out.append({
                "clause_id": job["clause"]["clause_id"], "a": a["passage_id"],
                "b": b["passage_id"], "verdict": "contradict" if hit else "agree",
                "probabilities": {"agree": 0.1 if hit else 0.9,
                                  "contradict": 0.9 if hit else 0.1, "unrelated": 0.0},
            })
        return out

    def check(self, items):
        return [
            {
                "claim_id": i["claim_id"],
                "verdict": self.verdicts.get(i["claim_id"], ("supports", 0.9))[0],
                "probability": self.verdicts.get(i["claim_id"], ("supports", 0.9))[1],
                "supports": None,
            }
            for i in items
        ]


def fact(clause_id, claim, *citations, found=True):
    return {
        "clause_id": clause_id,
        "claim": claim,
        "found": found,
        "citations": [{"passage_id": p, "quote": q} for p, q in citations],
    }


# A small, honest writer output for the stub case (passage ids from data/cases/stub/case.md).
STUB_FACTS = [
    fact("elig-debts", "In January the applicant owed $2,400 in arrears on a former tenancy.",
         ("stub:p2:2", "Arrears balance $2,400.00.")),
    fact("elig-debts", "By March the arrears were cleared in full.",
         ("stub:p3:2", "Arrears cleared in full. Balance $0.00.")),
    fact("elig-former-tenancy", "The previous tenancy ended by mutual agreement in June 2023.",
         ("stub:p4:1", "ended by mutual agreement on 12 June 2023")),
    fact("prio-category", "The applicant and her two children are fleeing family violence.",
         ("stub:p5:2", "Ms K. and her two children are fleeing family violence")),
    fact("elig-income", "The file holds no income statement.", found=False),
]


@pytest.fixture
def stub_facts():
    return [dict(f, citations=list(f["citations"])) for f in STUB_FACTS]
