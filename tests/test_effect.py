"""Tests for the two-stage effect sentence (PRD section 3.1)."""

import re
from datetime import date

import pytest

from fair_turn.core.effect import composition, outcomes, sentence
from fair_turn.core.types import FaultType, Job, SafetyClass, ScoredJob


def _scored(job_id: str, community_id: str) -> ScoredJob:
    job = Job(
        job_id=job_id,
        community_id=community_id,
        is_remote=community_id.startswith("remote"),
        reported_on=date(2025, 12, 30),
        fault_type=FaultType.COOLING,
        safety_class=SafetyClass.URGENT,
    )
    return ScoredJob(job=job, score=2.0, factors={}, rank=1, needs_human=False)


def _is_remote(community_id: str) -> bool:
    return community_id.startswith("remote")


def test_composition_counts_membership_changes_and_uses_singular_nouns() -> None:
    current = [_scored("job-1", "town-a"), _scored("job-3", "remote-a")]
    baseline = [_scored("job-1", "town-a"), _scored("job-2", "town-b")]

    assert composition(current, baseline, 2, _is_remote, "Balanced") == (
        "Balanced moves 1 job into today's list (1 remote, 0 town) and 1 job to the backlog "
        "(0 remote, 1 town)."
    )


def test_composition_returns_the_exact_zero_change_sentence() -> None:
    ranking = [_scored("job-1", "town-a"), _scored("job-2", "remote-a")]

    assert composition(ranking, ranking, 2, _is_remote, "Balanced") == (
        "No job changes between today's list and the backlog."
    )


def test_outcomes_formats_deltas_and_missing_values() -> None:
    current = {"median_wait_town": 4.5, "median_wait_remote": None, "travel_km": 120.0}
    baseline = {"median_wait_town": 4.0, "median_wait_remote": 7.0, "travel_km": 100.0}

    assert outcomes(current, baseline) == (
        "Simulated over the 90-day set against efficiency-first: town median wait +0.5 days, "
        "remote median wait not available, road km +20 %."
    )
    assert "road km not available" in outcomes(
        {**current, "travel_km": 100.0}, {**baseline, "travel_km": 0.0}
    )


@pytest.mark.parametrize(
    ("current", "baseline", "capacity"),
    [
        ([_scored("job-1", "town-a")], [_scored("job-2", "remote-a")], 1),
        ([_scored("job-1", "town-a")], [_scored("job-1", "town-a")], 1),
        (
            [_scored("job-1", "town-a"), _scored("job-3", "remote-a")],
            [_scored("job-1", "town-a"), _scored("job-2", "town-b")],
            2,
        ),
    ],
)
def test_before_signature_never_reveals_outcomes(
    current: list[ScoredJob], baseline: list[ScoredJob], capacity: int
) -> None:
    text = sentence("before_signature", current, baseline, capacity, _is_remote, "Balanced")

    assert not re.search(r"\b(wait|travel|median|cost)\b", text, flags=re.IGNORECASE)


def test_after_signature_adds_outcomes_and_requires_metrics() -> None:
    current = [_scored("job-1", "town-a")]
    baseline = [_scored("job-2", "remote-a")]
    metrics = {"median_wait_town": 4.5, "median_wait_remote": 6.0, "travel_km": 120.0}
    baseline_metrics = {"median_wait_town": 4.0, "median_wait_remote": 7.0, "travel_km": 100.0}

    text = sentence(
        "after_signature", current, baseline, 1, _is_remote, "Balanced", metrics, baseline_metrics
    )

    assert "efficiency-first" in text
    assert "90-day" in text
    assert "days" in text
    assert "%" in text
    with pytest.raises(ValueError, match="Metrics are required"):
        sentence("after_signature", current, baseline, 1, _is_remote, "Balanced")
