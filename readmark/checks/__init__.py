"""Code checks: deterministic, no model.

1. Each quote is in its cited passage after whitespace normalisation.
2. Every number and date in the claim appears in one of its cited quotes.

A failure is shown as "quote not found" and is never dropped. Negation is deliberately not
checked: "will not be withheld" against "not eligible" defeats any word count (notes, System).
What these checks cannot see is a quote that is real but out of date: "arrears $2,400" citing
the January ledger passes here, and only the checker or a contradiction pair can catch it
(``readmark.checks.cross``).

``claim_reasons`` folds the three kinds of check into one claim status, in the order the screen
ranks them: contradicted by another passage, quote not found, checker disagrees.
"""

import re
from decimal import Decimal

from readmark.ingest import normalise

_MONTH_NAMES = ["january", "february", "march", "april", "may", "june", "july", "august",
                "september", "october", "november", "december"]
MONTHS = {name: i for i, full in enumerate(_MONTH_NAMES, start=1) for name in (full, full[:3])}
MONTHS["sept"] = 9

_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
# A month counts only next to a day or a year, so "may" the verb is not read as May.
_M = "|".join(sorted(MONTHS, key=len, reverse=True))
_MONTH = re.compile(rf"\b\d{{1,2}}\s+({_M})\b|\b({_M})\b\.?,?\s+\d{{4}}", re.IGNORECASE)
# References to pages and sections are pointers, not facts, so they are not checked as numbers.
_REFERENCE = re.compile(
    r"\b(?:pp?|pages?)\.?\s*\d+(?:\s*(?:-|–|and|,)\s*\d+)*|§\s*[\d.]*\d", re.IGNORECASE
)


def _value(raw: str) -> Decimal:
    return Decimal(raw.replace(",", ""))


def _numbers(text: str) -> set[Decimal]:
    return {_value(raw) for raw in _NUMBER.findall(text)}


def _month_hits(text: str) -> list[str]:
    return [(a or b) for a, b in _MONTH.findall(text)]


def quote_present(quote: str, passage_text: str | None) -> bool:
    needle = normalise(quote)
    return bool(passage_text) and bool(needle) and needle in normalise(passage_text)


def values_missing(claim: str, quotes: list[str]) -> list[str]:
    """Numbers and months in the claim that none of its quotes contain.

    Numbers compare by value ("$2,400" matches "$2,400.00"); a month in the claim must appear in
    a quote by name or abbreviation ("March 2026" matches "4 Mar 2026")."""
    claim_text = _REFERENCE.sub(" ", claim)
    joined = " ".join(quotes)
    have_numbers = _numbers(joined)
    have_months = {MONTHS[m.lower()] for m in _month_hits(joined)}
    missing = [raw for raw in _NUMBER.findall(claim_text) if _value(raw) not in have_numbers]
    missing += [m for m in _month_hits(claim_text) if MONTHS[m.lower()] not in have_months]
    return missing


def check_fact(fact: dict, passages_by_id: dict[str, dict]) -> dict:
    """The code-check result for one writer fact."""
    citations = []
    for c in fact.get("citations", []):
        passage = passages_by_id.get(c["passage_id"])
        citations.append(
            {
                "passage_id": c["passage_id"],
                "passage_exists": passage is not None,
                "quote_found": quote_present(c["quote"], passage and passage["text"]),
            }
        )
    found_quotes = [c["quote"] for c, r in zip(fact.get("citations", []), citations, strict=True)
                    if r["quote_found"]]
    missing = values_missing(fact["claim"], found_quotes)
    # A fact marked found must cite at least one passage (writer contract: 1 to n citations).
    # One that arrives with none has nothing a reader can check, so it fails here and shows
    # "quote not found"; it can never look supported.
    quotes_ok = bool(citations) and all(r["quote_found"] for r in citations)
    return {
        "citations": citations,
        "values_missing": missing,
        "passed": quotes_ok and not missing,
    }


def claim_reasons(check: dict, verdict: dict | None, contradicted: list[str]) -> list[str]:
    """Every check a claim failed, most decisive first. Its status is the first, or
    "supported" when the list is empty.

    A checker verdict of "contradicts" is the checker disagreeing with the claim on its own
    passages; "contradicted" is reserved for a contradiction pair (another passage)."""
    reasons = ["contradicted"] if contradicted else []
    if not check["passed"]:
        reasons.append("quote_not_found")
    elif not verdict or verdict.get("verdict") != "supports":
        reasons.append("checker_disagrees")
    return reasons


def claim_status(reasons: list[str]) -> str:
    return reasons[0] if reasons else "supported"
