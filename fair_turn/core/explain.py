"""Two texts assembled from ``ScoredJob`` factors: the coordinator's rank sentence and the
tenant's answer (PRD sections 3.1, 3.4, 7). Both read enum labels and numbers only, so they
change with ``lam`` and never depend on any model-produced string; the only free text the
tenant answer carries is the coordinator's recorded reason.
"""

from dataclasses import dataclass
from typing import Literal, Protocol, get_args

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


# --- the tenant answer (PRD 3.4, wireframes §7) ---------------------------------------------

TenantState = Literal["ranked", "review", "backlog", "unsigned", "manual", "superseded", "unknown"]
TENANT_STATES: tuple[TenantState, ...] = get_args(TenantState)

QUESTIONS = (
    "What did we understand from your report?",
    "Where is your repair in the queue, and why?",
    "What happens next?",
    "Who can you ask?",
)

# What a registration number looks like, shown on the empty page and for an unknown id.
JOB_ID_PREFIX = "JR-2025-"
JOB_ID_EXAMPLE = f"{JOB_ID_PREFIX}00001"

# The policy source named when no indexed passage is available for the job's key.
DEFAULT_POLICY_SOURCE = "NT fact sheet FS17, Repairs and maintenance, October 2025"

# Plain words for a reordered visit when the recorded plan change carries no reason text.
DEFAULT_VISIT_REASON = (
    "the coordinator accepted a shorter drive that keeps the repairs on the same day"
)

MISSING_FIELD_SENTENCES = {
    "fault_type": "We could not read what is broken from the report.",
    "safety_class": "We could not read how urgent it is.",
}

_ORDINAL_WORDS = ("first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth")


@dataclass(frozen=True)
class Block:
    question: str
    paragraphs: tuple[str, ...]


@dataclass(frozen=True)
class TenantAnswer:
    blocks: tuple[Block, ...]

    @property
    def text(self) -> str:
        """Every paragraph of every block, joined; what the wording lint reads."""
        return "\n\n".join(p for block in self.blocks for p in block.paragraphs)


class PolicySource(Protocol):
    title: str
    section: str
    effective_date: str


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _ordinal_word(n: int) -> str:
    return _ORDINAL_WORDS[n - 1] if 1 <= n <= len(_ORDINAL_WORDS) else _ordinal(n)


def _understood(job: Job | None, missing_fields: tuple[str, ...]) -> list[str]:
    if job is None:
        return ["We could not find that job number."]
    sentences = []
    if job.fault_type is not None:
        sentences.append(f"We read your report as {LABELS[job.fault_type.value]}.")
    if job.safety_class is not None:
        label = LABELS[job.safety_class.value]
        sentences.append(f"We class it as {_article(label)} {label} repair.")
    sentences += [MISSING_FIELD_SENTENCES[f] for f in missing_fields]
    risk_labels = _health_risk_labels(job)
    if risk_labels:
        items = " ".join(f"We noted {label}." for label in risk_labels)
        risk = f"These count as {FACTOR_LABELS['health_risk']}. {items}"
    else:
        risk = f"We did not note any {FACTOR_LABELS['health_risk']} for your home."
    return [" ".join(sentences), risk]


def _why(rank_at_lambda0: int | None, lam: float | None) -> list[str]:
    paragraphs = [
        f"The number comes from four things: {FACTOR_LABELS['urgency']}, "
        f"{FACTOR_LABELS['safety']}, {FACTOR_LABELS['health_risk']} and "
        f"{FACTOR_LABELS['logistics']}."
    ]
    if lam is not None:
        clause = _logistics_clause(lam)
        paragraphs[0] += f" {clause[0].upper()}{clause[1:]}."
    if rank_at_lambda0 is not None:
        paragraphs.append(
            f"If distance did not count, your repair would be number {rank_at_lambda0}. "
            f"That is the same formula with {FACTOR_LABELS['logistics']} left out."
        )
    return paragraphs


def _visit(visit_order: tuple[int, str] | None) -> list[str]:
    if visit_order is None:
        return []
    position, reason = visit_order
    words = reason.strip().rstrip(".") or DEFAULT_VISIT_REASON
    return [f"The crew will visit it {_ordinal_word(position)} on the day, because {words}."]


def _where(
    state: TenantState,
    scored: ScoredJob | None,
    rank_at_lambda0: int | None,
    lam: float | None,
    signed_rank: int | None,
    visit_order: tuple[int, str] | None,
    decision_version: int | None,
) -> list[str]:
    draft_rank = scored.rank if scored is not None else None
    if state == "unknown":
        return [
            "Check the number and try again.",
            f"A job number starts with {JOB_ID_PREFIX} and ends with five digits, "
            f"like {JOB_ID_EXAMPLE}. You can find it on your report receipt.",
        ]
    if state == "review":
        return [
            "A person is checking your report before it is ranked.",
            "Your repair does not have a place in the queue yet.",
        ]
    if state == "manual":
        return [
            "Your home is reached by air or barge, not by a road crew.",
            "A person is arranging freight for your repair. There is no date for it yet.",
        ]
    if state == "unsigned":
        place = [
            "Today's list is still a draft. The coordinator has not signed it, "
            "so we cannot promise a place yet."
        ]
        if draft_rank is not None:
            place.append(f"On the draft, your repair is number {draft_rank}.")
        return place + _why(rank_at_lambda0, lam)
    if state == "backlog":
        number = signed_rank if signed_rank is not None else draft_rank
        return [
            f"Your repair is number {number} in the queue, but it is not on today's list.",
            "It waits for the next free crew day. There is no visit date for it yet.",
            *_why(rank_at_lambda0, lam),
        ]
    # ranked and superseded
    if signed_rank is not None:
        place = [f"Your repair is number {signed_rank} on the signed list."]
    else:
        place = [f"Your repair is number {draft_rank} on today's draft list."]
    if state == "superseded":
        place.insert(0, f"This answer uses the signed list version {decision_version}.")
    return place + _visit(visit_order) + _why(rank_at_lambda0, lam)


def _next(
    state: TenantState,
    job: Job | None,
    policy: PolicySource | None,
    visit_order: tuple[int, str] | None,
) -> list[str]:
    if job is None:
        return ["We can tell you what happens next once we find your job number."]
    if job.safety_class is None:
        return [
            "We can tell you the NT policy target once a person has read your report.",
            "We do not have a visit date yet.",
        ]
    label = LABELS[job.safety_class.value]
    if job.safety_class is SafetyClass.IMMEDIATE:
        target = (
            f"For an {label} repair like yours, the NT policy target is to make it safe "
            f"within {constants.MAKE_SAFE_HOURS} hours of the report."
        )
    else:
        days = constants.RESPONSE_BUSINESS_DAYS[(job.safety_class.value, job.is_remote)]
        target = (
            f"For {_article(label)} {label} repair like yours, the NT policy target is "
            f"{days} business days from the report date."
        )
    target += " That is a policy target, not a promised visit time."
    if visit_order is not None and state in ("ranked", "superseded"):
        date_line = "The crew plans to visit on the day of the signed list."
    else:
        date_line = "We do not have a visit date yet."
    if policy is not None:
        source = (
            f"Policy source: {policy.title}, {policy.section}, effective {policy.effective_date}."
        )
    else:
        source = f"Policy source: {DEFAULT_POLICY_SOURCE}."
    return [target, date_line, source]


def _ask(state: TenantState, coordinator_reason: str | None) -> list[str]:
    if state == "unknown":
        return ["Your Community Housing Officer can help you find your job number."]
    officer = "Your Community Housing Officer can look up this job for you."
    if coordinator_reason:
        return [officer, f"The coordinator's reason for today's setting: {coordinator_reason}"]
    return [officer, "The coordinator has not signed today's setting yet."]


def tenant_answer(
    *legacy,
    state: TenantState | None = None,
    scored: ScoredJob | None = None,
    rank_at_lambda0: int | None = None,
    window_days: float | None = None,
    coordinator_reason: str | None = None,
    lam: float | None = None,
    signed_rank: int | None = None,
    visit_order: tuple[int, str] | None = None,
    policy: PolicySource | None = None,
    decision_version: int | None = None,
    missing_fields: tuple[str, ...] = (),
) -> TenantAnswer:
    """Four question-headed blocks, in ``QUESTIONS`` order, for one tenant state.

    ``window_days`` is accepted for the Phase 1 form and not read: the window is stated in
    the class's own unit from ``constants``. The Phase 1 positional form
    ``tenant_answer(scored, rank_at_lambda0, window_days, coordinator_reason, lam)`` still
    works for one release and answers in the ``ranked`` state."""
    if legacy:
        if len(legacy) != 5 or state is not None:
            raise TypeError("the positional form takes exactly the five Phase 1 arguments")
        scored, rank_at_lambda0, window_days, coordinator_reason, lam = legacy
    if state is None:
        state = "ranked"
    if state not in TENANT_STATES:
        raise ValueError(f"unknown tenant state: {state}")
    ranked_like = state in ("ranked", "superseded", "backlog", "unsigned")
    if ranked_like and (scored is None or scored.needs_human or scored.rank is None):
        raise ValueError(f"tenant_answer in the {state} state requires a ranked job")
    if state == "superseded" and decision_version is None:
        raise ValueError("a superseded answer names the signed list version it uses")
    if state != "unknown" and scored is None:
        raise ValueError(f"tenant_answer in the {state} state requires a job")

    job = scored.job if scored is not None and state != "unknown" else None
    sections = (
        _understood(job, missing_fields if state == "review" else ()),
        _where(state, scored, rank_at_lambda0, lam, signed_rank, visit_order, decision_version),
        _next(state, job, policy, visit_order),
        _ask(state, coordinator_reason),
    )
    return TenantAnswer(
        tuple(
            Block(question, tuple(p for p in paragraphs if p))
            for question, paragraphs in zip(QUESTIONS, sections, strict=True)
        )
    )
