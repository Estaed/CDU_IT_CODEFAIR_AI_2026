"""The selectable workspace map (PRD 3.1).

Pydeck supplies the pan-and-zoom workspace map.  The existing inline Altair map remains
the offline fallback when a basemap cannot be rendered.

The map has two levels, and the sidebar region filter decides which one is drawn.  With no
region chosen the map draws one circle per region, and clicking one filters to that region,
which draws the community dots.  Clustering is click-driven because zoom-driven clustering
needs JavaScript, which Part 2 forbids.
"""

import pydeck as pdk
import streamlit as st

from fair_turn.app import state, theme
from fair_turn.app.components.map import nt_map

MARKER_MIN_PX = 6
MARKER_STEP_PX = 1
MARKER_MAX_PX = 14
REGION_MARKER_MAX_PX = 28
SELECTED_RADIUS_MULTIPLIER = 1.6
MARKER_LINE_WIDTH_MIN_PX = 1
SELECTED_LINE_WIDTH_MIN_PX = 3
COUNT_FONT_PX = 12
MAP_HEIGHT_PX = 320
NT_VIEW = (-19.0, 133.0, 4)  # the whole Territory: the view of the region level
REGION_ZOOM = 6

REGION_LEVEL = "region"
COMMUNITY_LEVEL = "community"
REGIONS_LAYER_ID = "regions"
JOBS_LAYER_ID = "jobs"
SELECTED_LAYER_ID = "selected"
COUNTS_LAYER_ID = "counts"
COMMUNITY_TOOLTIP = "<b>{job_id}</b><br/>{community_id} · {open_jobs} open"
REGION_TOOLTIP = "<b>{region}</b> · {open_jobs} open"


def _rgb(hex_value: str) -> list[int]:
    """Convert a theme colour to the RGB list expected by pydeck."""
    return [int(hex_value[index : index + 2], 16) for index in range(1, len(hex_value), 2)]


def _sized(points: list[dict], maximum: int) -> list[dict]:
    return [
        {
            **point,
            "colour": _rgb(theme.REGION_COLOURS[point["region"]]),
            "radius": min(MARKER_MIN_PX + MARKER_STEP_PX * int(point["open_jobs"]), maximum),
        }
        for point in points
    ]


def _count_points(layer_points: list[dict], minimum: int) -> list[dict]:
    return [
        {**point, "label": str(point["open_jobs"])}
        for point in layer_points
        if int(point["open_jobs"]) >= minimum
    ]


def _counts_layer(layer_points: list[dict], minimum: int) -> pdk.Layer:
    return pdk.Layer(
        "TextLayer",
        id=COUNTS_LAYER_ID,
        data=_count_points(layer_points, minimum),
        pickable=False,
        get_position=["lon", "lat"],
        get_text="label",
        get_size=COUNT_FONT_PX,
        size_units="'pixels'",
        get_color=_rgb(st.get_option("theme.backgroundColor")),
        get_text_anchor="'middle'",
        get_alignment_baseline="'center'",
    )


def region_points(points: list[dict]) -> list[dict]:
    """One point per region: the mean position of its communities and their total open jobs."""
    grouped: dict[str, list[dict]] = {}
    for point in points:
        grouped.setdefault(point["region"], []).append(point)
    return [
        {
            "region": region,
            "lat": sum(float(member["lat"]) for member in members) / len(members),
            "lon": sum(float(member["lon"]) for member in members) / len(members),
            "open_jobs": sum(int(member["open_jobs"]) for member in members),
        }
        for region, members in sorted(grouped.items())
    ]


def centre_of(points: list[dict]) -> tuple[float, float, float]:
    """The ``(lat, lon, zoom)`` view for a region's points; the Territory view when empty."""
    if not points:
        return NT_VIEW
    return (
        sum(float(point["lat"]) for point in points) / len(points),
        sum(float(point["lon"]) for point in points) / len(points),
        REGION_ZOOM,
    )


def _region_layers(points: list[dict]) -> list[pdk.Layer]:
    layer_points = _sized(region_points(points), REGION_MARKER_MAX_PX)
    regions = pdk.Layer(
        "ScatterplotLayer",
        id=REGIONS_LAYER_ID,
        data=layer_points,
        pickable=True,
        get_position=["lon", "lat"],
        get_radius="radius",
        get_fill_color="colour",
        radius_units="'pixels'",
        radius_min_pixels=MARKER_MIN_PX,
        radius_max_pixels=REGION_MARKER_MAX_PX,
        stroked=True,
        line_width_min_pixels=MARKER_LINE_WIDTH_MIN_PX,
    )
    return [regions, _counts_layer(layer_points, 1)]


def _community_layers(points: list[dict], selected_id: str | None) -> list[pdk.Layer]:
    layer_points = _sized(points, MARKER_MAX_PX)
    selected_points = [
        {**point, "radius": point["radius"] * SELECTED_RADIUS_MULTIPLIER}
        for point in layer_points
        if point["job_id"] == selected_id
    ]
    jobs = pdk.Layer(
        "ScatterplotLayer",
        id=JOBS_LAYER_ID,
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
        id=SELECTED_LAYER_ID,
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
    return [jobs, selected, _counts_layer(layer_points, 2)]


def build_deck(
    points: list[dict],
    selected_id: str | None,
    level: str = COMMUNITY_LEVEL,
    centre: tuple[float, float, float] | None = None,
) -> pdk.Deck:
    """Build the deck for one level: region circles, or community dots with a highlight."""
    if level == REGION_LEVEL:
        layers, tooltip = _region_layers(points), REGION_TOOLTIP
    else:
        layers, tooltip = _community_layers(points, selected_id), COMMUNITY_TOOLTIP
    latitude, longitude, zoom = centre if centre is not None else NT_VIEW
    return pdk.Deck(
        layers=layers,
        initial_view_state=pdk.ViewState(latitude=latitude, longitude=longitude, zoom=zoom),
        map_provider="carto",
        map_style="light",
        tooltip={"html": tooltip},
    )


def picked(event) -> tuple[str, str] | None:
    """Return ``("region", name)`` or ``("community", id)`` for the first selected marker.

    The community, not the job: a marker carries the community's best job id, and that id
    changes when a filter changes while the stored selection does not."""
    selection = getattr(event, "selection", None)
    if selection is None:
        return None
    for layer_id, objects in selection.get("objects", {}).items():
        if layer_id == COUNTS_LAYER_ID or not objects:
            continue
        if layer_id == REGIONS_LAYER_ID:
            return (REGION_LEVEL, objects[0].get("region"))
        return (COMMUNITY_LEVEL, objects[0].get("community_id"))
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


def render(
    points: list[dict],
    selected_id: str | None,
    level: str = COMMUNITY_LEVEL,
    centre: tuple[float, float, float] | None = None,
    key: str = "workspace_map",
) -> tuple[str, str] | None:
    """Render the map and return the click without touching session state.

    The key carries the level so a pick made at one level never re-applies itself at the
    other, which would make the "All regions" button look broken."""
    try:
        event = st.pydeck_chart(
            build_deck(points, selected_id, level, centre),
            on_select="rerun",
            selection_mode="single-object",
            height=MAP_HEIGHT_PX,
            key=key,
        )
        return picked(event)
    except Exception:
        st.altair_chart(_fallback_map(points), width="stretch")
        st.info("Basemap unavailable — showing the NT outline instead.")
        return None
