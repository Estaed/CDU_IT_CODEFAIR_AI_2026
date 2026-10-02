"""The weekly crew plan: where each base's crews go this week, and what that leaves waiting.

The unit of the decision is a **trip**, not a job, because that is where the cost is. A crew
working in its own town fixes ``JOBS_PER_CREW_DAY`` repairs a day. A trip to a remote
community first spends days on the road (there and back, at ``DRIVE_KM_PER_DAY``), then
fixes up to ``MAX_JOBS_PER_TRIP`` repairs there. Counting repairs per crew-day, the town
always wins: that is the brief's "efficiency" pressure, made exact.

One number, the **setting** ``s`` from 0 to 1, says what decides where crews go:

    priority of a trip = sum over its repairs of ((1 - s) + s * need)
                         / (work days + (1 - s) * driving days)

At ``s = 0`` (Efficiency first) every repair counts the same and driving counts in full, so
trips that fix the most per crew-day go first. That is a rule, not a guarantee of the
maximum: the fill is greedy, and a little weight on need sometimes packs more repairs. At
``s = 1`` (Most overdue first) repairs count by the household's need and driving days are
not held against a trip. Each base fills its crews' week greedily, highest priority first.
Pure Python, deterministic.
"""

import math
from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date

from fair_turn.core import constants, scoring
from fair_turn.core.types import Job, SafetyClass

# Why a community with open repairs gets no trip, or only part of one, this week.
CLOSED = "access is closed for most of this week"
DROPPED = "taken out of the plan by the coordinator"
OUTRANKED = "below the cut: the crews' days went to trips worth more per crew-day"
NO_ROOM = "its trip needs more days in a row than any crew had left"
TRIP_FULL = "a crew goes there, but its trip carries only part of the repairs"


@dataclass(frozen=True)
class Place:
    """One community as the planner sees it: its base and one-way road distance."""

    community_id: str
    base: str
    is_town: bool
    road_km: float
    lat: float
    lon: float


def travel_days(place: Place) -> float:
    """Days on the road there and back, in half days; nothing for the base town itself."""
    if place.is_town:
        return 0.0
    return math.ceil(4 * place.road_km / constants.DRIVE_KM_PER_DAY) / 2


def work_days(repairs: int) -> float:
    """Days to fix ``repairs`` at one place, in half days."""
    return math.ceil(2 * repairs / constants.JOBS_PER_CREW_DAY) / 2


def weight(job: Job, today: date, setting: float) -> float:
    """What one repair counts for under ``setting``."""
    return (1 - setting) + setting * scoring.need(job, today)


def in_plan(job: Job, today: date) -> bool:
    """A job the weekly plan can take: read, reported by ``today``, not an emergency.

    Immediate jobs go to the emergency make-safe contractor (FS17: four hours), never to a
    planned trip; a job missing a required field waits for a person."""
    return (
        not job.needs_human
        and job.safety_class is not SafetyClass.IMMEDIATE
        and job.reported_on <= today
    )


@dataclass(frozen=True)
class Trip:
    community_id: str
    base: str
    is_town: bool
    job_ids: tuple[str, ...]
    travel_days: float
    work_days: float
    priority: float  # under the plan's setting; higher goes first
    added: bool = False  # put in by the coordinator

    @property
    def days(self) -> float:
        return self.travel_days + self.work_days


@dataclass(frozen=True)
class Stop:
    trip: Trip
    start: float  # crew-day offset in the week, 0 = Monday morning


@dataclass(frozen=True)
class CrewWeek:
    crew_id: str
    base: str
    stops: tuple[Stop, ...]

    @property
    def days_used(self) -> float:
        return sum(stop.trip.days for stop in self.stops)


@dataclass(frozen=True)
class Waiting:
    community_id: str
    base: str
    job_ids: tuple[str, ...]
    reason: str
    priority: float | None  # of the full-week trip it would have been; None when it cannot go
    trip_repairs: int = 0  # repairs that trip would carry (TRIP_FULL: the trip that goes)
    trip_days: float = 0.0  # crew-days that trip takes


@dataclass(frozen=True)
class WeekPlan:
    day: date
    setting: float
    trips: tuple[Trip, ...]  # in the order they were chosen, base by base
    crews: tuple[CrewWeek, ...]
    waiting: tuple[Waiting, ...]
    spare_days: Mapping[str, float] = field(default_factory=dict)  # per base, in town on call
    not_fitted: tuple[str, ...] = ()  # communities the coordinator added that did not fit

    def planned_job_ids(self) -> set[str]:
        return {job_id for trip in self.trips for job_id in trip.job_ids}

    def trip_to(self, community_id: str) -> Trip | None:
        return next((t for t in self.trips if t.community_id == community_id), None)

    def waiting_at(self, community_id: str) -> Waiting | None:
        return next((w for w in self.waiting if w.community_id == community_id), None)

    def last_priority(self, base: str) -> float | None:
        """Priority of the lowest trip a base still made: the cut line a trip had to beat."""
        values = [t.priority for t in self.trips if t.base == base and not t.added]
        return min(values) if values else None


def crew_ids(base: str, count: int) -> list[str]:
    return [base] if count == 1 else [f"{base} {n}" for n in range(1, count + 1)]


def _trip(
    place: Place, pool: list[Job], today: date, setting: float, room: float, added: bool
) -> Trip | None:
    """The best trip to ``place`` that fits in ``room`` crew-days, or None."""
    limit = constants.JOBS_PER_CREW_DAY if place.is_town else constants.MAX_JOBS_PER_TRIP
    travel = travel_days(place)
    count = min(len(pool), limit)
    while count and travel + work_days(count) > room:
        count -= 1
    if not count:
        return None
    batch = pool[:count]
    work = work_days(count)
    counted = work + (1 - setting) * travel
    value = sum(weight(j, today, setting) for j in batch) / counted
    return Trip(
        community_id=place.community_id,
        base=place.base,
        is_town=place.is_town,
        job_ids=tuple(j.job_id for j in batch),
        travel_days=travel,
        work_days=work,
        priority=value,
        added=added,
    )


def plan(
    jobs: Iterable[Job],
    places: Mapping[str, Place],
    today: date,
    setting: float,
    crews_at_base: Mapping[str, int] | None = None,
    closed: Collection[str] = (),
    add: Collection[str] = (),
    drop: Collection[str] = (),
) -> WeekPlan:
    """Plan the week starting ``today``.

    ``closed`` communities cannot be reached this week. ``add`` are communities the
    coordinator puts in first (one trip each, before the greedy fill); ``drop`` are
    communities the coordinator takes out. Both carry a reason in the audit log, not here.
    """
    if not 0.0 <= setting <= 1.0:
        raise ValueError(f"setting must be between 0 and 1, got {setting}")
    crews_at_base = constants.CREWS_AT_BASE if crews_at_base is None else crews_at_base
    pools: dict[str, list[Job]] = {}
    for job in jobs:
        if in_plan(job, today):
            pools.setdefault(job.community_id, []).append(job)
    for cid, pool in pools.items():
        if cid not in places:
            raise ValueError(f"no place for community {cid!r}")
        pool.sort(key=lambda j: (-weight(j, today, setting), j.reported_on, j.job_id))

    trips: list[Trip] = []
    crews: list[CrewWeek] = []
    waiting: list[Waiting] = []
    spare: dict[str, float] = {}
    not_fitted: list[str] = []
    for base in constants.CREW_BASES:
        ids = crew_ids(base, crews_at_base.get(base, 0))
        left = [float(constants.CREW_DAYS_PER_WEEK)] * len(ids)
        stops: list[list[Stop]] = [[] for _ in ids]
        local = {cid: list(pool) for cid, pool in pools.items() if places[cid].base == base}
        visited: set[str] = set()

        def place_trip(trip: Trip, stops=stops, left=left, local=local, visited=visited) -> None:
            # Best fit: the crew with the fewest days left that still takes the trip, so whole
            # free weeks stay free for long trips.
            fits = [i for i in range(len(left)) if left[i] >= trip.days - 1e-9]
            crew = min(fits, key=lambda i: (left[i], i))
            start = constants.CREW_DAYS_PER_WEEK - left[crew]
            stops[crew].append(Stop(trip, start))
            left[crew] -= trip.days
            taken = set(trip.job_ids)
            local[trip.community_id] = [
                j for j in local[trip.community_id] if j.job_id not in taken
            ]
            if not trip.is_town:
                visited.add(trip.community_id)
            trips.append(trip)

        for cid in sorted(add):
            if cid not in local or places[cid].base != base or cid in closed:
                continue
            room = max(left, default=0.0)
            trip = _trip(places[cid], local[cid], today, setting, room, added=True)
            if trip is None:
                not_fitted.append(cid)
            else:
                place_trip(trip)

        while left and max(left) > 0:
            room = max(left)
            best: Trip | None = None
            for cid in sorted(local):
                if not local[cid] or cid in closed or cid in drop or cid in visited:
                    continue
                trip = _trip(places[cid], local[cid], today, setting, room, added=False)
                if trip is not None and (best is None or trip.priority > best.priority):
                    best = trip
            if best is None:
                break
            place_trip(best)

        # Days nothing fits stay in town, for reports that arrive during the week.
        for crew, days in enumerate(left):
            if days > 0:
                on_call = Trip(base, base, True, (), 0.0, days, 0.0)
                stops[crew].append(Stop(on_call, constants.CREW_DAYS_PER_WEEK - days))
        spare[base] = sum(left)
        crews.extend(
            CrewWeek(crew_id, base, tuple(crew_stops))
            for crew_id, crew_stops in zip(ids, stops, strict=True)
        )
        cut = min((t.priority for t in trips if t.base == base and not t.added), default=None)
        week = float(constants.CREW_DAYS_PER_WEEK)
        for cid in sorted(local):
            pool = local[cid]
            if not pool:
                continue
            ids_left = tuple(j.job_id for j in pool)
            full = _trip(places[cid], pool, today, setting, week, False)
            size = (len(full.job_ids), full.days) if full else (0, 0.0)
            if cid in closed:
                waiting.append(Waiting(cid, base, ids_left, CLOSED, None, *size))
            elif cid in drop:
                waiting.append(Waiting(cid, base, ids_left, DROPPED, None, *size))
            elif cid in visited:
                carried = next(t for t in trips if t.community_id == cid)
                waiting.append(
                    Waiting(
                        cid, base, ids_left, TRIP_FULL, None, len(carried.job_ids), carried.days
                    )
                )
            else:
                value = full.priority if full else None
                beaten = value is not None and cut is not None and value <= cut + 1e-9
                reason = OUTRANKED if beaten else NO_ROOM
                waiting.append(Waiting(cid, base, ids_left, reason, value, *size))

    return WeekPlan(
        day=today,
        setting=setting,
        trips=tuple(trips),
        crews=tuple(crews),
        waiting=tuple(waiting),
        spare_days=spare,
        not_fitted=tuple(not_fitted),
    )


@dataclass(frozen=True)
class Summary:
    """What a plan does this week, in the units a coordinator and a judge read."""

    repairs: int
    repairs_remote: int
    overdue: int  # past the NT window on the plan day, among plannable jobs
    overdue_remote: int
    overdue_left: int  # of those, not in this week's plan
    overdue_left_remote: int
    driving_days: float
    crew_days: float  # in the week, across every base
    remote_trips: int


def summarise(week: WeekPlan, jobs: Iterable[Job]) -> Summary:
    plannable = [j for j in jobs if in_plan(j, week.day)]
    planned = week.planned_job_ids()
    overdue = [j for j in plannable if scoring.is_overdue(j, week.day)]
    left = [j for j in overdue if j.job_id not in planned]
    in_week = [j for j in plannable if j.job_id in planned]
    return Summary(
        repairs=len(in_week),
        repairs_remote=sum(j.is_remote for j in in_week),
        overdue=len(overdue),
        overdue_remote=sum(j.is_remote for j in overdue),
        overdue_left=len(left),
        overdue_left_remote=sum(j.is_remote for j in left),
        driving_days=sum(t.travel_days for t in week.trips),
        crew_days=float(len(week.crews) * constants.CREW_DAYS_PER_WEEK),
        remote_trips=sum(not t.is_town for t in week.trips),
    )


def trip_lines(week: WeekPlan) -> tuple[str, ...]:
    """The plan as log lines, one per remote trip and one per base's town days."""
    lines = []
    for base in constants.CREW_BASES:
        town = [t for t in week.trips if t.base == base and t.is_town]
        if town:
            repairs = sum(len(t.job_ids) for t in town)
            days = sum(t.work_days for t in town)
            lines.append(f"{base} town: {repairs} repairs, {days:g} crew-days")
        lines.extend(
            f"{base} > {t.community_id}: {len(t.job_ids)} repairs, {t.days:g} crew-days"
            for t in week.trips
            if t.base == base and not t.is_town
        )
    return tuple(lines)


def setting_name(setting: float) -> str:
    """The preset's name, or "Custom (0.35)" for a value between presets."""
    for name, value in constants.SETTINGS.items():
        if math.isclose(value, setting, abs_tol=1e-9):
            return name
    return f"Custom ({setting:.2f})"
