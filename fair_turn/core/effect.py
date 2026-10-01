"""The two-stage weighting effect sentence (PRD section 3.1)."""

from collections.abc import Callable, Iterable
from typing import Literal

from fair_turn.core import constants
from fair_turn.core.types import ScoredJob


def _today(scored: list[ScoredJob], capacity: int) -> dict[str, ScoredJob]:
    return {item.job.job_id: item for item in scored[:capacity]}


def _count_remote(jobs: Iterable[ScoredJob], is_remote: Callable[[str], bool]) -> int:
    return sum(is_remote(scored.job.community_id) for scored in jobs)


def composition(
    current: list[ScoredJob],
    baseline: list[ScoredJob],
    capacity: int,
    is_remote: Callable[[str], bool],
    preset_label: str,
) -> str:
    """Describe only the membership change in today's list, never simulated outcomes."""
    current_today = _today(current, capacity)
    baseline_today = _today(baseline, capacity)
    moved_in = [current_today[job_id] for job_id in current_today.keys() - baseline_today.keys()]
    moved_out = [baseline_today[job_id] for job_id in baseline_today.keys() - current_today.keys()]
    if not moved_in and not moved_out:
        return "No job changes between today's list and the backlog."

    remote_in = _count_remote(moved_in, is_remote)
    remote_out = _count_remote(moved_out, is_remote)
    in_noun = "job" if len(moved_in) == 1 else "jobs"
    out_noun = "job" if len(moved_out) == 1 else "jobs"
    return (
        f"{preset_label} moves {len(moved_in)} {in_noun} into today's list "
        f"({remote_in} remote, {len(moved_in) - remote_in} town) and "
        f"{len(moved_out)} {out_noun} to the backlog "
        f"({remote_out} remote, {len(moved_out) - remote_out} town)."
    )


def _wait_clause(label: str, current: float | None, baseline: float | None) -> str:
    if current is None or baseline is None:
        return f"{label} not available"
    return f"{label} {current - baseline:+.1f} days"


def _travel_clause(current: float | None, baseline: float | None) -> str:
    if current is None or baseline is None or baseline == 0:
        return "road km not available"
    return f"road km {(current - baseline) / baseline * 100:+.0f} %"


def outcomes(
    current_metrics: dict[str, float | None], baseline_metrics: dict[str, float | None]
) -> str:
    """Describe post-signature simulated outcomes against efficiency-first."""
    town = _wait_clause(
        "town median wait",
        current_metrics.get("median_wait_town"),
        baseline_metrics.get("median_wait_town"),
    )
    remote = _wait_clause(
        "remote median wait",
        current_metrics.get("median_wait_remote"),
        baseline_metrics.get("median_wait_remote"),
    )
    travel = _travel_clause(current_metrics.get("travel_km"), baseline_metrics.get("travel_km"))
    return (
        f"Simulated over the {constants.WINDOW_DAYS}-day set against efficiency-first: "
        f"{town}, {remote}, {travel}."
    )


def sentence(
    stage: Literal["before_signature", "after_signature"],
    current: list[ScoredJob],
    baseline: list[ScoredJob],
    capacity: int,
    is_remote: Callable[[str], bool],
    preset_label: str,
    current_metrics: dict[str, float | None] | None = None,
    baseline_metrics: dict[str, float | None] | None = None,
) -> str:
    """Return composition before the first signature and outcomes only afterwards."""
    composition_text = composition(current, baseline, capacity, is_remote, preset_label)
    if stage == "before_signature":
        return composition_text
    if stage != "after_signature":
        raise ValueError(f"Unknown effect stage: {stage}")
    if current_metrics is None or baseline_metrics is None:
        raise ValueError("Metrics are required after signature")
    return f"{composition_text} {outcomes(current_metrics, baseline_metrics)}"
