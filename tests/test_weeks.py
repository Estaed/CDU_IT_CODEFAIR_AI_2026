"""Many weeks in a row: when jobs complete, what the season measure counts, road closures by
day, and the distance bands."""

from datetime import date, timedelta

import pytest

from fair_turn.core import weekly, weeks
from fair_turn.core.types import FaultType, Job, SafetyClass

MONDAY = date(2025, 6, 2)
OLD = MONDAY - timedelta(weeks=20)
BASE = "Katherine"
ONE_CREW = {BASE: 1}


def _place(cid: str, km: float, is_town: bool = False) -> weekly.Place:
    return weekly.Place(cid, BASE, is_town, km, -14.0, 132.0)


PLACES = {
    "K-TOWN": _place("K-TOWN", 0.0, is_town=True),
    "R-NEAR": _place("R-NEAR", 100.0),  # 0.5 driving days
    "R-MID": _place("R-MID", 200.0),  # 1.0
    "R-FAR": _place("R-FAR", 450.0),  # 2.5
}


def job(
    jid: str,
    cid: str,
    reported: date = MONDAY,
    cls: SafetyClass | None = SafetyClass.ROUTINE,
    fault: FaultType | None = FaultType.PLUMBING_WATER,
) -> Job:
    return Job(jid, cid, not PLACES[cid].is_town, reported, fault, cls)


def simulate(jobs, n_weeks=1, setting=0.5, closures=()) -> weeks.Season:
    return weeks.simulate(jobs, PLACES, setting, MONDAY, n_weeks, closures, ONE_CREW)


def test_simulate_refuses_a_day_that_is_not_monday() -> None:
    with pytest.raises(ValueError):
        weeks.simulate([], PLACES, 0.5, MONDAY + timedelta(1), 1, (), ONE_CREW)


def test_immediate_jobs_complete_on_their_report_day() -> None:
    before = job("E0", "R-FAR", MONDAY - timedelta(3), cls=SafetyClass.IMMEDIATE)
    midweek = job("E1", "K-TOWN", MONDAY + timedelta(2), cls=SafetyClass.IMMEDIATE)
    season = simulate([before, midweek])
    assert season.completed_on == {"E0": MONDAY - timedelta(3), "E1": MONDAY + timedelta(2)}


def test_needs_human_jobs_stay_open() -> None:
    season = simulate([job("H0", "K-TOWN", OLD, fault=None)], n_weeks=2)
    assert season.completed_on == {"H0": None}


def test_remote_trip_jobs_complete_when_the_work_ends() -> None:
    # R-MID: half of 1 driving day out, then 1 work day: work ends at 1.5, on Tuesday.
    jobs = [job(f"M{i}", "R-MID", OLD) for i in range(3)]
    season = simulate(jobs)
    assert set(season.completed_on.values()) == {MONDAY + timedelta(1)}


def test_remote_job_is_done_before_the_drive_home() -> None:
    # R-FAR: 1.25 days out, 0.5 work: done Tuesday. The crew is home only on Wednesday.
    season = simulate([job("F0", "R-FAR", OLD)])
    assert season.completed_on["F0"] == MONDAY + timedelta(1)


def test_work_ending_exactly_at_a_day_boundary_counts_that_day() -> None:
    # R-MID with 1 repair: 0.5 out + 0.5 work ends at 1.0, the end of Monday.
    season = simulate([job("M0", "R-MID", OLD)])
    assert season.completed_on["M0"] == MONDAY


def test_a_full_week_trip_and_its_leftovers_next_week() -> None:
    # 2.5 driving days leave room for 7 repairs (2.5 work days); the other 2 go next week.
    jobs = [job(f"F{i}", "R-FAR", OLD) for i in range(9)]
    season = simulate(jobs, n_weeks=2)
    done = sorted(season.completed_on.values())
    assert done[:7] == [MONDAY + timedelta(3)] * 7  # 1.25 out + 2.5 work = 3.75: Thursday
    assert done[7:] == [MONDAY + timedelta(weeks=1, days=2)] * 2  # 1.25 + 1 = 2.25: Wednesday
    for day in done:
        assert day.weekday() < 5


def test_town_job_reported_midweek_is_done_that_day() -> None:
    wednesday = MONDAY + timedelta(2)
    saturday = MONDAY + timedelta(5)
    season = simulate([job("W0", "K-TOWN", wednesday), job("S0", "K-TOWN", saturday)], 2)
    assert season.completed_on["W0"] == wednesday
    assert season.completed_on["S0"] == MONDAY + timedelta(weeks=1)


def _closure(cid: str, start: str, end: str) -> dict[str, str]:
    return {"community_id": cid, "closed_from": start, "closed_to": end}


def test_closed_road_keeps_a_remote_job_open() -> None:
    closures = [_closure("R-NEAR", "2025-06-01", "2025-06-08")]
    season = simulate([job("N0", "R-NEAR", OLD)], n_weeks=2, closures=closures)
    assert season.completed_on["N0"] == MONDAY + timedelta(weeks=1)  # first open Monday


def test_a_two_day_closure_does_not_block_the_week() -> None:
    closures = [_closure("R-NEAR", "2025-06-02", "2025-06-03")]  # Monday and Tuesday
    season = simulate([job("N0", "R-NEAR", OLD)], closures=closures)
    assert season.completed_on["N0"] is not None
    assert MONDAY <= season.completed_on["N0"] <= MONDAY + timedelta(4)


def test_closed_for_week_needs_three_closed_weekdays() -> None:
    closures = [
        _closure("THREE", "2025-06-02", "2025-06-04"),  # Mon-Wed
        _closure("TWO", "2025-06-02", "2025-06-03"),  # Mon-Tue
        _closure("WEEKEND", "2025-06-05", "2025-06-08"),  # Thu-Sun: two weekdays
        _closure("SPLIT", "2025-06-02", "2025-06-03"),  # Mon-Tue ...
        _closure("SPLIT", "2025-06-05", "2025-06-06"),  # ... and Thu-Fri: four
        _closure("OVERLAP", "2025-06-02", "2025-06-03"),  # the same two days twice
        _closure("OVERLAP", "2025-06-02", "2025-06-03"),
        _closure("WHOLE", "2025-05-20", "2025-06-30"),
        _closure("LAST WEEK", "2025-05-26", "2025-06-01"),
    ]
    assert weeks.closed_for_week(closures, MONDAY) == {"THREE", "SPLIT", "WHOLE"}
    assert weeks.closed_for_week([], MONDAY) == set()


def test_reopens_gives_the_first_open_day() -> None:
    closures = [
        _closure("A", "2025-06-01", "2025-06-04"),
        _closure("A", "2025-06-05", "2025-06-07"),  # back to back: one closure
        _closure("B", "2025-06-10", "2025-06-12"),
    ]
    assert weeks.reopens(closures, "A", MONDAY) == date(2025, 6, 8)
    assert weeks.reopens(closures, "A", date(2025, 6, 7)) == date(2025, 6, 8)
    assert weeks.reopens(closures, "A", date(2025, 6, 8)) is None  # open that day
    assert weeks.reopens(closures, "B", MONDAY) is None  # closes later, open now
    assert weeks.reopens(closures, "C", MONDAY) is None


def test_open_on() -> None:
    jobs = [job("W0", "K-TOWN", MONDAY + timedelta(2)), job("H0", "K-TOWN", fault=None)]
    season = simulate(jobs)
    assert [j.job_id for j in season.open_on(jobs, MONDAY)] == ["H0"]
    assert [j.job_id for j in season.open_on(jobs, MONDAY + timedelta(1))] == ["H0"]
    assert [j.job_id for j in season.open_on(jobs, MONDAY + timedelta(2))] == ["H0"]


def test_measure_counts_crew_jobs_only() -> None:
    jobs = [
        job("T0", "K-TOWN"),  # done Tuesday, after the remote day; on time
        job("N0", "R-NEAR", OLD),  # done Monday, 140 days after report, late
        job("F0", "R-FAR"),  # road closed all season: still open
        job("E0", "K-TOWN", cls=SafetyClass.IMMEDIATE),  # the make-safe contractor's
        job("H0", "K-TOWN", fault=None),  # waits for a person
        job("L0", "K-TOWN", MONDAY + timedelta(8)),  # reported in the last week
    ]
    closures = [{"community_id": "R-FAR", "closed_from": "2025-06-01", "closed_to": "2025-06-30"}]
    season = simulate(jobs, n_weeks=2, closures=closures)
    assert season.completed_on["T0"] == MONDAY + timedelta(1)
    assert season.completed_on["N0"] == MONDAY
    result = weeks.measure(season, jobs, PLACES, 0.5)
    assert result.bands == (
        weeks.BandResult("town", 1, 1.0, 1.0, 0),
        weeks.BandResult("under 150 km", 1, 140.0, 0.0, 0),
        weeks.BandResult("over 300 km", 1, 14.0, 0.0, 1),
    )
    assert result.repairs == 2
    assert result.driving_days == 0.5
    assert (result.on_time_town, result.on_time_remote) == (1.0, 0.0)


def test_closed_on_reads_closure_rows_inclusive() -> None:
    rows = [
        {"community_id": "A", "closed_from": "2025-06-02", "closed_to": "2025-06-04"},
        {"community_id": "B", "closed_from": "2025-06-04", "closed_to": "2025-06-10"},
    ]
    assert weeks.closed_on(rows, date(2025, 6, 1)) == set()
    assert weeks.closed_on(rows, date(2025, 6, 2)) == {"A"}
    assert weeks.closed_on(rows, date(2025, 6, 4)) == {"A", "B"}
    assert weeks.closed_on(rows, date(2025, 6, 10)) == {"B"}
    assert weeks.closed_on(rows, date(2025, 6, 11)) == set()
    assert weeks.closed_on([], date(2025, 6, 4)) == set()


@pytest.mark.parametrize(
    ("km", "is_town", "name"),
    [
        (0.0, True, "town"),
        (500.0, True, "town"),
        (0.0, False, "under 150 km"),
        (149.9, False, "under 150 km"),
        (150.0, False, "150-300 km"),
        (299.9, False, "150-300 km"),
        (300.0, False, "over 300 km"),
        (2000.0, False, "over 300 km"),
    ],
)
def test_band_boundaries(km, is_town, name) -> None:
    assert weeks.band(_place("X", km, is_town)) == name
