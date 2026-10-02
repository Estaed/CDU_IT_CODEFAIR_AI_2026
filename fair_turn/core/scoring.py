"""How much a household needs its repair: ``need = urgency + safety + household health risk``.

Reads typed ``Job`` fields only, never model text. Policy numbers come from ``constants``;
the weights below are formula choices of this module, not NT policy, and are named once
here so explanations can quote them.
"""

from datetime import date, timedelta

from fair_turn.core import constants
from fair_turn.core.types import FaultType, Job, SafetyClass

URGENCY_CAP = 3.0  # a job past its window keeps rising, up to three windows
SAFETY_WEIGHT = {SafetyClass.IMMEDIATE: 3.0, SafetyClass.URGENT: 2.0, SafetyClass.ROUTINE: 1.0}
HEAT_ESCALATION = 1.0  # QLD precedent: cooling and hot-water faults, remote, heat season
HEAT_SENSITIVE_FAULTS = frozenset({FaultType.COOLING, FaultType.HOT_WATER})
HEALTH_RISK_PER_FACTOR = 0.5


def window_days(job: Job) -> float:
    """NT response window for the job class and remoteness, in days."""
    if job.safety_class is None:
        raise ValueError(f"{job.job_id}: safety_class is required for a window")
    if job.safety_class is SafetyClass.IMMEDIATE:
        return constants.MAKE_SAFE_HOURS / 24
    return float(constants.RESPONSE_BUSINESS_DAYS[(job.safety_class.value, job.is_remote)])


def business_days_between(start: date, end: date) -> int:
    """Weekdays after ``start`` up to and including ``end``; 0 when ``end`` is not later.

    A report made on a Friday has used 0 business days on Saturday and Sunday and 1 on
    Monday. Public holidays are not modelled (no NT holiday table in ``data/raw``).
    """
    if end <= start:
        return 0
    days = (end - start).days
    weeks, rest = divmod(days, 7)
    count = weeks * 5
    for offset in range(1, rest + 1):
        if (start + timedelta(days=offset)).weekday() < 5:
            count += 1
    return count


def window_used(job: Job, today: date) -> float:
    """Time used of the job's window, in the window's own unit: business days for urgent and
    routine (FS17 states them in business days), calendar days for immediate (hours)."""
    if job.safety_class is SafetyClass.IMMEDIATE:
        return float(max(0, (today - job.reported_on).days))
    return float(business_days_between(job.reported_on, today))


def is_overdue(job: Job, today: date) -> bool:
    """Past the NT response window on ``today``."""
    return window_used(job, today) > window_days(job)


def urgency(job: Job, today: date) -> float:
    """Window used over the window, floored at 0 and capped at ``URGENCY_CAP``."""
    return min(URGENCY_CAP, window_used(job, today) / window_days(job))


def safety(job: Job, today: date) -> float:
    if job.safety_class is None:
        raise ValueError(f"{job.job_id}: safety_class is required for a safety factor")
    base = SAFETY_WEIGHT[job.safety_class]
    escalate = (
        job.is_remote
        and job.fault_type in HEAT_SENSITIVE_FAULTS
        and today.month in constants.HEAT_SEASON_MONTHS
    )
    return base + HEAT_ESCALATION if escalate else base


def health_risk(job: Job) -> float:
    return HEALTH_RISK_PER_FACTOR * len(job.health_risk)


def need(job: Job, today: date) -> float:
    """The household's need on ``today``; a job missing a required field has none (a person
    reads it first)."""
    if job.needs_human:
        raise ValueError(f"{job.job_id}: a job missing a required field has no need score")
    return urgency(job, today) + safety(job, today) + health_risk(job)


def need_factors(job: Job, today: date) -> dict[str, float]:
    """The three parts of ``need``, for explanations."""
    return {
        "urgency": urgency(job, today),
        "safety": safety(job, today),
        "health_risk": health_risk(job),
    }
