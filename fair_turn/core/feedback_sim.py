"""Feedback-loop simulation: reporting that fades where reports go unserved (PRD section 3.5).

Week by week, each community's reports are thinned by a multiplier
``m = max(REPORTING_FLOOR, 1 - decay * unserved_share)``, where ``unserved_share`` is the
share of its reports from the previous ``LOOKBACK_WEEKS`` weeks still open when the week
starts. ``decay`` is a labelled assumption, not a fitted parameter; no published estimate
exists. Thinning is a hash of the seed and ``job_id``, so no RNG state is carried.

The capacity model is causal (a job reported later never changes an earlier day), so the
state at the start of week ``w`` is a ``capacity_sim.simulate`` run over the weeks before it
with the reports admitted so far. The final run over the whole window plus
``COMPLETION_TAIL_DAYS`` with every admitted report gives the weekly series; reporting stops
at the window end, only completion continues. With ``decay = 0`` every report is admitted and
that run is the plain capacity run over the same horizon exactly.
"""

import hashlib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, timedelta
from statistics import median

from fair_turn.core import capacity_sim, constants
from fair_turn.core.capacity_sim import Closure, SimResult, Site
from fair_turn.core.types import Job

REPORTING_FLOOR = 0.2  # a community never stops reporting entirely
LOOKBACK_WEEKS = 4
WEEK_DAYS = 7
# Crews keep working past the window so late reports are observed to completion; censoring
# at the window end caps a last-week wait near 7 days and collapses the late-week gap.
COMPLETION_TAIL_DAYS = 28


@dataclass
class WeeklySeries:
    week_start: list[date]
    reports_town: list[int]
    reports_remote: list[int]
    median_wait_town: list[float | None]  # reports made that week; censored at horizon end
    median_wait_remote: list[float | None]
    gap: list[float | None]  # remote median minus town median
    sim: SimResult  # the window-plus-tail capacity run over the admitted reports


def _crews() -> dict[str, int]:
    crews = {region: constants.CREWS_PER_REMOTE_REGION for region in constants.REMOTE_REGIONS}
    crews[constants.TOWN_REGION] = constants.CREWS_TOWN
    return crews


def _keep_draw(job_id: str, seed: int) -> float:
    """A uniform value in [0, 1) fixed by the seed and the job id."""
    digest = hashlib.sha256(f"{seed}:{job_id}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def _simulate(
    jobs: list[Job],
    lam: float,
    days: int,
    closures: list[Closure],
    communities: Mapping[str, Site],
) -> SimResult:
    return capacity_sim.simulate(
        jobs,
        lam,
        constants.WINDOW_START,
        days,
        closures,
        _crews(),
        constants.JOBS_PER_CREW_DAY,
        constants.TRAVEL_DAY_KM,
        communities,
    )


def _multipliers(
    admitted: list[Job], state: SimResult, week_start: date, decay: float
) -> dict[str, float]:
    since = week_start - timedelta(days=LOOKBACK_WEEKS * WEEK_DAYS)
    reported: dict[str, int] = {}
    unserved: dict[str, int] = {}
    for j in admitted:
        if j.needs_human or not since <= j.reported_on < week_start:
            continue
        reported[j.community_id] = reported.get(j.community_id, 0) + 1
        if state.completed_on[j.job_id] is None:
            unserved[j.community_id] = unserved.get(j.community_id, 0) + 1
    return {
        cid: max(REPORTING_FLOOR, 1 - decay * unserved.get(cid, 0) / n)
        for cid, n in reported.items()
    }


def _median(values: list[int]) -> float | None:
    return float(median(values)) if values else None


def run(
    labels: list[Job],
    communities: Mapping[str, Site],
    lam: float,
    decay: float,
    seed: int,
    closures: Iterable[Closure] = (),
) -> WeeklySeries:
    """Replay the window week by week at ``lam`` with reporting decay ``decay``."""
    closures = list(closures)
    start, days = constants.WINDOW_START, constants.WINDOW_DAYS
    weeks = -(-days // WEEK_DAYS)
    admitted: list[Job] = []
    for w in range(weeks):
        week_start = start + timedelta(days=w * WEEK_DAYS)
        week_end = week_start + timedelta(days=WEEK_DAYS)
        week_jobs = [j for j in labels if week_start <= j.reported_on < week_end]
        if decay and admitted:
            state = _simulate(admitted, lam, w * WEEK_DAYS, closures, communities)
            m = _multipliers(admitted, state, week_start, decay)
            week_jobs = [
                j for j in week_jobs if _keep_draw(j.job_id, seed) < m.get(j.community_id, 1.0)
            ]
        admitted.extend(week_jobs)

    horizon = days + COMPLETION_TAIL_DAYS
    sim = _simulate(admitted, lam, horizon, closures, communities)
    end = start + timedelta(days=horizon)
    series = WeeklySeries([], [], [], [], [], [], sim)
    for w in range(weeks):
        week_start = start + timedelta(days=w * WEEK_DAYS)
        week_end = week_start + timedelta(days=WEEK_DAYS)
        week_jobs = [j for j in admitted if week_start <= j.reported_on < week_end]
        waits: dict[bool, list[int]] = {True: [], False: []}
        for j in week_jobs:
            if j.needs_human:
                continue
            wait = sim.wait_days[j.job_id]
            waits[j.is_remote].append(wait if wait is not None else (end - j.reported_on).days)
        remote, town = _median(waits[True]), _median(waits[False])
        series.week_start.append(week_start)
        series.reports_town.append(sum(not j.is_remote for j in week_jobs))
        series.reports_remote.append(sum(j.is_remote for j in week_jobs))
        series.median_wait_town.append(town)
        series.median_wait_remote.append(remote)
        series.gap.append(None if remote is None or town is None else remote - town)
    return series
