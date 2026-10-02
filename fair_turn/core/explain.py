"""Every sentence the product says about a plan, built from templates over typed values.

Nothing here reads model text. Tenant sentences stay short (``wording.check`` holds them to
reading grade 7) and name the policy they come from.
"""

from dataclasses import dataclass
from datetime import date

from fair_turn.core import constants, scoring, weekly
from fair_turn.core.types import FaultType, HealthRiskFactor, Job, SafetyClass

POLICY_SOURCE = "NT fact sheet FS17, Repairs and maintenance, October 2025"
JOB_ID_PREFIX = "JR-2025-"
JOB_ID_EXAMPLE = f"{JOB_ID_PREFIX}00001"

FAULT_WORDS = {
    FaultType.ELECTRICAL: "electrics",
    FaultType.PLUMBING_WATER: "water or plumbing",
    FaultType.SEWER_DRAINAGE: "sewer or drains",
    FaultType.COOLING: "cooling",
    FaultType.HOT_WATER: "hot water",
    FaultType.ROOF_STRUCTURE: "roof or structure",
    FaultType.DOORS_LOCKS_SECURITY: "doors, locks or security",
    FaultType.STOVE_COOKING: "stove or cooking",
    FaultType.PESTS: "pests",
    FaultType.OTHER: "another repair",
}

HEALTH_WORDS = {
    HealthRiskFactor.INFANT_OR_YOUNG_CHILD: "a young child lives in the house",
    HealthRiskFactor.ELDERLY: "an older person lives in the house",
    HealthRiskFactor.PREGNANCY_OR_CHRONIC_CONDITION: "someone is pregnant or has a long-term "
    "health condition",
    HealthRiskFactor.OVERCROWDING: "many people share the house",
    HealthRiskFactor.EXTREME_HEAT_EXPOSURE: "the house is very hot",
    HealthRiskFactor.NO_WATER_OR_SANITATION: "the house has no working water or toilet",
}

SETTING_MEANING = {
    "Efficiency first": "every repair counts the same, and days spent driving count in full",
    "Balanced": "a repair counts for more when it is past the NT time limit, serious, or in "
    "a house with a health risk, and driving days count half",
    "Most overdue first": "a repair counts by how far past the NT time limit it is, how "
    "serious it is and who lives there, and driving days are not counted against a trip",
}

WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")


def days(n: float) -> str:
    whole = f"{n:g}"
    return f"{whole} day" if n == 1 else f"{whole} days"


def window_sentence(job: Job) -> str:
    """The NT time limit for this job, in the policy's own unit."""
    if job.safety_class is SafetyClass.IMMEDIATE:
        return f"NT policy says an emergency is made safe within {constants.MAKE_SAFE_HOURS} hours."
    place = "remote" if job.is_remote else "town"
    limit = constants.RESPONSE_BUSINESS_DAYS[(job.safety_class.value, job.is_remote)]
    return (
        f"NT policy says {job.safety_class.value} repairs in a {place} home are done "
        f"within {limit} business days."
    )


def wait_sentence(job: Job, today: date) -> str:
    """How far into, or past, its time limit a job is on ``today``."""
    if job.safety_class is SafetyClass.IMMEDIATE:
        if today > job.reported_on:
            return "It was reported before today, so it is past that time limit."
        return "The time limit started when you reported it."
    used = int(scoring.window_used(job, today))
    limit = int(scoring.window_days(job))
    if used > limit:
        return f"It is {_business_days(used - limit)} past that time limit."
    if used == 0:
        return "The time limit started when you reported it."
    return f"It is {_business_days(used)} into that time limit."


def _business_days(n: int) -> str:
    return "1 business day" if n == 1 else f"{n} business days"


# --- the coordinator's view ----------------------------------------------------------------


def trip_line(trip: weekly.Trip, jobs: dict[str, Job], today: date) -> str:
    """One trip in plain words: repairs, how many are overdue, and the days it costs."""
    overdue = sum(scoring.is_overdue(jobs[j], today) for j in trip.job_ids)
    repairs = f"{len(trip.job_ids)} repairs" if len(trip.job_ids) != 1 else "1 repair"
    late = f", {overdue} past the NT time limit" if overdue else ""
    if trip.is_town:
        return f"{repairs}{late} · {days(trip.work_days)} in town"
    return f"{repairs}{late} · {days(trip.travel_days)} driving + {days(trip.work_days)} work"


def waiting_line(waiting: weekly.Waiting, plan: weekly.WeekPlan) -> str:
    """Why a community gets no trip, or only part of one, this week, in a few words."""
    if waiting.reason == weekly.CLOSED:
        return "Access closed most of the week"
    if waiting.reason == weekly.DROPPED:
        return "Taken out by you"
    if waiting.reason == weekly.TRIP_FULL:
        return f"Partly planned: the trip carries {waiting.trip_repairs}"
    if waiting.reason == weekly.NO_ROOM:
        return f"Needs {days(waiting.trip_days)} in a row; no crew had them left"
    cut = plan.last_priority(waiting.base)
    if waiting.priority is None or cut is None:
        return "Below the cut"
    added = any(t.added and t.base == waiting.base for t in plan.trips)
    after = " after your added trip" if added else ""
    return f"Below the cut{after}: {waiting.priority:.1f} against {cut:.1f}"


# --- the tenant answer ---------------------------------------------------------------------


@dataclass(frozen=True)
class TenantFacts:
    """What the page knows about one job, gathered by the app; every value is typed."""

    job: Job
    today: date  # the planning Monday
    base: str
    is_town: bool
    setting_name: str
    setting: float
    signed_by: str | None  # None while the week's plan is a proposal
    signed_reason: str | None
    done_on: date | None = None  # finished before this week
    trip: weekly.Trip | None = None  # this week's trip that carries the job
    start_day: float | None = None  # crew-day offset the trip starts
    waiting: weekly.Waiting | None = None  # why it has no trip this week
    travel_days: float = 0.0  # there and back, for a trip to the job's community
    reopens_on: date | None = None  # when closed access opens again
    in_plan_under: tuple[str, ...] = ()  # the named settings under which it has a trip
    missing_fields: tuple[str, ...] = ()  # required fields nobody has read yet


@dataclass(frozen=True)
class Block:
    question: str
    paragraphs: tuple[str, ...]


@dataclass(frozen=True)
class TenantAnswer:
    headline: str
    blocks: tuple[Block, ...]

    @property
    def text(self) -> str:
        """Every sentence, joined; what the wording lint reads."""
        return "\n\n".join([self.headline, *(p for b in self.blocks for p in b.paragraphs)])


def _read(f: TenantFacts) -> list[str]:
    job = f.job
    if f.missing_fields:
        missing = " and ".join(
            {"fault_type": "what is broken", "safety_class": "how urgent it is"}[m]
            for m in f.missing_fields
        )
        return [
            f"We could not read {missing} from your report.",
            "A person is reading it now. It joins the crew plan once they have.",
        ]
    lines = [
        f"Your report is about {FAULT_WORDS[job.fault_type]}. "
        f"We read it as {job.safety_class.value}."
    ]
    for factor in sorted(job.health_risk):
        lines.append(f"We also read that {HEALTH_WORDS[factor]}.")
    return lines


def _when(f: TenantFacts) -> str:
    if f.start_day is None:
        return "this week"
    day = WEEKDAYS[min(int(f.start_day), len(WEEKDAYS) - 1)]
    return f"this week, from {day}"


def _repairs(n: int) -> str:
    return "1 repair" if n == 1 else f"{n} repairs"


def _first(f: TenantFacts) -> str:
    """Which repairs came first under the setting, in words true for that setting."""
    if f.setting <= 0:
        return "Trips that fixed the most repairs for each crew day came first."
    return (
        "Trips with the most need for each crew day came first: repairs past the time "
        "limit, serious repairs, and houses with a health risk."
    )


def _why(f: TenantFacts) -> list[str]:
    job, waiting = f.job, f.waiting
    lines = [window_sentence(job), wait_sentence(job, f.today)]
    if f.trip is not None or waiting is None:
        return lines
    setting = (
        f'This week the setting is "{f.setting_name}": '
        f"{SETTING_MEANING.get(f.setting_name, 'a mix of the named settings')}."
    )
    if waiting.reason == weekly.CLOSED:
        until = f" until {f.reopens_on:%d %B}" if f.reopens_on else ""
        lines.append(
            f"Access to your community is closed{until}, for most of this week, so no trip "
            "was planned."
        )
    elif waiting.reason == weekly.DROPPED:
        lines.append("The coordinator took your community's trip out of this week's plan.")
    elif waiting.reason == weekly.TRIP_FULL:
        order = "were reported earlier" if f.setting <= 0 else "had more need under this setting"
        lines.append(
            f"A crew is going to your community this week, with time for "
            f"{_repairs(waiting.trip_repairs)}. Other repairs there {order}."
        )
    elif f.is_town:
        lines.append(
            f"The {f.base} crews have more repairs than days this week, and others came first."
        )
        lines += [setting, _first(f)]
    elif waiting.reason == weekly.NO_ROOM:
        lines.append(
            f"A trip to your community takes {days(waiting.trip_days)} of a crew's week, "
            f"with {days(f.travel_days)} of driving there and back. By the time it came up, "
            f"no {f.base} crew had that many days left."
        )
    else:
        if f.travel_days:
            lines.append(
                f"A trip to your community takes {days(f.travel_days)} of driving, there and "
                f"back, to fix {_repairs(waiting.trip_repairs)}."
            )
        lines += [setting, _first(f) + " The days ran out before your trip."]
    others = [name for name in f.in_plan_under if name != f.setting_name]
    if others:
        lines.append(f'Under "{others[0]}", a crew would come to you this week.')
    elif waiting.reason in (weekly.OUTRANKED, weekly.NO_ROOM):
        lines.append("None of the three named settings would plan your repair this week.")
    return lines


def _next(f: TenantFacts) -> list[str]:
    if f.trip is not None:
        return ["The crew will contact you before they come."]
    lines = ["The plan is made again every Monday."]
    if f.setting <= 0:
        lines.append(
            "Under this setting, waiting longer does not move a repair up. The coordinator can "
            "change the setting."
        )
    elif scoring.urgency(f.job, f.today) < scoring.URGENCY_CAP:
        lines.append("Each week your repair waits, it counts for more in the next plan.")
    else:
        lines.append("Your repair already counts as much as waiting can make it.")
    return lines


def _who(f: TenantFacts) -> list[str]:
    officer = "Your Community Housing Officer can look up this repair with you."
    if f.signed_by is None:
        return ["This week's plan is not signed yet. It can still change.", officer]
    reason = f" Their reason: {f.signed_reason}" if f.signed_reason else ""
    return [f"A person signed this week's plan: {f.signed_by}.{reason}", officer]


def tenant_answer(f: TenantFacts) -> TenantAnswer:
    """Plain answers to the four questions a tenant asks about one repair."""
    job = f.job
    if f.done_on is not None:
        if job.safety_class is SafetyClass.IMMEDIATE:
            return TenantAnswer(
                headline=f"This emergency was made safe on {f.done_on:%d %B %Y}.",
                blocks=(
                    Block(
                        "What happens next?",
                        ("Any repair it still needs is a separate job.", _who(f)[-1]),
                    ),
                ),
            )
        return TenantAnswer(
            headline=f"This repair was done on {f.done_on:%d %B %Y}.",
            blocks=(Block("Who can you ask?", (_who(f)[-1],)),),
        )
    if job.reported_on > f.today:
        return TenantAnswer(
            headline="Your report came in after this week's plan was made.",
            blocks=(
                Block("What happens next?", ("It joins the plan made next Monday.",)),
                Block("Who can you ask?", (_who(f)[-1],)),
            ),
        )
    if f.missing_fields:
        return TenantAnswer(
            headline="A person is reading your report.",
            blocks=(
                Block("What did we read in your report?", tuple(_read(f))),
                Block("Who can you ask?", tuple(_who(f))),
            ),
        )
    if job.safety_class is SafetyClass.IMMEDIATE:
        return TenantAnswer(
            headline="This is an emergency. It goes to the emergency make-safe team.",
            blocks=(
                Block("What did we read in your report?", tuple(_read(f))),
                Block(
                    "What happens next?",
                    (window_sentence(job), "It is not part of the weekly crew plan."),
                ),
            ),
        )
    if f.trip is not None:
        who = f"in {f.base}" if f.is_town else f"from {f.base} to your community"
        headline = f"Yes. A crew is planned {who} {_when(f)}."
    else:
        headline = "Not this week."
    return TenantAnswer(
        headline=headline,
        blocks=(
            Block("What did we read in your report?", tuple(_read(f))),
            Block("Why is it planned this way?", tuple(_why(f))),
            Block("What happens next?", tuple(_next(f))),
            Block("Who decided?", tuple(_who(f))),
        ),
    )
