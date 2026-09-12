"""Deficit-language lexicon and reading-level check for every text this project writes."""

import re

import textstat

DEFICIT_TERMS = ("vulnerable", "vulnerability", "at-risk", "non-compliant", "dysfunctional")
MAX_READING_GRADE = 7  # Flesch-Kincaid grade ceiling for tenant-facing text (PRD section 7)
READING_LEVEL = "reading_level"
MIN_WORDS_FOR_READING_LEVEL = 10  # Flesch-Kincaid is noise on a fragment

_TERM_RX = re.compile(
    r"(?<![\w-])(" + "|".join(map(re.escape, DEFICIT_TERMS)) + r")(?![\w-])", re.I
)


def check(text: str) -> list[str]:
    """Return offending deficit terms (lower-cased, in order of first appearance), plus
    ``"reading_level"`` when the Flesch-Kincaid grade exceeds ``MAX_READING_GRADE``."""
    found: list[str] = []
    for m in _TERM_RX.finditer(text):
        term = m.group(1).lower()
        if term not in found:
            found.append(term)
    long_enough = len(text.split()) >= MIN_WORDS_FOR_READING_LEVEL
    if long_enough and textstat.flesch_kincaid_grade(text) > MAX_READING_GRADE:
        found.append(READING_LEVEL)
    return found
