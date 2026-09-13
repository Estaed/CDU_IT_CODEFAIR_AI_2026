"""Fair Turn entry point: ``venv/Scripts/streamlit run fair_turn/app/main.py``."""

import streamlit as st

from fair_turn.app import state, theme

st.set_page_config(page_title="Fair Turn", layout="wide")
state.artefacts()

pg = st.navigation(
    [
        st.Page("pages/board.py", title="Triage board", default=True),
        st.Page("pages/job_card.py", title="Job card"),
        st.Page("pages/sign_off.py", title="Sign-off"),
        st.Page("pages/tenant.py", title="Tenant view"),
        st.Page("pages/feedback.py", title="Feedback loop"),
        st.Page("pages/audit_log.py", title="Audit log"),
    ]
)
st.sidebar.caption(theme.PROVENANCE_LINE)
pg.run()
