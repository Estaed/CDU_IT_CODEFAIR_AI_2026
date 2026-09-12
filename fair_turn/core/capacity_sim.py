"""Toy dispatch model that turns a ranking into wait times (PRD section 6.3).

A measurement device, not a scheduler: each day every crew takes the top-ranked open job
in its region, travels there (a whole travel day if the community is far and the crew is
not already there), then batches up to its daily capacity in that community. Deterministic;
no randomness inside.

Jobs carry no region or distance, so the caller passes a ``Site`` per community (from
``communities.csv``). A job still open at the end of the run counts in the medians with its
wait censored at the day after the last simulated day, so a region the ranking starves
cannot drop out of the gap.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, timedelta
from statistics import median

from fair_turn.core import scoring
from fair_turn.core.types import Job


@dataclass(frozen=True)
class Site:
    region: str
    km_to_base: float


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
    queue_length: list[int] = field(default_factory=list)  # open rankable jobs, start of day


@dataclass
class _Crew:
    region: str
    location: str | None = None  # community id; None is the crew base
    heading_to: str | None = None  # destination reached the day after a travel day
    target_job: str | None = None


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
    crews_per_region: Mapping[str, int],
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
    crews = [_Crew(region) for region, n in crews_per_region.items() for _ in range(n)]
    completed_on: dict[str, date | None] = {j.job_id: None for j in jobs}
    travel_cost = 0.0
    queue_length: list[int] = []

    for offset in range(days):
        today = start + timedelta(days=offset)
        open_jobs = [j for j in jobs if j.reported_on <= today and completed_on[j.job_id] is None]
        ranked = [s.job for s in scoring.rank(open_jobs, today, lam)]
        queue_length.append(len(ranked))

        for crew in crews:
            destination = crew.heading_to
            crew.heading_to = None
            if destination is not None and _is_closed(closed, destination, today):
                destination = None
            if destination is None:
                reserved = {c.target_job for c in crews if c.heading_to is not None}
                target = next(
                    (
                        j
                        for j in ranked
                        if completed_on[j.job_id] is None
                        and j.job_id not in reserved
                        and sites[j.community_id].region == crew.region
                        and not _is_closed(closed, j.community_id, today)
                    ),
                    None,
                )
                if target is None:
                    continue
                destination = target.community_id
                if crew.location != destination:
                    travel_cost += target.logistics_factor
                    crew.location = destination
                    if sites[destination].km_to_base > travel_day_km:
                        crew.heading_to = destination
                        crew.target_job = target.job_id
                        continue
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
        queue_length=queue_length,
    )
