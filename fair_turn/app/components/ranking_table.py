"""Open jobs on a day and the ranking table the board shows (PRD 3.1).

``rows_for`` is pure: it takes scored jobs and returns a frame, so a test can compare it
with ``scoring.rank`` directly.
"""

from dataclasses import replace
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from fair_turn.app import state
from fair_turn.core import audit, capacity_sim, constants, decisions, explain, scoring
from fair_turn.core.batch import HandMove
from fair_turn.core.capacity_sim import Closure
from fair_turn.core.types import Job, SafetyClass, ScoredJob
from fair_turn.data import geography, runtime
from fair_turn.data.artefacts import to_jobs

UNCHANGED = "·"
REVIEW_REQUESTED = "review_requested"
TABLE_HEADER_HEIGHT = 38
TABLE_ROW_HEIGHT = 35
MAX_VISIBLE_TABLE_ROWS = 20
# Column widths in pixels (table geometry, not theme): sized so the decision columns fit the
# list pane at 1440 px and the descriptive ones scroll.
RANK_PX, DELTA_PX, JOB_PX, CLASS_PX, WINDOW_PX = 45, 55, 118, 78, 70
SCORE_PX, FACTORS_PX, COMMUNITY_PX, FAULT_PX = 62, 90, 160, 120


def _runtime_stamp(path: Path) -> tuple[int, int]:
    """``(size, mtime_ns)`` of the runtime file, ``(0, 0)`` when it does not exist."""
    try:
        stat = path.stat()
    except FileNotFoundError:
        return (0, 0)
    return (stat.st_size, stat.st_mtime_ns)


def open_jobs(today: date) -> list[Job]:
    """Jobs reported by ``today`` that are still open after efficiency-first dispatch,
    with coordinator-set fields and extracted intake reports from the runtime file applied.

    Provisional: which jobs are open comes from the toy capacity model run at lam = 1.0
    from the window start to ``today``, standing in for what the contractor's system does
    today (PRD 4). A pilot would read open jobs from intake instead. An Immediate job
    reported on ``today`` stays open although the simulation completes it that day, so the
    coordinator can send it to the make-safe contractor; earlier ones stay closed.
    """
    path = state.get_runtime_path()
    return _open_jobs_cached(today, _runtime_stamp(path), path)


@st.cache_data
def _open_jobs_cached(today: date, runtime_stamp: tuple[int, int], runtime_path: Path):
    """Cached on the day, runtime-file identity and its current size and timestamp."""
    art = state.artefacts()
    records = runtime.read(runtime_path)
    intake = [r for r in records if isinstance(r, runtime.IntakeReport)]
    jobs = to_jobs(art, human_set=runtime.human_set_for(records), intake=intake)
    closures = [
        Closure(
            c["community_id"],
            date.fromisoformat(c["closed_from"]),
            date.fromisoformat(c["closed_to"]),
        )
        for c in art.closures
    ]
    result = capacity_sim.simulate(
        jobs,
        lam=1.0,
        start=constants.WINDOW_START,
        days=(today - constants.WINDOW_START).days + 1,
        closures=closures,
        crews=geography.crews(art.communities),
        jobs_per_crew_day=constants.JOBS_PER_CREW_DAY,
        travel_day_km=constants.TRAVEL_DAY_KM,
        sites=geography.sim_sites(art.communities),
    )
    return [
        j
        for j in jobs
        if j.reported_on <= today
        and (
            result.completed_on[j.job_id] is None
            or (decisions.is_make_safe(j) and j.reported_on == today)
        )
    ]


def capacity(region: str) -> int:
    """Today's job-count capacity: crews for the region times jobs per crew per day; the
    sum over every region for ``state.ALL_REGIONS`` (PRD 6.3)."""
    if region == state.ALL_REGIONS:
        return sum(capacity(r) for r in constants.REGIONS)
    remote = region in constants.REMOTE_REGIONS
    crews = constants.CREWS_PER_REMOTE_REGION if remote else constants.CREWS_TOWN
    return crews * constants.JOBS_PER_CREW_DAY


def apply_hand_moves(ranked: list[ScoredJob], moves) -> list[ScoredJob]:
    """Apply each move in order (take the job out, insert it at ``to_rank``), then renumber.
    A move naming a job that is not in ``ranked`` is ignored."""
    order = list(ranked)
    for move in moves:
        position = next((i for i, s in enumerate(order) if s.job.job_id == move.job_id), None)
        if position is None:
            continue
        item = order.pop(position)
        order.insert(min(max(move.to_rank - 1, 0), len(order)), item)
    return [replace(s, rank=i) for i, s in enumerate(order, start=1)]


def without_moves_for(moves, job_id: str) -> tuple[HandMove, ...]:
    return tuple(m for m in moves if m.job_id != job_id)


def review_requested_ids(records: list[audit.Record], today: date) -> set[str]:
    """Jobs a coordinator sent to the review queue on ``today``."""
    return {
        r.job_id
        for r in records
        if isinstance(r, audit.HumanSet) and r.field == REVIEW_REQUESTED and r.day == today
    }


def _label(value: str) -> str:
    return value.replace("_", " ")


def short_id(job_id: str) -> str:
    """The number a person reads aloud: ``JR-2025-00717`` shows as ``#717``. The full
    registration number stays the identity everywhere else (audit log, tenant lookup)."""
    prefix, _, number = job_id.rpartition("-")
    if not number.isdigit() or not prefix:
        return job_id
    return f"#{int(number)}"


def community_label(community_id: str) -> str:
    """Region words in title case, the pseudonymous code as it is:
    ``CENTRAL AUSTRALIA R-01`` shows as ``Central Australia R-01``."""
    return " ".join(
        word.capitalize() if word.rstrip(",").isalpha() else word
        for word in community_id.split(" ")
    )


def rank_change(places: int) -> str:
    """``places`` is how many places higher the job sits at the current lam."""
    if places > 0:
        return f"▲{places}"
    if places < 0:
        return f"▼{-places}"
    return UNCHANGED


def window_text(job: Job, today: date) -> str:
    """Days used of the NT window, ``3 of 5 d``; the 4 h make-safe window in hours."""
    used = (today - job.reported_on).days
    if job.safety_class is SafetyClass.IMMEDIATE:
        return f"{used} d of {constants.MAKE_SAFE_HOURS} h"
    return f"{used} of {round(scoring.window_days(job))} d"


def rows_for(
    scored: list[ScoredJob],
    other: list[ScoredJob] | None,
    lam: float,
    today: date,
    *,
    baseline: list[ScoredJob] | None = None,
) -> pd.DataFrame:
    """One row per ranked job in ``scored`` (ranked at ``lam``). When ``other`` (the ranking
    at the current lam) is given, a rank-change column compares the two. When ``scored`` is
    itself the current ranking, pass the efficiency-first ranking as ``baseline`` instead."""
    factor_names = list(scored[0].factors) if scored else list(scoring.FACTOR_NAMES)
    other_rank = {s.job.job_id: s.rank for s in other} if other is not None else {}
    baseline_rank = {s.job.job_id: s.rank for s in baseline} if baseline is not None else {}
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
            "window": window_text(job, today),
            "health risk": ", ".join(sorted(_label(f.value) for f in job.health_risk)),
            "days open": days_open,
            "days left in window": round(scoring.window_days(job) - days_open, 1),
            "score": round(s.score, 1),
            "score_bar": float(s.score),
            **{name: s.factors[name] for name in factor_names},
            "why": explain.why_sentence(s, lam),
        }
        if other is not None:
            record["rank change"] = rank_change(s.rank - other_rank[job.job_id])
        elif baseline is not None:
            record["rank change"] = rank_change(baseline_rank.get(job.job_id, s.rank) - s.rank)
        records.append(record)
    columns = [
        "rank",
        "job id",
        "community id",
        "fault type",
        "safety class",
        "window",
        "health risk",
        "days open",
        "days left in window",
        "score",
        "score_bar",
        *factor_names,
        "why",
    ]
    if other is not None or baseline is not None:
        columns.insert(1, "rank change")
    return pd.DataFrame(records, columns=columns)


def table_height(n_rows: int) -> int:
    """Return room for a dataframe header and up to 20 complete rows, avoiding inner scrollbars."""
    return TABLE_HEADER_HEIGHT + TABLE_ROW_HEIGHT * min(max(n_rows, 0), MAX_VISIBLE_TABLE_ROWS)


def column_config(frame: pd.DataFrame) -> dict:
    """Workspace display columns plus progress bars for score factors used by other callers."""
    score_max = max(float(frame["score_bar"].max()), 1.0) if len(frame) else 1.0
    config = {
        "rank": st.column_config.NumberColumn("#", width=RANK_PX),
        "rank change": st.column_config.TextColumn(
            "Δ", width=DELTA_PX, help="Change against efficiency-first"
        ),
        "job_id": st.column_config.TextColumn("Job", width=JOB_PX, pinned=True),
        "community id": st.column_config.TextColumn("Community", width=COMMUNITY_PX),
        "fault type": st.column_config.TextColumn("Fault", width=FAULT_PX),
        "safety class": st.column_config.TextColumn("Class", width=CLASS_PX),
        "window": st.column_config.TextColumn(
            "Window", width=WINDOW_PX, help="Days used of the NT window"
        ),
        "score": st.column_config.NumberColumn("Score", format="%.1f", width=SCORE_PX),
        "score_bar": st.column_config.ProgressColumn(
            "Factors", format="%.1f", min_value=0.0, max_value=score_max, width=FACTORS_PX
        ),
    }
    for name in (column for column in frame.columns if column in scoring.FACTOR_NAMES):
        config[name] = st.column_config.ProgressColumn(
            _label(name),
            min_value=0.0,
            max_value=max(float(frame[name].max()), 1.0) if len(frame) else 1.0,
            format="%.2f",
        )
    return config
