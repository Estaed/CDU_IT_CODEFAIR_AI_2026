"""The selectable workspace map (PRD 3.1).

Pydeck supplies the pan-and-zoom workspace map.  The existing inline Altair map remains
the offline fallback when a basemap cannot be rendered.
"""

import pydeck as pdk
import streamlit as st

from fair_turn.app import state, theme
from fair_turn.app.components.map import nt_map

MARKER_MIN_PX = 6
MARKER_STEP_PX = 1
MARKER_MAX_PX = 14
SELECTED_RADIUS_MULTIPLIER = 1.6
MARKER_LINE_WIDTH_MIN_PX = 1
SELECTED_LINE_WIDTH_MIN_PX = 3
COUNT_FONT_PX = 12
MAP_HEIGHT_PX = 320


def _rgb(hex_value: str) -> list[int]:
    """Convert a theme colour to the RGB list expected by pydeck."""
    return [int(hex_value[index : index + 2], 16) for index in range(1, len(hex_value), 2)]


def _layer_points(points: list[dict]) -> list[dict]:
    return [
        {
            **point,
            "colour": _rgb(theme.REGION_COLOURS[point["region"]]),
            "radius": min(MARKER_MIN_PX + MARKER_STEP_PX * int(point["open_jobs"]), MARKER_MAX_PX),
        }
        for point in points
    ]


def _count_points(layer_points: list[dict]) -> list[dict]:
    return [
        {**point, "label": str(point["open_jobs"])}
        for point in layer_points
        if int(point["open_jobs"]) > 1
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
        radius_units="'pixels'",
        radius_min_pixels=MARKER_MIN_PX,
        radius_max_pixels=MARKER_MAX_PX,
        stroked=True,
        line_width_min_pixels=MARKER_LINE_WIDTH_MIN_PX,
    )
    selected = pdk.Layer(
        "ScatterplotLayer",
        id="selected",
        data=selected_points,
        pickable=True,
        get_position=["lon", "lat"],
        get_radius="radius",
        get_fill_color="colour",
        radius_units="'pixels'",
        radius_min_pixels=MARKER_MIN_PX,
        radius_max_pixels=int(MARKER_MAX_PX * SELECTED_RADIUS_MULTIPLIER),
        stroked=True,
        get_line_color=_rgb(st.get_option("theme.primaryColor")),
        line_width_min_pixels=SELECTED_LINE_WIDTH_MIN_PX,
    )
    counts = pdk.Layer(
        "TextLayer",
        id="counts",
        data=_count_points(layer_points),
        pickable=False,
        get_position=["lon", "lat"],
        get_text="label",
        get_size=COUNT_FONT_PX,
        size_units="'pixels'",
        get_color=_rgb(st.get_option("theme.backgroundColor")),
        get_text_anchor="'middle'",
        get_alignment_baseline="'center'",
    )
    return pdk.Deck(
        layers=[jobs, selected, counts],
        initial_view_state=pdk.ViewState(latitude=-19, longitude=133, zoom=4),
        map_provider="carto",
        map_style="light",
        tooltip={"html": "<b>{job_id}</b><br/>{community_id} · {open_jobs} open"},
    )


def picked_community_id(event) -> str | None:
    """Return the community of the first selected marker, if there is one.

    The community, not the job: a marker carries the community's best job id, and that id
    changes when a filter changes while the stored selection does not."""
    selection = getattr(event, "selection", None)
    if selection is None:
        return None
    objects = selection.get("objects", {})
    for layer_id, picked in objects.items():
        if layer_id != "counts" and picked:
            return picked[0].get("community_id")
    return None


def choice_for(community_id: str | None, by_community: dict[str, list]) -> tuple | None:
    """Resolve a map pick to ``(community id, sorted job ids)``.

    A pick naming a community the current filters no longer show is stale and yields no
    choice, rather than an error."""
    members = by_community.get(community_id) if community_id is not None else None
    if not members:
        return None
    return (community_id, sorted(job.job_id for job in members))


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
    """Render the map and return the clicked community id without touching session state."""
    try:
        event = st.pydeck_chart(
            build_deck(points, selected_id),
            on_select="rerun",
            selection_mode="single-object",
            height=MAP_HEIGHT_PX,
            key="workspace_map",
        )
        return picked_community_id(event)
    except Exception:
        st.altair_chart(_fallback_map(points), width="stretch")
        st.info("Basemap unavailable — showing the NT outline instead.")
        return None
