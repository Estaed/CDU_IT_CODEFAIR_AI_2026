"""Workspace map and job-list interaction spike (Task-22)."""

import json
import socket
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from fair_turn.app.components import job_list, workspace_map
from fair_turn.core import constants


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
            "open_jobs": 2,
        },
        {
            "job_id": "JR-2025-00003",
            "community_id": "COMMUNITY-03",
            "lat": -19.7,
            "lon": 134.2,
            "region": constants.REMOTE_REGIONS[1],
            "open_jobs": 3,
        },
    ]


def _script(tmp_path: Path, points: list[dict]) -> Path:
    path = tmp_path / "workspace_map_app.py"
    path.write_text(
        "from fair_turn.app.components import workspace_map\n"
        f"workspace_map.render({points!r}, 'JR-2025-00002')\n",
        encoding="utf-8",
        newline="",
    )
    return path


def _deck_nodes(at: AppTest):
    return [node for node in at if "deck" in node.type]


def _map_choice_script(tmp_path: Path, community_id: str, job_ids: list[str]) -> Path:
    path = tmp_path / "map_choice_app.py"
    path.write_text(
        "import streamlit as st\n"
        "from fair_turn.app import state\n"
        "from fair_turn.app.components import details_pane\n"
        f"details_pane._map_choice(({community_id!r}, {job_ids!r}), state.get_selected_job_id())\n"
        "st.write(state.get_selected_job_id())\n",
        encoding="utf-8",
        newline="",
    )
    return path


def test_deck_spec_has_selected_layer_and_carto_style(points) -> None:
    spec = json.loads(workspace_map.build_deck(points, "JR-2025-00002").to_json())
    assert len(spec["layers"]) == 3
    assert [layer["id"] for layer in spec["layers"]] == ["jobs", "selected", "counts"]
    assert len(spec["layers"][1]["data"]) == 1
    assert spec["layers"][1]["data"][0]["job_id"] == "JR-2025-00002"
    assert spec["mapProvider"] == "carto"
    assert "cartocdn.com" in spec["mapStyle"]
    assert all("cartocdn.com" in value for value in _urls(spec))


def test_counts_layer_only_covers_multi_job_points_and_is_not_pickable(points) -> None:
    spec = json.loads(workspace_map.build_deck(points, "JR-2025-00002").to_json())
    counts = spec["layers"][2]
    assert counts["sizeUnits"] == "pixels"
    assert "@@=" not in counts["sizeUnits"]
    assert counts["pickable"] is False
    assert [point["job_id"] for point in counts["data"]] == ["JR-2025-00002", "JR-2025-00003"]
    assert [point["label"] for point in counts["data"]] == ["2", "3"]


def test_tooltip_carries_the_open_job_count(points) -> None:
    deck = workspace_map.build_deck(points, "JR-2025-00002")
    assert "{open_jobs} open" in deck._tooltip["html"]


def test_deck_spec_uses_pixel_markers_without_accessor_units(points) -> None:
    points[-1]["open_jobs"] = 99
    spec = json.loads(workspace_map.build_deck(points, "JR-2025-00002").to_json())
    jobs, selected, _counts = spec["layers"]
    for layer in (jobs, selected):
        assert layer["radiusUnits"] == "pixels"
        assert "@@=" not in layer["radiusUnits"]
        assert layer["radiusMinPixels"] == workspace_map.MARKER_MIN_PX
        assert layer["stroked"] is True
    assert jobs["radiusMaxPixels"] == workspace_map.MARKER_MAX_PX
    assert jobs["lineWidthMinPixels"] == workspace_map.MARKER_LINE_WIDTH_MIN_PX
    # The highlight ring may grow past the marker cap and is drawn thicker.
    assert selected["radiusMaxPixels"] == int(
        workspace_map.MARKER_MAX_PX * workspace_map.SELECTED_RADIUS_MULTIPLIER
    )
    assert selected["lineWidthMinPixels"] == workspace_map.SELECTED_LINE_WIDTH_MIN_PX
    assert [point["radius"] for point in spec["layers"][0]["data"]] == [7, 8, 14]
    assert spec["layers"][1]["data"][0]["radius"] == 8 * workspace_map.SELECTED_RADIUS_MULTIPLIER


def test_one_job_map_choice_selects_directly_without_a_selectbox(tmp_path, no_network) -> None:
    at = AppTest.from_file(str(_map_choice_script(tmp_path, "COMMUNITY-01", ["JR-1"]))).run(
        timeout=60
    )
    assert not at.exception
    assert at.session_state["selected_job_id"] == "JR-1"
    assert not at.selectbox


def test_multi_job_map_choice_renders_one_compact_chooser(tmp_path, no_network) -> None:
    job_ids = ["JR-1", "JR-2", "JR-3"]
    at = AppTest.from_file(str(_map_choice_script(tmp_path, "COMMUNITY-01", job_ids))).run(
        timeout=60
    )
    assert not at.exception
    assert len(at.selectbox) == 1
    assert at.selectbox[0].options == job_ids
    assert not [button for button in at.button if button.label in job_ids]
    at.selectbox[0].set_value("JR-2").run(timeout=60)
    assert at.session_state["selected_job_id"] == "JR-2"


def _urls(node) -> list[str]:
    if isinstance(node, dict):
        own = [value for key, value in node.items() if key == "url" and isinstance(value, str)]
        return own + [url for value in node.values() for url in _urls(value)]
    if isinstance(node, list):
        return [url for value in node for url in _urls(value)]
    return []


def test_map_selection_proto_renders_offline(tmp_path, no_network, points) -> None:
    at = AppTest.from_file(str(_script(tmp_path, points))).run(timeout=60)
    assert not at.exception
    nodes = _deck_nodes(at)
    assert len(nodes) == 1
    assert nodes[0].proto.selection_mode


def test_map_falls_back_to_outline_once(tmp_path, monkeypatch, no_network, points) -> None:
    def raiser(*args, **kwargs):
        raise RuntimeError("basemap unavailable")

    monkeypatch.setattr(workspace_map, "build_deck", raiser)
    at = AppTest.from_file(str(_script(tmp_path, points))).run(timeout=60)
    assert not at.exception
    assert len(at.get("vega_lite_chart")) == 1
    assert len(at.info) == 1
    spec = json.loads(at.get("vega_lite_chart")[0].proto.spec)
    assert len(spec["layer"][1]["data"]["values"]) == len(points)


def test_selected_job_id_handles_positions_and_empty_frame() -> None:
    frame = pd.DataFrame({"job_id": ["JR-1", "JR-2", "JR-3"]})
    assert job_list.selected_job_id(frame, [2]) == "JR-3"
    assert job_list.selected_job_id(frame.iloc[0:0], [0]) is None
    assert job_list.selected_job_id(frame, [7]) is None


def test_picked_community_id_handles_first_object_and_empty_selection() -> None:
    event = SimpleNamespace(
        selection={
            "objects": {
                "jobs": [{"job_id": "JR-2", "community_id": "COMMUNITY-02"}],
                "selected": [{"job_id": "JR-1", "community_id": "COMMUNITY-01"}],
            }
        }
    )
    assert workspace_map.picked_community_id(event) == "COMMUNITY-02"
    assert workspace_map.picked_community_id(SimpleNamespace(selection={"objects": {}})) is None


def test_picked_community_id_ignores_a_counts_only_selection() -> None:
    event = SimpleNamespace(selection={"objects": {"counts": [{"community_id": "COMMUNITY-02"}]}})
    assert workspace_map.picked_community_id(event) is None


def test_choice_for_resolves_a_community_and_ignores_a_stale_pick() -> None:
    by_community = {
        "COMMUNITY-02": [SimpleNamespace(job_id="JR-9"), SimpleNamespace(job_id="JR-2")]
    }
    assert workspace_map.choice_for("COMMUNITY-02", by_community) == (
        "COMMUNITY-02",
        ["JR-2", "JR-9"],
    )
    # A filter change can drop the picked community from the map while the pick survives.
    assert workspace_map.choice_for("COMMUNITY-03", by_community) is None
    assert workspace_map.choice_for(None, by_community) is None
    assert workspace_map.choice_for("COMMUNITY-04", {"COMMUNITY-04": []}) is None
