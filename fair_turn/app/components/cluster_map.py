"""The zoom-driven clustered workspace map (PRD 3.1).

A ``st.components.v2`` component running the vendored MapLibre GL (``app/static/maplibre``)
over the Carto Positron basemap. Communities cluster by screen distance; a cluster circle
carries the summed open jobs and splits into community dots as the map zooms in. Clicking a
dot sends its community id back to Python; any failure before the map loads (module import,
style, tiles, an 8 s timeout) sends a reason instead, and the page draws the offline Altair
outline for the rest of the session.

Everything the script needs arrives in ``data``: the GeoJSON, the colours (from ``theme`` and
the ``[theme]`` config, so the JS file carries no colour literal) and the layout numbers
below. On a rerun the same map object receives the new data, so the camera is never reset;
it moves only when the selected community changes after mount, easing to that community.
"""

from pathlib import Path

import streamlit as st

from fair_turn.app import state, theme
from fair_turn.app.components import workspace_map

MAP_HEIGHT_PX = 420
CLUSTER_RADIUS_PX = 45
CLUSTER_MAX_ZOOM = 8
# A newly selected community eases to at least this zoom: one step past clustering, so its
# own dot and selected ring show instead of a cluster circle.
SELECTED_ZOOM = CLUSTER_MAX_ZOOM + 1
POINT_MIN_RADIUS_PX = 6
POINT_MAX_RADIUS_PX = 14
POINT_MAX_JOBS = 8  # a community with this many open jobs or more draws the largest dot
POINT_STROKE_PX = 1
CLUSTER_MIN_RADIUS_PX = 14
CLUSTER_MAX_RADIUS_PX = 30
CLUSTER_MAX_JOBS = 40
CLUSTER_STROKE_PX = 2
CLUSTER_OPACITY = 0.85
LABEL_SIZE_PX = 12
# Glyph stacks the Carto Positron style serves; not a UI font, the basemap's own.
LABEL_FONTS = ["Montserrat Medium", "Open Sans Bold", "Noto Sans Regular"]
SELECTED_RING_PX = 4
CREW_RADIUS_PX = 5  # a crew is a small dark dot with its id beside it
CREW_LABEL_OFFSET_EM = 0.9
LOAD_TIMEOUT_MS = 8000
CENTRE = (133.5, -19.5)  # (lon, lat): the whole Territory
ZOOM = 4.2
STYLE_URL = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
MODULE_PATH = "app/static/maplibre/maplibre-gl.mjs"
CSS_PATH = "app/static/maplibre/maplibre-gl.css"
COMPONENT_NAME = "ft_cluster_map"
JS_FILE = Path(__file__).parent / "cluster_map.js"
UNAVAILABLE = "Basemap unavailable — showing the NT outline instead."

_JS = JS_FILE.read_text("utf-8")


def feature_collection(points: list[dict]) -> dict:
    """GeoJSON with one point feature per community, carrying its id, region, open job count
    and the id of its best-ranked job."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(point["lon"]), float(point["lat"])],
                },
                "properties": {
                    "community_id": point["community_id"],
                    "region": point["region"],
                    "open_jobs": int(point["open_jobs"]),
                    "job_id": point["job_id"],
                },
            }
            for point in points
        ],
    }


def crew_points(starts: dict[str, tuple[float, float]]) -> list[dict]:
    """One marker per place a crew is this morning; crews at the same place share a marker
    and a label ("Darwin 2, Darwin 3")."""
    at: dict[tuple[float, float], list[str]] = {}
    for crew_id, position in starts.items():
        at.setdefault(position, []).append(crew_id)
    return [{"crew_id": ", ".join(ids), "lat": lat, "lon": lon} for (lat, lon), ids in at.items()]


def crew_collection(crews: list[dict]) -> dict:
    """GeoJSON with one point per crew where it is this morning, labelled with its id."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [float(c["lon"]), float(c["lat"])]},
                "properties": {"crew_id": c["crew_id"]},
            }
            for c in crews
        ],
    }


def payload(
    points: list[dict], selected_community_id: str | None, crews: list[dict] | None = None
) -> dict:
    """The complete ``data`` the script receives: features, crews, colours and layout numbers."""
    accent = st.get_option("theme.primaryColor")
    background = st.get_option("theme.backgroundColor")
    return {
        "features": feature_collection(points),
        "crews": crew_collection(crews or []),
        "selected": selected_community_id or "",
        "colours": {
            "regions": dict(theme.REGION_COLOURS),
            "cluster": accent,
            "ring": accent,
            "stroke": background,
            "label": background,
            "crew": theme.CREW_MARKER,
            "crew_label": theme.CREW_MARKER,
        },
        "layout": {
            "height": MAP_HEIGHT_PX,
            "cluster_radius": CLUSTER_RADIUS_PX,
            "cluster_max_zoom": CLUSTER_MAX_ZOOM,
            "point_min_radius": POINT_MIN_RADIUS_PX,
            "point_max_radius": POINT_MAX_RADIUS_PX,
            "point_max_jobs": POINT_MAX_JOBS,
            "point_stroke": POINT_STROKE_PX,
            "cluster_min_radius": CLUSTER_MIN_RADIUS_PX,
            "cluster_max_radius": CLUSTER_MAX_RADIUS_PX,
            "cluster_max_jobs": CLUSTER_MAX_JOBS,
            "cluster_stroke": CLUSTER_STROKE_PX,
            "cluster_opacity": CLUSTER_OPACITY,
            "label_size": LABEL_SIZE_PX,
            "label_fonts": LABEL_FONTS,
            "ring": SELECTED_RING_PX,
            "crew_radius": CREW_RADIUS_PX,
            "crew_label_offset": CREW_LABEL_OFFSET_EM,
            "timeout_ms": LOAD_TIMEOUT_MS,
            "centre": list(CENTRE),
            "zoom": ZOOM,
            "selected_zoom": SELECTED_ZOOM,
        },
        "urls": {"style": STYLE_URL, "module": MODULE_PATH, "css": CSS_PATH},
    }


def _mount(data: dict, key: str):
    # Registered on every call: the registry belongs to the running app, so a registration
    # made at import time (in another runtime, such as a test process) is not found.
    component = st.components.v2.component(COMPONENT_NAME, js=_JS)
    return component(
        data=data,
        on_picked_change=lambda: None,
        on_failed_change=lambda: None,
        key=key,
    )


def render(
    points: list[dict],
    selected_community_id: str | None,
    key: str = "workspace_map",
    mount=None,
    crews: list[dict] | None = None,
) -> str | None:
    """Draw the map and return the community id clicked in this rerun, if any.

    ``mount`` is the component call (``_mount``, looked up at call time); tests inject a fake
    because ``AppTest`` cannot click inside a component. A ``failed`` trigger is remembered in
    session state, so the outline replaces the map in the same rerun and stays for the
    session."""
    mount = mount or _mount
    slot = st.empty()
    picked = None
    if state.get_map_failed() is None:
        with slot.container():
            result = mount(payload(points, selected_community_id, crews), key)
        if getattr(result, "failed", None):
            state.set_map_failed(str(result.failed))
        else:
            picked = getattr(result, "picked", None)
    if state.get_map_failed() is not None:
        with slot.container():
            st.altair_chart(workspace_map._fallback_map(points, crews), width="stretch")
            st.info(UNAVAILABLE)
        return None
    return picked or None
