"""PRD 3.1 Workspace."""

import streamlit as st

from fair_turn.app import state, theme

state.artefacts()
st.title("Workspace")
st.caption(theme.PROVENANCE_LINE)
st.info("Built in Task-29")
