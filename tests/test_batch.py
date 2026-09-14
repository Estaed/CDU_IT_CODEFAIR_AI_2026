"""Tests for frozen sign-off batches (PRD section 3.1)."""

from datetime import date

import pytest

from fair_turn.core.batch import (
    TRANSITIONS,
    HandMove,
    can_submit,
    fingerprint_of,
    freeze,
    is_stale,
    next_status,
    preset_label,
)
from fair_turn.core.types import FaultType, Job, SafetyClass, ScoredJob


def _scored(job_id: str, community_id: str = "community-1") -> ScoredJob:
    job = Job(
        job_id=job_id,
        community_id=community_id,
        is_remote=False,
        reported_on=date(2025, 12, 30),
        fault_type=FaultType.COOLING,
        safety_class=SafetyClass.URGENT,
    )
    return ScoredJob(job=job, score=2.0, factors={}, rank=1, needs_human=False)


def test_freeze_preserves_final_order_capacity_and_canonical_fingerprint() -> None:
    moves = [HandMove("job-2", 3, 1, "Crew is already nearby")]
    human_set = {"job-3": {"safety_class": "urgent"}}
    ranked = [_scored("job-2"), _scored("job-1"), _scored("job-3")]

    batch = freeze(date(2025, 12, 30), 3, 0.5, "Balanced", ranked, 2, moves, human_set)

    assert batch.today_job_ids == ("job-2", "job-1")
    assert batch.ranked_job_ids == ("job-2", "job-1", "job-3")
    assert batch.hand_moves == tuple(moves)
    assert batch.fingerprint == fingerprint_of(0.5, batch.ranked_job_ids, moves, human_set)
    assert preset_label(0.5, "Balanced") == "Balanced"
    assert preset_label(0.35, None) == "Custom (0.35)"


@pytest.mark.parametrize(
    ("lam", "ranked_ids", "moves", "human_set"),
    [
        (0.35, ("job-1", "job-2"), (), None),
        (0.5, ("job-1", "job-2"), (), None),
        (0.35, ("job-2", "job-1"), (), None),
        (0.35, ("job-1", "job-2"), (HandMove("job-1", 2, 1, "reason"),), None),
        (0.35, ("job-1", "job-2"), (), {"job-1": {"fault_type": "cooling"}}),
    ],
)
def test_each_fingerprint_input_change_makes_a_batch_stale(
    lam: float,
    ranked_ids: tuple[str, ...],
    moves: tuple[HandMove, ...],
    human_set: dict[str, dict[str, str]] | None,
) -> None:
    original = fingerprint_of(0.35, ("job-1", "job-2"), (), None)
    batch = freeze(
        date(2025, 12, 30),
        1,
        0.35,
        None,
        [_scored("job-1"), _scored("job-2")],
        1,
        (),
    )

    assert batch.fingerprint == original
    assert is_stale(batch, fingerprint_of(lam, ranked_ids, moves, human_set)) is (
        lam != 0.35 or ranked_ids != ("job-1", "job-2") or bool(moves) or human_set is not None
    )


def test_accepted_list_is_today_and_a_decision_change_makes_a_batch_stale() -> None:
    ranked = [_scored("job-1"), _scored("job-2"), _scored("job-3")]
    standing = {"job-3": "accepted", "job-1": "accepted"}
    batch = freeze(
        date(2025, 12, 30),
        1,
        0.5,
        None,
        ranked,
        2,
        (),
        today_job_ids=["job-1", "job-3"],
        decisions=standing,
    )
    assert batch.today_job_ids == ("job-1", "job-3")
    ids = batch.ranked_job_ids
    assert not is_stale(batch, fingerprint_of(0.5, ids, (), None, dict(standing)))
    assert is_stale(batch, fingerprint_of(0.5, ids, (), None, {"job-1": "accepted"}))
    assert is_stale(batch, fingerprint_of(0.5, ids, (), None, {**standing, "job-2": "not_today"}))
    assert fingerprint_of(0.5, ids, (), None, {}) == fingerprint_of(0.5, ids, (), None)


@pytest.mark.parametrize("current,event", TRANSITIONS)
def test_every_valid_transition_has_its_declared_target(current: str, event: str) -> None:
    assert next_status(current, event) == TRANSITIONS[(current, event)]


def test_every_undeclared_transition_raises() -> None:
    statuses = (
        "draft",
        "review_open",
        "saving",
        "save_failed",
        "signed",
        "changed_since_signature",
    )
    events = ("open_review", "change", "submit", "submit_ok", "submit_fail", "cancel")

    for current in statuses:
        for event in events:
            if (current, event) not in TRANSITIONS:
                with pytest.raises(ValueError, match=f"{current} cannot take {event}"):
                    next_status(current, event)


def test_can_submit_refuses_stale_before_duplicate_and_then_duplicate_version() -> None:
    batch = freeze(
        date(2025, 12, 30),
        4,
        0.5,
        "Balanced",
        [_scored("job-1")],
        1,
        (),
    )

    assert can_submit(batch, "different", [4]) == (
        False,
        "The list changed since you opened this review; open it again.",
    )
    assert can_submit(batch, batch.fingerprint, [4]) == (
        False,
        "Batch v4 was already signed; open the review again for v5.",
    )
    assert can_submit(batch, batch.fingerprint, [3]) == (True, "")
