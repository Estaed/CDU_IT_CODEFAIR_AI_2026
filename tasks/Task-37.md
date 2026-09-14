# Task-37: Map markers in pixels, direct single-job pick, compact multi-job chooser

Status: TODO

> **Execution:** agent `codex` · effort `high` · plan mode **no**
> *Why:* the root cause is verified (Part 2 pydeck row, 2026-09-14) and the behaviour is fixed by PRD 3.1; only the two components change.

**Lane**
- OWNS: `fair_turn/app/components/workspace_map.py`, `fair_turn/app/components/details_pane.py` (only `_map_choice` and what it needs), `tests/test_workspace_components.py`
- MUST NOT TOUCH: `fair_turn/app/pages/`, `fair_turn/app/state.py`, `fair_turn/app/theme.py`, `fair_turn/app/components/map.py`
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: none

## Objective

Markers on the workspace map are 1-3 px at NT zoom and swallow a town when zoomed in, because
pydeck serialised `radius_units` as a data accessor and the layer fell back to metres
(Part 2, pydeck row). Fix the units, size markers in pixels, and make a marker that holds one
job select it directly; a marker that holds several offers a compact chooser, never a column of
buttons (`review-visual` 2026-09-14, BACKLOG).

## Execution Guide

- `workspace_map.py`: on both `ScatterplotLayer`s pass `radius_units="'pixels'"` (inner quotes;
  assert in a test that `deck.to_json()` contains `"radiusUnits": "pixels"` and no `@@=`),
  `radius_min_pixels=MARKER_MIN_PX`, `radius_max_pixels=MARKER_MAX_PX`, `stroked=True`,
  `line_width_min_pixels=1`, and compute the radius in pixels from `open_jobs`
  (`MARKER_MIN_PX + MARKER_STEP_PX * open_jobs`, clamped at `MARKER_MAX_PX`); rename the metre
  constants. Values: min 6, step 1, max 14, selected x 1.6. Keep the `id="jobs"` /
  `id="selected"` layers and the explicit ids. Keep `map_provider="carto"`, `map_style="light"`,
  the fallback path and `picked_id` unchanged.
- `details_pane._map_choice(map_choice, selected)`: when `job_ids` has exactly one id and it is
  not `selected`, call `state.set_selected_job_id(job_id)` and `st.rerun()` (no widget). When it
  has several, render one `st.selectbox("Choose a job at <community>", job_ids, index=None,
  placeholder="Pick a job", key=f"workspace_choose_{community_id}")`; on a choice set the
  selected id and rerun. Never render a button per job.
- Tests (AppTest with `socket.socket` refused, tiny throwaway scripts under `tmp_path`, as the
  file already does): the deck JSON carries pixel units on both layers and no `@@=` string; a
  one-job `map_choice` sets the selected id without rendering a selectbox; a three-job
  `map_choice` renders exactly one selectbox with three options and no buttons named after
  job ids; the existing tests stay green.

## Acceptance Criteria (DoD)

- [ ] `build_deck(...).to_json()` contains `"radiusUnits": "pixels"` for both layers and no `@@=`.
- [ ] Markers carry `radiusMinPixels`, `radiusMaxPixels`, `stroked` in the deck JSON.
- [ ] One-job marker selects directly; multi-job marker renders one selectbox and no per-job buttons (tests).
- [ ] No hex, size or font literal outside `theme.py` (existing theme test stays green).
- [ ] Gate green.
