"""Capacity simulation: the PRD section 6.3 toy model on hand-built fixtures, plus a timed run
over the committed labels (CLAUDE.md Part 2 verification rule 2)."""

import csv
import json
import time
from datetime import date, timedelta
from pathlib import Path

import pytest

from fair_turn.core import capacity_sim, constants
from fair_turn.core.capacity_sim import Closure, Site
from fair_turn.core.types import FaultType, HealthRiskFactor, Job, SafetyClass

BUILD_DIR = Path(__file__).resolve().parent.parent / "data" / "build"
START = constants.WINDOW_START
REGION = "R"
SITES = {
    "town": Site(region=REGION, km_to_base=0.0),
    "near": Site(region=REGION, km_to_base=50.0),
    "near2": Site(region=REGION, km_to_base=60.0),
    "far": Site(region=REGION, km_to_base=500.0),
    "other": Site(region="OTHER", km_to_base=0.0),
}


def make_job(job_id: str, community_id: str = "town", **overrides) -> Job:
    base = dict(
        job_id=job_id,
        community_id=community_id,
        is_remote=community_id != "town",
        reported_on=START,
        fault_type=FaultType.PLUMBING_WATER,
        safety_class=SafetyClass.ROUTINE,
    )
    base.update(overrides)
    return Job(**base)


def run(jobs: list[Job], lam: float = 0.0, days: int = 10, **overrides):
    kwargs = dict(
        closures=[],
        crews_per_region={REGION: 1},
        jobs_per_crew_day=1,
        travel_day_km=200,
        sites=SITES,
    )
    kwargs.update(overrides)
    return capacity_sim.simulate(jobs, lam, START, days, **kwargs)


def test_two_jobs_one_crew_wait_zero_and_one_in_rank_order() -> None:
    routine = make_job("a")
    urgent = make_job("b", safety_class=SafetyClass.URGENT)
    result = run([routine, urgent])
    assert result.wait_days == {"b": 0, "a": 1}
    assert result.completed_on == {"b": START, "a": START + timedelta(days=1)}


def test_batching_completes_a_community_in_one_visit() -> None:
    jobs = [make_job(f"j{i}", "near") for i in range(3)] + [make_job("x", "near2")]
    result = run(jobs, jobs_per_crew_day=4)
    assert [result.wait_days[f"j{i}"] for i in range(3)] == [0, 0, 0]
    assert result.wait_days["x"] == 1  # batching stays in the visited community


def test_batching_is_capped_by_capacity_in_rank_order() -> None:
    jobs = [make_job(f"j{i}", "near") for i in range(4)]
    jobs.append(make_job("top", "near", safety_class=SafetyClass.IMMEDIATE))
    result = run(jobs, jobs_per_crew_day=4)
    assert result.wait_days["top"] == 0
    assert sorted(result.wait_days[f"j{i}"] for i in range(4)) == [0, 0, 0, 1]
    assert result.wait_days["j3"] == 1  # job_id breaks the tie, last in rank


def test_closure_blocks_completion_until_it_lifts() -> None:
    job = make_job("a", "near")
    closure = Closure("near", START, START + timedelta(days=2))
    result = run([job], closures=[closure])
    assert result.wait_days["a"] == 3
    open_town = make_job("t")
    result = run([job, open_town], closures=[closure])
    assert result.wait_days == {"t": 0, "a": 3}


def test_travel_day_adds_one_and_not_when_already_there() -> None:
    assert run([make_job("a", "near")]).wait_days["a"] == 0
    first = make_job("a", "far")
    second = make_job("b", "far", reported_on=START + timedelta(days=1))
    result = run([first, second])
    assert result.wait_days == {"a": 1, "b": 1}
    assert result.travel_cost == first.logistics_factor


def test_travel_cost_sums_trips_actually_made() -> None:
    near = make_job("a", "near", logistics_factor=40.0)
    near2 = make_job("b", "near2", logistics_factor=70.0, reported_on=START + timedelta(days=1))
    again = make_job("c", "near2", logistics_factor=70.0, reported_on=START + timedelta(days=2))
    assert run([near, near2, again]).travel_cost == 110.0


def _far_high_need_fixture() -> list[Job]:
    far = make_job(
        "far",
        "far",
        safety_class=SafetyClass.IMMEDIATE,
        health_risk=frozenset({HealthRiskFactor.ELDERLY}),
        logistics_factor=380.0,
    )
    return [far, make_job("town")]


def test_lambda_zero_narrows_the_gap_for_a_far_high_need_job() -> None:
    at_zero = run(_far_high_need_fixture(), lam=0.0)
    at_one = run(_far_high_need_fixture(), lam=1.0)
    assert at_zero.wait_days == {"far": 1, "town": 2}
    assert at_one.wait_days == {"town": 0, "far": 2}
    assert at_zero.gap == -1.0
    assert at_one.gap == 2.0
    assert at_zero.gap < at_one.gap


def test_crews_only_serve_their_own_region() -> None:
    result = run([make_job("o", "other")], days=3)
    assert result.completed_on["o"] is None
    assert result.wait_days["o"] is None
    assert result.median_wait_remote == 3.0  # still open, censored at the end of the run


def test_medians_split_town_and_remote_and_queue_length_counts_open_jobs() -> None:
    jobs = [make_job("t1"), make_job("t2"), make_job("r1", "near"), make_job("r2", "near")]
    jobs.append(make_job("human", fault_type=None))
    result = run(jobs, jobs_per_crew_day=2, days=3)
    # Tied scores rank by job_id, so the remote pair is batched first.
    assert result.median_wait_remote == 0.0
    assert result.median_wait_town == 1.0
    assert result.gap == -1.0
    assert result.queue_length == [4, 2, 0]
    assert result.completed_on["human"] is None


def test_two_crews_do_not_both_travel_for_the_same_job() -> None:
    far = make_job("a", "far")
    town = make_job("t", reported_on=START)
    result = run([far, town], crews_per_region={REGION: 2})
    assert result.wait_days == {"a": 1, "t": 0}


def test_unknown_community_is_an_error() -> None:
    with pytest.raises(ValueError, match="no site"):
        run([make_job("a", "nowhere")])


def test_deterministic() -> None:
    assert run(_far_high_need_fixture()) == run(_far_high_need_fixture())


def test_thirty_day_slice_of_committed_labels_runs_fast_and_consistent() -> None:
    labels_path = BUILD_DIR / "labels.json"
    if not labels_path.exists():
        pytest.skip("data/build/labels.json absent")
    with (BUILD_DIR / "communities.csv").open(newline="", encoding="utf-8") as f:
        rows = {r["community_id"]: r for r in csv.DictReader(f)}
    sites = {cid: Site(r["region"], float(r["km_to_base"])) for cid, r in rows.items()}
    end = START + timedelta(days=30)
    jobs = []
    for label in json.loads(labels_path.read_text(encoding="utf-8")):
        reported = date.fromisoformat(label["reported_on"])
        if reported >= end:
            continue
        community = rows[label["community_id"]]
        jobs.append(
            Job(
                job_id=label["job_id"],
                community_id=label["community_id"],
                is_remote=community["is_remote"] == "True",
                reported_on=reported,
                fault_type=FaultType(label["fault_type"]),
                safety_class=SafetyClass(label["safety_class"]),
                health_risk=frozenset(HealthRiskFactor(h) for h in label["health_risk"]),
                logistics_factor=float(community["logistics_factor"]),
            )
        )
    closures = [
        Closure(
            c["community_id"],
            date.fromisoformat(c["closed_from"]),
            date.fromisoformat(c["closed_to"]),
        )
        for c in json.loads((BUILD_DIR / "closures.json").read_text(encoding="utf-8"))
    ]
    crews = {r: constants.CREWS_PER_REMOTE_REGION for r in constants.REMOTE_REGIONS}
    crews[constants.TOWN_REGION] = constants.CREWS_TOWN
    began = time.perf_counter()
    result = capacity_sim.simulate(
        jobs,
        1.0,
        START,
        30,
        closures,
        crews,
        constants.JOBS_PER_CREW_DAY,
        constants.TRAVEL_DAY_KM,
        sites,
    )
    assert time.perf_counter() - began < 5.0
    assert jobs
    assert any(done is not None for done in result.completed_on.values())
    by_id = {j.job_id: j for j in jobs}
    for job_id, done in result.completed_on.items():
        assert done is None or end > done >= by_id[job_id].reported_on
    assert len(result.queue_length) == 30
