"""Chart palette, fixed UI strings and the one application stylesheet seam."""

from pathlib import Path

import streamlit as st

PLANNED = "#198038"  # a crew goes there this week
WAITING_LATE = "#da1e28"  # no crew this week, and repairs past the NT time limit
WAITING = "#8d8d8d"  # no crew this week, nothing overdue yet
BASE = "#161616"  # a crew base
TOWN = "#262626"
REMOTE = "#8a3ffc"
SETTING_COLOURS = {
    "Most repairs": "#0072c3",
    "Balanced": "#8a6400",
    "Most overdue first": "#b4462a",
}
HIGHLIGHT = "#b4462a"
GRIDLINE = "#e0e0e0"
OUTLINE_FILL = "#f4f4f4"
AXIS_LABEL = "#525252"
STROKE_WIDTH = 1.5
PROVENANCE_LINE = (
    "Geography real (BushTel, ABS); reports and events synthetic; crew numbers are our assumption."
)


def inject_css() -> None:
    """Add the scoped application stylesheet after page configuration."""
    css = (Path(__file__).parent / "static" / "theme.css").read_text("utf-8")
    st.html(f"<style>{css}</style>")


def chart(c):
    """Shared axis styling for every Altair chart."""
    return c.configure_axis(
        gridColor=GRIDLINE, labelColor=AXIS_LABEL, titleColor=AXIS_LABEL
    ).configure_view(stroke=None)
