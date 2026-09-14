"""Toy dispatch model that turns a ranking into wait times (PRD section 6.3).

A measurement device, not a scheduler. Crews are one NT-wide pool, each working from its
home base. A crew **reaches** a community in its home region, or one whose road km from the
base (haversine times the road factor) is at most the travel-day distance. Each day the ranked
open jobs are walked in rank order, each community once (closed-road and already-targeted
communities skipped): the community takes the nearest free crew that reaches it, measured
from that crew's current location, until no crew is free. Reach is physical feasibility;
inside it a lower-ranked community is never served before a higher-ranked one a free crew
could reach. A trip longer than the travel-day distance costs the crew that day; at the
community it batches up to its daily capacity in rank order. Deterministic; no randomness
inside.

Jobs carry no region or distance, so the caller passes a ``Site`` per community (from
``communities.csv``). A job still open at the end of the run counts in the medians with its
wait censored at the day after the last simulated day, so a region the ranking starves
cannot drop out of the gap.
"""

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta
from statistics import median

from fair_turn.core import constants, scoring
from fair_turn.core.types import Job


@dataclass(frozen=True)
class Site:
    region: str
    km_to_base: float
    lat: float
    lon: float
    road_factor: float  # multiplier on haversine km for the community's road access


@dataclass(frozen=True)
class CrewBase:
    """One crew and the base it starts from."""

    crew_id: str  # the base name, numbered when the base holds more than one crew
    base: str
    lat: float
    lon: float
    region: str  # home region: the crew reaches all of it whatever the distance


@dataclass(frozen=True)
class Closure:
    community_id: str
    closed_from: date
    closed_to: date  # inclusive


@dataclass
class SimResult:
    completed_on: dict[str, date | None]  # every input job; None while still open
    wait_days: dict[str, int | None]  # completion day minus report day; None while open
    median_wait_remote: float | None
    median_wait_town: float | None
    gap: float | None  # remote median minus town median
    travel_cost: float  # sum of ``logistics_factor`` over trips actually made
    travel_km: float  # sum of assigned trip km (haversine times road factor)
    queue_length: list[int] = field(default_factory=list)  # open rankable jobs, start of day
    visits: list[tuple[date, str, str]] = field(default_factory=list)  # day, crew, community


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres (core cannot import the data layer's copy)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dlmb = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def base_road_km(crew: CrewBase, lat: float, lon: float, road_factor: float) -> float:
    """Road km from the crew's base: haversine times the community's road factor."""
    return haversine_km(crew.lat, crew.lon, lat, lon) * road_factor


def reaches(crew: CrewBase, region: str, km_from_base: float, travel_day_km: float) -> bool:
    """A crew reaches its home region, and any community within the travel-day distance of
    its base by road."""
    return region == crew.region or km_from_base <= travel_day_km


def crew_roster(base_for_region: Mapping[str, str]) -> tuple[CrewBase, ...]:
    """The NT-wide crew pool: ``CREWS_PER_REMOTE_REGION`` crews at each remote region's base
    and ``CREWS_TOWN`` at the town region's base. ``base_for_region`` is the ``crew_base``
    column of ``communities.csv`` keyed by region."""
    missing = [region for region in constants.REGIONS if region not in base_for_region]
    if missing:
        raise ValueError(f"no crew base for {missing}")
    homes: list[tuple[str, str]] = []  # (base, home region) per crew
    for region in constants.REGIONS:
        count = (
            constants.CREWS_PER_REMOTE_REGION
            if region in constants.REMOTE_REGIONS
            else constants.CREWS_TOWN
        )
        homes.extend([(base_for_region[region], region)] * count)
    totals = {base: sum(1 for b, _ in homes if b == base) for base, _ in homes}
    seen: dict[str, int] = {}
    roster = []
    for base, region in homes:
        seen[base] = seen.get(base, 0) + 1
        crew_id = base if totals[base] == 1 else f"{base} {seen[base]}"
        roster.append(CrewBase(crew_id, base, *constants.CREW_BASE_COORDS[base], region))
    return tuple(roster)


@dataclass
class _Crew:
    lat: float
    lon: float
    location: str | None = None  # community id; None is the crew base
    heading_to: str | None = None  # destination reached the day after a travel day


def _is_closed(closed: Mapping[str, list[Closure]], community_id: str, today: date) -> bool:
    return any(c.closed_from <= today <= c.closed_to for c in closed.get(community_id, ()))


def _median(values: list[int]) -> float | None:
    return float(median(values)) if values else None


def simulate(
    jobs: list[Job],
    lam: float,
    start: date,
    days: int,
    closures: Iterable[Closure],
    crews: Sequence[CrewBase],
    jobs_per_crew_day: int,
    travel_day_km: float,
    sites: Mapping[str, Site],
) -> SimResult:
    """Run ``days`` days from ``start`` and return per-job completion and wait metrics."""
    for job in jobs:
        if job.community_id not in sites:
            raise ValueError(f"{job.job_id}: no site for community {job.community_id!r}")
    closed: dict[str, list[Closure]] = {}
    for c in closures:
        closed.setdefault(c.community_id, []).append(c)
    pool = [_Crew(crew.lat, crew.lon) for crew in crews]
    reach: dict[str, tuple[bool, ...]] = {}  # community -> reached, per crew in roster order
    completed_on: dict[str, date | None] = {j.job_id: None for j in jobs}
    travel_cost = 0.0
    travel_km = 0.0
    queue_length: list[int] = []
    visits: list[tuple[date, str, str]] = []

    for offset in range(days):
        today = start + timedelta(days=offset)
        open_jobs = [j for j in jobs if j.reported_on <= today and completed_on[j.job_id] is None]
        ranked = [s.job for s in scoring.rank(open_jobs, today, lam)]
        queue_length.append(len(ranked))

        # Crews arriving after a travel day work where they are headed, unless it closed.
        working: list[tuple[int, str]] = []
        free: list[int] = []  # roster order, so a km tie goes to the earlier crew
        for index, crew in enumerate(pool):
            destination, crew.heading_to = crew.heading_to, None
            if destination is not None and not _is_closed(closed, destination, today):
                working.append((index, destination))
            else:
                free.append(index)

        # Rank order, each community once: the nearest free crew that reaches it goes.
        considered = {destination for _, destination in working}
        for j in ranked:
            if not free:
                break
            cid = j.community_id
            if cid in considered or _is_closed(closed, cid, today):
                continue
            considered.add(cid)
            site = sites[cid]
            if cid not in reach:
                reach[cid] = tuple(
                    reaches(
                        crew,
                        site.region,
                        base_road_km(crew, site.lat, site.lon, site.road_factor),
                        travel_day_km,
                    )
                    for crew in crews
                )
            candidates = [index for index in free if reach[cid][index]]
            if not candidates:
                continue
            km, chosen = min(
                (
                    haversine_km(pool[i].lat, pool[i].lon, site.lat, site.lon) * site.road_factor,
                    i,
                )
                for i in candidates
            )
            free.remove(chosen)
            crew = pool[chosen]
            if crew.location != cid:
                travel_cost += j.logistics_factor
                travel_km += km
                crew.location = cid
                crew.lat, crew.lon = site.lat, site.lon
                if km > travel_day_km:
                    crew.heading_to = cid
                    continue
            working.append((chosen, cid))

        for index, destination in working:
            visits.append((today, crews[index].crew_id, destination))
            batch = [
                j
                for j in ranked
                if j.community_id == destination and completed_on[j.job_id] is None
            ][:jobs_per_crew_day]
            for j in batch:
                completed_on[j.job_id] = today

    end = start + timedelta(days=days)
    wait_days = {
        j.job_id: (done - j.reported_on).days if (done := completed_on[j.job_id]) else None
        for j in jobs
    }
    remote: list[int] = []
    town: list[int] = []
    for j in jobs:
        if j.needs_human or j.reported_on >= end:
            continue
        wait = wait_days[j.job_id]
        (remote if j.is_remote else town).append(
            wait if wait is not None else (end - j.reported_on).days
        )
    median_remote, median_town = _median(remote), _median(town)
    gap = None if median_remote is None or median_town is None else median_remote - median_town
    return SimResult(
        completed_on=completed_on,
        wait_days=wait_days,
        median_wait_remote=median_remote,
        median_wait_town=median_town,
        gap=gap,
        travel_cost=travel_cost,
        travel_km=travel_km,
        queue_length=queue_length,
        visits=visits,
    )
