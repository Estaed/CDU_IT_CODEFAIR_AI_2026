"""Explanation templates: the rank sentence and the tenant answer (PRD sections 3.1, 3.4,
7; wireframes §7). Every text here must pass the wording lint and cover every non-zero
factor; every tenant state answers the four questions, in order."""

import itertools
import re
from dataclasses import dataclass
from datetime import timedelta

import pytest

from fair_turn.core import constants, explain, scoring, wording
from fair_turn.core.types import FaultType, HealthRiskFactor, Job, SafetyClass
from fair_turn.data import artefacts, policy

TODAY = constants.WINDOW_START + timedelta(days=30)
COORDINATOR_REASON = "Crews are busy this week. We use this setting to keep remote jobs moving."
VISIT_REASON = "the crew can reach both homes on one road before the river rises"
PROMISED_TIME = re.compile(r"will arrive|at \d")


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
        1,
        scoring.window_days(job),
        COORDINATOR_REASON,
        lam,
    ).text


@dataclass(frozen=True)
class FakePassage:
    title: str
    section: str
    effective_date: str


PASSAGE = FakePassage("Housing fact sheet", "Repairs", "2025-10")


def state_kwargs(state: str, **extra) -> dict:
    """A plausible input set for each tenant state."""
    job = make_job(health_risk=frozenset({HealthRiskFactor.ELDERLY}))
    if state == "unknown":
        kwargs = {}
    elif state == "review":
        kwargs = dict(
            scored=scoring.score_job(make_job(fault_type=None), TODAY, 0.5),
            missing_fields=("fault_type",),
            policy=PASSAGE,
        )
    elif state == "manual":
        kwargs = dict(scored=scored_for(job), policy=PASSAGE)
    elif state == "unsigned":
        kwargs = dict(scored=scored_for(job), rank_at_lambda0=2, lam=0.5, policy=PASSAGE)
    else:
        kwargs = dict(
            scored=scored_for(job),
            rank_at_lambda0=2,
            lam=0.5,
            signed_rank=4,
            coordinator_reason=COORDINATOR_REASON,
            policy=PASSAGE,
            decision_version=2,
        )
    kwargs.update(extra)
    return dict(state=state, **kwargs)


def tenant(state: str, **extra) -> explain.TenantAnswer:
    return explain.tenant_answer(**state_kwargs(state, **extra))


# --- Phase 1 form, kept for one release ------------------------------------------------------

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
    assert f"number {scored.rank} on today's draft list" in answer.text
    assert "would be number 3" in answer.text
    assert COORDINATOR_REASON in answer.text


def test_tenant_answer_requires_ranked_job() -> None:
    unranked = scoring.score_job(make_job(fault_type=None), TODAY, 0.5)
    with pytest.raises(ValueError):
        explain.tenant_answer(unranked, 1, 5.0, COORDINATOR_REASON, 0.5)


# --- the four blocks, per state --------------------------------------------------------------


@pytest.mark.parametrize("state", explain.TENANT_STATES)
def test_every_state_has_four_blocks_in_question_order(state: str) -> None:
    answer = tenant(state)
    assert tuple(b.question for b in answer.blocks) == explain.QUESTIONS
    assert all(b.paragraphs and all(p.strip() for p in b.paragraphs) for b in answer.blocks)


@pytest.mark.parametrize("state", explain.TENANT_STATES)
@pytest.mark.parametrize("with_visit", [False, True])
def test_every_state_passes_wording_check(state: str, with_visit: bool) -> None:
    extra = {"visit_order": (2, VISIT_REASON)} if with_visit else {}
    text = tenant(state, **extra).text
    assert len(text.split()) >= wording.MIN_WORDS_FOR_READING_LEVEL
    assert wording.check(text) == []


@pytest.mark.parametrize("state", explain.TENANT_STATES)
def test_no_promised_time_in_any_state(state: str) -> None:
    for extra in ({}, {"visit_order": (2, VISIT_REASON)}):
        assert not PROMISED_TIME.search(tenant(state, **extra).text)


@pytest.mark.parametrize("state", explain.TENANT_STATES)
def test_counterfactual_is_a_formula_comparison_never_a_route(state: str) -> None:
    text = tenant(state, visit_order=(2, VISIT_REASON)).text
    for sentence in re.split(r"(?<=\.)\s+", text):
        assert "route" not in sentence.lower()
        assert "itinerary" not in sentence.lower()
    if state in ("ranked", "superseded", "backlog", "unsigned"):
        assert "If distance did not count, your repair would be number 2." in text


def test_state_copy_is_distinct() -> None:
    assert "A person is checking your report before it is ranked." in tenant("review").text
    assert "We could not read what is broken from the report." in tenant("review").text
    assert "not on today's list" in tenant("backlog").text
    assert "has not signed it" in tenant("unsigned").text
    assert "freight" in tenant("manual").text
    assert "This answer uses the signed list version 2." in tenant("superseded").text
    unknown = tenant("unknown").text
    assert "We could not find that job number." in unknown
    assert explain.JOB_ID_EXAMPLE == "JR-2025-00001"
    assert explain.JOB_ID_EXAMPLE in unknown
    texts = {state: tenant(state).text for state in explain.TENANT_STATES}
    assert len(set(texts.values())) == len(texts)


def test_review_names_each_missing_field_and_no_rank() -> None:
    both = tenant("review", missing_fields=("fault_type", "safety_class")).text
    assert "We could not read what is broken from the report." in both
    assert "We could not read how urgent it is." in both
    assert "is number" not in both
    assert "would be number" not in both
    assert "We do not have a visit date yet." in both


def test_ranked_signed_versus_draft_rank() -> None:
    assert "number 4 on the signed list" in tenant("ranked").text
    draft = tenant("ranked", signed_rank=None)
    assert "on today's draft list" in draft.text
    assert "signed list" not in draft.text


def test_visit_order_sentence_only_when_set_and_names_the_reason() -> None:
    plain = tenant("ranked")
    assert "The crew will visit it" not in plain.text
    assert "We do not have a visit date yet." in plain.text

    moved = tenant("ranked", visit_order=(2, VISIT_REASON + "."))
    where = moved.blocks[1].paragraphs
    sentence = f"The crew will visit it second on the day, because {VISIT_REASON}."
    assert sentence in where
    assert where.index(sentence) == 1  # right after the signed rank
    assert "We do not have a visit date yet." not in moved.text

    blank = tenant("ranked", visit_order=(3, "  "))
    assert f"third on the day, because {explain.DEFAULT_VISIT_REASON}." in blank.text


@pytest.mark.parametrize(
    ("safety", "remote", "phrase"),
    [
        (SafetyClass.IMMEDIATE, True, "For an immediate repair like yours"),
        (SafetyClass.URGENT, False, "For an urgent repair like yours"),
        (SafetyClass.ROUTINE, True, "For a routine repair like yours"),
    ],
)
def test_window_uses_article_and_business_days(safety, remote, phrase) -> None:
    job = make_job(safety_class=safety, is_remote=remote)
    answer = explain.tenant_answer(state="manual", scored=scored_for(job))
    next_block = answer.blocks[2].paragraphs
    assert phrase in next_block[0]
    assert "That is a policy target, not a promised visit time." in next_block[0]
    if safety is SafetyClass.IMMEDIATE:
        assert f"make it safe within {constants.MAKE_SAFE_HOURS} hours" in next_block[0]
    else:
        days = constants.RESPONSE_BUSINESS_DAYS[(safety.value, remote)]
        assert f"{days} business days from the report date" in next_block[0]


def test_policy_source_line_from_passage_or_default() -> None:
    cited = tenant("ranked").blocks[2].paragraphs
    assert "Policy source: Housing fact sheet, Repairs, effective 2025-10." in cited
    fallback = tenant("ranked", policy=None).blocks[2].paragraphs
    assert f"Policy source: {explain.DEFAULT_POLICY_SOURCE}." in fallback


def test_contact_block_names_the_officer_and_invents_no_details() -> None:
    for state in explain.TENANT_STATES:
        ask = " ".join(tenant(state).blocks[3].paragraphs)
        assert "Community Housing Officer" in ask
        assert not re.search(r"\d|@|phone|street|email", ask, re.I)
    assert COORDINATOR_REASON in tenant("ranked").blocks[3].paragraphs[1]
    unsigned = tenant("unsigned").blocks[3].paragraphs
    assert "The coordinator has not signed today's setting yet." in unsigned


def test_bad_inputs_are_refused() -> None:
    with pytest.raises(ValueError):
        explain.tenant_answer(state="ranked")
    with pytest.raises(ValueError):
        explain.tenant_answer(**state_kwargs("superseded", decision_version=None))
    with pytest.raises(ValueError):
        explain.tenant_answer(**{**state_kwargs("ranked"), "state": "closed"})


# --- reading level over committed jobs -------------------------------------------------------


def _committed_sample() -> list[scoring.ScoredJob]:
    art = artefacts.load_all()
    jobs = sorted((j for j in artefacts.to_jobs(art) if not j.needs_human), key=lambda j: j.job_id)
    day = constants.WINDOW_START + timedelta(days=constants.WINDOW_DAYS)
    return scoring.rank(jobs[:50], day, 1.0)


def test_reading_grade_over_fifty_committed_jobs_in_ranked_state() -> None:
    sample = _committed_sample()
    assert len(sample) == 50
    index = policy.load()
    for position, scored in enumerate(sample, start=1):
        job = scored.job
        passages = policy.lookup(index, job.safety_class.value, job.is_remote, job.fault_type)
        answer = explain.tenant_answer(
            state="ranked",
            scored=scored,
            rank_at_lambda0=position,
            lam=1.0,
            signed_rank=position,
            coordinator_reason=COORDINATOR_REASON,
            policy=passages[0] if passages else None,
        )
        assert wording.check(answer.text) == [], job.job_id
        for name in scoring.FACTOR_NAMES:
            assert explain.FACTOR_LABELS[name] in answer.text
        for factor in job.health_risk:
            assert explain.LABELS[factor.value] in answer.text


# --- the coordinator's rank sentence (unchanged) ---------------------------------------------


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
