"""The selectable workspace map (PRD 3.1).

Pydeck supplies the pan-and-zoom workspace map.  The existing inline Altair map remains
the offline fallback when a basemap cannot be rendered.
"""

import pydeck as pdk
import streamlit as st

from fair_turn.app import state, theme
from fair_turn.app.components.map import nt_map

MARKER_BASE_M = 4_000
MARKER_STEP_M = 1_000
SELECTED_RADIUS_MULTIPLIER = 1.6
SELECTED_LINE_WIDTH_MIN_PIXELS = 3


def _rgb(hex_value: str) -> list[int]:
    """Convert a theme colour to the RGB list expected by pydeck."""
    return [int(hex_value[index : index + 2], 16) for index in range(1, len(hex_value), 2)]


def _layer_points(points: list[dict]) -> list[dict]:
    return [
        {
            **point,
            "colour": _rgb(theme.REGION_COLOURS[point["region"]]),
            "radius": MARKER_BASE_M + MARKER_STEP_M * int(point["open_jobs"]),
        }
        for point in points
    ]


def build_deck(points: list[dict], selected_id: str | None) -> pdk.Deck:
    """Build the workspace deck with a separate selected-job highlight layer."""
    layer_points = _layer_points(points)
    selected_points = [
        {**point, "radius": point["radius"] * SELECTED_RADIUS_MULTIPLIER}
        for point in layer_points
        if point["job_id"] == selected_id
    ]
    jobs = pdk.Layer(
        "ScatterplotLayer",
        id="jobs",
        data=layer_points,
        pickable=True,
        get_position=["lon", "lat"],
        get_radius="radius",
        get_fill_color="colour",
    )
    selected = pdk.Layer(
        "ScatterplotLayer",
        id="selected",
        data=selected_points,
        pickable=True,
        get_position=["lon", "lat"],
        get_radius="radius",
        get_fill_color="colour",
        stroked=True,
        get_line_color=_rgb(st.get_option("theme.primaryColor")),
        line_width_min_pixels=SELECTED_LINE_WIDTH_MIN_PIXELS,
    )
    return pdk.Deck(
        layers=[jobs, selected],
        initial_view_state=pdk.ViewState(latitude=-19, longitude=133, zoom=4),
        map_provider="carto",
        map_style="light",
        tooltip={"html": "<b>{job_id}</b><br/>{community_id}"},
    )


def picked_id(event) -> str | None:
    """Return the first selected job from a pydeck selection event, if there is one."""
    selection = getattr(event, "selection", None)
    if selection is None:
        return None
    objects = selection.get("objects", {})
    for picked in objects.values():
        if picked:
            return picked[0].get("job_id")
    return None


def _fallback_map(points: list[dict]):
    communities = {
        point["community_id"]: {
            "region": str(point["region"]),
            "lon": str(point["lon"]),
            "lat": str(point["lat"]),
        }
        for point in points
    }
    open_counts = {point["community_id"]: int(point["open_jobs"]) for point in points}
    return nt_map(communities, open_counts, state.ALL_REGIONS)


def render(points: list[dict], selected_id: str | None) -> str | None:
    """Render the map and return the clicked job id without touching session state."""
    try:
        event = st.pydeck_chart(
            build_deck(points, selected_id),
            on_select="rerun",
            selection_mode="single-object",
            key="workspace_map",
        )
        return picked_id(event)
    except Exception:
        st.altair_chart(_fallback_map(points), width="stretch")
        st.info("Basemap unavailable — showing the NT outline instead.")
        return None
