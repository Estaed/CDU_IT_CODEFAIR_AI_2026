"""The NT map of this week's plan: bases, the trips crews make, and who is left waiting.

Inline data only, so it renders through Streamlit's bundled Vega-Lite with no network.
"""

import json

import altair as alt
import streamlit as st

from fair_turn.app import theme
from fair_turn.core import scoring, weekly
from fair_turn.core.types import Job
from fair_turn.data import artefacts

OUTLINE_PATH = artefacts.ROOT / "data" / "geo" / "nt_outline.geojson"
STATUS_COLOURS = {
    "Crew this week": theme.PLANNED,
    "No crew, overdue repairs": theme.WAITING_LATE,
    "No crew, none overdue yet": theme.WAITING,
}


@st.cache_data
def outline_features() -> list[dict]:
    return json.loads(OUTLINE_PATH.read_text("utf-8"))["features"]


def points(
    plan: weekly.WeekPlan, places: dict[str, weekly.Place], jobs: dict[str, Job]
) -> list[dict]:
    """One row per remote community with open repairs, and the trip line to it."""
    rows = []
    for trip in plan.trips:
        if trip.is_town:
            continue
        place = places[trip.community_id]
        rows.append(
            {
                "community": trip.community_id,
                "status": "Crew this week",
                "repairs": len(trip.job_ids),
                "overdue": sum(scoring.is_overdue(jobs[j], plan.day) for j in trip.job_ids),
                "lon": place.lon,
                "lat": place.lat,
            }
        )
    for waiting in plan.waiting:
        place = places[waiting.community_id]
        if place.is_town or plan.trip_to(waiting.community_id) is not None:
            continue
        overdue = sum(scoring.is_overdue(jobs[j], plan.day) for j in waiting.job_ids)
        rows.append(
            {
                "community": waiting.community_id,
                "status": "No crew, overdue repairs" if overdue else "No crew, none overdue yet",
                "repairs": len(waiting.job_ids),
                "overdue": overdue,
                "lon": place.lon,
                "lat": place.lat,
            }
        )
    return rows


def plan_map(
    plan: weekly.WeekPlan, places: dict[str, weekly.Place], jobs: dict[str, Job]
) -> alt.Chart:
    rows = points(plan, places, jobs)
    bases = {p.base: p for p in places.values() if p.is_town}
    lines = []
    for trip in plan.trips:
        if trip.is_town:
            continue
        base, place = bases[trip.base], places[trip.community_id]
        lines.append({"lon": base.lon, "lat": base.lat, "lon2": place.lon, "lat2": place.lat})
    outline = alt.Chart(alt.Data(values=outline_features())).mark_geoshape(
        fill=theme.OUTLINE_FILL, stroke=theme.AXIS_LABEL, strokeWidth=theme.STROKE_WIDTH
    )
    trip_lines = (
        alt.Chart(alt.Data(values=lines))
        .mark_rule(color=theme.PLANNED, strokeWidth=theme.STROKE_WIDTH, opacity=0.6)
        .encode(longitude="lon:Q", latitude="lat:Q", longitude2="lon2:Q", latitude2="lat2:Q")
    )
    dots = (
        alt.Chart(alt.Data(values=rows))
        .mark_circle(opacity=0.9, stroke="white", strokeWidth=0.5)
        .encode(
            longitude="lon:Q",
            latitude="lat:Q",
            size=alt.Size("repairs:Q", scale=alt.Scale(range=[30, 400]), title="Repairs"),
            color=alt.Color(
                "status:N",
                scale=alt.Scale(domain=list(STATUS_COLOURS), range=list(STATUS_COLOURS.values())),
                legend=alt.Legend(title=None, orient="bottom", direction="vertical"),
            ),
            tooltip=[
                alt.Tooltip("community:N", title="Community"),
                alt.Tooltip("status:N", title="This week"),
                alt.Tooltip("repairs:Q", title="Open repairs"),
                alt.Tooltip("overdue:Q", title="Past the NT time limit"),
            ],
        )
    )
    base_rows = [{"base": b, "lon": p.lon, "lat": p.lat} for b, p in bases.items()]
    base_marks = (
        alt.Chart(alt.Data(values=base_rows))
        .mark_point(shape="square", filled=True, color=theme.BASE, size=80)
        .encode(longitude="lon:Q", latitude="lat:Q", tooltip=alt.Tooltip("base:N", title="Base"))
    )
    base_labels = (
        alt.Chart(alt.Data(values=base_rows))
        .mark_text(align="left", dx=8, fontWeight="bold", color=theme.BASE)
        .encode(longitude="lon:Q", latitude="lat:Q", text="base:N")
    )
    return (
        alt.layer(outline, trip_lines, dots, base_marks, base_labels)
        .project("mercator")
        .properties(height=560)
        .configure_view(stroke=None)
    )
