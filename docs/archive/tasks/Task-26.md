# Task-26: Core: visit plan in signed order with distance suggestions

Status: DONE

> **Execution:** agent `codex` · effort `high`
> *Why:* Deterministic planner with property tests; PRD §3.3 and Blueprint's constraint fix the rule (signed order is the plan, distance only suggests).

**Lane**
- OWNS: `fair_turn/core/visit_plan.py`, `tests/test_visit_plan.py`, `fair_turn/core/constants.py` (append-only: `CREW_BASE_COORDS`, `SUGGESTION_MIN_SAVING_KM`), `constants.md` (append provenance rows for the two)
- MUST NOT TOUCH: `fair_turn/core/scoring.py`, `fair_turn/core/capacity_sim.py`, `fair_turn/data/`, `fair_turn/app/`
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-25

## Objective

Turn a signed batch into a stop order per crew that is the signed order, measured in
kilometres, with at most a few explicit swap suggestions the coordinator may accept.
Air and barge jobs are never routed; nothing changes membership.

## Execution Guide

- Inputs are plain Python (core rule): `Stop(job_id, community_id, region, lat, lon, access: "road" | "air" | "barge", road_open: bool, signed_rank: int, window_days_left: int)`, `Crew(base: str, region: str, lat, lon, jobs_per_day: int)`. `CREW_BASE_COORDS` in `constants.py` maps the five `CREW_BASES` to (lat, lon) read from BushTel town records; add the provenance row.
- `plan(batch_version: int, stops: list[Stop], crews: list[Crew], road_factor: Callable[[Stop], float]) -> Plan`: assign each road stop to the crew of its region in signed order up to `jobs_per_day`; leftover road stops → `unplanned` with reason "over crew capacity"; `road_open=False` → `unplanned` with reason "road closed"; air/barge → `manual` with next action text "book air/barge freight". Per crew: `stops` in signed order, `km` as the sum of haversine (copy `haversine_km` into core; core cannot import `data`) × `road_factor` along base → stops → base. `within_capacity` is `len(stops) <= jobs_per_day and not unplanned`.
- `suggestions(plan) -> list[Suggestion]`: for each crew, every adjacent swap that lowers `km` by at least `SUGGESTION_MIN_SAVING_KM` (constant, provisional, 50) and keeps both stops on the same day (always true within one crew-day) and both `window_days_left >= 1`; `Suggestion(crew, job_a, job_b, old_order, new_order, saving_km)`. Never applied by `plan`.
- `apply(plan, suggestion, reason) -> Plan` returns a new plan with `changes` appended (`PlanChange(job_ids, reason, saving_km)`). `edit_order(plan, crew, new_order: list[str], reason) -> Plan` validates same membership.
- hypothesis tests: for random signed lists, `set(planned + unplanned + manual) == set(stops)`; planned order per crew is strictly increasing `signed_rank`; every `Suggestion` saving is ≥ the constant and applying it changes only the two named stops; `within_capacity` is False whenever `unplanned` is non-empty; no `manual` job ever appears in a crew's stops.

## Acceptance Criteria (DoD)

- [ ] Membership, signed-order and manual-never-routed invariants hold under hypothesis.
- [ ] Suggestions are never applied without `apply`, and `apply` records a reason.
- [ ] Constants appended with provenance rows; no literal copies of crew or capacity numbers in `visit_plan.py`.
- [ ] Gate green.
