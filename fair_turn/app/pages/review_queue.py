"""PRD 3.2 Review queue."""

import streamlit as st

from fair_turn.app import state, theme

state.artefacts()
st.title("Review queue")
st.caption(theme.PROVENANCE_LINE)
st.info("Built in Task-31")
