"""Workspace map helpers and job-list interaction (Task-22). The clustered map component
itself is tested in ``tests/test_cluster_map.py``."""

import socket
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from fair_turn.app.components import job_list, workspace_map


def _refuse(*args, **kwargs):
    raise RuntimeError("network disabled")


@pytest.fixture
def no_network(monkeypatch):
    monkeypatch.setattr(socket, "socket", _refuse)


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


def test_selected_job_id_handles_positions_and_empty_frame() -> None:
    frame = pd.DataFrame({"job_id": ["JR-1", "JR-2", "JR-3"]})
    assert job_list.selected_job_id(frame, [2]) == "JR-3"
    assert job_list.selected_job_id(frame.iloc[0:0], [0]) is None
    assert job_list.selected_job_id(frame, [7]) is None


def test_workspace_map_no_longer_carries_a_deck() -> None:
    source = Path(workspace_map.__file__).read_text("utf-8")
    assert "pydeck" not in source
    assert not hasattr(workspace_map, "build_deck")
    assert not hasattr(workspace_map, "picked")


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
