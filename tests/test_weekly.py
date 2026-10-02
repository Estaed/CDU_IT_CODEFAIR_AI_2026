"""The weekly crew plan: trip costs in half days, what each setting does, the crew-week limits,
the coordinator's add / drop / closed, and that every plannable job lands in exactly one place.

The fixture is one base town and three remote communities at known road km, so every number
below can be worked out by hand (travel = ceil(km / 100) / 2 days there and back).
"""

from collections import Counter
from datetime import date, timedelta

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from fair_turn.core import constants, weekly
from fair_turn.core.types import FaultType, HealthRiskFactor, Job, SafetyClass

TODAY = date(2025, 6, 2)  # a Monday outside the heat season
OLD = TODAY - timedelta(weeks=20)  # past every window, urgency at its cap
BASE = "Katherine"
ONE_CREW = {BASE: 1}
TWO_CREWS = {BASE: 2}


def _place(cid: str, base: str, km: float, is_town: bool = False) -> weekly.Place:
    return weekly.Place(cid, base, is_town, km, -14.0, 132.0)


PLACES = {
    "K-TOWN": _place("K-TOWN", BASE, 0.0, is_town=True),
    "R-NEAR": _place("R-NEAR", BASE, 100.0),  # 0.5 driving days
    "R-MID": _place("R-MID", BASE, 200.0),  # 1.0
    "R-FAR": _place("R-FAR", BASE, 450.0),  # 2.5
    "T-TOWN": _place("T-TOWN", "Tennant Creek", 0.0, is_town=True),
    "T-R1": _place("T-R1", "Tennant Creek", 300.0),  # 1.5
}


def job(
    jid: str,
    cid: str,
    reported: date = TODAY,
    cls: SafetyClass | None = SafetyClass.ROUTINE,
    fault: FaultType | None = FaultType.PLUMBING_WATER,
    health: frozenset[HealthRiskFactor] = frozenset(),
) -> Job:
    return Job(jid, cid, not PLACES[cid].is_town, reported, fault, cls, health)


def town_jobs(n: int, prefix: str = "T", reported: date = TODAY) -> list[Job]:
    return [job(f"{prefix}{i:02d}", "K-TOWN", reported) for i in range(n)]


def plan(jobs, setting, crews=ONE_CREW, **kw) -> weekly.WeekPlan:
    return weekly.plan(jobs, PLACES, TODAY, setting, crews, **kw)


# --- trip costs ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("km", "days"), [(0, 0.0), (1, 0.5), (100, 0.5), (101, 1.0), (200, 1.0), (250, 1.5)]
)
def test_travel_days_round_up_to_half_days(km, days) -> None:
    assert weekly.travel_days(_place("X", BASE, km)) == days


def test_travel_days_nothing_for_the_base_town() -> None:
    assert weekly.travel_days(_place("X", BASE, 300.0, is_town=True)) == 0.0
    assert weekly.travel_days(PLACES["R-FAR"]) == 2.5


@pytest.mark.parametrize(
    ("repairs", "days"), [(1, 0.5), (2, 1.0), (3, 1.0), (4, 1.5), (5, 2.0), (6, 2.0), (9, 3.0)]
)
def test_work_days_round_up_to_half_days(repairs, days) -> None:
    assert weekly.work_days(repairs) == days


# --- what the setting does ----------------------------------------------------------------


def test_at_most_repairs_enough_town_work_keeps_the_crew_in_town() -> None:
    remote = [job(f"N{i}", "R-NEAR", OLD) for i in range(9)]  # the best remote trip there is
    week = plan(town_jobs(15) + remote, 0.0)
    assert [t.community_id for t in week.trips] == ["K-TOWN"] * 5
    assert all(t.priority == 3.0 for t in week.trips)
    waiting = week.waiting_at("R-NEAR")
    assert waiting.reason == weekly.OUTRANKED
    assert waiting.priority == pytest.approx(9 / 3.5)
    assert waiting.priority <= week.last_priority(BASE)
    assert (waiting.trip_repairs, waiting.trip_days) == (9, 3.5)


remote_spec = st.tuples(
    st.sampled_from(["R-NEAR", "R-MID", "R-FAR"]),
    st.integers(0, 300),  # days before today
    st.sampled_from([SafetyClass.URGENT, SafetyClass.ROUTINE]),
)


@given(st.lists(remote_spec, max_size=30), st.integers(1, 3))
@settings(max_examples=100, deadline=None)
def test_at_most_repairs_town_three_a_day_beats_any_remote_trip(specs, crews) -> None:
    remote = [
        job(f"R{i}", cid, TODAY - timedelta(back), cls) for i, (cid, back, cls) in enumerate(specs)
    ]
    town = town_jobs(15 * crews)
    week = plan(town + remote, 0.0, crews={BASE: crews})
    assert all(t.is_town for t in week.trips)
    assert week.planned_job_ids() == {j.job_id for j in town}


def test_at_most_overdue_first_an_overdue_remote_job_outranks_fresh_town_jobs() -> None:
    far = job("F0", "R-FAR", OLD)  # need 3 + 1 = 4, trip 2.5 + 0.5 days
    jobs = [*town_jobs(15), far]
    week = plan(jobs, 1.0)
    assert week.trips[0].community_id == "R-FAR"
    assert week.trips[0].priority == pytest.approx(4 / 0.5)  # driving not held against it
    assert [t.community_id for t in week.trips[1:]] == ["K-TOWN", "K-TOWN"]
    assert plan(jobs, 0.0).waiting_at("R-FAR").reason == weekly.OUTRANKED


# --- coordinator controls -----------------------------------------------------------------


def test_closed_community_gets_no_trip_and_reason_closed() -> None:
    jobs = [job(f"N{i}", "R-NEAR", OLD) for i in range(3)]
    week = plan(jobs, 1.0, closed={"R-NEAR"})
    assert week.trip_to("R-NEAR") is None
    waiting = week.waiting_at("R-NEAR")
    assert (waiting.reason, waiting.priority) == (weekly.CLOSED, None)
    assert set(waiting.job_ids) == {"N0", "N1", "N2"}


def test_dropped_community_gets_no_trip_and_reason_dropped() -> None:
    jobs = [job(f"N{i}", "R-NEAR", OLD) for i in range(3)]
    week = plan(jobs, 1.0, drop={"R-NEAR"})
    assert week.trips == ()
    waiting = week.waiting_at("R-NEAR")
    assert (waiting.reason, waiting.priority) == (weekly.DROPPED, None)


def test_add_puts_an_outranked_trip_in_first() -> None:
    jobs = [*town_jobs(15), job("F0", "R-FAR")]
    assert plan(jobs, 0.0).trip_to("R-FAR") is None
    week = plan(jobs, 0.0, add={"R-FAR"})
    first = week.trips[0]
    assert (first.community_id, first.added, first.days) == ("R-FAR", True, 3.0)
    assert all(not t.added for t in week.trips[1:])
    assert week.planned_job_ids() == {"F0", "T00", "T01", "T02", "T03", "T04", "T05"}
    assert week.last_priority(BASE) == 3.0  # the added trip is not the cut line
    assert week.crews[0].stops[0].start == 0.0


def test_add_skips_a_closed_community() -> None:
    week = plan([job("F0", "R-FAR")], 0.0, add={"R-FAR"}, closed={"R-FAR"})
    assert week.trips == ()
    assert week.waiting_at("R-FAR").reason == weekly.CLOSED


def test_one_trip_per_remote_community_and_leftovers_are_trip_full() -> None:
    fresh = [job(f"N{i}", "R-NEAR") for i in range(3)]
    old = [job(f"O{i}", "R-NEAR", OLD) for i in range(9)]
    week = plan(fresh + old, 1.0, crews=TWO_CREWS)
    remote = [t for t in week.trips if t.community_id == "R-NEAR"]
    assert len(remote) == 1
    assert len(remote[0].job_ids) == constants.MAX_JOBS_PER_TRIP
    assert set(remote[0].job_ids) == {j.job_id for j in old}  # most needed go first
    waiting = week.waiting_at("R-NEAR")
    assert (waiting.reason, waiting.priority) == (weekly.TRIP_FULL, None)
    assert set(waiting.job_ids) == {"N0", "N1", "N2"}
    # the size of the trip that goes, not of a trip for the leftovers
    assert (waiting.trip_repairs, waiting.trip_days) == (len(remote[0].job_ids), remote[0].days)
    assert (waiting.trip_repairs, waiting.trip_days) == (9, 3.5)
    assert week.spare_days[BASE] == 10.0 - 3.5  # the second crew stays on call


def test_no_room_when_a_trip_above_the_cut_needs_more_days_in_a_row() -> None:
    # One crew, most overdue first: R-MID (9 repairs, 4 days, priority 12) goes first, the
    # town day (priority 3) fills the last day; R-FAR (priority 8) beats that cut but needs
    # 3 days in a row, and only 1 was left when it came up.
    mid = [job(f"M{i}", "R-MID", OLD) for i in range(9)]
    week = plan([*mid, job("F0", "R-FAR", OLD), *town_jobs(3)], 1.0)
    assert [t.community_id for t in week.trips] == ["R-MID", "K-TOWN"]
    assert week.last_priority(BASE) == 3.0
    waiting = week.waiting_at("R-FAR")
    assert waiting.reason == weekly.NO_ROOM
    assert waiting.priority == pytest.approx(8.0)
    assert waiting.priority > week.last_priority(BASE)
    assert (waiting.trip_repairs, waiting.trip_days) == (1, 3.0)


def test_below_the_cut_is_outranked_not_no_room() -> None:
    mid = [job(f"M{i}", "R-MID", OLD) for i in range(9)]
    week = plan([*mid, job("F0", "R-FAR", OLD)], 1.0)  # no town day: the cut is R-MID's 12
    waiting = week.waiting_at("R-FAR")
    assert waiting.reason == weekly.OUTRANKED
    assert waiting.priority <= week.last_priority(BASE)


def test_an_added_trip_that_cannot_fit_is_listed_and_gets_no_trip() -> None:
    # R-FAR goes first (sorted) and takes the whole week; R-MID has no room left.
    far = [job(f"F{i}", "R-FAR", OLD) for i in range(9)]
    week = plan([*far, job("M0", "R-MID", OLD)], 0.0, add={"R-FAR", "R-MID"})
    assert week.not_fitted == ("R-MID",)
    assert week.trip_to("R-MID") is None
    assert week.waiting_at("R-MID").job_ids == ("M0",)
    carried = week.trip_to("R-FAR")
    assert carried.added and len(carried.job_ids) == 7  # 2.5 driving + 2.5 work days
    full = week.waiting_at("R-FAR")
    assert (full.reason, full.trip_repairs, full.trip_days) == (weekly.TRIP_FULL, 7, 5.0)


def test_added_trips_that_fit_are_not_listed_as_not_fitted() -> None:
    week = plan([job("F0", "R-FAR")], 0.0, add={"R-FAR"})
    assert week.not_fitted == ()


def test_town_leftovers_wait_outranked_with_a_priority() -> None:
    week = plan(town_jobs(18), 0.0)
    waiting = week.waiting_at("K-TOWN")
    assert waiting.reason == weekly.OUTRANKED
    assert waiting.job_ids == ("T15", "T16", "T17")
    assert waiting.priority == 3.0
    assert (waiting.trip_repairs, waiting.trip_days) == (3, 1.0)


def test_spare_days_become_an_on_call_stop_in_town() -> None:
    week = plan([job("M0", "R-MID")], 0.0)
    (crew,) = week.crews
    assert [s.trip.community_id for s in crew.stops] == ["R-MID", BASE]
    on_call = crew.stops[1]
    assert (on_call.start, on_call.trip.job_ids, on_call.trip.days) == (1.5, (), 3.5)
    assert week.spare_days == {BASE: 3.5, **{b: 0 for b in constants.CREW_BASES if b != BASE}}


# --- who the plan can take ----------------------------------------------------------------


def test_immediate_and_needs_human_jobs_never_go_in_the_plan() -> None:
    emergency = job("E0", "K-TOWN", OLD, cls=SafetyClass.IMMEDIATE)
    unread = job("H0", "K-TOWN", OLD, fault=None)
    unclassed = job("H1", "R-NEAR", OLD, cls=None)
    week = plan([emergency, unread, unclassed, *town_jobs(2)], 1.0)
    listed = week.planned_job_ids() | {i for w in week.waiting for i in w.job_ids}
    assert listed == {"T00", "T01"}


def test_jobs_reported_after_today_are_left_out() -> None:
    later = job("L0", "K-TOWN", TODAY + timedelta(1))
    week = plan([later, *town_jobs(1)], 0.0)
    assert week.planned_job_ids() == {"T00"}
    assert week.waiting == ()


def test_unknown_community_raises() -> None:
    stray = Job("X0", "NOWHERE", True, TODAY, FaultType.OTHER, SafetyClass.ROUTINE)
    with pytest.raises(ValueError):
        weekly.plan([stray], PLACES, TODAY, 0.0, ONE_CREW)


@pytest.mark.parametrize("setting", [-0.01, 1.01, 2.0])
def test_setting_outside_zero_to_one_raises(setting) -> None:
    with pytest.raises(ValueError):
        plan(town_jobs(3), setting)


def test_same_input_same_plan() -> None:
    jobs = [
        *town_jobs(10),
        *(job(f"N{i}", "R-NEAR", OLD + timedelta(i)) for i in range(5)),
        job("M0", "R-MID", OLD),
        job("F0", "R-FAR", cls=SafetyClass.URGENT),
        job("T9", "T-R1", OLD),
    ]
    crews = {BASE: 2, "Tennant Creek": 1}
    first = plan(jobs, 0.5, crews=crews)
    assert plan(jobs, 0.5, crews=crews) == first
    assert plan(list(reversed(jobs)), 0.5, crews=crews) == first


# --- every plannable job in exactly one place (property) ----------------------------------

COMMUNITIES = sorted(PLACES)
job_spec = st.tuples(
    st.sampled_from(COMMUNITIES),
    st.integers(-3, 200),  # days before the plan day; negative = reported after it
    st.sampled_from([SafetyClass.IMMEDIATE, SafetyClass.URGENT, SafetyClass.ROUTINE, None]),
    st.sampled_from([FaultType.PLUMBING_WATER, FaultType.COOLING, None]),
    st.sets(st.sampled_from(list(HealthRiskFactor)), max_size=2),
)
communities = st.sets(st.sampled_from(COMMUNITIES), max_size=3)


@given(
    specs=st.lists(job_spec, max_size=40),
    setting=st.floats(0.0, 1.0),
    crews=st.fixed_dictionaries({BASE: st.integers(0, 3), "Tennant Creek": st.integers(0, 2)}),
    closed=communities,
    drop=communities,
    add=communities,
    heat=st.booleans(),
)
@settings(max_examples=300, deadline=None)
def test_plan_invariants(specs, setting, crews, closed, drop, add, heat) -> None:
    today = date(2025, 12, 29) if heat else TODAY
    jobs = [
        Job(f"J{i:03d}", cid, not PLACES[cid].is_town, today - timedelta(back), f, c, frozenset(h))
        for i, (cid, back, c, f, h) in enumerate(specs)
    ]
    week = weekly.plan(jobs, PLACES, today, setting, crews, closed=closed, add=add, drop=drop)

    # membership is a partition of the plannable jobs
    plannable = {j.job_id for j in jobs if weekly.in_plan(j, today)}
    in_trips = [i for t in week.trips for i in t.job_ids]
    in_waiting = [i for w in week.waiting for i in w.job_ids]
    assert len(in_trips) == len(set(in_trips))
    assert len(in_waiting) == len(set(in_waiting))
    assert not set(in_trips) & set(in_waiting)
    assert set(in_trips) | set(in_waiting) == plannable

    # crew weeks: within the week, no overlapping stops, own base only
    assert len(week.crews) == sum(crews.values())
    for crew in week.crews:
        assert crew.days_used <= constants.CREW_DAYS_PER_WEEK + 1e-9
        end = 0.0
        for stop in crew.stops:
            assert stop.trip.base == crew.base
            assert stop.start >= end - 1e-9
            end = stop.start + stop.trip.days
        assert end <= constants.CREW_DAYS_PER_WEEK + 1e-9

    # every trip sits on exactly one crew; on-call stops carry no jobs
    on_crews = [s.trip for c in week.crews for s in c.stops if s.trip.job_ids]
    assert Counter(on_crews) == Counter(week.trips)

    # trip sizes, one trip per remote community, closed and dropped respected
    remote = Counter(t.community_id for t in week.trips if not t.is_town)
    assert all(n == 1 for n in remote.values())
    for trip in week.trips:
        limit = constants.JOBS_PER_CREW_DAY if trip.is_town else constants.MAX_JOBS_PER_TRIP
        assert 0 < len(trip.job_ids) <= limit
        assert trip.community_id not in closed
        assert trip.community_id not in drop or trip.added
        assert trip.added == (trip.community_id in add) or trip.is_town
    for waiting in week.waiting:
        if waiting.community_id in closed:
            assert waiting.reason == weekly.CLOSED
        cut = week.last_priority(waiting.base)
        if waiting.reason == weekly.OUTRANKED:
            # below the cut means below the cut: never above the lowest trip the base made
            assert waiting.priority is not None and cut is not None
            assert waiting.priority <= cut + 1e-9
        if waiting.reason == weekly.NO_ROOM:
            assert waiting.priority is None or cut is None or waiting.priority > cut
        if waiting.reason == weekly.TRIP_FULL:
            carried = week.trip_to(waiting.community_id)
            assert waiting.trip_repairs == len(carried.job_ids)
            assert waiting.trip_days == carried.days
        else:
            assert waiting.trip_repairs <= constants.MAX_JOBS_PER_TRIP
            assert waiting.trip_days <= constants.CREW_DAYS_PER_WEEK

    # an added community that did not fit is listed and has no trip
    assert set(week.not_fitted) <= set(add) - set(closed)
    assert len(week.not_fitted) == len(set(week.not_fitted))
    for cid in week.not_fitted:
        assert week.trip_to(cid) is None


# --- summary and log lines ----------------------------------------------------------------


def test_summarise_matches_a_hand_count() -> None:
    jobs = [
        job("T0", "K-TOWN", TODAY - timedelta(weeks=3)),  # 15 of 10 business days: overdue
        job("T1", "K-TOWN", TODAY - timedelta(weeks=3)),
        job("T2", "K-TOWN"),
        job("T3", "K-TOWN"),
        job("N0", "R-NEAR", OLD),  # overdue, dropped
        job("N1", "R-NEAR", OLD),
        job("M0", "R-MID"),  # fresh, planned after the town days
        job("E0", "K-TOWN", OLD, cls=SafetyClass.IMMEDIATE),  # not plannable
        job("H0", "R-MID", OLD, fault=None),  # not plannable
    ]
    week = plan(jobs, 0.0, drop={"R-NEAR"})
    assert week.planned_job_ids() == {"T0", "T1", "T2", "T3", "M0"}
    assert weekly.summarise(week, jobs) == weekly.Summary(
        repairs=5,
        repairs_remote=1,
        overdue=4,
        overdue_remote=2,
        overdue_left=2,
        overdue_left_remote=2,
        driving_days=1.0,
        crew_days=5.0,
        remote_trips=1,
    )


@pytest.mark.parametrize(
    ("value", "name"),
    [
        (0.0, "Efficiency first"),
        (0.5, "Balanced"),
        (1.0, "Most overdue first"),
        (0.35, "Custom (0.35)"),
        (0.7, "Custom (0.70)"),
    ],
)
def test_setting_name(value, name) -> None:
    assert weekly.setting_name(value) == name


def test_setting_name_for_every_preset() -> None:
    for name, value in constants.SETTINGS.items():
        assert weekly.setting_name(value) == name


def test_trip_lines_merge_a_bases_town_days() -> None:
    week = plan([*town_jobs(9), job("M0", "R-MID")], 0.0, crews=TWO_CREWS)
    assert sum(t.is_town for t in week.trips) == 3
    assert weekly.trip_lines(week) == (
        "Katherine town: 9 repairs, 3 crew-days",
        "Katherine > R-MID: 1 repairs, 1.5 crew-days",
    )
