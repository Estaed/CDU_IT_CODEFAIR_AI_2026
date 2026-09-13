"""Fair Turn entry point: ``venv/Scripts/streamlit run fair_turn/app/main.py``."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  # `streamlit run` puts only this folder on sys.path

import streamlit as st  # noqa: E402 -- sys.path shim above must run first

from fair_turn.app import state, theme  # noqa: E402 -- sys.path shim above must run first

st.set_page_config(page_title="Fair Turn", layout="wide")
state.artefacts()

pg = st.navigation(
    [
        st.Page("pages/workspace.py", title="Workspace", default=True),
        st.Page("pages/review_queue.py", title="Review queue"),
        st.Page("pages/visit_plan.py", title="Visit plan"),
        st.Page("pages/tenant.py", title="Tenant answer"),
        st.Page("pages/evidence_lab.py", title="Evidence lab"),
    ]
)
st.sidebar.caption(theme.PROVENANCE_LINE)
pg.run()
