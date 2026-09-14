"""The clustered workspace map: the GeoJSON and payload it is given, the offline render, the
fallback on a failed load, and a click returned as a community id. ``AppTest`` cannot see
inside a v2 component, so the click and failure paths inject a fake mount."""

import json
import re
import socket
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from fair_turn.app import theme
from fair_turn.app.components import cluster_map
from fair_turn.core import constants

JS = Path(cluster_map.__file__).with_name("cluster_map.js")


def _refuse(*args, **kwargs):
    raise RuntimeError("network disabled")


@pytest.fixture
def no_network(monkeypatch):
    monkeypatch.setattr(socket, "socket", _refuse)


@pytest.fixture
def points() -> list[dict]:
    return [
        {
            "job_id": "JR-2025-00001",
            "community_id": "COMMUNITY-01",
            "lat": -12.4,
            "lon": 130.8,
            "region": constants.TOWN_REGION,
            "open_jobs": 1,
        },
        {
            "job_id": "JR-2025-00002",
            "community_id": "COMMUNITY-02",
            "lat": -14.5,
            "lon": 132.2,
            "region": constants.REMOTE_REGIONS[0],
            "open_jobs": 3,
        },
    ]


def _script(tmp_path: Path, points: list[dict], fake: str | None = None) -> Path:
    """Render the map; ``fake`` is a Python expression for the mount result, or the real
    component when omitted."""
    lines = [
        "import streamlit as st",
        "from types import SimpleNamespace",
        "from fair_turn.app import state",
        "from fair_turn.app.components import cluster_map",
        "calls = st.session_state.setdefault('mount_calls', [])",
    ]
    if fake is None:
        lines.append(f"result = cluster_map.render({points!r}, 'COMMUNITY-02')")
    else:
        lines += [
            "def fake(data, key):",
            "    calls.append(key)",
            f"    return {fake}",
            f"result = cluster_map.render({points!r}, 'COMMUNITY-02', mount=fake)",
        ]
    lines.append("st.text(f'picked={result}')")
    path = tmp_path / "cluster_map_app.py"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="")
    return path


def test_feature_collection_has_one_feature_per_community(points) -> None:
    collection = cluster_map.feature_collection(points)
    assert collection["type"] == "FeatureCollection"
    features = collection["features"]
    assert [f["geometry"]["coordinates"] for f in features] == [[130.8, -12.4], [132.2, -14.5]]
    assert features[1]["properties"] == {
        "community_id": "COMMUNITY-02",
        "region": constants.REMOTE_REGIONS[0],
        "open_jobs": 3,
        "job_id": "JR-2025-00002",
    }
    assert cluster_map.feature_collection([]) == {"type": "FeatureCollection", "features": []}


def test_payload_carries_theme_colours_layout_and_the_selection(points) -> None:
    data = cluster_map.payload(points, "COMMUNITY-02")
    assert data["selected"] == "COMMUNITY-02"
    assert data["colours"]["regions"] == theme.REGION_COLOURS
    assert data["layout"]["cluster_radius"] == cluster_map.CLUSTER_RADIUS_PX
    assert data["layout"]["cluster_max_zoom"] == cluster_map.CLUSTER_MAX_ZOOM
    assert data["layout"]["height"] == cluster_map.MAP_HEIGHT_PX
    assert data["layout"]["selected_zoom"] == cluster_map.CLUSTER_MAX_ZOOM + 1
    assert data["urls"]["module"].startswith("app/static/maplibre/")
    assert cluster_map.payload(points, None)["selected"] == ""


def test_vendored_maplibre_files_exist() -> None:
    static = Path(cluster_map.__file__).parents[1] / "static" / "maplibre"
    for name in ("maplibre-gl.mjs", "maplibre-gl-shared.mjs", "maplibre-gl-worker.mjs"):
        assert (static / name).is_file()
    assert (static / "maplibre-gl.css").is_file()
    assert (static / "LICENSE.txt").is_file()


def test_script_has_no_colour_literal_and_reuses_the_map_on_rerun() -> None:
    source = JS.read_text("utf-8")
    assert not re.search(r"#[0-9a-fA-F]{3,6}\b", source)
    # The map object is kept on the parent element and updated, never rebuilt.
    assert "setData(" in source
    assert "parentElement[STATE_KEY]" in source
    assert 'setTriggerValue("picked"' in source
    assert 'setTriggerValue("failed"' in source
    assert "getClusterExpansionZoom" in source
    # A changed selection eases the camera to at least the payload's zoom past clustering.
    assert "data.selected !== previous" in source
    assert "data.layout.selected_zoom" in source


def test_component_renders_offline_with_its_features(tmp_path, no_network, points) -> None:
    at = AppTest.from_file(str(_script(tmp_path, points))).run(timeout=60)
    assert not at.exception
    nodes = at.get("bidi_component")
    assert len(nodes) == 1
    assert nodes[0].proto.component_name.endswith(cluster_map.COMPONENT_NAME)
    data = json.loads(nodes[0].proto.json)
    assert len(data["features"]["features"]) == len(points)
    assert data["selected"] == "COMMUNITY-02"
    assert not at.get("vega_lite_chart")
    assert "picked=None" in [t.value for t in at.text]


def test_a_click_returns_the_community_id(tmp_path, no_network, points) -> None:
    fake = "SimpleNamespace(picked='COMMUNITY-02', failed=None)"
    at = AppTest.from_file(str(_script(tmp_path, points, fake))).run(timeout=60)
    assert not at.exception
    assert "picked=COMMUNITY-02" in [t.value for t in at.text]


def test_a_failed_load_shows_the_outline_and_stays_on_it(tmp_path, no_network, points) -> None:
    fake = "SimpleNamespace(picked=None, failed='style: network error')"
    at = AppTest.from_file(str(_script(tmp_path, points, fake))).run(timeout=60)
    assert not at.exception
    assert at.session_state["map_failed"] == "style: network error"
    assert len(at.get("vega_lite_chart")) == 1
    assert [i.value for i in at.info] == [cluster_map.UNAVAILABLE]
    spec = json.loads(at.get("vega_lite_chart")[0].proto.spec)
    assert len(spec["layer"][1]["data"]["values"]) == len(points)
    assert not at.get("bidi_component")
    at.run(timeout=60)  # the next rerun draws the outline without mounting the map again
    assert not at.exception
    assert at.session_state["mount_calls"] == ["workspace_map"]
    assert len(at.get("vega_lite_chart")) == 1
