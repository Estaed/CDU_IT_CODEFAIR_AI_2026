"""Two texts assembled from ``ScoredJob`` factors: the coordinator's rank sentence and the
tenant's answer (PRD sections 3.1, 3.4, 7). Both read enum labels and numbers only, so they
change with ``lam`` and never depend on any model-produced string.
"""

from fair_turn.core import constants, scoring
from fair_turn.core.types import FaultType, HealthRiskFactor, Job, SafetyClass, ScoredJob

LABELS: dict[str, str] = {
    HealthRiskFactor.INFANT_OR_YOUNG_CHILD.value: "a child under five in the house",
    HealthRiskFactor.ELDERLY.value: "an elderly person in the house",
    HealthRiskFactor.PREGNANCY_OR_CHRONIC_CONDITION.value: (
        "a pregnancy or chronic condition in the house"
    ),
    HealthRiskFactor.OVERCROWDING.value: "overcrowding in the house",
    HealthRiskFactor.EXTREME_HEAT_EXPOSURE.value: "extreme heat exposure",
    HealthRiskFactor.NO_WATER_OR_SANITATION.value: "no working water or sanitation",
    FaultType.ELECTRICAL.value: "an electrical fault",
    FaultType.PLUMBING_WATER.value: "a plumbing or water fault",
    FaultType.SEWER_DRAINAGE.value: "a sewer or drainage fault",
    FaultType.COOLING.value: "a cooling fault",
    FaultType.HOT_WATER.value: "a hot water fault",
    FaultType.ROOF_STRUCTURE.value: "a roof or structural fault",
    FaultType.DOORS_LOCKS_SECURITY.value: "a door, lock or security fault",
    FaultType.STOVE_COOKING.value: "a stove or cooking fault",
    FaultType.PESTS.value: "a pest problem",
    FaultType.OTHER.value: "another kind of fault",
    SafetyClass.IMMEDIATE.value: "immediate",
    SafetyClass.URGENT.value: "urgent",
    SafetyClass.ROUTINE.value: "routine",
}

# Words for the score factors themselves (``scoring.FACTOR_NAMES``), used so every
# factor with a non-zero weight is named somewhere in the tenant answer.
FACTOR_LABELS: dict[str, str] = {
    "urgency": "the NT response window",
    "safety": "its safety class",
    "health_risk": "household health risk",
    "logistics": "travel cost",
}

NEED_FACTORS = ("urgency", "safety", "health_risk")


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _join(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _window_label(job: Job) -> str:
    if job.safety_class is SafetyClass.IMMEDIATE:
        return f"{constants.MAKE_SAFE_HOURS}-hour"
    return f"{scoring.window_days(job):g}-day"


def _health_risk_labels(job: Job) -> list[str]:
    return [LABELS[f.value] for f in sorted(job.health_risk, key=lambda f: f.value)]


def _urgency_clause(job: Job, factors: dict[str, float]) -> str:
    window = _window_label(job)
    urgency = factors["urgency"]
    elapsed = round(urgency * scoring.window_days(job))
    if urgency <= 0:
        return f"the job is inside its {window} window"
    if urgency >= scoring.URGENCY_CAP:
        return f"the job is well past its {window} window, {elapsed} days overdue"
    return f"the job is {elapsed} days past its {window} window"


def _safety_clause(job: Job, factors: dict[str, float]) -> str:
    label = LABELS[job.safety_class.value]
    heat = factors["safety"] > scoring.SAFETY_WEIGHT[job.safety_class]
    if heat:
        return f"the job is classed {label} and heat-escalated this season"
    return f"the job is classed {label}"


def _health_risk_clause(job: Job, factors: dict[str, float]) -> str:
    labels = _health_risk_labels(job)
    if not labels:
        return "no household health risk factor is recorded for the house"
    return _join(labels)


_CLAUSE_BUILDERS = {
    "urgency": _urgency_clause,
    "safety": _safety_clause,
    "health_risk": _health_risk_clause,
}


def _logistics_clause(lam: float) -> str:
    if lam <= 0:
        return "travel cost is not counted at the current setting"
    if lam < 1:
        return "travel cost is counted at the current setting"
    return "travel cost is weighted heavily at the current setting"


def why_sentence(scored: ScoredJob, lam: float) -> str:
    """One sentence naming the two largest need factors, plus how travel cost is
    counted at the current ``lam``. Requires a ranked, scored job."""
    if scored.needs_human or scored.rank is None or scored.score is None:
        raise ValueError("why_sentence requires a ranked job")
    job, factors = scored.job, scored.factors
    top_two = sorted(NEED_FACTORS, key=lambda name: factors[name], reverse=True)[:2]
    clauses = [_CLAUSE_BUILDERS[name](job, factors) for name in top_two]
    logistics_clause = _logistics_clause(lam)
    return f"Ranked {_ordinal(scored.rank)}: {clauses[0]} and {clauses[1]}; {logistics_clause}."


def tenant_answer(
    scored: ScoredJob,
    rank_at_lambda0: int,
    window_days: float,
    coordinator_reason: str,
    lam: float,
) -> str:
    """Paragraphs for what was understood, where the job sits and why, where it would
    sit if distance were ignored, the NT window for its class, and the coordinator's
    reason for the day's setting. Requires a ranked, scored job."""
    if scored.needs_human or scored.rank is None or scored.score is None:
        raise ValueError("tenant_answer requires a ranked job")
    job = scored.job

    fault_label = LABELS[job.fault_type.value]
    safety_label = LABELS[job.safety_class.value]
    risk_labels = _health_risk_labels(job)
    if risk_labels:
        risk_items = " ".join(f"{label}." for label in risk_labels)
        risk_sentence = f"We recorded these household health risks. {risk_items}"
    else:
        risk_sentence = "No household health risk factor was recorded for the house."
    understood = (
        f"We understood your report as {fault_label}, classed {safety_label}. {risk_sentence}"
    )

    where_it_sits = (
        f"Your job is ranked {scored.rank} today. This rank weighs {FACTOR_LABELS['urgency']}, "
        f"{FACTOR_LABELS['safety']}, {FACTOR_LABELS['health_risk']} and "
        f"{FACTOR_LABELS['logistics']} together, at the current setting for travel cost."
    )

    without_distance = (
        f"If travel cost were left out of the count, your job would rank {rank_at_lambda0} instead."
    )

    window = (
        f"For a {safety_label} job like yours, the NT policy window is {window_days:g} "
        f"days from the report date."
    )

    reason = f"The coordinator's reason for today's setting: {coordinator_reason}"

    return "\n\n".join([understood, where_it_sits, without_distance, window, reason])
