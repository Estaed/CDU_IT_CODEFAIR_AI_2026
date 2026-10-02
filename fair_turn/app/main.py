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
st.logo(str(STATIC / "logo.svg"), size="large", icon_image=str(STATIC / "logo-mark.svg"))
state.artefacts()

pg = st.navigation(
    [
        st.Page("pages/plan.py", title="This week's plan", icon=":material/route:", default=True),
        st.Page("pages/reports.py", title="Reports", icon=":material/description:"),
        st.Page("pages/tenant.py", title="Ask about a repair", icon=":material/question_answer:"),
        st.Page("pages/evidence.py", title="Evidence", icon=":material/analytics:"),
    ]
)
with st.sidebar:
    st.caption(theme.PROVENANCE_LINE)
pg.run()
