"""Sidebar controls of the workspace: the weighting presets and the display filters
(PRD 3.1, wireframes §3).

The lam values below are named settings of this screen, not NT policy numbers.
"""

import streamlit as st

from fair_turn.app import state
from fair_turn.core import batch, constants
from fair_turn.core.types import FaultType

PRESETS = {"Efficiency first": 1.0, "Balanced": 0.5, "Need first": 0.0}
FAULT_FILTER_KEY = "workspace_filter_fault"
SAFETY_FILTER_KEY = "workspace_filter_safety"


def _preset_for(lam: float) -> str | None:
    return next((name for name, value in PRESETS.items() if value == lam), None)


def render() -> tuple[float, str]:
    """Presets, the always-visible number and the Advanced slider; returns ``(lam, label)``."""
    lam = state.get_lam()
    names = list(PRESETS)
    preset = _preset_for(lam)
    choice = st.radio(
        "Weighting",
        names,
        index=names.index(preset) if preset is not None else None,
    )
    if choice is not None and PRESETS[choice] != lam:
        lam = PRESETS[choice]
    caption_slot = st.empty()
    with st.expander("Advanced"):
        st.caption("Ignore travel cost ↔ Full travel-cost penalty")
        value = st.slider("Travel-cost weight", 0.0, 1.0, value=lam, step=0.05)
    if value != lam:
        lam = round(float(value), 2)
    label = batch.preset_label(lam, _preset_for(lam))
    caption_slot.caption(
        f"Travel-cost weight {lam:.2f}. 0 ignores travel cost, 1 applies the full penalty."
    )
    state.set_lam(lam)
    state.set_preset(label)
    return lam, label


def clear_filters() -> None:
    """Button callback: runs before the widgets are drawn on the next run."""
    state.set_region(state.ALL_REGIONS)
    st.session_state[FAULT_FILTER_KEY] = []
    st.session_state[SAFETY_FILTER_KEY] = []


def filters() -> tuple[str, list[str], list[str]]:
    """Region, fault types and safety classes; returns ``(region, faults, safeties)``."""
    regions = [state.ALL_REGIONS, *constants.REGIONS]
    region = st.selectbox("Region", regions, index=regions.index(state.get_region()))
    state.set_region(region)
    faults = st.multiselect("Fault type", [f.value for f in FaultType], key=FAULT_FILTER_KEY)
    safeties = st.multiselect("Safety class", list(constants.SAFETY_CLASSES), key=SAFETY_FILTER_KEY)
    st.button("Clear filters", on_click=clear_filters, key="workspace_clear_filters")
    st.caption(
        "Fault and safety filters change what the lists and the map show, never today's "
        "capacity or the proposed list. Region sets the capacity."
    )
    return region, faults, safeties
