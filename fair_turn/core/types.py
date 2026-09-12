"""The typed job record every layer shares.

Fields are enums and plain values only: the ranking never reads model free text, and the
extraction schema (Task-08) is built from these same enums.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum


class FaultType(StrEnum):
    ELECTRICAL = "electrical"
    PLUMBING_WATER = "plumbing_water"
    SEWER_DRAINAGE = "sewer_drainage"
    COOLING = "cooling"
    HOT_WATER = "hot_water"
    ROOF_STRUCTURE = "roof_structure"
    DOORS_LOCKS_SECURITY = "doors_locks_security"
    STOVE_COOKING = "stove_cooking"
    PESTS = "pests"
    OTHER = "other"


class SafetyClass(StrEnum):
    IMMEDIATE = "immediate"
    URGENT = "urgent"
    ROUTINE = "routine"


class HealthRiskFactor(StrEnum):
    INFANT_OR_YOUNG_CHILD = "infant_or_young_child"
    ELDERLY = "elderly"
    PREGNANCY_OR_CHRONIC_CONDITION = "pregnancy_or_chronic_condition"
    OVERCROWDING = "overcrowding"
    EXTREME_HEAT_EXPOSURE = "extreme_heat_exposure"
    NO_WATER_OR_SANITATION = "no_water_or_sanitation"


@dataclass(frozen=True)
class Job:
    job_id: str
    community_id: str
    is_remote: bool
    reported_on: date
    fault_type: FaultType | None
    safety_class: SafetyClass | None
    health_risk: frozenset[HealthRiskFactor] = field(default_factory=frozenset)
    logistics_factor: float = 0.0  # travel cost from the crew base, 0-100 scale (Task-01)
    road_closed: bool = False
    crew_nearby: bool = False

    @property
    def needs_human(self) -> bool:
        """A job missing a required typed field is never ranked; a person decides it."""
        return self.fault_type is None or self.safety_class is None


@dataclass(frozen=True)
class ScoredJob:
    job: Job
    score: float | None
    factors: dict[str, float]
    rank: int | None
    needs_human: bool
