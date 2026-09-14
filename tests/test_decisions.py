"""Today's per-job decisions split the ranking into accepted, to decide, not today and backlog
(PRD 3.1): an acceptance is never dropped, a job decided not today never comes back that day,
and the free places go to the best-ranked undecided jobs."""

from datetime import date

from hypothesis import given
from hypothesis import strategies as st

from fair_turn.core import decisions
from fair_turn.core.types import FaultType, Job, SafetyClass

DECISION = st.sampled_from(["accepted", "not_today", "undone", None])


@st.composite
def days(draw):
    count = draw(st.integers(min_value=0, max_value=30))
    ranked = [f"job-{i}" for i in range(count)]
    latest = {}
    for job_id in ranked:
        value = draw(DECISION)
        if value is not None:
            latest[job_id] = value
    capacity = draw(st.integers(min_value=0, max_value=20))
    return ranked, latest, capacity


def _lists(split: decisions.Split) -> list[list[str]]:
    return [split.accepted, split.to_decide, split.not_today, split.backlog]


def test_worked_example() -> None:
    ranked = ["a", "b", "c", "d", "e", "f"]
    latest = {"b": "accepted", "c": "not_today", "e": "accepted", "a": "undone"}
    split = decisions.split(ranked, latest, 3)
    assert split == decisions.Split(["b", "e"], ["a"], ["c"], ["d", "f"])


def test_acceptances_past_capacity_are_kept() -> None:
    split = decisions.split(["a", "b", "c"], {"a": "accepted", "b": "accepted"}, 1)
    assert split.accepted == ["a", "b"]
    assert split.to_decide == []
    assert split.backlog == ["c"]


@given(days())
def test_the_four_lists_partition_the_ranking_in_rank_order(day) -> None:
    ranked, latest, capacity = day
    split = decisions.split(ranked, latest, capacity)
    joined = [job_id for part in _lists(split) for job_id in part]
    assert sorted(joined) == sorted(ranked)
    assert len(joined) == len(set(joined))
    for part in _lists(split):
        assert part == [job_id for job_id in ranked if job_id in part]


@given(days())
def test_today_never_exceeds_capacity_except_by_acceptances(day) -> None:
    ranked, latest, capacity = day
    split = decisions.split(ranked, latest, capacity)
    assert len(split.accepted) + len(split.to_decide) <= max(capacity, len(split.accepted))


@given(days(), st.data())
def test_accepting_a_job_to_decide_shrinks_to_decide_by_one_and_adds_nothing(day, data) -> None:
    ranked, latest, capacity = day
    before = decisions.split(ranked, latest, capacity)
    if not before.to_decide:
        return
    job_id = data.draw(st.sampled_from(before.to_decide))
    after = decisions.split(ranked, {**latest, job_id: "accepted"}, capacity)
    assert len(after.to_decide) == len(before.to_decide) - 1
    assert set(after.to_decide) <= set(before.to_decide)
    assert job_id in after.accepted


@given(days(), st.data())
def test_not_today_pulls_in_the_next_undecided_job(day, data) -> None:
    ranked, latest, capacity = day
    before = decisions.split(ranked, latest, capacity)
    if not before.to_decide:
        return
    job_id = data.draw(st.sampled_from(before.to_decide))
    after = decisions.split(ranked, {**latest, job_id: "not_today"}, capacity)
    assert job_id in after.not_today and job_id not in after.to_decide
    if before.backlog:  # the backlog holds only undecided jobs
        assert len(after.to_decide) == len(before.to_decide)
        assert before.backlog[0] in after.to_decide


@given(days(), st.data())
def test_undo_restores_the_earlier_split(day, data) -> None:
    ranked, latest, capacity = day
    undecided = [job_id for job_id in ranked if latest.get(job_id) not in decisions_made()]
    if not undecided:
        return
    job_id = data.draw(st.sampled_from(undecided))
    decision = data.draw(st.sampled_from(["accepted", "not_today"]))
    before = decisions.split(ranked, latest, capacity)
    decided = decisions.split(ranked, {**latest, job_id: decision}, capacity)
    undone = decisions.split(ranked, {**latest, job_id: "undone"}, capacity)
    assert decided != before or not ranked
    assert undone == before


def decisions_made() -> tuple[str, str]:
    return (decisions.ACCEPTED, decisions.NOT_TODAY)


# --- the make-safe lane (PRD 3.1 and 6.3, amended 2026-09-15) ------------------------------------


def _job(**overrides) -> Job:
    base = dict(
        job_id="job-1",
        community_id="c1",
        is_remote=True,
        reported_on=date(2026, 9, 1),
        fault_type=FaultType.PLUMBING_WATER,
        safety_class=SafetyClass.IMMEDIATE,
    )
    base.update(overrides)
    return Job(**base)


@given(
    st.sampled_from([None, *FaultType]),
    st.sampled_from([None, *SafetyClass]),
)
def test_is_make_safe_iff_every_required_field_and_immediate(fault, safety) -> None:
    job = _job(fault_type=fault, safety_class=safety)
    expected = fault is not None and safety is SafetyClass.IMMEDIATE
    assert decisions.is_make_safe(job) is expected
    assert decisions.is_make_safe(job) is (
        not job.needs_human and job.safety_class is SafetyClass.IMMEDIATE
    )


def test_an_immediate_job_missing_its_fault_type_is_for_a_person_not_make_safe() -> None:
    assert decisions.is_make_safe(_job())
    assert not decisions.is_make_safe(_job(fault_type=None))
    assert not decisions.is_make_safe(_job(safety_class=SafetyClass.URGENT))
