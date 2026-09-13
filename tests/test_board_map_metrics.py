"""Board map and wait metrics (Task-15): the map is inline data with an outline layer, and
the metrics stay hidden until sign-off, then equal ``capacity_sim`` output."""

import json
import socket
from datetime import date, timedelta
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from fair_turn.app import state
from fair_turn.app.components import map as nt_map_component
from fair_turn.app.components import metrics
from fair_turn.core import capacity_sim, constants
from fair_turn.data import artefacts

ROOT = Path(__file__).resolve().parent.parent
BOARD = ROOT / "fair_turn" / "app" / "pages" / "board.py"
SIGNED_KEY = "signed_today"  # the key ``state.get_signed_today`` reads
REGION = constants.REMOTE_REGIONS[0]


def _refuse(*args, **kwargs):
    raise RuntimeError("network disabled")


@pytest.fixture
def no_network(monkeypatch):
    monkeypatch.setattr(socket, "socket", _refuse)


@pytest.fixture(scope="module")
def art() -> artefacts.Artefacts:
    return artefacts.load_all()


def _keys(node) -> set[str]:
    if isinstance(node, dict):
        return set(node).union(*(_keys(v) for v in node.values()))
    if isinstance(node, list):
        return set().union(*(_keys(v) for v in node))
    return set()


def _marks(spec: dict) -> list[str]:
    layers = spec.get("layer", [spec])
    return [m if isinstance(m, str) else m["type"] for m in (layer["mark"] for layer in layers)]


def _simulate(art: artefacts.Artefacts, today: date, lam: float, jobs=None):
    inputs = metrics.sim_inputs(art)
    if jobs is not None:
        inputs["jobs"] = jobs
    return capacity_sim.simulate(
        lam=lam,
        start=constants.WINDOW_START,
        days=(today - constants.WINDOW_START).days + 1,
        **inputs,
    )


# --- nt_map ----------------------------------------------------------------------------------


def test_map_spec_is_inline_with_outline_and_dots(art) -> None:
    counts = {cid: 2 for cid in list(art.communities)[:3]}
    spec = nt_map_component.nt_map(art.communities, counts, state.ALL_REGIONS).to_dict()
    assert "url" not in _keys(spec)
    assert _marks(spec) == ["geoshape", "circle"]
    points = spec["layer"][1]["data"]["values"]
    assert {p["community_id"] for p in points} == set(art.communities)
    assert {p["community_id"]: p["open"] for p in points if p["open"]} == counts
    outline = spec["layer"][0]["data"]["values"]
    assert [f["properties"]["iso_3166_2"] for f in outline] == ["AU-NT"]


def test_map_for_one_region_drops_outline_and_other_regions(art) -> None:
    spec = nt_map_component.nt_map(art.communities, {}, REGION).to_dict()
    assert "url" not in _keys(spec)
    assert _marks(spec) == ["circle"]
    ids = {p["community_id"] for p in spec["data"]["values"]}
    assert ids == {cid for cid, row in art.communities.items() if row["region"] == REGION}
    assert 0 < len(ids) < len(art.communities)


# --- panel values ----------------------------------------------------------------------------


def test_region_panel_equals_a_simulation_of_that_region_alone(art) -> None:
    """Crews only take jobs in their own region and scores do not depend on other jobs, so
    the region's medians in the full run equal those of a run over the region's jobs only."""
    today = constants.WINDOW_START + timedelta(days=45)
    jobs = artefacts.to_jobs(art)
    full = _simulate(art, today, 0.0)
    for region in (REGION, constants.TOWN_REGION):
        own = [j for j in jobs if art.communities[j.community_id]["region"] == region]
        alone = _simulate(art, today, 0.0, own)
        values = metrics.panel_values(full, jobs, art.communities, region)
        assert values["median_wait_remote"] == alone.median_wait_remote
        assert values["median_wait_town"] == alone.median_wait_town
        assert values["gap"] == alone.gap
        assert values["travel_cost"] == full.travel_cost
    town = metrics.panel_values(full, jobs, art.communities, constants.TOWN_REGION)
    assert town["median_wait_town"] is not None
    assert town["median_wait_remote"] is None and town["gap"] is None


def test_formatting_and_deltas() -> None:
    values = {
        "median_wait_remote": 12.5,
        "median_wait_town": None,
        "gap": 3.0,
        "travel_cost": 1234.4,
    }
    base = {"median_wait_remote": 10.0, "median_wait_town": 4.0, "gap": 3.5, "travel_cost": 1000.0}
    assert metrics.formatted(values) == {
        "median_wait_remote": "12.5 days",
        "median_wait_town": metrics.NOT_AVAILABLE,
        "gap": "3.0 days",
        "travel_cost": "1,234",
    }
    assert metrics.deltas(values, base) == {
        "median_wait_remote": "+2.5 days",
        "median_wait_town": None,
        "gap": "-0.5 days",
        "travel_cost": "+234",
    }


# --- the board -------------------------------------------------------------------------------


def _charts(at: AppTest) -> list[dict]:
    return [json.loads(c.proto.spec) for c in at.get("vega_lite_chart")]


def test_board_map_and_decide_before_reveal(no_network, art) -> None:
    at = AppTest.from_file(str(BOARD)).run(timeout=60)
    assert not at.exception
    maps = [s for s in _charts(at) if "geoshape" in _marks(s)]
    assert len(maps) == 1
    assert "url" not in _keys(maps[0])
    assert len(at.metric) == 0
    assert any("sign-off" in i.value for i in at.info)

    lam = 0.5
    at.session_state[SIGNED_KEY] = True
    at.slider[0].set_value(lam).run(timeout=60)
    assert not at.exception
    assert not any("sign-off" in i.value for i in at.info)
    today = at.date_input[0].value
    jobs = artefacts.to_jobs(art)
    chosen = _simulate(art, today, lam)
    efficiency = _simulate(art, today, 1.0)
    values = metrics.panel_values(chosen, jobs, art.communities, state.ALL_REGIONS)
    baseline = metrics.panel_values(efficiency, jobs, art.communities, state.ALL_REGIONS)
    assert values == {
        "median_wait_remote": chosen.median_wait_remote,
        "median_wait_town": chosen.median_wait_town,
        "gap": chosen.gap,
        "travel_cost": chosen.travel_cost,
    }
    assert len(at.metric) == 4
    assert [m.label for m in at.metric] == list(metrics.LABELS.values())
    assert [m.value for m in at.metric] == list(metrics.formatted(values).values())
    shown_deltas = [m.delta or None for m in at.metric]
    assert shown_deltas == list(metrics.deltas(values, baseline).values())
    assert values != baseline  # otherwise the delta comparison proves nothing


def test_board_map_zooms_to_region(no_network, art) -> None:
    at = AppTest.from_file(str(BOARD)).run(timeout=60)
    at.selectbox(key="board_region").set_value(REGION).run(timeout=60)
    assert not at.exception
    (spec,) = [s for s in _charts(at) if "circle" in _marks(s)]
    assert _marks(spec) == ["circle"]
    assert "url" not in _keys(spec)
