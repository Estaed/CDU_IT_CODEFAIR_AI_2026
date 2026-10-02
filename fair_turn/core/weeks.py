"""Many weeks of plans in a row: what a setting does to who waits, over a season.

A measurement device, not a scheduler. Every Monday the planner (``weekly.plan``) makes the
week's trips from the jobs open that morning. A remote trip fixes the repairs it took on
Monday, done on the day its work ends (before the drive home); if the community's access is
closed early in the week, the trip starts the day it reopens, and work pushed past Friday
waits for next week's plan. Town days are flexible, as they are in
practice: each day a crew works in town it fixes the most needed open town repairs of that
day, including ones reported since Monday. Immediate jobs go to the emergency make-safe
contractor and are done on their report day. Deterministic.
"""

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, timedelta
from statistics import median

from fair_turn.core import constants, scoring, weekly
from fair_turn.core.types import Job, SafetyClass

# Every Monday of the synthetic window: the season the Evidence page replays, and the weeks
# before the planning day that leave its backlog.
FIRST_MONDAY = constants.WINDOW_START + timedelta(days=(7 - constants.WINDOW_START.weekday()) % 7)
_LAST_DAY = constants.WINDOW_START + timedelta(days=constants.WINDOW_DAYS - 1)
SEASON_WEEKS = (_LAST_DAY - FIRST_MONDAY).days // 7 + 1
HISTORY_WEEKS = (constants.PLAN_DAY - FIRST_MONDAY).days // 7

# Distance bands for the "who waits" table: road km one way from the crew base.
BANDS = (("town", 0.0), ("under 150 km", 150.0), ("150-300 km", 300.0), ("over 300 km", math.inf))


def band(place: weekly.Place) -> str:
    if place.is_town:
        return "town"
    for name, upper in BANDS[1:]:
        if place.road_km < upper:
            return name
    raise AssertionError("unreachable")


def closed_on(closures: Iterable[Mapping[str, str]], day: date) -> set[str]:
    """Communities whose access is closed on ``day`` (rows of ``closures.json``)."""
    return {
        c["community_id"]
        for c in closures
        if date.fromisoformat(c["closed_from"]) <= day <= date.fromisoformat(c["closed_to"])
    }


CLOSED_WEEKDAYS = 3  # access closed on at least this many weekdays: no trip that week


def closed_for_week(closures: Iterable[Mapping[str, str]], monday: date) -> set[str]:
    """Communities a crew cannot plan a trip to in the week from ``monday``: access closed on
    most of its weekdays. A two-day closure leaves room to go later in the week."""
    closures = list(closures)
    counts: dict[str, int] = {}
    for offset in range(constants.CREW_DAYS_PER_WEEK):
        for cid in closed_on(closures, monday + timedelta(days=offset)):
            counts[cid] = counts.get(cid, 0) + 1
    return {cid for cid, n in counts.items() if n >= CLOSED_WEEKDAYS}


def reopens(closures: Iterable[Mapping[str, str]], community_id: str, day: date) -> date | None:
    """The first day after ``day`` the community's access is open again, if it is closed."""
    spans = [
        (date.fromisoformat(c["closed_from"]), date.fromisoformat(c["closed_to"]))
        for c in closures
        if c["community_id"] == community_id
    ]
    current = day
    while any(start <= current <= end for start, end in spans):
        current += timedelta(days=1)
    return None if current == day else current


@dataclass
class Season:
    completed_on: dict[str, date | None]  # every job; None while still open at the end
    end: date  # the day after the last simulated day
    driving_days: float

    def open_on(self, jobs: Iterable[Job], day: date) -> list[Job]:
        return [
            j
            for j in jobs
            if j.reported_on <= day
            and ((done := self.completed_on.get(j.job_id)) is None or done > day)
        ]


def simulate(
    jobs: list[Job],
    places: Mapping[str, weekly.Place],
    setting: float,
    first_monday: date,
    weeks: int,
    closures: Iterable[Mapping[str, str]] = (),
    crews_at_base: Mapping[str, int] | None = None,
) -> Season:
    if first_monday.weekday() != 0:
        raise ValueError(f"{first_monday} is not a Monday")
    closures = list(closures)
    done: dict[str, date | None] = {j.job_id: None for j in jobs}
    driving = 0.0
    for job in jobs:
        if not job.needs_human and job.safety_class is SafetyClass.IMMEDIATE:
            done[job.job_id] = job.reported_on
    for week in range(weeks):
        monday = first_monday + timedelta(weeks=week)
        open_jobs = [j for j in jobs if j.reported_on <= monday and done[j.job_id] is None]
        plan = weekly.plan(
            open_jobs,
            places,
            monday,
            setting,
            crews_at_base,
            closed=closed_for_week(closures, monday),
        )
        driving += sum(t.travel_days for t in plan.trips)
        town_slots: dict[tuple[str, int], float] = {}  # (base, weekday) -> repairs
        for crew in plan.crews:
            for stop in crew.stops:
                trip = stop.trip
                if trip.is_town:
                    for day in range(constants.CREW_DAYS_PER_WEEK):
                        overlap = min(day + 1, stop.start + trip.days) - max(day, stop.start)
                        if overlap > 0:
                            key = (trip.base, day)
                            town_slots[key] = (
                                town_slots.get(key, 0.0) + overlap * constants.JOBS_PER_CREW_DAY
                            )
                else:
                    # Done when the work is, before the drive home; a closed road at the
                    # start of the week delays the trip to the day access reopens.
                    opens = reopens(closures, trip.community_id, monday)
                    delay = max(0, (opens - monday).days - stop.start) if opens else 0
                    finished = stop.start + delay + trip.travel_days / 2 + trip.work_days
                    last = math.ceil(finished - 1e-9) - 1
                    if last >= constants.CREW_DAYS_PER_WEEK:
                        continue
                    for job_id in trip.job_ids:
                        done[job_id] = monday + timedelta(days=last)
        for day in range(constants.CREW_DAYS_PER_WEEK):
            today = monday + timedelta(days=day)
            for base in constants.CREW_BASES:
                slots = math.floor(town_slots.get((base, day), 0.0) + 1e-9)
                if not slots:
                    continue
                waiting = [
                    j
                    for j in jobs
                    if done[j.job_id] is None
                    and j.reported_on <= today
                    and weekly.in_plan(j, today)
                    and places[j.community_id].is_town
                    and places[j.community_id].base == base
                ]
                waiting.sort(key=lambda j: (-weekly.weight(j, today, setting), j.job_id))
                for job in waiting[:slots]:
                    done[job.job_id] = today
    end = first_monday + timedelta(weeks=weeks)
    return Season(completed_on=done, end=end, driving_days=driving)


@dataclass(frozen=True)
class BandResult:
    band: str
    jobs: int
    median_wait: float  # days; a job still open counts its time open so far (a lower bound)
    on_time_share: float  # finished within the NT window
    still_open: int


@dataclass(frozen=True)
class SeasonResult:
    setting: float
    repairs: int
    driving_days: float
    bands: tuple[BandResult, ...]
    on_time_remote: float
    on_time_town: float


def measure(
    season: Season, jobs: Iterable[Job], places: Mapping[str, weekly.Place], setting: float
) -> SeasonResult:
    """Crew jobs only (an emergency is the make-safe contractor's), reported at least a week
    before the end so each had a fair chance at a plan."""
    counted = [
        j
        for j in jobs
        if not j.needs_human
        and j.safety_class is not SafetyClass.IMMEDIATE
        and j.reported_on < season.end - timedelta(weeks=1)
    ]

    def wait(j: Job) -> int:
        done = season.completed_on[j.job_id]
        return ((done or season.end) - j.reported_on).days

    def on_time(j: Job) -> bool:
        done = season.completed_on[j.job_id]
        return done is not None and not scoring.is_overdue(j, done)

    bands = []
    for name, _ in BANDS:
        group = [j for j in counted if band(places[j.community_id]) == name]
        if not group:
            continue
        bands.append(
            BandResult(
                band=name,
                jobs=len(group),
                median_wait=float(median(wait(j) for j in group)),
                on_time_share=sum(on_time(j) for j in group) / len(group),
                still_open=sum(season.completed_on[j.job_id] is None for j in group),
            )
        )
    remote = [j for j in counted if j.is_remote]
    town = [j for j in counted if not j.is_remote]
    return SeasonResult(
        setting=setting,
        repairs=sum(season.completed_on[j.job_id] is not None for j in counted),
        driving_days=season.driving_days,
        bands=tuple(bands),
        on_time_remote=sum(on_time(j) for j in remote) / len(remote) if remote else 0.0,
        on_time_town=sum(on_time(j) for j in town) / len(town) if town else 0.0,
    )
