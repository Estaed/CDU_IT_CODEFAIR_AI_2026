"""Signed or proposed job ids -> visit-plan stops (PRD 3.3), shared by the visit plan page and
the workspace's crew reach line, so both plan a list the same way."""

from collections.abc import Mapping, Sequence
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


def reach_line(job_ids: Sequence[str], jobs_by_id: Mapping[str, Job], today: date) -> str:
    """The workspace caption: how many of today's proposed jobs no crew within reach can take,
    planned exactly as the visit plan would plan the list if it were signed."""
    planned = visit_plan.plan(
        0, stops(job_ids, jobs_by_id, today)[0], geography.crews(state.artefacts().communities)
    )
    count = planned.out_of_reach
    if count == 0:
        return "Crew reach: every job on today's list has a crew within reach."
    verb = "has" if count == 1 else "have"
    return (
        f"Crew reach: {count} of today's {len(job_ids)} jobs {verb} no crew within reach "
        "with a free slot."
    )
