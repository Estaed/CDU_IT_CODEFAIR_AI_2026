"""PRD 3.2 Job card. Stub: body comes in a later task."""

import streamlit as st

from fair_turn.app import state, theme

state.artefacts()
st.title("Job card")
st.caption(theme.PROVENANCE_LINE)
