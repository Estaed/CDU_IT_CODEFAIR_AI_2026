# Task-02: Core types and the ranking formula

> **Execution:** agent `codex` · effort `high` · plan mode **no**
> *Why:* fully specified by PRD §4 and Part 2; pure Python; the criterion is tests plus a hypothesis property.

**Lane**
- OWNS: `fair_turn/core/types.py`, `fair_turn/core/scoring.py`, `tests/test_scoring.py`
- MUST NOT TOUCH: `fair_turn/core/constants.py` (Task-00), `fair_turn/data/` (Task-01, Task-03)
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-00

## Objective

Define the typed job record every layer shares and the transparent score the
coordinator controls: `score = need − λ · logistics`, reading typed fields only.

## Execution Guide

- `types.py`: `enum.StrEnum`s `FaultType` (electrical, plumbing_water, sewer_drainage, cooling, hot_water, roof_structure, doors_locks_security, stove_cooking, pests, other), `SafetyClass` (immediate, urgent, routine), `HealthRiskFactor` (infant_or_young_child, elderly, pregnancy_or_chronic_condition, overcrowding, extreme_heat_exposure, no_water_or_sanitation). Frozen dataclasses `Job` (job_id, community_id, is_remote, reported_on, fault_type | None, safety_class | None, health_risk: frozenset[HealthRiskFactor], logistics_factor, road_closed: bool, crew_nearby: bool) and `ScoredJob` (job, score, factors: dict[str, float], rank, needs_human: bool).
- `scoring.py`: `urgency(job, today)` = days elapsed / window days for its class and remoteness (from `constants`), capped at 3.0 so a job past its window keeps rising; `safety(job, today)` = 3 / 2 / 1 for immediate / urgent / routine, +1 for cooling or hot_water in a remote community during heat-season months; `health_risk(job)` = 0.5 per factor; `logistics(job)` = `logistics_factor / 100`, +2 if `road_closed`, −0.5 if `crew_nearby`, floor 0. `score_job(job, today, lam) -> ScoredJob`; `rank(jobs, today, lam) -> list[ScoredJob]` sorts descending, stable on job_id; any job with `fault_type is None or safety_class is None` gets `needs_human=True`, `score=None` and is excluded from ranks (returned in a separate list by `split_human_queue(jobs)`).
- `tests/test_scoring.py`: fixture jobs for each rule; hypothesis property: for random job lists, `rank(jobs, today, 0.0)` order is identical after shuffling every `logistics_factor` and `road_closed` across jobs; λ = 1 puts a far routine job below a near routine job with equal need; human-queue jobs never appear in `rank` output.

## Acceptance Criteria (DoD)

- [ ] `score_job` returns factors for exactly `urgency`, `safety`, `health_risk`, `logistics`, and `score == urgency + safety + health_risk − lam * logistics` within 1e-9.
- [ ] Hypothesis property (λ = 0 invariance) passes with at least 200 examples.
- [ ] Human-queue exclusion and stable ordering tested.
- [ ] `fair_turn/core` imports no pandas, streamlit, subprocess or network module (layer test).
- [ ] Gate green.
