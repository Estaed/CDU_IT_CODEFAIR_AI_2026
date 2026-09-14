"""Today's per-job decisions split the ranking into four lists (PRD 3.1).

A coordinator accepts a job for today or rejects it; an accepted job is never dropped, even
past capacity, and a job decided "not today" never comes back into To decide that day. The
free places of today's capacity go to the best-ranked undecided jobs.
"""

from dataclasses import dataclass

ACCEPTED = "accepted"
NOT_TODAY = "not_today"


@dataclass(frozen=True)
class Split:
    accepted: list[str]
    to_decide: list[str]
    not_today: list[str]
    backlog: list[str]


def split(ranked_ids: list[str], latest: dict[str, str], capacity: int) -> Split:
    """``latest`` maps a job id to its latest decision today; ``"undone"``, any other value or
    no entry means undecided. Every list keeps rank order."""
    accepted = [job_id for job_id in ranked_ids if latest.get(job_id) == ACCEPTED]
    not_today = [job_id for job_id in ranked_ids if latest.get(job_id) == NOT_TODAY]
    undecided = [job_id for job_id in ranked_ids if latest.get(job_id) not in (ACCEPTED, NOT_TODAY)]
    room = max(capacity - len(accepted), 0)
    return Split(accepted, undecided[:room], not_today, undecided[room:])
