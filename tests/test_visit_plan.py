"""Pooled visit-plan invariants (PRD section 3.3, pooled crews 2026-09-14).

Distance chooses which crew goes, never which job is served: membership is the signed list,
overflow is dropped by signed rank only, and within a crew the order is the shortest route."""

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
    OVER_CAPACITY,
    ROAD_CLOSED,
    Stop,
    _measure,
    edit_order,
    plan,
)
from fair_turn.data.geography import BASE_FOR_REGION

CAP = constants.JOBS_PER_CREW_DAY


def roster() -> tuple[CrewBase, ...]:
    return crew_roster({region: base.title() for region, base in BASE_FOR_REGION.items()})


def stop(job_id: str, rank: int, lat: float, lon: float, **overrides) -> Stop:
    values = dict(
        job_id=job_id,
        community_id=f"community-{job_id}",
        region=constants.REGIONS[0],
        lat=lat,
        lon=lon,
        access="road",
        road_open=True,
        signed_rank=rank,
        road_factor=1.0,
    )
    values.update(overrides)
    return Stop(**values)


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
            ),
            min_size=1,
            max_size=18,
        )
    )
    return [
        Stop(
            f"j{index:02d}",
            f"community-{shared if shared else index}",
            constants.REGIONS[0],
            lat,
            lon,
            access,
            road_open,
            index,
            factor,
        )
        for index, (lat, lon, access, road_open, shared, factor) in enumerate(entries, start=1)
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
    for crew in current.crews:
        assert len(crew.stops) <= CAP
        assert len(crew.legs_km) == (len(crew.stops) + 1 if crew.stops else 0)
        assert crew.travel_day_legs == tuple(leg > constants.TRAVEL_DAY_KM for leg in crew.legs_km)
    assert current.batch_version == 7


@settings(max_examples=100, deadline=None)
@given(stop_lists())
def test_with_enough_slots_no_road_stop_is_over_capacity(stops: list[Stop]) -> None:
    crews = roster()
    drivable = [s for s in stops if s.access == "road" and s.road_open]
    if len(drivable) > len(crews) * CAP:
        crews = crews * (len(drivable) // (len(crews) * CAP) + 1)
    current = plan(1, stops, crews)
    assert current.within_capacity
    assert not [i for i in current.unplanned if i.reason == OVER_CAPACITY]


@settings(max_examples=100, deadline=None)
@given(stop_lists())
def test_overflow_is_the_lowest_signed_ranks(stops: list[Stop]) -> None:
    crews = roster()[:2]
    current = plan(1, stops, crews)
    drivable = sorted(
        (s for s in stops if s.access == "road" and s.road_open), key=lambda s: s.signed_rank
    )
    expected = [s.job_id for s in drivable[len(crews) * CAP :]]
    assert [i.stop.job_id for i in current.unplanned if i.reason == OVER_CAPACITY] == expected
    assert current.within_capacity == (not expected)


def test_a_far_high_rank_stop_is_planned_and_a_near_low_rank_stop_is_left_over() -> None:
    crew = CrewBase("Base", "Base", 0.0, 0.0)
    far = stop("far", 1, 0.0, 5.0)
    fillers = [stop(f"f{i}", i + 2, 0.0, 0.5) for i in range(CAP - 1)]
    near = stop("near", 99, 0.0, 0.01)
    current = plan(3, [near, far, *fillers], [crew])
    planned, unplanned, _ = _ids(current)
    assert "far" in planned
    assert unplanned == ["near"]
    assert current.unplanned[0].reason == OVER_CAPACITY
    assert not current.within_capacity


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


def test_same_community_stops_share_a_crew() -> None:
    crews = (CrewBase("A 1", "A", 0.0, 0.0), CrewBase("A 2", "A", 0.0, 0.0))
    here = dict(community_id="shared")
    stops = [
        stop("a", 1, 0.0, 1.0, **here),
        stop("b", 2, 0.0, 1.2),
        stop("c", 3, 0.0, 1.0, **here),
    ]
    current = plan(1, stops, crews)
    holders = [
        {s.job_id for s in crew.stops}
        for crew in current.crews
        if {"a", "c"} & {s.job_id for s in crew.stops}
    ]
    assert holders == [{"a", "c"}]


def test_legs_are_measured_from_base_and_back_and_flag_travel_days() -> None:
    crew = CrewBase("Base", "Base", 0.0, 0.0)
    far = stop("one", 1, 0.0, 3.0, road_factor=1.4)
    current = plan(1, [far], [crew])
    leg = haversine_km(0.0, 0.0, 0.0, 3.0) * 1.4
    assert current.crews[0].legs_km == pytest.approx((leg, leg))
    assert current.crews[0].km == pytest.approx(2 * leg)
    assert current.crews[0].travel_day_legs == (True, True)
    assert current.road_km == pytest.approx(2 * leg)


def test_edit_order_needs_a_reason_keeps_membership_and_the_batch_version() -> None:
    crew = CrewBase("Base", "Base", 0.0, 0.0)
    stops = [stop("a", 1, 0.0, 1.0), stop("b", 2, 1.0, 1.0)]
    current = plan(5, stops, [crew])
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
