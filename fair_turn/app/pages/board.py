"""PRD 3.1 Triage board. Stub: body comes in a later task."""

import streamlit as st

from fair_turn.app import state, theme

state.artefacts()
st.title("Triage board")
st.caption(theme.PROVENANCE_LINE)
