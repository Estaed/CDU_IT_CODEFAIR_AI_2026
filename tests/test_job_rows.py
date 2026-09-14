"""Today's list renders one bordered, openable row per job and reports the row that was
opened, without touching session state itself (Task-45, PRD 3.1)."""

import socket
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from fair_turn.app.components import job_rows
from fair_turn.app.components.ranking_table import short_id

CLICKED = "clicked"


def _refuse(*args, **kwargs):
    raise RuntimeError("network disabled")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(socket, "socket", _refuse)


def _row(rank: int, job_id: str, **overrides) -> dict:
    row = {
        "job_id": job_id,
        "rank": rank,
        "rank_change": job_rows.UNCHANGED,
        "community_id": f"COMMUNITY-0{rank}",
        "is_remote": rank != 1,
        "fault_type": "cooling",
        "safety_class": "urgent",
        "window": "6 of 2 d",
        "score": 4.0 - rank,
        "score_max": 4.0,
        "human_queue": False,
        "check": None,
    }
    return {**row, **overrides}


@pytest.fixture
def rows() -> list[dict]:
    return [
        _row(1, "JR-2025-00001", is_remote=False, rank_change="▲2"),
        _row(2, "JR-2025-00002", safety_class="immediate", check="confirmed"),
        _row(3, "JR-2025-00003", safety_class="routine", human_queue=True, check="corrected"),
    ]


def _script(tmp_path: Path, rows: list[dict], selected: str | None) -> Path:
    """A throwaway page that stores what ``render`` returned, so the assertion is on the
    component's return value rather than on anything it wrote itself."""
    path = tmp_path / "job_rows_app.py"
    path.write_text(
        "import streamlit as st\n"
        "from fair_turn.app.components import job_rows\n"
        f"opened = job_rows.render({rows!r}, {selected!r}, 'rows')\n"
        "if opened is not None:\n"
        f"    st.session_state[{CLICKED!r}] = opened\n"
        f"st.write(st.session_state.get({CLICKED!r}))\n",
        encoding="utf-8",
        newline="",
    )
    return path


def _run(path: Path) -> AppTest:
    at = AppTest.from_file(str(path)).run(timeout=60)
    assert not at.exception
    return at


def _bordered(at: AppTest) -> list:
    return [
        node for node in at if type(node).__name__ == "Block" and node.proto.flex_container.border
    ]


def test_one_bordered_row_per_job_with_an_open_button(tmp_path, rows) -> None:
    at = _run(_script(tmp_path, rows, rows[0]["job_id"]))
    assert len(_bordered(at)) == len(rows)
    assert [button.label for button in at.button] == [job_rows.OPEN] * len(rows)
    values = [markdown.value for markdown in at.markdown]
    for row in rows:
        assert f"**{row['fault_type'].capitalize()}**" in values
    captions = [caption.value for caption in at.caption]
    for row in rows:
        locality = "Remote" if row["is_remote"] else "Town"
        assert f"Job {short_id(row['job_id'])} · {row['community_id']} · {locality}" in captions
    assert captions.count("6 of 2 d") == len(rows)
    assert "▲2" in captions
    assert ":red-badge[Immediate]" in values
    assert ":gray-badge[Routine]" in values
    assert f":yellow-badge[{job_rows.NEEDS_HUMAN}]" in values
    assert len([node for node in at if getattr(node, "type", None) == "progress"]) == len(rows)


def test_selected_row_is_marked_and_its_button_is_primary(tmp_path, rows) -> None:
    at = _run(_script(tmp_path, rows, rows[1]["job_id"]))
    assert f":orange-badge[{job_rows.SELECTED}]" in [markdown.value for markdown in at.markdown]
    assert [button.proto.type for button in at.button] == ["secondary", "primary", "secondary"]
    none_selected = _run(_script(tmp_path, rows, None))
    assert f":orange-badge[{job_rows.SELECTED}]" not in [
        markdown.value for markdown in none_selected.markdown
    ]
    assert {button.proto.type for button in none_selected.button} == {"secondary"}


def test_open_returns_that_job_id(tmp_path, rows) -> None:
    at = _run(_script(tmp_path, rows, rows[0]["job_id"]))
    assert CLICKED not in at.session_state
    at.button(key=f"rows_open_{rows[1]['job_id']}").click().run(timeout=60)
    assert not at.exception
    assert at.session_state[CLICKED] == rows[1]["job_id"]


def test_each_row_shows_its_check_state_badge(tmp_path, rows) -> None:
    at = _run(_script(tmp_path, rows, None))
    badges = [m.value for m in at.markdown]
    assert sum("Not checked" in b for b in badges) == 1
    assert sum(":material/check: Checked" in b for b in badges) == 1
    assert sum(":material/close: Corrected" in b for b in badges) == 1
    assert any("green" in b and ":material/check: Checked" in b for b in badges)
    assert any("red" in b and ":material/close: Corrected" in b for b in badges)
