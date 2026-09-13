"""Visit-plan invariants from PRD section 3.3."""

from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from fair_turn.core import constants
from fair_turn.core.visit_plan import (
    Crew,
    Stop,
    apply,
    edit_order,
    haversine_km,
    plan,
    suggestions,
)
from fair_turn.data.geography import BASE_FOR_REGION


def factor(_: Stop) -> float:
    return 1.0


def crews_for_regions() -> list[Crew]:
    return [
        Crew(base, region, *constants.CREW_BASE_COORDS[base], jobs_per_day=2)
        for region in constants.REGIONS
        for base in (BASE_FOR_REGION[region].title(),)
    ]


@st.composite
def stop_lists(draw) -> list[Stop]:
    entries = draw(
        st.lists(
            st.tuples(
                st.sampled_from(constants.REGIONS),
                st.floats(-26, -11, allow_nan=False, allow_infinity=False),
                st.floats(129, 138, allow_nan=False, allow_infinity=False),
                st.sampled_from(("road", "air", "barge")),
                st.booleans(),
                st.integers(0, 5),
            ),
            min_size=1,
            max_size=12,
        )
    )
    return [
        Stop(f"j{index}", f"community-{index}", region, lat, lon, access, road_open, index, window)
        for index, (region, lat, lon, access, road_open, window) in enumerate(entries, start=1)
    ]


@settings(max_examples=100, deadline=None)
@given(stop_lists())
def test_plan_preserves_membership_and_signed_order(stops: list[Stop]) -> None:
    current = plan(7, stops, crews_for_regions(), factor)
    planned = [stop.job_id for crew in current.crews for stop in crew.stops]
    unplanned = [item.stop.job_id for item in current.unplanned]
    manual = [item.stop.job_id for item in current.manual]
    assert set(planned) | set(unplanned) | set(manual) == {stop.job_id for stop in stops}
    assert len(planned) + len(unplanned) + len(manual) == len(stops)
    assert all(
        [stop.signed_rank for stop in crew.stops] == sorted(stop.signed_rank for stop in crew.stops)
        for crew in current.crews
    )
    assert not set(planned) & set(manual)
    for crew in current.crews:
        expected_leg_count = len(crew.stops) + 1 if crew.stops else 0
        assert len(crew.legs_km) == expected_leg_count
    over_capacity_regions = {
        item.stop.region for item in current.unplanned if item.reason == "over crew capacity"
    }
    assert all(
        not crew.within_capacity
        for crew in current.crews
        if crew.crew.region in over_capacity_regions
    )


def test_road_closed_and_missing_crew_are_unplanned() -> None:
    closed = Stop("closed", "c", constants.REGIONS[0], -20, 133, "road", False, 1, 1)
    unknown = Stop("unknown", "u", "OUTSIDE", -20, 133, "road", True, 2, 1)
    current = plan(4, [closed, unknown], [], factor)
    assert [(item.stop.job_id, item.reason) for item in current.unplanned] == [
        ("closed", "road closed"),
        ("unknown", "no crew for region"),
    ]


def test_manual_work_is_not_routed() -> None:
    stop = Stop("air", "c", constants.REGIONS[0], -20, 133, "air", True, 1, 1)
    current = plan(4, [stop], crews_for_regions(), factor)
    assert current.manual[0].next_action == "book air/barge freight"
    assert all(not crew.stops for crew in current.crews)


def test_suggestion_requires_reason_and_only_swaps_named_stops() -> None:
    crew = Crew("Darwin", constants.REGIONS[0], -12.5, 130.8, 3)
    stops = [
        Stop("a", "a", crew.region, -20, 133, "road", True, 1, 2),
        Stop("b", "b", crew.region, -12.6, 130.9, "road", True, 2, 2),
        Stop("c", "c", crew.region, -21, 133, "road", True, 3, 2),
    ]
    current = plan(5, stops, [crew], factor)
    suggestion = suggestions(current, factor)[0]
    assert suggestion.saving_km >= constants.SUGGESTION_MIN_SAVING_KM
    with pytest.raises(ValueError, match="reason"):
        apply(current, suggestion, "  ", factor)
    applied = apply(current, suggestion, "Avoid a repeat drive.", factor)
    before = current.crews[0].stops
    after = applied.crews[0].stops
    changed = [
        index for index, pair in enumerate(zip(before, after, strict=True)) if pair[0] != pair[1]
    ]
    assert changed == [
        index
        for index, job in enumerate(suggestion.old_order)
        if job != suggestion.new_order[index]
    ]
    assert {before[index].job_id for index in changed} == {suggestion.job_a, suggestion.job_b}
    assert applied.changes[-1].reason == "Avoid a repeat drive."
    assert applied.batch_version == 5


def test_edit_order_rejects_membership_change() -> None:
    crew = crews_for_regions()[0]
    stops = [
        Stop("a", "a", crew.region, -13, 131, "road", True, 1, 1),
        Stop("b", "b", crew.region, -14, 132, "road", True, 2, 1),
    ]
    current = plan(2, stops, [crew], factor)
    with pytest.raises(ValueError, match="membership"):
        edit_order(current, crew.base, ["a", "new"], "Need a change.", factor)


def test_haversine_and_kilometres_are_measured_from_base_and_back() -> None:
    crew = Crew("Darwin", constants.REGIONS[0], 0.0, 0.0, 1)
    stop = Stop("one", "one", crew.region, 0.0, 1.0, "road", True, 1, 1)
    current = plan(1, [stop], [crew], factor)
    expected_leg = haversine_km(0.0, 0.0, 0.0, 1.0)
    assert current.crews[0].legs_km == pytest.approx((expected_leg, expected_leg))
    assert current.crews[0].km == pytest.approx(expected_leg * 2)


def test_planner_reads_capacity_and_coordinate_constants() -> None:
    source = Path("fair_turn/core/visit_plan.py").read_text(encoding="utf-8")
    assert "SUGGESTION_MIN_SAVING_KM" in source
    assert "50" not in source
    for coordinates in constants.CREW_BASE_COORDS.values():
        assert str(coordinates[0]) not in source
        assert str(coordinates[1]) not in source
