"""Chart palette, fixed UI strings and the one application stylesheet seam."""

from pathlib import Path

import streamlit as st

from fair_turn.core.constants import REMOTE_REGIONS, TOWN_REGION

REGION_COLOURS = dict(
    zip(
        (*REMOTE_REGIONS, TOWN_REGION),
        ("#8a6400", "#007d79", "#9f1853", "#198038", "#2d5bbf", "#4d5358"),
        strict=True,
    )
)
TOWN = "#262626"
REMOTE = "#8a3ffc"
LOCALITY_STROKE = {"town": "solid", "remote": "dashed"}
FACTOR_COLOURS = {
    "urgency": "#da1e28",
    "safety": "#b35c00",
    "health_risk": "#6929c4",
    "logistics": "#0072c3",
}
HUMAN_QUEUE = "#684e00"
HUMAN_QUEUE_BACKGROUND = "#fcf4d6"
GRIDLINE = "#e0e0e0"
AXIS_LABEL = "#525252"
STROKE_WIDTH = 2
PROVENANCE_LINE = "Geography real (BushTel/ABS); events synthetic"


def inject_css() -> None:
    """Add the scoped application stylesheet after page configuration."""
    css = (Path(__file__).parent / "static" / "theme.css").read_text("utf-8")
    st.html(f"<style>{css}</style>")
