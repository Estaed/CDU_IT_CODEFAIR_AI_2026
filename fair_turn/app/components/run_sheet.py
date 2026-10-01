"""Signed or proposed job ids -> visit-plan stops (PRD 3.3), shared by the visit plan page and
the workspace's crew reach line, so both plan a list the same way."""

from collections import Counter
from collections.abc import Collection, Mapping, Sequence
from datetime import date

from fair_turn.app import state
from fair_turn.core import visit_plan
from fair_turn.core.types import Job
from fair_turn.data import geography


def _stop_access(road_access: str) -> str:
    return "air" if road_access == "barge_or_air" else "road"


def stops(
    job_ids: Sequence[str], jobs_by_id: Mapping[str, Job], today: date
) -> tuple[list[visit_plan.Stop], list[str]]:
    """One stop per job id still in ``jobs_by_id``, ranked by list position, and the ids that
    are no longer open."""
    art = state.artefacts()
    closed_today = {
        c["community_id"]
        for c in art.closures
        if c["closed_from"] <= today.isoformat() <= c["closed_to"]
    }
    result: list[visit_plan.Stop] = []
    missing: list[str] = []
    for rank, job_id in enumerate(job_ids, start=1):
        job = jobs_by_id.get(job_id)
        if job is None:
            missing.append(job_id)
            continue
        community = art.communities[job.community_id]
        result.append(
            visit_plan.Stop(
                job_id=job.job_id,
                community_id=job.community_id,
                region=community["region"],
                lat=float(community["lat"]),
                lon=float(community["lon"]),
                access=_stop_access(community["road_access"]),
                road_open=job.community_id not in closed_today,
                signed_rank=rank,
                road_factor=geography.ROAD_FACTORS[community["road_access"]],
            )
        )
    return result, missing


WAIT_LABELS = {
    visit_plan.NO_FREE_SLOT: "every crew that reaches them is full",
    visit_plan.NO_REACH: "no crew reaches them in a day",
    visit_plan.ROAD_CLOSED: "road closed",
}


def today_ids(
    ranked_ids: Sequence[str],
    jobs_by_id: Mapping[str, Job],
    today: date,
    starts: Mapping[str, tuple[float, float]],
    keep: Collection[str] = (),
) -> tuple[list[str], dict[str, str]]:
    """``visit_plan.fill_today`` over a ranked id list: the jobs the crews can take today,
    from where they are this morning, and why each other job waits."""
    proposal, _ = stops(ranked_ids, jobs_by_id, today)
    crews = geography.crews(state.artefacts().communities)
    return visit_plan.fill_today(proposal, crews, starts, keep)


def wait_line(waiting: Mapping[str, str]) -> str:
    """The workspace caption under the effect line: why the jobs off today's list wait."""
    if not waiting:
        return "Crews: every open job fits a crew today."
    counts = Counter(waiting.values())
    parts = ", ".join(
        f"{counts[reason]} {label}" for reason, label in WAIT_LABELS.items() if counts[reason]
    )
    return (
        "Crews: today's list is what the crews can take from where they are this morning. "
        f"{len(waiting)} more jobs wait: {parts}."
    )
