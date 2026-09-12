"""Deficit-language lint over everything the project writes, plus the check itself."""

from pathlib import Path

from fair_turn.core import wording

ROOT = Path(__file__).resolve().parent.parent
DEFINITION = "DEFICIT_TERMS = ("


def _scanned() -> list[Path]:
    files = sorted((ROOT / "fair_turn").rglob("*.py")) + [ROOT / "docs" / "PRD.md"]
    build = ROOT / "data" / "build"
    if build.exists():
        files += sorted(build.rglob("*.json")) + sorted(build.rglob("*.csv"))
    return files


def test_no_deficit_language_in_repo() -> None:
    bad = {}
    for f in _scanned():
        text = "\n".join(
            line for line in f.read_text("utf-8").splitlines() if DEFINITION not in line
        )
        terms = [t for t in wording.check(text) if t != wording.READING_LEVEL]
        if terms:
            bad[str(f.relative_to(ROOT))] = terms
    assert not bad, bad


def test_check_finds_terms() -> None:
    assert wording.check("The vulnerable tenant") == ["vulnerable"]
    assert wording.check("Flagged as At-Risk and non-compliant.") == ["at-risk", "non-compliant"]
    assert wording.check("Vulnerability scan") == ["vulnerability"]


def test_check_plain_sentence_passes() -> None:
    plain = (
        "The tap in the kitchen leaks all day. A crew will come on Monday. "
        "They will fix the tap and check the sink. You do not need to do anything. "
        "Call us if the water gets worse before then."
    )
    assert wording.check(plain) == []


def test_check_reading_level() -> None:
    dense = (
        "Notwithstanding the aforementioned considerations, the remediation methodology "
        "necessitates comprehensive infrastructural reassessment prior to implementation."
    )
    assert wording.check(dense) == [wording.READING_LEVEL]
