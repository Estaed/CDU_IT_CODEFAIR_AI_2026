"""PRD 3.3 Sign-off. Stub: body comes in a later task."""

import streamlit as st

from fair_turn.app import state, theme

state.artefacts()
st.title("Sign-off")
st.caption(theme.PROVENANCE_LINE)
