"""PRD 3.5 Evidence lab."""

import streamlit as st

from fair_turn.app import state, theme

state.artefacts()
st.title("Evidence lab")
st.caption(theme.PROVENANCE_LINE)
st.info("Built in Task-34")
