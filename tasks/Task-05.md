# Task-05: Feedback-loop simulation

> **Execution:** agent `codex` · effort `high` · plan mode **no**
> *Why:* PRD §3.5 and report 6 fix the shape (reporting rate as a function of past service, decay as a slider parameter); pure Python; assertion-tested.

**Lane**
- OWNS: `fair_turn/core/feedback_sim.py`, `tests/test_feedback_sim.py`
- MUST NOT TOUCH: `fair_turn/core/capacity_sim.py` (Task-04), `fair_turn/core/scoring.py` (Task-02)
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-04

## Objective

Show over 90 days that efficiency-only allocation makes remote demand look like it dried
up, and that the equity setting does not, with the decay rate a labelled assumption.

## Execution Guide

- `feedback_sim.py`: `run(labels, communities, lam, decay, seed) -> WeeklySeries`. Week by week: each community's reporting multiplier `m = max(0.2, 1 − decay · unserved_share_last_4_weeks)`; the week's reports are the label set's reports for that community thinned by `m` (deterministic thinning by hashing job_id with the seed, no RNG state); `capacity_sim.simulate` runs the week; unserved share updates. Output per week: reports town / remote, median wait town / remote, gap.
- `decay = 0` must reproduce the plain capacity run exactly.
- Tests: decay 0 equals `capacity_sim` totals; with decay 0.5, λ = 1: remote reports in the last 4 weeks are below the first 4 weeks and the gap in week 12 exceeds week 1; with decay 0.5, λ = 0: remote reports in the last 4 weeks are at least 90 % of the first 4 weeks.

## Acceptance Criteria (DoD)

- [ ] The three assertions above pass on `data/build/labels.json` and `communities.csv` (fixtures if absent, but the artefact run is the real criterion once Task-03 lands).
- [ ] `run` is deterministic for a given seed.
- [ ] Runtime under 20 s for 90 days at any λ.
- [ ] Gate green.
