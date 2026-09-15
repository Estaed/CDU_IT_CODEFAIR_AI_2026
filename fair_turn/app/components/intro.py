"""PRD section 3 purpose lines and the shared AI transparency footer."""

import re
from pathlib import Path

import streamlit as st

_GUIDE_PATH = Path(__file__).resolve().parents[3] / "docs" / "user-guide.md"
_SECTION_RX = re.compile(r"^## (\d+)\. (.+)$", re.MULTILINE)
_HOW_TO_USE_SECTIONS = (1, 3)  # what Fair Turn is; a coordinator's morning

COPY: dict[str, str] = {
    "workspace": (
        "Fair Turn reads today's repair reports and puts them in a suggested order. You decide "
        "the order that is signed. Nothing here is sent to a crew until you sign it."
    ),
    "review_queue": (
        "Some reports do not say enough for the system to fill a field. Those jobs come here so "
        "a person can fill it in. The system never fills a field on its own."
    ),
    "visit_plan": (
        "This is the run sheet for the jobs you signed. Distance decides which crew goes to "
        "each job. It never decides which jobs are done: that is the list you signed."
    ),
    "tenant": (
        "Here is where your repair sits today, and what moved it there. A housing officer decides "
        "and signs the list; the answer below says whether today's list is signed yet."
    ),
    "evidence_lab": (
        "This page shows how well the system reads reports, measured on the synthetic set. It "
        "shows what it gets wrong as well as what it gets right."
    ),
    "about": (
        "Fair Turn reads free-text repair reports and suggests an order. It does not approve, "
        "refuse or schedule a repair. A housing coordinator decides and signs. Every decision is "
        "logged with who made it and when. The data in this demo is made up. The geography is real "
        "(BushTel/ABS)."
    ),
}


def _guide_sections() -> dict[int, tuple[str, str]]:
    """Return ``{number: (heading, body)}`` for every ``## N. Heading`` block in the
    user guide."""
    text = _GUIDE_PATH.read_text(encoding="utf-8")
    matches = list(_SECTION_RX.finditer(text))
    sections: dict[int, tuple[str, str]] = {}
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[int(m.group(1))] = (m.group(2).strip(), text[start:end].strip())
    return sections


def _how_to_use() -> None:
    """Render the "How to use" popover in the main area, once per page.

    Main area, not the sidebar: in the sidebar the opened panel showed no text in the browser
    (seen 2026-09-14, cause not traced); the main area needs no sidebar theme at all."""
    sections = _guide_sections()
    with st.popover("How to use", icon=":material/help:"):
        for number in _HOW_TO_USE_SECTIONS:
            heading, body = sections[number]
            st.markdown(f"**{heading}**")
            st.markdown(body)


def purpose(page: str) -> None:
    """Render the page purpose immediately below its title, and the "How to use"
    popover under it."""
    st.markdown(COPY[page])
    _how_to_use()


def about() -> None:
    """Render the shared transparency statement at the page footer."""
    with st.expander("About this AI"):
        st.markdown(COPY["about"])
