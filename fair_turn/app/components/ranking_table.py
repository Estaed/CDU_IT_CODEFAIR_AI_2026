"""Open jobs on a day and the ranking table the board shows (PRD 3.1).

``rows_for`` is pure: it takes scored jobs and returns a frame, so a test can compare it
with ``scoring.rank`` directly.
"""

from datetime import date

import pandas as pd
import streamlit as st

from fair_turn.app import state
from fair_turn.core import capacity_sim, constants, explain, scoring
from fair_turn.core.capacity_sim import Closure, Site
from fair_turn.core.types import Job, ScoredJob
from fair_turn.data.artefacts import to_jobs

UNCHANGED = "·"


@st.cache_data
def open_jobs(today: date) -> list[Job]:
    """Jobs reported by ``today`` that are still open after efficiency-first dispatch.

    Provisional: which jobs are open comes from the toy capacity model run at lam = 1.0
    from the window start to ``today``, standing in for what the contractor's system does
    today (PRD 4). A pilot would read open jobs from intake instead.
    """
    art = state.artefacts()
    jobs = to_jobs(art)
    sites = {
        cid: Site(row["region"], float(row["km_to_base"])) for cid, row in art.communities.items()
    }
    closures = [
        Closure(
            c["community_id"],
            date.fromisoformat(c["closed_from"]),
            date.fromisoformat(c["closed_to"]),
        )
        for c in art.closures
    ]
    crews = {region: constants.CREWS_PER_REMOTE_REGION for region in constants.REMOTE_REGIONS}
    crews[constants.TOWN_REGION] = constants.CREWS_TOWN
    result = capacity_sim.simulate(
        jobs,
        lam=1.0,
        start=constants.WINDOW_START,
        days=(today - constants.WINDOW_START).days + 1,
        closures=closures,
        crews_per_region=crews,
        jobs_per_crew_day=constants.JOBS_PER_CREW_DAY,
        travel_day_km=constants.TRAVEL_DAY_KM,
        sites=sites,
    )
    return [j for j in jobs if j.reported_on <= today and result.completed_on[j.job_id] is None]


def _label(value: str) -> str:
    return value.replace("_", " ")


def rank_change(places: int) -> str:
    """``places`` is how many places higher the job sits at the current lam."""
    if places > 0:
        return f"▲{places}"
    if places < 0:
        return f"▼{-places}"
    return UNCHANGED


def rows_for(
    scored: list[ScoredJob], other: list[ScoredJob] | None, lam: float, today: date
) -> pd.DataFrame:
    """One row per ranked job in ``scored`` (ranked at ``lam``). When ``other`` (the ranking
    at the current lam) is given, a rank-change column compares the two."""
    factor_names = list(scored[0].factors) if scored else list(scoring.FACTOR_NAMES)
    other_rank = {s.job.job_id: s.rank for s in other} if other is not None else {}
    records = []
    for s in scored:
        job = s.job
        days_open = (today - job.reported_on).days
        record = {
            "rank": s.rank,
            "job id": job.job_id,
            "community id": job.community_id,
            "fault type": _label(job.fault_type.value),
            "safety class": job.safety_class.value,
            "health risk": ", ".join(sorted(_label(f.value) for f in job.health_risk)),
            "days open": days_open,
            "days left in window": round(scoring.window_days(job) - days_open, 1),
            "score": round(s.score, 1),
            **{name: s.factors[name] for name in factor_names},
            "why": explain.why_sentence(s, lam),
        }
        if other is not None:
            record["rank change"] = rank_change(s.rank - other_rank[job.job_id])
        records.append(record)
    columns = [
        "rank",
        "job id",
        "community id",
        "fault type",
        "safety class",
        "health risk",
        "days open",
        "days left in window",
        "score",
        *factor_names,
        "why",
    ]
    if other is not None:
        columns.insert(1, "rank change")
    return pd.DataFrame(records, columns=columns)


def column_config(frame: pd.DataFrame) -> dict:
    """A progress bar per factor column, scaled to the largest value in the frame."""
    factors = [c for c in frame.columns if c in scoring.FACTOR_NAMES]
    return {
        name: st.column_config.ProgressColumn(
            _label(name),
            min_value=0.0,
            max_value=max(float(frame[name].max()), 1.0) if len(frame) else 1.0,
            format="%.2f",
        )
        for name in factors
    }
