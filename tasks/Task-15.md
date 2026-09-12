# Task-15: Board map and metrics panel with decide-before-reveal

> **Execution:** agent `codex` · effort `high` · plan mode **no**
> *Why:* Altair map pattern is fixed by the Part 2 spike; the reveal rule is a boolean in `state`; assertions on chart presence and hidden state decide.

**Lane**
- OWNS: `fair_turn/app/components/map.py`, `fair_turn/app/components/metrics.py`, `tests/test_board_map_metrics.py`, `fair_turn/app/pages/board.py` (append two calls; Task-14 owns the file)
- MUST NOT TOUCH: `fair_turn/core/` (earlier tasks), `fair_turn/app/state.py` (Task-13)
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-14, Task-04

## Objective

The NT map of open jobs and the live wait metrics, hidden until the coordinator has
committed today's setting.

## Execution Guide

- `map.py`: `nt_map(communities, open_counts, region) -> alt.Chart`: `mark_geoshape` from `data/geo/nt_outline.geojson` loaded as inline `alt.Data(values=features)`, `mark_circle` at lon/lat sized by open jobs, coloured by `theme` region colours, tooltip community id / open / region; when a region is selected, filter and let the projection fit; `width="stretch"`. No `url` in the spec.
- `metrics.py`: `metrics_panel(sim_result_lam, sim_result_eff)`: four `st.metric`s (remote median wait, town median wait, gap, travel cost) with deltas against λ = 1.0; runs `capacity_sim.simulate` for the day's window, cached with `st.cache_data` keyed by (day, region, λ).
- Board wiring: map always shown; metrics shown only if `state.signed_today` is true, otherwise an `st.info` explaining that the panel appears after today's sign-off (PRD §3.1 decide-before-reveal).
- Tests: AppTest on the board: a Vega-Lite chart element exists whose spec has no `url`; with `signed_today` false there is no `st.metric`; setting the session key true and rerunning shows four metrics whose values equal `capacity_sim` output.

## Acceptance Criteria (DoD)

- [ ] Map spec contains no `url` and at least one geoshape layer (asserted from the AppTest element proto).
- [ ] Metrics hidden before sign-off and equal to `capacity_sim` after (asserted).
- [ ] Gate green.
