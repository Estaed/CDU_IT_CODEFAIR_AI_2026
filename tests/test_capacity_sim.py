"""Capacity simulation: the PRD section 6.3 toy model on hand-built fixtures, plus a timed run
over the committed labels (CLAUDE.md Part 2 verification rule 2).

The pooled rule under test: a crew reaches its home region and anything within the
travel-day distance of its base; inside reach, communities are served in rank order, each by
the nearest free crew that reaches it."""

import csv
import json
import time
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from fair_turn.core import capacity_sim, constants, scoring
from fair_turn.core.capacity_sim import Closure, CrewBase, Site
from fair_turn.core.types import FaultType, HealthRiskFactor, Job, SafetyClass
from fair_turn.data import geography

BUILD_DIR = Path(__file__).resolve().parent.parent / "data" / "build"
START = constants.WINDOW_START
REGION = "R"
KM_PER_DEGREE = capacity_sim.haversine_km(0.0, 0.0, 0.0, 1.0)


def site_at(km: float, region: str = REGION) -> Site:
    """A sealed-road site ``km`` east of the base at (0, 0)."""
    return Site(region, km, 0.0, km / KM_PER_DEGREE, 1.0)


SITES = {
    "town": site_at(0.0),
    "near": site_at(50.0),
    "near2": site_at(60.0),
    "far": site_at(500.0),
    "other": site_at(0.0, region="OTHER"),
}
CREW = CrewBase("Base", "Base", 0.0, 0.0, REGION)


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
        crews=[CREW],
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
    # Urgent, not Immediate: an Immediate job goes to the make-safe contractor, no slot.
    jobs.append(make_job("top", "near", safety_class=SafetyClass.URGENT))
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
    assert result.travel_km == pytest.approx(500.0)


def test_travel_day_is_measured_from_the_crews_own_location() -> None:
    # A crew already out at "far" reaches a community 50 km further on without a travel day.
    beyond = {**SITES, "beyond": site_at(550.0)}
    first = make_job("a", "far")
    second = make_job("b", "beyond", reported_on=START + timedelta(days=2))
    result = run([first, second], sites=beyond)
    assert result.wait_days == {"a": 1, "b": 0}
    assert result.travel_km == pytest.approx(550.0)


def test_travel_cost_sums_trips_actually_made() -> None:
    near = make_job("a", "near", logistics_factor=40.0)
    near2 = make_job("b", "near2", logistics_factor=70.0, reported_on=START + timedelta(days=1))
    again = make_job("c", "near2", logistics_factor=70.0, reported_on=START + timedelta(days=2))
    result = run([near, near2, again])
    assert result.travel_cost == 110.0
    assert result.travel_km == pytest.approx(60.0)  # base to near 50, near to near2 10


def test_road_factor_scales_trip_km_and_the_travel_day_rule() -> None:
    rough = {**SITES, "rough": Site(REGION, 150.0, 0.0, 150.0 / KM_PER_DEGREE, 1.4)}
    result = run([make_job("a", "rough")], sites=rough)
    assert result.travel_km == pytest.approx(210.0)
    assert result.wait_days["a"] == 1  # 150 km at factor 1.4 is over the 200 km rule


def _far_high_need_fixture() -> list[Job]:
    far = make_job(  # Urgent, not Immediate: Immediate jobs never use a crew
        "far",
        "far",
        safety_class=SafetyClass.URGENT,
        health_risk=frozenset({HealthRiskFactor.ELDERLY}),
        logistics_factor=380.0,
    )
    return [far, make_job("town")]


def test_lambda_zero_narrows_the_gap_for_a_far_high_need_job() -> None:
    at_zero = run(_far_high_need_fixture(), lam=0.0)
    at_one = run(_far_high_need_fixture(), lam=1.0)
    # At lambda 0 the crew is out at "far" after day 1, so the town job costs a travel day back.
    assert at_zero.wait_days == {"far": 1, "town": 3}
    assert at_one.wait_days == {"town": 0, "far": 2}
    assert at_zero.gap == -2.0
    assert at_one.gap == 2.0
    assert at_zero.gap < at_one.gap


def test_a_far_higher_ranked_job_is_served_before_a_near_lower_ranked_one() -> None:
    far = make_job("far", "far", safety_class=SafetyClass.URGENT)
    near = make_job("near", "near")
    result = run([far, near], lam=0.0)
    # Travel day out, work far, travel day back (450 km), then the near job.
    assert result.wait_days == {"far": 1, "near": 3}


def test_a_crew_serves_another_region_within_the_travel_day_distance() -> None:
    result = run([make_job("o", "other")], days=3)
    assert result.wait_days["o"] == 0


def test_a_crew_never_serves_a_community_outside_its_reach() -> None:
    sites = {**SITES, "away": site_at(500.0, region="OTHER")}
    result = run([make_job("x", "away"), make_job("t")], sites=sites)
    assert result.completed_on["x"] is None
    assert result.wait_days["t"] == 0
    assert {community for _, _, community in result.visits} == {"town"}


def test_a_higher_ranked_community_nobody_free_reaches_does_not_hold_back_the_next() -> None:
    sites = {**SITES, "away": site_at(500.0, region="OTHER")}
    away = make_job("x", "away", safety_class=SafetyClass.URGENT)  # Immediate: no crew
    result = run([away, make_job("n", "near")], sites=sites)
    assert result.wait_days["n"] == 0


CREW_CLASSES = tuple(c for c in SafetyClass if c is not SafetyClass.IMMEDIATE)


@st.composite
def pooled_days(draw, crew_classes=CREW_CLASSES):
    community_count = draw(st.integers(1, 6))
    coords = [
        (
            draw(st.floats(-26, -11, allow_nan=False, allow_infinity=False)),
            draw(st.floats(129, 138, allow_nan=False, allow_infinity=False)),
        )
        for _ in range(community_count)
    ]
    regions = [draw(st.sampled_from(("R", "OTHER"))) for _ in range(community_count)]
    sites = {f"c{i}": Site(regions[i], 0.0, lat, lon, 1.0) for i, (lat, lon) in enumerate(coords)}
    entries = draw(
        st.lists(
            st.tuples(
                st.integers(0, community_count - 1),
                # Crew dispatch covers crew jobs; Immediate jobs have their own property.
                st.sampled_from(crew_classes),
                st.floats(0, 100, allow_nan=False, allow_infinity=False),
            ),
            min_size=1,
            max_size=12,
        )
    )
    jobs = [
        make_job(f"j{n:02d}", f"c{c}", safety_class=safety, logistics_factor=logistics)
        for n, (c, safety, logistics) in enumerate(entries)
    ]
    base_coords = draw(
        st.lists(
            st.tuples(
                st.floats(-26, -11, allow_nan=False, allow_infinity=False),
                st.floats(129, 138, allow_nan=False, allow_infinity=False),
            ),
            min_size=1,
            max_size=5,
        )
    )
    placed = draw(st.permutations(base_coords))
    crews = [
        CrewBase(f"crew{i}", f"crew{i}", lat, lon, draw(st.sampled_from(("R", "OTHER"))))
        for i, (lat, lon) in enumerate(placed)
    ]
    lam = draw(st.sampled_from((0.0, 0.5, 1.0)))
    return jobs, sites, crews, lam


TRAVEL_DAY = 300.0


def _km(crew: CrewBase, site: Site) -> float:
    return capacity_sim.haversine_km(crew.lat, crew.lon, site.lat, site.lon) * site.road_factor


def _reached(crew: CrewBase, site: Site) -> bool:
    return site.region == crew.region or _km(crew, site) <= TRAVEL_DAY


@settings(max_examples=150, deadline=None)
@given(pooled_days())
def test_day_one_serves_what_rank_order_nearest_reaching_crew_yields(case) -> None:
    jobs, sites, crews, lam = case
    result = capacity_sim.simulate(
        jobs,
        lam,
        START,
        1,
        closures=[],
        crews=crews,
        jobs_per_crew_day=len(jobs),
        travel_day_km=TRAVEL_DAY,
        sites=sites,
    )
    free = list(range(len(crews)))
    seen: set[str] = set()
    served: set[str] = set()
    for scored in scoring.rank(jobs, START, lam):
        community = scored.job.community_id
        if not free:
            break
        if community in seen:
            continue
        seen.add(community)
        reaching = [i for i in free if _reached(crews[i], sites[community])]
        if not reaching:
            continue
        km, chosen = min((_km(crews[i], sites[community]), i) for i in reaching)
        free.remove(chosen)
        if km <= TRAVEL_DAY:  # every crew starts at base, so only a longer trip costs the day
            served.add(community)
    done = {job_id for job_id, day in result.completed_on.items() if day == START}
    assert done == {j.job_id for j in jobs if j.community_id in served}


@settings(max_examples=100, deadline=None)
@given(pooled_days())
def test_no_crew_ever_serves_a_community_outside_its_reach(case) -> None:
    jobs, sites, crews, lam = case
    result = capacity_sim.simulate(
        jobs,
        lam,
        START,
        6,
        closures=[],
        crews=crews,
        jobs_per_crew_day=1,
        travel_day_km=TRAVEL_DAY,
        sites=sites,
    )
    by_id = {crew.crew_id: crew for crew in crews}
    for _, crew_id, community in result.visits:
        assert _reached(by_id[crew_id], sites[community])


@settings(max_examples=100, deadline=None)
@given(pooled_days(crew_classes=tuple(SafetyClass)), st.data())
def test_immediate_jobs_change_nothing_for_crew_jobs_and_complete_on_their_report_day(
    case, data
) -> None:
    jobs, sites, crews, lam = case
    shift = data.draw(st.lists(st.integers(0, 4), min_size=len(jobs), max_size=len(jobs)))
    jobs = [
        replace(j, reported_on=START + timedelta(days=d)) for j, d in zip(jobs, shift, strict=True)
    ]
    kwargs = dict(
        closures=[],
        crews=crews,
        jobs_per_crew_day=1,
        travel_day_km=TRAVEL_DAY,
        sites=sites,
    )
    crew_jobs = [j for j in jobs if j.safety_class is not SafetyClass.IMMEDIATE]
    everything = capacity_sim.simulate(jobs, lam, START, 6, **kwargs)
    crews_only = capacity_sim.simulate(crew_jobs, lam, START, 6, **kwargs)
    for job in jobs:
        if job.safety_class is SafetyClass.IMMEDIATE:
            assert everything.completed_on[job.job_id] == job.reported_on
            assert everything.wait_days[job.job_id] == 0
        else:
            assert everything.completed_on[job.job_id] == crews_only.completed_on[job.job_id]
    assert everything.visits == crews_only.visits
    assert everything.travel_cost == crews_only.travel_cost
    assert everything.travel_km == pytest.approx(crews_only.travel_km)
    assert everything.queue_length == crews_only.queue_length


def test_an_immediate_job_takes_no_crew_slot() -> None:
    routine = make_job("a")
    immediate = make_job("b", safety_class=SafetyClass.IMMEDIATE)
    result = run([routine, immediate])
    assert result.completed_on == {"a": START, "b": START}
    assert result.wait_days == {"a": 0, "b": 0}


def test_an_immediate_job_far_away_costs_no_travel_and_no_visit() -> None:
    far = make_job("x", "far", safety_class=SafetyClass.IMMEDIATE, logistics_factor=380.0)
    result = run([far])
    assert result.completed_on["x"] == START
    assert result.wait_days["x"] == 0
    assert result.travel_cost == 0.0
    assert result.travel_km == 0.0
    assert result.visits == []


def test_an_immediate_job_outside_every_crews_reach_is_still_made_safe() -> None:
    sites = {**SITES, "away": site_at(500.0, region="OTHER")}
    result = run([make_job("x", "away", safety_class=SafetyClass.IMMEDIATE)], sites=sites)
    assert result.completed_on["x"] == START
    assert result.visits == []


def test_a_road_closure_does_not_delay_an_immediate_job() -> None:
    closure = Closure("near", START, START + timedelta(days=5))
    immediate = make_job("i", "near", safety_class=SafetyClass.IMMEDIATE)
    routine = make_job("r", "near")
    result = run([immediate, routine], closures=[closure])
    assert result.completed_on["i"] == START and result.wait_days["i"] == 0
    assert result.wait_days["r"] == 6  # the crew job still waits for the road


def test_an_immediate_job_is_completed_on_its_report_day_not_before() -> None:
    later = START + timedelta(days=3)
    immediate = make_job("i", "near", safety_class=SafetyClass.IMMEDIATE, reported_on=later)
    result = run([immediate], days=6)
    assert result.completed_on["i"] == later
    assert result.wait_days["i"] == 0


def test_immediate_jobs_are_not_in_the_queue_but_count_in_the_medians_with_wait_zero() -> None:
    jobs = [
        make_job("t1"),
        make_job("t2"),
        make_job("t3", safety_class=SafetyClass.IMMEDIATE),
        make_job("r1", "near", safety_class=SafetyClass.IMMEDIATE),
    ]
    result = run(jobs, days=3)
    assert result.queue_length == [2, 1, 0]
    assert result.wait_days == {"t1": 0, "t2": 1, "t3": 0, "r1": 0}
    assert result.median_wait_town == 0.0  # waits 0, 1, 0
    assert result.median_wait_remote == 0.0


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
    result = run([far, town], crews=[CREW, CrewBase("Base 2", "Base", 0.0, 0.0, REGION)])
    assert result.wait_days == {"a": 1, "t": 0}


def test_crew_roster_places_each_regions_crews_at_its_base() -> None:
    bases = {region: "Darwin" for region in constants.REGIONS}
    bases[constants.REMOTE_REGIONS[0]] = "Alice Springs"
    roster = capacity_sim.crew_roster(bases)
    expected = constants.CREWS_PER_REMOTE_REGION * len(constants.REMOTE_REGIONS)
    assert len(roster) == expected + constants.CREWS_TOWN
    assert len({crew.crew_id for crew in roster}) == len(roster)
    for crew in roster:
        assert (crew.lat, crew.lon) == constants.CREW_BASE_COORDS[crew.base]
        assert crew.base == bases[crew.region]
    assert [crew.region for crew in roster].count(constants.TOWN_REGION) == constants.CREWS_TOWN
    with pytest.raises(ValueError, match="no crew base"):
        capacity_sim.crew_roster({})


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
    began = time.perf_counter()
    result = capacity_sim.simulate(
        jobs,
        1.0,
        START,
        30,
        closures,
        geography.crews(rows),
        constants.JOBS_PER_CREW_DAY,
        constants.TRAVEL_DAY_KM,
        geography.sim_sites(rows),
    )
    assert time.perf_counter() - began < 5.0
    assert jobs
    assert any(done is not None for done in result.completed_on.values())
    by_id = {j.job_id: j for j in jobs}
    for job_id, done in result.completed_on.items():
        assert done is None or end > done >= by_id[job_id].reported_on
    assert len(result.queue_length) == 30
