"""Pooled visit-plan invariants with crew reach (PRD section 3.3, 2026-09-14 night).

Distance chooses which crew goes, never which job is served: membership is the signed list, a
crew only takes stops it reaches, slots go in signed-rank order to the nearest crew that
reaches the stop, and within a crew the order is the shortest route."""

from itertools import permutations
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from fair_turn.core import constants
from fair_turn.core.capacity_sim import CrewBase, crew_roster, haversine_km
from fair_turn.core.visit_plan import (
    MANUAL_NEXT_ACTION,
    MANUAL_OWNER,
    NO_FREE_SLOT,
    NO_REACH,
    ROAD_CLOSED,
    Stop,
    _measure,
    edit_order,
    plan,
)
from fair_turn.data.geography import BASE_FOR_REGION

CAP = constants.JOBS_PER_CREW_DAY
REGION = constants.REGIONS[0]


def roster() -> tuple[CrewBase, ...]:
    return crew_roster({region: base.title() for region, base in BASE_FOR_REGION.items()})


def base_crew(crew_id: str = "Base", lat: float = 0.0, lon: float = 0.0) -> CrewBase:
    return CrewBase(crew_id, "Base", lat, lon, REGION)


def stop(job_id: str, rank: int, lat: float, lon: float, **overrides) -> Stop:
    values = dict(
        job_id=job_id,
        community_id=f"community-{job_id}",
        region=REGION,
        lat=lat,
        lon=lon,
        access="road",
        road_open=True,
        signed_rank=rank,
        road_factor=1.0,
    )
    values.update(overrides)
    return Stop(**values)


def km_from_base(crew: CrewBase, s: Stop) -> float:
    return haversine_km(crew.lat, crew.lon, s.lat, s.lon) * s.road_factor


def reached(crew: CrewBase, s: Stop) -> bool:
    return s.region == crew.region or km_from_base(crew, s) <= constants.TRAVEL_DAY_KM


@st.composite
def stop_lists(draw) -> list[Stop]:
    entries = draw(
        st.lists(
            st.tuples(
                st.floats(-26, -11, allow_nan=False, allow_infinity=False),
                st.floats(129, 138, allow_nan=False, allow_infinity=False),
                st.sampled_from(("road", "road", "air", "barge")),
                st.booleans() | st.just(True),
                st.integers(0, 3),  # a few shared communities
                st.sampled_from((1.0, 1.4)),
                st.sampled_from(constants.REGIONS),
            ),
            min_size=1,
            max_size=18,
        )
    )
    return [
        Stop(
            f"j{index:02d}",
            f"community-{shared if shared else index}",
            region,
            lat,
            lon,
            access,
            road_open,
            index,
            factor,
        )
        for index, (lat, lon, access, road_open, shared, factor, region) in enumerate(
            entries, start=1
        )
    ]


def _ids(current) -> tuple[list[str], list[str], list[str]]:
    planned = [s.job_id for crew in current.crews for s in crew.stops]
    return (
        planned,
        [item.stop.job_id for item in current.unplanned],
        [item.stop.job_id for item in current.manual],
    )


@settings(max_examples=100, deadline=None)
@given(stop_lists())
def test_membership_is_the_signed_list(stops: list[Stop]) -> None:
    current = plan(7, stops, roster())
    planned, unplanned, manual = _ids(current)
    assert sorted(planned + unplanned + manual) == sorted(s.job_id for s in stops)
    assert all(item.next_action == MANUAL_NEXT_ACTION for item in current.manual)
    assert all(item.owner == MANUAL_OWNER for item in current.manual)
    assert {s.job_id for s in stops if s.access != "road"} == set(manual)
    closed = {s.job_id for s in stops if s.access == "road" and not s.road_open}
    assert closed == {i.stop.job_id for i in current.unplanned if i.reason == ROAD_CLOSED}
    assert current.out_of_reach == sum(
        i.reason in (NO_FREE_SLOT, NO_REACH) for i in current.unplanned
    )
    for crew in current.crews:
        assert len(crew.stops) <= CAP
        assert len(crew.legs_km) == (len(crew.stops) + 1 if crew.stops else 0)
        assert crew.travel_day_legs == tuple(leg > constants.TRAVEL_DAY_KM for leg in crew.legs_km)
    assert current.batch_version == 7


@settings(max_examples=100, deadline=None)
@given(stop_lists())
def test_no_planned_stop_lies_outside_its_crews_reach(stops: list[Stop]) -> None:
    for crew_plan in plan(1, stops, roster()).crews:
        assert all(reached(crew_plan.crew, s) for s in crew_plan.stops)


@settings(max_examples=150, deadline=None)
@given(stop_lists())
def test_slots_go_in_signed_rank_order_to_the_nearest_crew_that_reaches(stops) -> None:
    crews = roster()
    current = plan(1, stops, crews)
    held = {index: crew_plan.stops for index, crew_plan in enumerate(current.crews)}

    def full_of_higher_ranks(index: int, s: Stop) -> bool:
        return len(held[index]) == CAP and all(o.signed_rank < s.signed_rank for o in held[index])

    for index, crew_plan in enumerate(current.crews):
        for s in crew_plan.stops:
            mine = (km_from_base(crews[index], s), index)
            for other, crew in enumerate(crews):
                if reached(crew, s) and (km_from_base(crew, s), other) < mine:
                    assert full_of_higher_ranks(other, s)
    for item in current.unplanned:
        reaching = [i for i, crew in enumerate(crews) if reached(crew, item.stop)]
        if item.reason == NO_REACH:
            assert not reaching
        elif item.reason == NO_FREE_SLOT:
            assert reaching
            assert all(full_of_higher_ranks(i, item.stop) for i in reaching)


def test_a_darwin_heavy_list_leaves_the_overflow_unplanned() -> None:
    crews = roster()
    darwin_lat, darwin_lon = constants.CREW_BASE_COORDS["Darwin"]
    darwin_crews = sum(crew.base == "Darwin" for crew in crews)
    count = darwin_crews * CAP + 3
    stops = [
        stop(f"d{i:02d}", i, darwin_lat + 0.01 * i, darwin_lon, region=constants.TOWN_REGION)
        for i in range(1, count + 1)
    ]
    current = plan(1, stops, crews)
    for crew_plan in current.crews:
        if crew_plan.crew.base != "Darwin":
            assert not crew_plan.stops, f"{crew_plan.crew.crew_id} sent to Darwin"
    planned, unplanned, _ = _ids(current)
    assert sorted(planned) == [s.job_id for s in stops[: darwin_crews * CAP]]
    assert unplanned == [s.job_id for s in stops[darwin_crews * CAP :]]
    assert {item.reason for item in current.unplanned} == {NO_FREE_SLOT}
    assert current.out_of_reach == 3


def test_a_far_high_rank_stop_is_planned_and_a_near_low_rank_stop_is_left_over() -> None:
    far = stop("far", 1, 0.0, 5.0)
    fillers = [stop(f"f{i}", i + 2, 0.0, 0.5) for i in range(CAP - 1)]
    near = stop("near", 99, 0.0, 0.01)
    current = plan(3, [near, far, *fillers], [base_crew()])
    planned, unplanned, _ = _ids(current)
    assert "far" in planned
    assert unplanned == ["near"]
    assert current.unplanned[0].reason == NO_FREE_SLOT


def test_a_community_no_crew_reaches_stays_unplanned_with_that_reason() -> None:
    other_region = constants.REGIONS[1]
    own = stop("own", 1, 0.0, 5.0)  # over the travel-day distance, but in the home region
    foreign_far = stop("foreign", 2, 0.0, 5.0, region=other_region)
    foreign_near = stop("close", 3, 0.0, 0.5, region=other_region)
    current = plan(1, [own, foreign_far, foreign_near], [base_crew()])
    planned, unplanned, _ = _ids(current)
    assert sorted(planned) == ["close", "own"]
    assert [(i.stop.job_id, i.reason) for i in current.unplanned] == [("foreign", NO_REACH)]
    assert unplanned == ["foreign"]


def test_a_km_tie_goes_to_the_earlier_crew_in_the_roster() -> None:
    crews = (base_crew("A 1"), base_crew("A 2"))
    stops = [stop(f"s{i}", i, 0.0, 1.0) for i in range(1, CAP + 2)]
    current = plan(1, stops, crews)
    assert {s.job_id for s in current.crews[0].stops} == {f"s{i}" for i in range(1, CAP + 1)}
    assert [s.job_id for s in current.crews[1].stops] == [f"s{CAP + 1}"]


@settings(max_examples=100, deadline=None)
@given(stop_lists())
def test_each_crew_drives_the_shortest_route(stops: list[Stop]) -> None:
    for crew_plan in plan(1, stops, roster()).crews:
        if not crew_plan.stops:
            continue
        best = min(
            _measure(crew_plan.crew, list(order))[1] for order in permutations(crew_plan.stops)
        )
        assert crew_plan.km == pytest.approx(best, abs=1e-6)


def test_legs_are_measured_from_base_and_back_and_flag_travel_days() -> None:
    far = stop("one", 1, 0.0, 3.0, road_factor=1.4)
    current = plan(1, [far], [base_crew()])
    leg = haversine_km(0.0, 0.0, 0.0, 3.0) * 1.4
    assert current.crews[0].legs_km == pytest.approx((leg, leg))
    assert current.crews[0].km == pytest.approx(2 * leg)
    assert current.crews[0].travel_day_legs == (True, True)
    assert current.road_km == pytest.approx(2 * leg)


def test_edit_order_needs_a_reason_keeps_membership_and_the_batch_version() -> None:
    stops = [stop("a", 1, 0.0, 1.0), stop("b", 2, 1.0, 1.0)]
    current = plan(5, stops, [base_crew()])
    order = [s.job_id for s in current.crews[0].stops]
    with pytest.raises(ValueError, match="reason"):
        edit_order(current, "Base", list(reversed(order)), "  ")
    with pytest.raises(ValueError, match="membership"):
        edit_order(current, "Base", ["a", "new"], "Need a change.")
    edited = edit_order(current, "Base", list(reversed(order)), "Tenant asked for the afternoon.")
    assert [s.job_id for s in edited.crews[0].stops] == list(reversed(order))
    assert edited.changes[-1].reason == "Tenant asked for the afternoon."
    assert edited.changes[-1].job_ids == tuple(reversed(order))
    assert edited.batch_version == 5


def test_air_and_closed_road_stops_are_never_routed() -> None:
    air = stop("air", 1, -20.0, 133.0, access="air")
    closed = stop("closed", 2, -20.0, 133.0, road_open=False)
    current = plan(4, [air, closed], roster())
    assert [item.stop.job_id for item in current.manual] == ["air"]
    assert [(i.stop.job_id, i.reason) for i in current.unplanned] == [("closed", ROAD_CLOSED)]
    assert all(not crew.stops for crew in current.crews)


def test_planner_reads_capacity_and_travel_day_constants() -> None:
    source = Path("fair_turn/core/visit_plan.py").read_text(encoding="utf-8")
    assert "JOBS_PER_CREW_DAY" in source and "TRAVEL_DAY_KM" in source
    assert "200" not in source
    for coordinates in constants.CREW_BASE_COORDS.values():
        assert str(coordinates[0]) not in source
        assert str(coordinates[1]) not in source
