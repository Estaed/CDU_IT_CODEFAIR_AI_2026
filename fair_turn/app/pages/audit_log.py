"""PRD 3.6 Audit log. Stub: body comes in a later task."""

import streamlit as st

from fair_turn.app import state, theme

state.artefacts()
st.title("Audit log")
st.caption(theme.PROVENANCE_LINE)
