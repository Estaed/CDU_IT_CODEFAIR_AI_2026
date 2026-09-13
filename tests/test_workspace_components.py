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


def test_deck_spec_has_selected_layer_and_carto_style(points) -> None:
    spec = json.loads(workspace_map.build_deck(points, "JR-2025-00002").to_json())
    assert len(spec["layers"]) == 2
    assert len(spec["layers"][1]["data"]) == 1
    assert spec["layers"][1]["data"][0]["job_id"] == "JR-2025-00002"
    assert spec["mapProvider"] == "carto"
    assert "cartocdn.com" in spec["mapStyle"]
    assert all("cartocdn.com" in value for value in _urls(spec))


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


def test_picked_id_handles_first_object_and_empty_selection() -> None:
    event = SimpleNamespace(
        selection={"objects": {"jobs": [{"job_id": "JR-2"}], "selected": [{"job_id": "JR-1"}]}}
    )
    assert workspace_map.picked_id(event) == "JR-2"
    assert workspace_map.picked_id(SimpleNamespace(selection={"objects": {}})) is None
