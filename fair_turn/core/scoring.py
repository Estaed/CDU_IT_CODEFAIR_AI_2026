"""The transparent score the coordinator controls: ``score = need - lam * logistics``.

Reads typed ``Job`` fields only (PRD section 4). Policy numbers come from ``constants``;
the weights below are formula choices of this module, not NT policy, and are named once
here so explanations (Task-06) can quote them.
"""

from dataclasses import replace
from datetime import date, timedelta

from fair_turn.core import constants
from fair_turn.core.types import FaultType, Job, SafetyClass, ScoredJob

URGENCY_CAP = 3.0  # a job past its window keeps rising, up to three windows
SAFETY_WEIGHT = {SafetyClass.IMMEDIATE: 3.0, SafetyClass.URGENT: 2.0, SafetyClass.ROUTINE: 1.0}
HEAT_ESCALATION = 1.0  # QLD precedent: cooling and hot-water faults, remote, heat season
HEAT_SENSITIVE_FAULTS = frozenset({FaultType.COOLING, FaultType.HOT_WATER})
HEALTH_RISK_PER_FACTOR = 0.5
LOGISTICS_SCALE = 100.0  # ``Job.logistics_factor`` is on a 0-100 scale
ROAD_CLOSED_PENALTY = 2.0
CREW_NEARBY_CREDIT = 0.5

FACTOR_NAMES = ("urgency", "safety", "health_risk", "logistics")


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


def logistics(job: Job) -> float:
    cost = job.logistics_factor / LOGISTICS_SCALE
    if job.road_closed:
        cost += ROAD_CLOSED_PENALTY
    if job.crew_nearby:
        cost -= CREW_NEARBY_CREDIT
    return max(0.0, cost)


def score_job(job: Job, today: date, lam: float) -> ScoredJob:
    """Score one job; a job missing a required field gets no score and ``needs_human``."""
    if job.needs_human:
        return ScoredJob(job=job, score=None, factors={}, rank=None, needs_human=True)
    factors = {
        "urgency": urgency(job, today),
        "safety": safety(job, today),
        "health_risk": health_risk(job),
        "logistics": logistics(job),
    }
    need = factors["urgency"] + factors["safety"] + factors["health_risk"]
    score = need - lam * factors["logistics"]
    return ScoredJob(job=job, score=score, factors=factors, rank=None, needs_human=False)


def split_human_queue(jobs: list[Job]) -> tuple[list[Job], list[Job]]:
    """Return ``(rankable, human_queue)`` preserving input order."""
    rankable = [j for j in jobs if not j.needs_human]
    human = [j for j in jobs if j.needs_human]
    return rankable, human


def rank(jobs: list[Job], today: date, lam: float) -> list[ScoredJob]:
    """Rankable jobs scored and sorted by score descending, ties broken by ``job_id``.

    Human-queue jobs are excluded; get them from ``split_human_queue``.
    """
    rankable, _ = split_human_queue(jobs)
    scored = [score_job(j, today, lam) for j in rankable]
    scored.sort(key=lambda s: (-(s.score or 0.0), s.job.job_id))
    return [replace(s, rank=i) for i, s in enumerate(scored, start=1)]
