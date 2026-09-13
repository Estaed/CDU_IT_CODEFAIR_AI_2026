"""The NT map of open jobs (PRD 3.1): the territory outline and one dot per community.

Everything is inline data, so the chart renders through Streamlit's bundled Vega-Lite with
no network (Part 2 spike). Vega-Lite geo projections do not pan or zoom; choosing a region
drops the outline and the other regions' dots, and the projection fits what is left.
"""

import json

import altair as alt
import streamlit as st

from fair_turn.app import state, theme
from fair_turn.data import artefacts

OUTLINE_PATH = artefacts.ROOT / "data" / "geo" / "nt_outline.geojson"


@st.cache_data
def outline_features() -> list[dict]:
    return json.loads(OUTLINE_PATH.read_text("utf-8"))["features"]


def nt_map(
    communities: dict[str, dict[str, str]], open_counts: dict[str, int], region: str
) -> alt.Chart:
    """Dots sized by ``open_counts`` (communities with none are still drawn, smallest)."""
    points = [
        {
            "community_id": cid,
            "region": row["region"],
            "lon": float(row["lon"]),
            "lat": float(row["lat"]),
            "open": open_counts.get(cid, 0),
        }
        for cid, row in communities.items()
        if region == state.ALL_REGIONS or row["region"] == region
    ]
    dots = (
        alt.Chart(alt.Data(values=points))
        .mark_circle()
        .encode(
            longitude="lon:Q",
            latitude="lat:Q",
            size=alt.Size("open:Q", scale=alt.Scale(range=[20, 600]), title="Open jobs"),
            color=alt.Color(
                "region:N",
                scale=alt.Scale(
                    domain=list(theme.REGION_COLOURS), range=list(theme.REGION_COLOURS.values())
                ),
                title="Region",
            ),
            tooltip=[
                alt.Tooltip("community_id:N", title="community id"),
                alt.Tooltip("open:Q", title="open jobs"),
                alt.Tooltip("region:N", title="region"),
            ],
        )
    )
    if region != state.ALL_REGIONS:
        return dots.project("mercator")
    outline = alt.Chart(alt.Data(values=outline_features())).mark_geoshape(
        fill=theme.GRIDLINE, stroke=theme.AXIS_LABEL, strokeWidth=theme.STROKE_WIDTH
    )
    return alt.layer(outline, dots).project("mercator")
