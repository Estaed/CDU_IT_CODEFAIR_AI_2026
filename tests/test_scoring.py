"""Ranking formula: each factor rule, the identity, the human queue, and the lambda = 0
invariance property (PRD section 4, CLAUDE.md Blueprint verification rule 2)."""

from dataclasses import replace
from datetime import date, timedelta

from hypothesis import given, settings
from hypothesis import strategies as st

from fair_turn.core import constants, scoring
from fair_turn.core.types import FaultType, HealthRiskFactor, Job, SafetyClass

TODAY = constants.WINDOW_START + timedelta(days=30)  # 31 Oct 2025, heat season
OUT_OF_SEASON = date(2025, 6, 15)


def make_job(job_id: str = "j1", **overrides) -> Job:
    base = dict(
        job_id=job_id,
        community_id="c1",
        is_remote=True,
        reported_on=TODAY - timedelta(days=5),
        fault_type=FaultType.PLUMBING_WATER,
        safety_class=SafetyClass.ROUTINE,
    )
    base.update(overrides)
    return Job(**base)


# --- factor rules -----------------------------------------------------------------------


def test_urgency_is_elapsed_over_window() -> None:
    remote_routine = make_job(reported_on=TODAY - timedelta(days=5))
    assert scoring.urgency(remote_routine, TODAY) == 5 / 25
    town_routine = make_job(is_remote=False, reported_on=TODAY - timedelta(days=5))
    assert scoring.urgency(town_routine, TODAY) == 5 / 10


def test_urgency_caps_at_three_and_floors_at_zero() -> None:
    immediate = make_job(safety_class=SafetyClass.IMMEDIATE, reported_on=TODAY - timedelta(2))
    assert scoring.urgency(immediate, TODAY) == 3.0  # task: capped at 3.0
    future = make_job(reported_on=TODAY + timedelta(days=1))
    assert scoring.urgency(future, TODAY) == 0.0


def test_safety_weights_and_heat_escalation() -> None:
    assert scoring.safety(make_job(safety_class=SafetyClass.IMMEDIATE), TODAY) == 3.0
    assert scoring.safety(make_job(safety_class=SafetyClass.URGENT), TODAY) == 2.0
    assert scoring.safety(make_job(safety_class=SafetyClass.ROUTINE), TODAY) == 1.0
    cooling_remote = make_job(fault_type=FaultType.COOLING)
    assert scoring.safety(cooling_remote, TODAY) == 1.0 + scoring.HEAT_ESCALATION
    assert scoring.safety(cooling_remote, OUT_OF_SEASON) == 1.0
    assert scoring.safety(replace(cooling_remote, is_remote=False), TODAY) == 1.0
    assert scoring.safety(make_job(fault_type=FaultType.HOT_WATER), TODAY) == 2.0


def test_health_risk_is_half_per_factor() -> None:
    assert scoring.health_risk(make_job()) == 0.0
    two = make_job(health_risk=frozenset({HealthRiskFactor.ELDERLY, HealthRiskFactor.OVERCROWDING}))
    assert scoring.health_risk(two) == 1.0


def test_logistics_rules() -> None:
    assert scoring.logistics(make_job(logistics_factor=50)) == 0.5
    assert scoring.logistics(make_job(logistics_factor=50, road_closed=True)) == 2.5
    assert scoring.logistics(make_job(logistics_factor=50, crew_nearby=True)) == 0.0
    assert scoring.logistics(make_job(logistics_factor=10, crew_nearby=True)) == 0.0  # floor


# --- score_job and rank -----------------------------------------------------------------


def test_score_job_factors_and_identity() -> None:
    job = make_job(
        fault_type=FaultType.COOLING,
        health_risk=frozenset({HealthRiskFactor.INFANT_OR_YOUNG_CHILD}),
        logistics_factor=80,
        road_closed=True,
    )
    scored = scoring.score_job(job, TODAY, lam=0.7)
    assert tuple(scored.factors) == scoring.FACTOR_NAMES
    f = scored.factors
    expected = f["urgency"] + f["safety"] + f["health_risk"] - 0.7 * f["logistics"]
    assert abs(scored.score - expected) < 1e-9
    assert scored.needs_human is False
    assert scored.rank is None


def test_missing_field_goes_to_human_queue() -> None:
    no_fault = make_job("a", fault_type=None)
    no_class = make_job("b", safety_class=None)
    for job in (no_fault, no_class):
        scored = scoring.score_job(job, TODAY, 1.0)
        assert scored.needs_human is True
        assert scored.score is None
        assert scored.factors == {}
    complete = make_job("c")
    rankable, human = scoring.split_human_queue([no_fault, complete, no_class])
    assert rankable == [complete]
    assert human == [no_fault, no_class]
    ranked = scoring.rank([no_fault, complete, no_class], TODAY, 1.0)
    assert [s.job.job_id for s in ranked] == ["c"]


def test_lambda_one_puts_far_job_below_near_job_with_equal_need() -> None:
    near = make_job("near", logistics_factor=10)
    far = make_job("far", logistics_factor=90)
    assert [s.job.job_id for s in scoring.rank([far, near], TODAY, 0.0)] == ["far", "near"]
    assert [s.job.job_id for s in scoring.rank([far, near], TODAY, 1.0)] == ["near", "far"]


def test_rank_is_descending_and_stable_on_job_id() -> None:
    jobs = [make_job("b"), make_job("a"), make_job("c", safety_class=SafetyClass.URGENT)]
    ranked = scoring.rank(jobs, TODAY, 1.0)
    assert [s.job.job_id for s in ranked] == ["c", "a", "b"]
    assert [s.rank for s in ranked] == [1, 2, 3]
    scores = [s.score for s in ranked]
    assert scores == sorted(scores, reverse=True)


# --- property: lambda = 0 ignores logistics entirely ------------------------------------

job_fields = st.builds(
    make_job,
    job_id=st.just(""),
    is_remote=st.booleans(),
    reported_on=st.dates(constants.WINDOW_START, TODAY),
    fault_type=st.sampled_from(FaultType),
    safety_class=st.sampled_from(SafetyClass),
    health_risk=st.frozensets(st.sampled_from(HealthRiskFactor)),
    logistics_factor=st.floats(0, 100),
    road_closed=st.booleans(),
    crew_nearby=st.booleans(),
)


@st.composite
def job_lists(draw) -> list[Job]:
    jobs = draw(st.lists(job_fields, min_size=1, max_size=12))
    return [replace(j, job_id=f"j{i:02d}") for i, j in enumerate(jobs)]


@settings(max_examples=200, deadline=None)
@given(job_lists(), st.data())
def test_lambda_zero_ranking_ignores_logistics(jobs: list[Job], data) -> None:
    before = [s.job.job_id for s in scoring.rank(jobs, TODAY, 0.0)]
    order = data.draw(st.permutations(range(len(jobs))))
    shuffled = [
        replace(j, logistics_factor=jobs[k].logistics_factor, road_closed=jobs[k].road_closed)
        for j, k in zip(jobs, order, strict=True)
    ]
    after = [s.job.job_id for s in scoring.rank(shuffled, TODAY, 0.0)]
    assert before == after


@settings(max_examples=100, deadline=None)
@given(job_lists(), st.floats(0, 1))
def test_human_queue_never_ranked(jobs: list[Job], lam: float) -> None:
    jobs = [replace(j, fault_type=None) if i % 3 == 0 else j for i, j in enumerate(jobs)]
    ranked = {s.job.job_id for s in scoring.rank(jobs, TODAY, lam)}
    _, human = scoring.split_human_queue(jobs)
    assert ranked.isdisjoint(j.job_id for j in human)
    assert len(ranked) + len(human) == len(jobs)


# --- business days (FS17 states urgent and routine windows in business days) ---------------


def test_business_days_skip_the_weekend() -> None:
    friday = date(2025, 10, 3)
    assert scoring.business_days_between(friday, friday + timedelta(days=1)) == 0  # Saturday
    assert scoring.business_days_between(friday, friday + timedelta(days=2)) == 0  # Sunday
    assert scoring.business_days_between(friday, friday + timedelta(days=3)) == 1  # Monday
    assert scoring.business_days_between(friday, friday + timedelta(days=14)) == 10
    assert scoring.business_days_between(friday, friday) == 0
    assert scoring.business_days_between(friday, friday - timedelta(days=1)) == 0


def test_urgency_counts_business_days_not_calendar_days() -> None:
    friday = date(2025, 10, 3)
    town_urgent = make_job(is_remote=False, safety_class=SafetyClass.URGENT, reported_on=friday)
    monday = friday + timedelta(days=3)
    assert scoring.urgency(town_urgent, monday) == 1 / 2  # one of two business days used
    assert scoring.urgency(town_urgent, friday + timedelta(days=2)) == 0
