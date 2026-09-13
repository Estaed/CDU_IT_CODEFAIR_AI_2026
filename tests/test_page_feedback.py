"""Feedback-loop page (Task-19): three charts only after Run, and the plotted data is the
``feedback_sim.run`` output. Network disabled as in ``test_app_smoke``."""

import socket
from pathlib import Path

import pyarrow as pa
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest
from test_feedback_sim import artefacts

from fair_turn.core import constants, feedback_sim

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "fair_turn" / "app" / "pages" / "feedback.py"
CHOSEN_LAM = 0.5
DECAY = 0.3
EFFICIENCY_RUN = "Efficiency only (λ = 1.0)"
REAL_RUN = feedback_sim.run


def _refuse(*args, **kwargs):
    raise RuntimeError("network disabled")


@pytest.fixture
def no_network(monkeypatch):
    monkeypatch.setattr(socket, "socket", _refuse)


@pytest.fixture
def run_calls(monkeypatch) -> list[tuple[float, float]]:
    """Every ``feedback_sim.run`` call as ``(lam, decay)``; the cache starts empty."""
    st.cache_data.clear()
    calls = []

    def counting(labels, communities, lam, decay, *args, **kwargs):
        calls.append((lam, decay))
        return REAL_RUN(labels, communities, lam, decay, *args, **kwargs)

    monkeypatch.setattr(feedback_sim, "run", counting)
    yield calls
    st.cache_data.clear()


def _open(lam: float, decay: float) -> AppTest:
    at = AppTest.from_file(str(PAGE)).run(timeout=60)
    at.slider[0].set_value(lam)
    at.slider[1].set_value(decay)
    return at.run(timeout=60)


def _run(lam: float, decay: float) -> AppTest:
    at = _open(lam, decay).button[0].click().run(timeout=60)
    assert not at.exception
    return at


def _plotted(at: AppTest):
    """The rows behind each chart, decoded from the Arrow dataset Streamlit ships."""
    return [
        pa.ipc.open_stream(c.proto.datasets[0].data.data).read_pandas()
        for c in at.get("vega_lite_chart")
    ]


def _report_series(at: AppTest) -> dict[str, list]:
    reports = _plotted(at)[0]
    return {
        run: list(zip(rows["week"], rows["locality"], rows["value"], strict=True))
        for run, rows in reports.groupby("run")
    }


def test_simulation_runs_only_when_run_is_pressed(no_network, run_calls) -> None:
    at = _open(CHOSEN_LAM, DECAY)
    assert not at.exception
    assert run_calls == []
    assert not at.get("vega_lite_chart")

    at.button[0].click().run(timeout=60)
    assert not at.exception
    assert sorted(run_calls) == [(CHOSEN_LAM, DECAY), (1.0, DECAY)]
    assert len(at.get("vega_lite_chart")) == 3

    at.slider[1].set_value(0.4).run(timeout=60)  # a widget move alone runs nothing
    assert len(run_calls) == 2
    assert not at.get("vega_lite_chart")


def test_plotted_gap_of_the_efficiency_run_is_the_simulation_output(no_network) -> None:
    at = _run(CHOSEN_LAM, DECAY)
    gap = _plotted(at)[2]
    plotted = gap[gap["run"] == EFFICIENCY_RUN]
    jobs, sites, closures = artefacts()
    expected = REAL_RUN(jobs, sites, 1.0, DECAY, constants.SEED, closures)
    assert list(zip(plotted["week"], plotted["value"], strict=True)) == [
        (week.isoformat(), g)
        for week, g in zip(expected.week_start, expected.gap, strict=True)
        if g is not None
    ]
    assert set(gap["run"]) == {EFFICIENCY_RUN, f"Chosen (λ = {CHOSEN_LAM:g})"}
    # With decay the two runs thin reports differently, so the zero-decay test below can fail.
    first, second = _report_series(at).values()
    assert first != second


def test_zero_decay_gives_identical_report_series(no_network) -> None:
    at = _run(CHOSEN_LAM, 0.0)
    series = _report_series(at)
    assert len(series) == 2
    first, second = series.values()
    assert first == second
