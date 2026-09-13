"""PRD 3.5 Feedback-loop simulation. Stub: body comes in a later task."""

import streamlit as st

from fair_turn.app import state, theme

state.artefacts()
st.title("Feedback loop")
st.caption(theme.PROVENANCE_LINE)
