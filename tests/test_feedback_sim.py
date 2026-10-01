"""Feedback-loop simulation over the committed labels (Task-05 acceptance criteria)."""

import csv
import json
import time
from datetime import date
from functools import cache
from pathlib import Path

import pytest

from fair_turn.core import capacity_sim, constants, decisions, feedback_sim
from fair_turn.core.capacity_sim import Closure, CrewBase, Site
from fair_turn.core.types import FaultType, HealthRiskFactor, Job, SafetyClass
from fair_turn.data import geography

BUILD_DIR = Path(__file__).resolve().parent.parent / "data" / "build"
DECAY = 0.5


@cache
def artefacts() -> tuple[list[Job], dict[str, Site], tuple[CrewBase, ...], list[Closure]]:
    if not (BUILD_DIR / "labels.json").exists():
        pytest.skip("data/build/labels.json absent")
    with (BUILD_DIR / "communities.csv").open(newline="", encoding="utf-8") as f:
        rows = {r["community_id"]: r for r in csv.DictReader(f)}
    sites = geography.sim_sites(rows)
    jobs = []
    for label in json.loads((BUILD_DIR / "labels.json").read_text(encoding="utf-8")):
        community = rows[label["community_id"]]
        jobs.append(
            Job(
                job_id=label["job_id"],
                community_id=label["community_id"],
                is_remote=community["is_remote"] == "True",
                reported_on=date.fromisoformat(label["reported_on"]),
                fault_type=FaultType(label["fault_type"]),
                safety_class=SafetyClass(label["safety_class"]),
                health_risk=frozenset(HealthRiskFactor(h) for h in label["health_risk"]),
                logistics_factor=float(community["logistics_factor"]),
            )
        )
    closures = [
        Closure(
            c["community_id"],
            date.fromisoformat(c["closed_from"]),
            date.fromisoformat(c["closed_to"]),
        )
        for c in json.loads((BUILD_DIR / "closures.json").read_text(encoding="utf-8"))
    ]
    return jobs, sites, geography.crews(rows), closures


@cache
def series(lam: float, decay: float, seed: int = constants.SEED) -> feedback_sim.WeeklySeries:
    jobs, sites, crews, closures = artefacts()
    return feedback_sim.run(jobs, sites, crews, lam, decay, seed, closures)


def test_decay_zero_is_the_plain_capacity_run() -> None:
    jobs, sites, crews, closures = artefacts()
    horizon = constants.WINDOW_DAYS + feedback_sim.COMPLETION_TAIL_DAYS
    plain = capacity_sim.simulate(
        jobs,
        1.0,
        constants.WINDOW_START,
        horizon,
        closures,
        crews,
        constants.JOBS_PER_CREW_DAY,
        constants.TRAVEL_DAY_KM,
        sites,
    )
    result = series(1.0, 0.0)
    assert result.sim == plain
    assert sum(result.reports_town) == sum(not j.is_remote for j in jobs)
    assert sum(result.reports_remote) == sum(j.is_remote for j in jobs)
    assert len(result.week_start) == 13
    # Weekly medians are drawn from the plain run's waits, censored at the horizon end.
    first_week = [
        j
        for j in jobs
        if j.is_remote
        and not j.needs_human
        and not decisions.is_make_safe(j)
        and (j.reported_on - constants.WINDOW_START).days < 7
    ]
    end = date.fromordinal(constants.WINDOW_START.toordinal() + horizon)
    waits = sorted(
        plain.wait_days[j.job_id]
        if plain.wait_days[j.job_id] is not None
        else (end - j.reported_on).days
        for j in first_week
    )
    mid = len(waits) // 2
    expected = waits[mid] if len(waits) % 2 else (waits[mid - 1] + waits[mid]) / 2
    assert result.median_wait_remote[0] == expected


def test_reporting_fades_under_both_runs_and_town_fades_less() -> None:
    for lam in (1.0, 0.0):
        decayed, plain = series(lam, DECAY), series(lam, 0.0)
        remote_drop = 1 - sum(decayed.reports_remote) / sum(plain.reports_remote)
        town_drop = 1 - sum(decayed.reports_town) / sum(plain.reports_town)
        assert remote_drop > 0
        assert town_drop < remote_drop


def test_equity_run_serves_no_fewer_remote_reports_at_more_km_and_town_wait() -> None:
    jobs, *_ = artefacts()
    equity, efficiency = series(0.0, 0.0), series(1.0, 0.0)

    def served(s: feedback_sim.WeeklySeries) -> int:
        return sum(
            wait is not None
            for job in jobs
            if job.is_remote
            for wait in [s.sim.wait_days[job.job_id]]
        )

    assert served(equity) >= served(efficiency)
    assert equity.sim.travel_km > efficiency.sim.travel_km
    # Town crews clear most town jobs the same day at either setting, so the town price of
    # equity shows as town jobs left open, not as a longer town median.
    assert equity.sim.unfinished_town > efficiency.sim.unfinished_town


def test_served_within_window_is_a_share_and_excludes_make_safe() -> None:
    jobs, *_ = artefacts()
    s = series(1.0, 0.0)
    remote, town = feedback_sim.served_within_window(s.sim, jobs)
    assert remote is not None and town is not None
    assert 0.0 < remote < town <= 1.0
    only_make_safe = [job for job in jobs if decisions.is_make_safe(job)]
    assert feedback_sim.served_within_window(s.sim, only_make_safe) == (None, None)


def test_decay_thins_only_where_reports_went_unserved() -> None:
    plain, decayed = series(1.0, 0.0), series(1.0, DECAY)
    assert decayed.reports_remote[0] == plain.reports_remote[0]  # no history in week 1
    assert sum(decayed.reports_remote) < sum(plain.reports_remote)
    assert all(d <= p for d, p in zip(decayed.reports_town, plain.reports_town, strict=True))


def test_deterministic_for_a_seed_and_seed_changes_thinning() -> None:
    jobs, sites, crews, closures = artefacts()
    again = feedback_sim.run(jobs, sites, crews, 1.0, DECAY, constants.SEED, closures)
    assert again == series(1.0, DECAY)
    other = series(1.0, DECAY, constants.SEED + 1)
    assert other.sim.completed_on.keys() != again.sim.completed_on.keys()


@pytest.mark.parametrize("lam", [0.0, 1.0])
def test_ninety_days_runs_under_twenty_seconds(lam: float) -> None:
    jobs, sites, crews, closures = artefacts()
    began = time.perf_counter()
    feedback_sim.run(jobs, sites, crews, lam, 1.0, constants.SEED, closures)
    assert time.perf_counter() - began < 20.0
