"""The user guide has the seven required sections, its walkthrough passes the wording
check, README links it, and every page renders it in a "How to use" popover
(Task 50)."""

import re
import socket
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from fair_turn.core import wording

ROOT = Path(__file__).resolve().parent.parent
GUIDE = ROOT / "docs" / "user-guide.md"
APP = ROOT / "fair_turn" / "app"
PAGE_FILES = sorted(p.stem for p in (APP / "pages").glob("*.py"))
SECTION_RX = re.compile(r"^## (\d+)\. (.+)$", re.MULTILINE)
EXPECTED_HEADINGS = [
    "What Fair Turn is",
    "Who uses which page",
    "A coordinator's morning, step by step",
    "How to test intake",
    "The keyboard path",
    "Glossary",
    "Where the numbers come from",
]


def _refuse(*args, **kwargs):
    raise RuntimeError("network disabled")


@pytest.fixture
def no_network(monkeypatch):
    monkeypatch.setattr(socket, "socket", _refuse)


def _sections() -> dict[int, tuple[str, str]]:
    text = GUIDE.read_text(encoding="utf-8")
    matches = list(SECTION_RX.finditer(text))
    out = {}
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[int(m.group(1))] = (m.group(2).strip(), text[start:end].strip())
    return out


def test_guide_has_the_seven_sections_in_order() -> None:
    text = GUIDE.read_text(encoding="utf-8")
    headings = [m.group(2).strip() for m in SECTION_RX.finditer(text)]
    assert headings == EXPECTED_HEADINGS
    numbers = [int(m.group(1)) for m in SECTION_RX.finditer(text)]
    assert numbers == [1, 2, 3, 4, 5, 6, 7]


def test_guide_is_between_120_and_180_lines() -> None:
    lines = GUIDE.read_text(encoding="utf-8").splitlines()
    assert 120 <= len(lines) <= 180


def test_guide_uses_lf_line_endings() -> None:
    raw = GUIDE.read_bytes()
    assert b"\r\n" not in raw


def test_readme_links_the_guide() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "docs/user-guide.md" in readme


def test_walkthrough_paragraphs_pass_the_wording_check() -> None:
    _, body = _sections()[3]
    blocks = [b for b in re.split(r"\n\n", body) if b.strip()]
    numbered = next(b for b in blocks if b.startswith("1."))
    steps = re.split(r"\n(?=\d+\. )", numbered)
    for block in [b for b in blocks if not b.startswith("1.")] + steps:
        assert wording.check(block) == [], block


def test_guide_has_no_deficit_language() -> None:
    text = GUIDE.read_text(encoding="utf-8").lower()
    assert not any(term in text for term in wording.DEFICIT_TERMS)


@pytest.mark.parametrize("page", PAGE_FILES)
def test_how_to_use_popover_renders_guide_sections_1_and_3(page, no_network) -> None:
    at = AppTest.from_file(str(APP / "pages" / f"{page}.py")).run(timeout=60)
    assert not at.exception
    heading_1, text_1 = _sections()[1]
    # Other popovers exist on a page (a long policy passage opens in one); the guide's is
    # the one that starts with the guide's first heading.
    popovers = [
        p
        for p in at.main.get("popover")
        if p.get("markdown") and p.get("markdown")[0].value == f"**{heading_1}**"
    ]
    assert len(popovers) == 1
    body = "\n".join(m.value for m in popovers[0].get("markdown"))
    heading_3, text_3 = _sections()[3]
    assert heading_1 in body
    assert heading_3 in body
    # A source phrase from each section proves the real file was read, not a stub.
    assert text_1.splitlines()[0] in body
    assert "Read the numbers at the top of the Workspace" in body
