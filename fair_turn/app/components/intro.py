"""PRD section 3 purpose lines and the shared AI transparency footer."""

import streamlit as st

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
        "This is the run sheet for the jobs you signed. The order is yours. Distance suggestions "
        "are only suggestions, and each one shows its reason."
    ),
    "tenant": (
        "Here is where your repair sits today, and what moved it there. A housing officer checked "
        "and signed this list."
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


def purpose(page: str) -> None:
    """Render the page purpose immediately below its title."""
    st.markdown(COPY[page])


def about() -> None:
    """Render the shared transparency statement at the page footer."""
    with st.expander("About this AI"):
        st.markdown(COPY["about"])
