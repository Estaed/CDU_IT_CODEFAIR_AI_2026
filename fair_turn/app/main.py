"""Fair Turn entry point: ``venv/Scripts/streamlit run fair_turn/app/main.py``."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  # `streamlit run` puts only this folder on sys.path

import streamlit as st  # noqa: E402 -- sys.path shim above must run first

from fair_turn.app import state, theme  # noqa: E402 -- sys.path shim above must run first

STATIC = Path(__file__).parent / "static"

st.set_page_config(page_title="Fair Turn", layout="wide", initial_sidebar_state="expanded")
theme.inject_css()
st.logo(
    str(STATIC / "logo.svg"),
    size="large",
    icon_image=str(STATIC / "logo-mark.svg"),
    link=None,
)
state.artefacts()

pg = st.navigation(
    {
        "Today's work": [
            st.Page(
                "pages/workspace.py",
                title="Workspace",
                icon=":material/dashboard:",
                default=True,
            ),
            st.Page("pages/review_queue.py", title="Review queue", icon=":material/rule:"),
            st.Page("pages/visit_plan.py", title="Visit plan", icon=":material/route:"),
        ],
        "Evidence": [
            st.Page("pages/tenant.py", title="Tenant answer", icon=":material/question_answer:"),
            st.Page("pages/evidence_lab.py", title="Evidence lab", icon=":material/analytics:"),
        ],
    }
)
with st.sidebar:
    theme.legend()
pg.run()
