# Task-25: Core: sign-off batch freeze and the two-stage effect sentence

Status: DONE

> **Execution:** agent `codex` · effort `high`
> *Why:* Two pure modules with exhaustive unit tests; PRD §3.1 and wireframes §3/§5 fix every rule.

**Lane**
- OWNS: `fair_turn/core/batch.py`, `fair_turn/core/effect.py`, `tests/test_batch.py`, `tests/test_effect.py`
- MUST NOT TOUCH: `fair_turn/core/audit.py` (Task-24), `fair_turn/core/scoring.py`, `fair_turn/app/`
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-24

## Objective

Decide-before-reveal and sign-off integrity as plain functions the page cannot get wrong:
a frozen batch that a later change invalidates, and an effect sentence that says only
composition before the first signature and outcomes after it.

## Execution Guide

- `batch.py`: `@dataclass(frozen=True) class Batch(day, version, lam, preset, today_job_ids, ranked_job_ids, hand_moves: tuple[HandMove, ...], fingerprint: str)`; `HandMove(job_id, from_rank, to_rank, reason)`. `freeze(day, version, lam, preset, ranked: list[ScoredJob], capacity: int, hand_moves) -> Batch` computes `today_job_ids` as the first `capacity` ranked ids and `fingerprint` as sha256 over (lam, ranked ids, hand moves, human-set values passed in). `is_stale(batch, current_fingerprint) -> bool`. `Status = Literal["draft", "review_open", "saving", "save_failed", "signed", "changed_since_signature"]`; `next_status(current, event) -> Status` as a table-driven state machine over events `open_review, change, submit_ok, submit_fail, cancel`; invalid transitions raise `ValueError`. `can_submit(batch, current_fingerprint, already_signed_versions) -> tuple[bool, str]` refuses a stale batch and a repeated version with a reason string.
- `effect.py`: `composition(current: list[ScoredJob], baseline: list[ScoredJob], capacity: int, is_remote: Callable[[str], bool]) -> str` → "Balanced moves 5 remote jobs into today's list and 5 town jobs to the backlog." (preset name passed in; "Custom (0.35)" when none); `outcomes(current_metrics: dict, baseline_metrics: dict) -> str` → the second sentence with baseline, period and units, using the metric keys `metrics.py` already produces; `sentence(stage: "before_signature" | "after_signature", ...)` composes. Words `wait`, `travel`, `median`, `cost` must not appear in the `before_signature` output (test greps for them).
- Tests: state machine table exhaustively; stale detection on each input change; duplicate version refused; composition counts on hand-built rankings including the zero case ("No job changes between today's list and the backlog."); before-signature sentence contains none of the forbidden words; after-signature sentence contains baseline, "90-day" and units.

## Acceptance Criteria (DoD)

- [ ] Every status transition in Part 2's decision-state table is tested, valid and invalid.
- [ ] Stale and duplicate submissions are refused with a reason.
- [ ] Before-signature sentence never names wait, travel, median or cost (test).
- [ ] Gate green.
