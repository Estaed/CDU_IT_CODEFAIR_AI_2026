"""Today's per-job decisions split the ranking into four lists (PRD 3.1).

A coordinator accepts a job for today or rejects it; an accepted job is never dropped, even
past capacity, and a job decided "not today" never comes back into To decide that day. The
free places of today's capacity go to the best-ranked undecided jobs. An Immediate job goes to
the emergency make-safe contractor and never enters these lists.
"""

from collections.abc import Collection
from dataclasses import dataclass

from fair_turn.core.types import Job, SafetyClass

ACCEPTED = "accepted"
NOT_TODAY = "not_today"


@dataclass(frozen=True)
class Split:
    accepted: list[str]
    to_decide: list[str]
    not_today: list[str]
    backlog: list[str]


def split(
    ranked_ids: list[str],
    latest: dict[str, str],
    capacity: int,
    planned: Collection[str] | None = None,
) -> Split:
    """``latest`` maps a job id to its latest decision today; ``"undone"``, any other value or
    no entry means undecided. Every list keeps rank order. With ``planned`` (the jobs a crew
    can take today, ``visit_plan.fill_today``), To decide is the undecided jobs in it and the
    rest wait in the backlog; without it, the first ``capacity`` places go to the best-ranked
    undecided jobs."""
    accepted = [job_id for job_id in ranked_ids if latest.get(job_id) == ACCEPTED]
    not_today = [job_id for job_id in ranked_ids if latest.get(job_id) == NOT_TODAY]
    undecided = [job_id for job_id in ranked_ids if latest.get(job_id) not in (ACCEPTED, NOT_TODAY)]
    if planned is not None:
        on = set(planned)
        return Split(
            accepted,
            [job_id for job_id in undecided if job_id in on],
            not_today,
            [job_id for job_id in undecided if job_id not in on],
        )
    room = max(capacity - len(accepted), 0)
    return Split(accepted, undecided[:room], not_today, undecided[room:])


def is_make_safe(job: Job) -> bool:
    """An Immediate job with every required field goes to the emergency make-safe contractor,
    not into the crew ranking (PRD 3.1, 6.3)."""
    return not job.needs_human and job.safety_class is SafetyClass.IMMEDIATE
