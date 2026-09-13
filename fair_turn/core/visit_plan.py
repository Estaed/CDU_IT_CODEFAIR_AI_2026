"""Signed-order visit planning with optional, explicit distance suggestions (PRD section 3.3)."""

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from fair_turn.core.constants import (
    CREWS_PER_REMOTE_REGION,
    CREWS_TOWN,
    JOBS_PER_CREW_DAY,
    REMOTE_REGIONS,
    SUGGESTION_MIN_SAVING_KM,
)


@dataclass(frozen=True)
class Stop:
    """A signed job with the information required to make a crew visit plan."""

    job_id: str
    community_id: str
    region: str
    lat: float
    lon: float
    access: Literal["road", "air", "barge"]
    road_open: bool
    signed_rank: int
    window_days_left: int


@dataclass(frozen=True)
class Crew:
    """A crew base and its one-day job capacity."""

    base: str
    region: str
    lat: float
    lon: float
    jobs_per_day: int


@dataclass(frozen=True)
class CrewPlan:
    """One crew's signed-order stops and measured return route."""

    crew: Crew
    stops: tuple[Stop, ...]
    legs_km: tuple[float, ...]
    km: float
    within_capacity: bool


@dataclass(frozen=True)
class Unplanned:
    """A signed road stop that cannot fit this plan."""

    stop: Stop
    reason: str


@dataclass(frozen=True)
class Manual:
    """A signed non-road stop requiring freight coordination."""

    stop: Stop
    next_action: str


@dataclass(frozen=True)
class Suggestion:
    """An adjacent stop swap that a coordinator may accept explicitly."""

    crew_base: str
    job_a: str
    job_b: str
    old_order: tuple[str, ...]
    new_order: tuple[str, ...]
    saving_km: float


@dataclass(frozen=True)
class PlanChange:
    """An accepted explanation for a departure from signed order."""

    job_ids: tuple[str, ...]
    reason: str
    saving_km: float


@dataclass(frozen=True)
class Plan:
    """The visit plan derived from one immutable signed batch version."""

    batch_version: int
    crews: tuple[CrewPlan, ...]
    unplanned: tuple[Unplanned, ...]
    manual: tuple[Manual, ...]
    changes: tuple[PlanChange, ...]


def crew_capacity(region: str) -> int:
    """Return the signed-list capacity allocated to a region for one day."""
    crew_count = CREWS_PER_REMOTE_REGION if region in REMOTE_REGIONS else CREWS_TOWN
    return crew_count * JOBS_PER_CREW_DAY


# Copied here because the core layer cannot import the data layer.
def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance between two latitude/longitude points in kilometres."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dlmb = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def _measure(
    crew: Crew, stops: tuple[Stop, ...], road_factor: Callable[[Stop], float]
) -> tuple[tuple[float, ...], float]:
    if not stops:
        return (), 0.0
    points = [(crew.lat, crew.lon), *((stop.lat, stop.lon) for stop in stops)]
    legs = tuple(
        haversine_km(*points[index], *points[index + 1]) * road_factor(stops[index])
        for index in range(len(stops))
    )
    return_leg = haversine_km(*points[-1], crew.lat, crew.lon) * road_factor(stops[-1])
    measured = (*legs, return_leg)
    return measured, sum(measured)


def _crew_plan(
    crew: Crew,
    stops: tuple[Stop, ...],
    road_factor: Callable[[Stop], float],
    over_capacity_regions: set[str],
) -> CrewPlan:
    legs_km, km = _measure(crew, stops, road_factor)
    return CrewPlan(
        crew=crew,
        stops=stops,
        legs_km=legs_km,
        km=km,
        within_capacity=len(stops) <= crew.jobs_per_day
        and crew.region not in over_capacity_regions,
    )


def plan(
    batch_version: int,
    stops: list[Stop],
    crews: list[Crew],
    road_factor: Callable[[Stop], float],
) -> Plan:
    """Allocate signed road stops without silently changing their signed order."""
    assigned: dict[int, list[Stop]] = {index: [] for index in range(len(crews))}
    unplanned: list[Unplanned] = []
    manual: list[Manual] = []

    for stop in sorted(stops, key=lambda item: item.signed_rank):
        if stop.access != "road":
            manual.append(Manual(stop, "book air/barge freight"))
            continue
        if not stop.road_open:
            unplanned.append(Unplanned(stop, "road closed"))
            continue
        candidates = [
            (index, crew) for index, crew in enumerate(crews) if crew.region == stop.region
        ]
        if not candidates:
            unplanned.append(Unplanned(stop, "no crew for region"))
            continue
        assignment = next(
            (
                (index, crew)
                for index, crew in candidates
                if len(assigned[index]) < crew.jobs_per_day
            ),
            None,
        )
        if assignment is None:
            unplanned.append(Unplanned(stop, "over crew capacity"))
            continue
        crew_index, _ = assignment
        assigned[crew_index].append(stop)

    over_capacity_regions = {
        item.stop.region for item in unplanned if item.reason == "over crew capacity"
    }
    crew_plans = tuple(
        _crew_plan(crew, tuple(assigned[index]), road_factor, over_capacity_regions)
        for index, crew in enumerate(crews)
    )
    return Plan(batch_version, crew_plans, tuple(unplanned), tuple(manual), ())


def suggestions(current: Plan, road_factor: Callable[[Stop], float]) -> list[Suggestion]:
    """Return eligible adjacent swaps, ordered from greatest to smallest distance saving."""
    result: list[Suggestion] = []
    for crew_plan in current.crews:
        old_order = tuple(stop.job_id for stop in crew_plan.stops)
        for index, first in enumerate(crew_plan.stops[:-1]):
            second = crew_plan.stops[index + 1]
            if first.window_days_left < 1 or second.window_days_left < 1:
                continue
            swapped = list(crew_plan.stops)
            swapped[index], swapped[index + 1] = swapped[index + 1], swapped[index]
            _, swapped_km = _measure(crew_plan.crew, tuple(swapped), road_factor)
            saving_km = crew_plan.km - swapped_km
            if saving_km >= SUGGESTION_MIN_SAVING_KM:
                result.append(
                    Suggestion(
                        crew_plan.crew.base,
                        first.job_id,
                        second.job_id,
                        old_order,
                        tuple(stop.job_id for stop in swapped),
                        saving_km,
                    )
                )
    return sorted(result, key=lambda item: item.saving_km, reverse=True)


def _require_reason(reason: str) -> None:
    if not reason.strip():
        raise ValueError("A coordinator reason is required.")


def _replace_crew(current: Plan, original: CrewPlan, changed: CrewPlan, change: PlanChange) -> Plan:
    crews = tuple(changed if item is original else item for item in current.crews)
    return Plan(
        current.batch_version, crews, current.unplanned, current.manual, (*current.changes, change)
    )


def apply(
    current: Plan,
    suggestion: Suggestion,
    reason: str,
    road_factor: Callable[[Stop], float],
) -> Plan:
    """Accept one displayed suggestion and record the coordinator's reason."""
    _require_reason(reason)
    crew_plan = next(
        (
            item
            for item in current.crews
            if item.crew.base == suggestion.crew_base
            and tuple(stop.job_id for stop in item.stops) == suggestion.old_order
        ),
        None,
    )
    if crew_plan is None:
        raise ValueError("The crew order no longer matches this suggestion.")
    by_id = {stop.job_id: stop for stop in crew_plan.stops}
    changed = _crew_plan(
        crew_plan.crew,
        tuple(by_id[job_id] for job_id in suggestion.new_order),
        road_factor,
        {item.stop.region for item in current.unplanned if item.reason == "over crew capacity"},
    )
    return _replace_crew(
        current,
        crew_plan,
        changed,
        PlanChange((suggestion.job_a, suggestion.job_b), reason, suggestion.saving_km),
    )


def edit_order(
    current: Plan,
    crew_base: str,
    new_order: list[str],
    reason: str,
    road_factor: Callable[[Stop], float],
) -> Plan:
    """Apply a manually ordered, same-membership crew route with an explicit reason."""
    _require_reason(reason)
    crew_plan = next((item for item in current.crews if item.crew.base == crew_base), None)
    if crew_plan is None:
        raise ValueError("Unknown crew base.")
    old_order = tuple(stop.job_id for stop in crew_plan.stops)
    if sorted(new_order) != sorted(old_order):
        raise ValueError("A manual edit must keep the same job membership.")
    by_id = {stop.job_id: stop for stop in crew_plan.stops}
    changed = _crew_plan(
        crew_plan.crew,
        tuple(by_id[job_id] for job_id in new_order),
        road_factor,
        {item.stop.region for item in current.unplanned if item.reason == "over crew capacity"},
    )
    return _replace_crew(
        current,
        crew_plan,
        changed,
        PlanChange(tuple(new_order), reason, crew_plan.km - changed.km),
    )
