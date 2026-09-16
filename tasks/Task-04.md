# Task-04: Capacity simulation and wait metrics

Status: DONE

> **Execution:** agent `codex` · effort `high`
> *Why:* PRD §6.3 fixes the toy model; pure Python over `core.types`; tests decide.

**Lane**
- OWNS: `fair_turn/core/capacity_sim.py`, `tests/test_capacity_sim.py`
- MUST NOT TOUCH: `fair_turn/core/scoring.py` (Task-02), `fair_turn/core/constants.py` (Task-00)
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-02

## Objective

Turn a ranking into wait times so the board can show remote median wait, town median
wait, the gap and travel cost for any λ. A measurement device, not a scheduler.

## Execution Guide

- `capacity_sim.py`: `simulate(jobs, lam, start, days, closures, crews_per_region, jobs_per_crew_day, travel_day_km) -> SimResult`. Each day: open jobs = reported and not completed; rank with `scoring.rank`; for each region's crews in order, take the top-ranked open job in that region, travel to its community (a travel day if `km_to_base > travel_day_km` and the crew is not already there), then complete up to `jobs_per_crew_day` open jobs in that community in rank order (batching); a community whose road is closed that day is skipped. Record `completed_on` per job.
- `SimResult`: per-job wait days, `median_wait_remote`, `median_wait_town`, `gap`, `travel_cost` (sum of `logistics_factor` of trips actually made), per-day open-queue length.
- Deterministic; no randomness inside.
- As built (otopilot 2026-09-13): `simulate` takes an extra `sites: Mapping[str, Site]` (region, km_to_base per community) because `Job` carries neither; jobs still open at the end count with a censored wait; `gap` is remote minus town and may be negative.
- Tests: two jobs, one crew → waits 0 and 1; batching: three jobs in one community complete the same day with capacity 4; closure blocks completion until it lifts; travel day adds one; λ = 1 vs λ = 0 on a fixture with one far high-need job: gap smaller at λ = 0.

## Acceptance Criteria (DoD)

- [x] `simulate` on the fixtures above matches the expected waits exactly.
- [x] On a 30-day slice of `data/build/labels.json` (skip if absent) the run completes in under 5 s and every job has `completed_on >= reported_on` or is still open at the end.
- [x] No import of pandas or numpy in `core`.
- [x] Gate green.
