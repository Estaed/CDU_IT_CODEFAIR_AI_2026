"""Pooled visit plan for the signed list (PRD section 3.3, pooled crews decided 2026-09-14).

Distance chooses which crew goes, never which job is served. Membership is the signed list:
air and barge stops stay manual coordination, closed-road stops stay listed with their
reason, and when road stops outnumber crew slots the ones left over are the lowest signed
ranks. Road stops are assigned to crew slots at minimum round-trip km; each crew then drives
the shortest route over its stops. The coordinator may reorder a crew with a reason.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from itertools import permutations
from typing import Literal

from fair_turn.core.assignment import min_cost_assignment
from fair_turn.core.capacity_sim import CrewBase, haversine_km
from fair_turn.core.constants import JOBS_PER_CREW_DAY, TRAVEL_DAY_KM

MANUAL_NEXT_ACTION = "book air/barge freight"
MANUAL_OWNER = "coordinator"
ROAD_CLOSED = "road closed"
OVER_CAPACITY = "over crew capacity"
_KM_EPS = 1e-9


@dataclass(frozen=True)
class Stop:
    """A signed job with what the plan needs to place it."""

    job_id: str
    community_id: str
    region: str
    lat: float
    lon: float
    access: Literal["road", "air", "barge"]
    road_open: bool
    signed_rank: int
    road_factor: float  # multiplier on haversine km for the community's road access


@dataclass(frozen=True)
class CrewPlan:
    """One crew's stops in driving order, with every leg including the return to base."""

    crew: CrewBase
    stops: tuple[Stop, ...]
    legs_km: tuple[float, ...]
    travel_day_legs: tuple[bool, ...]  # leg over the capacity model's travel-day distance
    km: float


@dataclass(frozen=True)
class Unplanned:
    """A signed road stop with no crew slot today, and why."""

    stop: Stop
    reason: str


@dataclass(frozen=True)
class Manual:
    """A signed air or barge stop: coordinated by hand, never routed."""

    stop: Stop
    next_action: str
    owner: str


@dataclass(frozen=True)
class PlanChange:
    """A coordinator's reordering of one crew, with the reason and the km it changed."""

    job_ids: tuple[str, ...]
    reason: str
    km_change: float  # new route km minus old


@dataclass(frozen=True)
class Plan:
    """The visit plan derived from one immutable signed batch version."""

    batch_version: int
    crews: tuple[CrewPlan, ...]
    unplanned: tuple[Unplanned, ...]
    manual: tuple[Manual, ...]
    changes: tuple[PlanChange, ...]

    @property
    def road_km(self) -> float:
        return sum(crew.km for crew in self.crews)

    @property
    def within_capacity(self) -> bool:
        return not any(item.reason == OVER_CAPACITY for item in self.unplanned)


def _measure(crew: CrewBase, stops: Sequence[Stop]) -> tuple[tuple[float, ...], float]:
    """Legs base -> stops -> base; a leg takes the road factor of its community end."""
    if not stops:
        return (), 0.0
    points = [(crew.lat, crew.lon), *((stop.lat, stop.lon) for stop in stops)]
    legs = [
        haversine_km(*points[index], *points[index + 1]) * stops[index].road_factor
        for index in range(len(stops))
    ]
    legs.append(haversine_km(*points[-1], crew.lat, crew.lon) * stops[-1].road_factor)
    return tuple(legs), sum(legs)


def _shortest(crew: CrewBase, stops: Sequence[Stop]) -> tuple[Stop, ...]:
    """The exact shortest base -> stops -> base order; ties keep the earliest permutation of
    the signed order."""
    ordered = sorted(stops, key=lambda stop: stop.signed_rank)
    best, best_km = tuple(ordered), _measure(crew, ordered)[1]
    for candidate in permutations(ordered):
        km = _measure(crew, candidate)[1]
        if km < best_km - _KM_EPS:
            best, best_km = candidate, km
    return best


def _crew_plan(crew: CrewBase, stops: Sequence[Stop]) -> CrewPlan:
    legs, km = _measure(crew, stops)
    return CrewPlan(crew, tuple(stops), legs, tuple(leg > TRAVEL_DAY_KM for leg in legs), km)


def _split_count(assigned: list[list[Stop]]) -> int:
    """How many extra crews the communities are spread over (0 when none is split)."""
    crews_of: dict[str, set[int]] = {}
    for index, stops in enumerate(assigned):
        for stop in stops:
            crews_of.setdefault(stop.community_id, set()).add(index)
    return sum(len(indices) - 1 for indices in crews_of.values())


def _route_km(crew: CrewBase, stops: Sequence[Stop]) -> float:
    return _measure(crew, _shortest(crew, stops))[1]


def _consolidate(crews: Sequence[CrewBase], assigned: list[list[Stop]]) -> list[list[Stop]]:
    """Move or swap stops so one community's stops share a crew, only when that does not
    raise the total route km. Each accepted change strictly reduces the split count."""
    changed = True
    while changed:
        changed = False
        split = _split_count(assigned)
        if split == 0:
            break
        for a, b in permutations(range(len(crews)), 2):
            here = {stop.community_id for stop in assigned[a]}
            for stop in assigned[b]:
                if stop.community_id not in here:
                    continue
                rest_b = [s for s in assigned[b] if s is not stop]
                options: list[tuple[list[Stop], list[Stop]]] = []
                if len(assigned[a]) < JOBS_PER_CREW_DAY:
                    options.append(([*assigned[a], stop], rest_b))
                options += [
                    ([*(s for s in assigned[a] if s is not other), stop], [*rest_b, other])
                    for other in assigned[a]
                    if other.community_id != stop.community_id
                ]
                before = _route_km(crews[a], assigned[a]) + _route_km(crews[b], assigned[b])
                for new_a, new_b in options:
                    trial = list(assigned)
                    trial[a] = sorted(new_a, key=lambda s: s.signed_rank)
                    trial[b] = sorted(new_b, key=lambda s: s.signed_rank)
                    after = _route_km(crews[a], trial[a]) + _route_km(crews[b], trial[b])
                    if _split_count(trial) < split and after <= before + _KM_EPS:
                        assigned, changed = trial, True
                        break
                if changed:
                    break
            if changed:
                break
    return assigned


def plan(batch_version: int, stops: Sequence[Stop], crews: Sequence[CrewBase]) -> Plan:
    """Place every signed stop: manual, unplanned with a reason, or on a crew's route."""
    ordered = sorted(stops, key=lambda stop: stop.signed_rank)
    manual = tuple(
        Manual(stop, MANUAL_NEXT_ACTION, MANUAL_OWNER) for stop in ordered if stop.access != "road"
    )
    road = [stop for stop in ordered if stop.access == "road"]
    unplanned = [Unplanned(stop, ROAD_CLOSED) for stop in road if not stop.road_open]
    drivable = [stop for stop in road if stop.road_open]

    slots = [index for index in range(len(crews)) for _ in range(JOBS_PER_CREW_DAY)]
    fits, over = drivable[: len(slots)], drivable[len(slots) :]  # overflow by signed rank only
    unplanned += [Unplanned(stop, OVER_CAPACITY) for stop in over]

    costs = [
        [2 * haversine_km(crews[c].lat, crews[c].lon, s.lat, s.lon) * s.road_factor for c in slots]
        for s in fits
    ]
    assigned: list[list[Stop]] = [[] for _ in crews]
    for stop, slot in zip(fits, min_cost_assignment(costs), strict=True):
        assigned[slots[slot]].append(stop)
    assigned = _consolidate(crews, assigned)

    crew_plans = tuple(
        _crew_plan(crew, _shortest(crew, stops_for))
        for crew, stops_for in zip(crews, assigned, strict=True)
    )
    unplanned.sort(key=lambda item: item.stop.signed_rank)
    return Plan(batch_version, crew_plans, tuple(unplanned), manual, ())


def edit_order(current: Plan, crew_id: str, new_order: list[str], reason: str) -> Plan:
    """Reorder one crew's stops, same membership, with the coordinator's reason."""
    if not reason.strip():
        raise ValueError("A coordinator reason is required.")
    crew_plan = next((item for item in current.crews if item.crew.crew_id == crew_id), None)
    if crew_plan is None:
        raise ValueError("Unknown crew.")
    if sorted(new_order) != sorted(stop.job_id for stop in crew_plan.stops):
        raise ValueError("A manual edit must keep the same job membership.")
    by_id = {stop.job_id: stop for stop in crew_plan.stops}
    changed = _crew_plan(crew_plan.crew, [by_id[job_id] for job_id in new_order])
    crews = tuple(changed if item is crew_plan else item for item in current.crews)
    change = PlanChange(tuple(new_order), reason, changed.km - crew_plan.km)
    return Plan(
        current.batch_version, crews, current.unplanned, current.manual, (*current.changes, change)
    )
