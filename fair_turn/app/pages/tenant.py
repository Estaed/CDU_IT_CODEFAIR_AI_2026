"""PRD 3.4 Tenant view. Stub: body comes in a later task."""

import streamlit as st

from fair_turn.app import state, theme

state.artefacts()
st.title("Tenant view")
st.caption(theme.PROVENANCE_LINE)
