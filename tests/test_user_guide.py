"""The user guide has its seven sections, the step-by-step part reads at grade 7 or below,
and README links it."""

import re
from pathlib import Path

from fair_turn.core import wording

ROOT = Path(__file__).resolve().parent.parent
GUIDE = ROOT / "docs" / "user-guide.md"
SECTION_RX = re.compile(r"^## (\d+)\. (.+)$", re.MULTILINE)
EXPECTED_HEADINGS = [
    "What Fair Turn is",
    "The four pages",
    "A coordinator's Monday, step by step",
    "Adding a report",
    "Answering a tenant",
    "Where the numbers come from",
    "Glossary",
]


def _sections() -> dict[int, tuple[str, str]]:
    text = GUIDE.read_text(encoding="utf-8")
    matches = list(SECTION_RX.finditer(text))
    out = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[int(m.group(1))] = (m.group(2).strip(), text[m.end() : end].strip())
    return out


def test_guide_has_the_seven_sections_in_order() -> None:
    assert [heading for heading, _ in _sections().values()] == EXPECTED_HEADINGS


def test_guide_uses_lf_line_endings() -> None:
    assert b"\r\n" not in GUIDE.read_bytes()


def test_readme_links_the_guide() -> None:
    assert "docs/user-guide.md" in (ROOT / "README.md").read_text(encoding="utf-8")


def test_walkthrough_steps_pass_the_wording_check() -> None:
    _, body = _sections()[3]
    for block in (b for b in re.split(r"\n\n", body) if b.strip()):
        assert wording.check(block) == [], block


def test_guide_has_no_deficit_language() -> None:
    text = GUIDE.read_text(encoding="utf-8").lower()
    assert not any(term in text for term in wording.DEFICIT_TERMS)
