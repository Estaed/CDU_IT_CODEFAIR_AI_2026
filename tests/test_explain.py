"""Explanation templates: the rank sentence and the tenant answer (PRD sections 3.1, 3.4,
7). Every text here must pass the wording lint and cover every non-zero factor."""

import itertools
from datetime import timedelta

import pytest

from fair_turn.core import constants, explain, scoring, wording
from fair_turn.core.types import FaultType, HealthRiskFactor, Job, SafetyClass

TODAY = constants.WINDOW_START + timedelta(days=30)
COORDINATOR_REASON = "Crews are busy this week. We use this setting to keep remote jobs moving."


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


def scored_for(job: Job, lam: float = 0.5) -> scoring.ScoredJob:
    return scoring.rank([job], TODAY, lam)[0]


def answer_for(job: Job, lam: float = 0.5) -> str:
    scored = scored_for(job, lam)
    return explain.tenant_answer(
        scored,
        rank_at_lambda0=1,
        window_days=scoring.window_days(job),
        coordinator_reason=COORDINATOR_REASON,
        lam=lam,
    )


# Ten fixtures: one per FaultType, cycling every SafetyClass and remoteness, varying
# health-risk factor counts (PRD-required coverage: all enums, both remoteness values).
SAFETY_CYCLE = list(SafetyClass)
FIXTURES = [
    make_job(
        f"f{i}",
        fault_type=fault,
        safety_class=SAFETY_CYCLE[i % len(SAFETY_CYCLE)],
        is_remote=(i % 2 == 0),
        health_risk=frozenset(list(HealthRiskFactor)[: i % (len(HealthRiskFactor) + 1)]),
    )
    for i, fault in enumerate(FaultType)
]


def test_ten_fixtures_pass_wording_check() -> None:
    assert len(FIXTURES) == 10
    for job in FIXTURES:
        assert wording.check(answer_for(job)) == []


def test_all_factor_labels_present_in_tenant_answer() -> None:
    for job in FIXTURES:
        answer = answer_for(job)
        for name in scoring.FACTOR_NAMES:
            assert explain.FACTOR_LABELS[name] in answer


@pytest.mark.parametrize(
    "subset",
    [
        frozenset(s)
        for r in range(len(HealthRiskFactor) + 1)
        for s in itertools.combinations(HealthRiskFactor, r)
    ],
)
def test_every_health_risk_combination_is_labelled(subset: frozenset) -> None:
    job = make_job(health_risk=subset)
    answer = answer_for(job)
    for factor in subset:
        assert explain.LABELS[factor.value] in answer


def test_tenant_answer_mentions_rank_and_reason() -> None:
    job = make_job()
    scored = scored_for(job, lam=0.5)
    answer = explain.tenant_answer(scored, 3, scoring.window_days(job), COORDINATOR_REASON, 0.5)
    assert str(scored.rank) in answer
    assert "3" in answer
    assert COORDINATOR_REASON in answer


def test_tenant_answer_requires_ranked_job() -> None:
    unranked = scoring.score_job(make_job(fault_type=None), TODAY, 0.5)
    with pytest.raises(ValueError):
        explain.tenant_answer(unranked, 1, 5.0, COORDINATOR_REASON, 0.5)


def test_why_sentence_mentions_two_largest_factors() -> None:
    job = make_job(
        health_risk=frozenset({HealthRiskFactor.INFANT_OR_YOUNG_CHILD}),
        reported_on=TODAY - timedelta(days=20),
    )
    scored = scored_for(job, lam=0.5)
    sentence = explain.why_sentence(scored, lam=0.5)
    top_two = sorted(explain.NEED_FACTORS, key=lambda n: scored.factors[n], reverse=True)[:2]
    for name in top_two:
        clause = explain._CLAUSE_BUILDERS[name](job, scored.factors)
        assert clause in sentence


def test_why_sentence_requires_ranked_job() -> None:
    unranked = scoring.score_job(make_job(fault_type=None), TODAY, 0.5)
    with pytest.raises(ValueError):
        explain.why_sentence(unranked, 0.5)


def test_lambda_changes_logistics_phrase() -> None:
    job = make_job(logistics_factor=50)
    zero = explain.why_sentence(scored_for(job, lam=0.0), lam=0.0)
    heavy = explain.why_sentence(scored_for(job, lam=1.5), lam=1.5)
    assert zero != heavy
    assert "not counted" in zero
    assert "weighted heavily" in heavy
