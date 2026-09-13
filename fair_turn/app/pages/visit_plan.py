"""PRD 3.3 Visit plan."""

import streamlit as st

from fair_turn.app import state, theme

state.artefacts()
st.title("Visit plan")
st.caption(theme.PROVENANCE_LINE)
st.info("Built in Task-32")
