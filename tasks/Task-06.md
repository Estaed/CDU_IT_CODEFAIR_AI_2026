# Task-06: Explanation templates: "why it sits here" and the tenant answer

Status: DONE

> **Execution:** agent `codex` · effort `high` · plan mode **no**
> *Why:* templates over `ScoredJob` factors, fully specified by PRD §3.1, §3.4 and §7; checked by unit tests and the wording lint.

**Lane**
- OWNS: `fair_turn/core/explain.py`, `tests/test_explain.py`
- MUST NOT TOUCH: `fair_turn/core/scoring.py` (Task-02), `fair_turn/core/wording.py` (Task-00)
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-02

## Objective

Every rank gets a sentence and every tenant a real answer, assembled from the score's
factors so they change instantly with λ and never come from a model.

## Execution Guide

- `explain.py`: `why_sentence(scored: ScoredJob, lam) -> str`: one sentence naming the two largest factors in words ("Ranked 4th: the job is 3 days past its 5-day remote window and a child under five lives in the house; travel cost is counted at the current setting."). `tenant_answer(scored, rank_at_lambda0, window_days, coordinator_reason, lam) -> str`: paragraphs for what was understood, where it sits and why, where it would sit if distance were ignored, the NT window for its class, and the coordinator's reason for the day's setting. Active voice, sentences about 15 words, year-7 level, no blame, no deficit terms; use "household health risk" wording from the enum names via a `LABELS` dict.
- Every factor with non-zero weight must be mentioned by its label at least once in `tenant_answer`.
- Tests: for a fixture `ScoredJob`, each factor label appears in the answer; `wording.check(answer) == []` for ten varied fixtures (all enums, both remoteness values); `why_sentence` mentions the two largest factors; changing λ changes the logistics phrase.

## Acceptance Criteria (DoD)

- [x] `tenant_answer` passes `wording.check` (no deficit term, FK grade at most 7) on all ten fixtures.
- [x] Factor-coverage test passes for every combination of health-risk factors.
- [x] No f-string reads any string field that could originate from a model; only enum labels and numbers.
- [x] Gate green.
