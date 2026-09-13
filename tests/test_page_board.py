"""The triage board renders offline at both lam extremes, shows exactly what ``scoring``
computes, and keeps human-queue jobs out of both rankings."""

import socket
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from fair_turn.app.components import ranking_table
from fair_turn.core import constants, scoring
from fair_turn.core.types import FaultType, Job, SafetyClass, ScoredJob

ROOT = Path(__file__).resolve().parent.parent
BOARD = ROOT / "fair_turn" / "app" / "pages" / "board.py"


LAST_DAY = constants.WINDOW_START + timedelta(days=constants.WINDOW_DAYS)


def _refuse(*args, **kwargs):
    raise RuntimeError("network disabled")


@pytest.fixture(scope="module")
def board_runs() -> dict[float, AppTest]:
    """One run at the default lam and one after moving the slider to 0.0."""
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(socket, "socket", _refuse)
        at = AppTest.from_file(str(BOARD)).run(timeout=60)
        assert not at.exception
        default = {
            "lam": at.slider[0].value,
            "today": at.date_input[0].value,
            "frames": [at.dataframe[0].value, at.dataframe[1].value],
            "warning": at.warning[0].value if at.warning else "",
        }
        at.slider[0].set_value(0.0).run(timeout=60)
        assert not at.exception
        equity = {
            "lam": at.slider[0].value,
            "today": at.date_input[0].value,
            "frames": [at.dataframe[0].value, at.dataframe[1].value],
            "warning": at.warning[0].value if at.warning else "",
        }
    return {1.0: default, 0.0: equity}


def test_default_is_efficiency_first_on_the_last_day(board_runs) -> None:
    run = board_runs[1.0]
    assert run["lam"] == 1.0
    assert run["today"] == LAST_DAY


@pytest.mark.parametrize("lam", [1.0, 0.0])
def test_two_frames_and_scores_equal_scoring(board_runs, lam) -> None:
    run = board_runs[lam]
    assert run["lam"] == lam
    today: date = run["today"]
    jobs = ranking_table.open_jobs(today)
    left, right = run["frames"]
    for frame, table_lam in ((left, lam), (right, 1.0)):
        expected = scoring.rank(jobs, today, table_lam)
        assert len(frame) == len(expected) > 0
        assert list(frame["job id"]) == [s.job.job_id for s in expected]
        assert list(frame["rank"]) == [s.rank for s in expected]
        assert list(frame["score"]) == [round(s.score, 1) for s in expected]
        for name in scoring.FACTOR_NAMES:
            assert list(frame[name]) == [s.factors[name] for s in expected]


def test_orders_differ_at_lam_zero(board_runs) -> None:
    left, right = board_runs[0.0]["frames"]
    assert list(left["job id"]) != list(right["job id"])
    assert set(left["job id"]) == set(right["job id"])
    assert (right["rank change"] != ranking_table.UNCHANGED).any()
    same_left, same_right = board_runs[1.0]["frames"]
    assert list(same_left["job id"]) == list(same_right["job id"])
    assert (same_right["rank change"] == ranking_table.UNCHANGED).all()


@pytest.mark.parametrize("lam", [1.0, 0.0])
def test_human_queue_in_warning_and_in_neither_frame(board_runs, lam) -> None:
    run = board_runs[lam]
    _, queue = scoring.split_human_queue(ranking_table.open_jobs(run["today"]))
    assert queue, "the committed artefacts should leave at least one job for a human"
    shown = set().union(*(set(f["job id"]) for f in run["frames"]))
    for job in queue:
        assert job.job_id in run["warning"]
        assert job.job_id not in shown


def test_open_jobs_are_reported_and_unfinished() -> None:
    first = ranking_table.open_jobs(LAST_DAY - timedelta(days=60))
    last = ranking_table.open_jobs(LAST_DAY)
    assert all(j.reported_on <= LAST_DAY for j in last)
    assert len({j.job_id for j in last}) == len(last)
    assert first and last and {j.job_id for j in first} != {j.job_id for j in last}


# --- rank-change column on hand-built jobs ---------------------------------------------------


def _scored(job_id: str, rank: int, score: float) -> ScoredJob:
    job = Job(
        job_id=job_id,
        community_id="C-01",
        is_remote=False,
        reported_on=date(2025, 10, 1),
        fault_type=FaultType.PESTS,
        safety_class=SafetyClass.ROUTINE,
    )
    factors = {"urgency": 0.1, "safety": 1.0, "health_risk": 0.0, "logistics": 0.2}
    return ScoredJob(job=job, score=score, factors=factors, rank=rank, needs_human=False)


def test_rank_change_column_on_hand_built_list() -> None:
    at_one = [_scored("A", 1, 3.0), _scored("B", 2, 2.0), _scored("C", 3, 1.0)]
    at_lam = [replace(at_one[2], rank=1), replace(at_one[0], rank=2), replace(at_one[1], rank=3)]
    frame = ranking_table.rows_for(at_one, at_lam, 1.0, date(2025, 10, 3))
    assert dict(zip(frame["job id"], frame["rank change"], strict=True)) == {
        "A": "▼1",
        "B": "▼1",
        "C": "▲2",
    }
    assert list(frame.columns[:2]) == ["rank", "rank change"]
    left = ranking_table.rows_for(at_lam, None, 0.0, date(2025, 10, 3))
    assert "rank change" not in left.columns
    assert list(left["days open"]) == [2, 2, 2]
    assert list(left["days left in window"]) == [8.0, 8.0, 8.0]
    same = ranking_table.rows_for(at_one, at_one, 1.0, date(2025, 10, 3))
    assert set(same["rank change"]) == {ranking_table.UNCHANGED}


@pytest.mark.parametrize(("places", "text"), [(3, "▲3"), (-2, "▼2"), (0, "·")])
def test_rank_change_text(places, text) -> None:
    assert ranking_table.rank_change(places) == text
