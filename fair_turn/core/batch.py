"""Frozen sign-off batches and decision states (PRD section 3.1)."""

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from typing import Literal

from fair_turn.core.types import ScoredJob


@dataclass(frozen=True)
class HandMove:
    """A coordinator's explained rank change in a frozen sign-off batch."""

    job_id: str
    from_rank: int
    to_rank: int
    reason: str


@dataclass(frozen=True)
class Batch:
    """The exact ranked list a coordinator opened for review."""

    day: date
    version: int
    lam: float
    preset: str | None
    today_job_ids: tuple[str, ...]
    ranked_job_ids: tuple[str, ...]
    hand_moves: tuple[HandMove, ...]
    fingerprint: str


def fingerprint_of(
    lam: float,
    ranked_job_ids: tuple[str, ...] | list[str],
    hand_moves: Iterable[HandMove],
    human_set: dict[str, dict[str, str]] | None,
) -> str:
    """Return the canonical digest for all inputs that can invalidate a review."""
    payload = {
        "lam": lam,
        "ranked_job_ids": list(ranked_job_ids),
        "hand_moves": [
            [move.job_id, move.from_rank, move.to_rank, move.reason] for move in hand_moves
        ],
        "human_set": human_set,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def freeze(
    day: date,
    version: int,
    lam: float,
    preset: str | None,
    ranked: list[ScoredJob],
    capacity: int,
    hand_moves: Iterable[HandMove],
    human_set: dict[str, dict[str, str]] | None = None,
) -> Batch:
    """Freeze the page's already-final order for a batch version."""
    ranked_job_ids = tuple(scored.job.job_id for scored in ranked)
    frozen_moves = tuple(hand_moves)
    return Batch(
        day=day,
        version=version,
        lam=lam,
        preset=preset,
        today_job_ids=ranked_job_ids[:capacity],
        ranked_job_ids=ranked_job_ids,
        hand_moves=frozen_moves,
        fingerprint=fingerprint_of(lam, ranked_job_ids, frozen_moves, human_set),
    )


def is_stale(batch: Batch, current_fingerprint: str) -> bool:
    """Whether the current list, weighting, moves, or fields differ from the review."""
    return batch.fingerprint != current_fingerprint


def preset_label(lam: float, preset: str | None) -> str:
    """Display a named weighting preset or the current custom value."""
    return preset if preset is not None else f"Custom ({lam:.2f})"


Status = Literal[
    "draft",
    "review_open",
    "saving",
    "save_failed",
    "signed",
    "changed_since_signature",
]
Event = Literal["open_review", "change", "submit", "submit_ok", "submit_fail", "cancel"]

TRANSITIONS: dict[tuple[Status, Event], Status] = {
    ("draft", "change"): "draft",
    ("draft", "open_review"): "review_open",
    ("review_open", "change"): "draft",
    ("review_open", "cancel"): "draft",
    ("review_open", "submit"): "saving",
    ("saving", "submit_ok"): "signed",
    ("saving", "submit_fail"): "save_failed",
    ("save_failed", "open_review"): "review_open",
    ("save_failed", "cancel"): "draft",
    ("save_failed", "change"): "draft",
    ("signed", "change"): "changed_since_signature",
    ("signed", "open_review"): "review_open",
    ("changed_since_signature", "change"): "changed_since_signature",
    ("changed_since_signature", "open_review"): "review_open",
}


def next_status(current: Status, event: Event) -> Status:
    """Advance the sign-off state machine or reject an impossible transition."""
    try:
        return TRANSITIONS[(current, event)]
    except KeyError as exc:
        raise ValueError(f"{current} cannot take {event}") from exc


def can_submit(
    batch: Batch, current_fingerprint: str, already_signed_versions: Iterable[int]
) -> tuple[bool, str]:
    """Validate a review remains current and has not already been signed."""
    if is_stale(batch, current_fingerprint):
        return False, "The list changed since you opened this review; open it again."
    signed_versions = set(already_signed_versions)
    if batch.version in signed_versions:
        return (
            False,
            f"Batch v{batch.version} was already signed; open the review again "
            f"for v{batch.version + 1}.",
        )
    return True, ""
