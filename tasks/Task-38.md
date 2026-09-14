# Task-38: Workspace table shows the whole row; a job is always selected; filters as pills

Status: DONE

> **Execution:** agent `codex` · effort `high` · plan mode **no**
> *Why:* `review-visual` 2026-09-14 found the row's safety class, window, score and factor bar behind a horizontal scroll and the page opening on an empty pane; the fixes are `column_config` and an auto-selection, both decided.

**Lane**
- OWNS: `fair_turn/app/pages/workspace.py`, `fair_turn/app/components/ranking_table.py`, `fair_turn/app/components/weighting.py`, `tests/test_page_workspace.py`
- MUST NOT TOUCH: `fair_turn/app/components/details_pane.py`, `fair_turn/app/components/workspace_map.py`, `fair_turn/app/components/intro.py`, `fair_turn/app/theme.py`, `.streamlit/config.toml`, `fair_turn/app/state.py`
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: 40

## Objective

At 1440 px the ranked table shows rank, change, job id, community and fault type and hides
the rest; the workspace opens with "Select a job" and an empty pane. Make every PRD 3.1 row
column visible without horizontal scroll, open the page on the top job of today's list, and
turn the fault and safety filters into pills.

## Execution Guide

- `ranking_table.column_config(frame)`: return a full config for the workspace `DISPLAY`
  columns: `rank` -> `NumberColumn("#", width="small")`; `rank change` -> `TextColumn("Delta",
  width="small", help="Change against efficiency-first")`; `job_id` -> `TextColumn("Job",
  width="medium", pinned=True)` (verify `pinned` exists on 1.63 with `inspect.signature`; if
  not, omit it and say so in NOTES); `community id` -> `TextColumn("Community",
  width="medium")`; `fault type` -> `TextColumn("Fault", width="small")`; `safety class` ->
  `TextColumn("Class", width="small")`; `window` -> `TextColumn("Window", width="small",
  help="Days used of the NT window")`; `score` -> `NumberColumn("Score", format="%.1f",
  width="small")`; `score_bar` -> `ProgressColumn("Factors", format="%.1f", min_value=0,
  max_value=<max of frame or 1>)`. Keep the per-factor `ProgressColumn`s for other callers.
- `workspace.py`: pass `column_config=ranking_table.column_config(frame)`, `hide_index=True`,
  `width="stretch"`, and a `height` that shows the whole of today's list without an inner
  scroll (`ranking_table.table_height(n_rows)` = header 38 px + 35 px per row, capped at 20
  rows; two named constants). When `state.get_selected_job_id()` is `None` and `today_list`
  is not empty, select `today_list[0].job.job_id` before rendering the pane (call the state
  setter; no rerun needed if done before the pane renders). Keep `selection_mode="single-row"`
  (a `"single-row-required"` on two tabs would fight over the selection).
- Column widths must hold at `st.columns([3, 2])`: if the nine columns still overflow at 1440 px
  after the config, fold `rank change` into the `#` column as a suffix (`"3 ^2"`) rather than
  hiding a PRD column, and say so in NOTES.
- `weighting.filters()`: replace the two `st.multiselect`s with `st.pills(label, options,
  selection_mode="multi", key=...)`; the return type stays `(region, faults, safeties)` with
  lists of enum values; `clear_filters` clears the pill keys. Region stays a selectbox (it sets
  capacity).
- Tests (`tests/test_page_workspace.py`, AppTest offline): on first render the details pane
  shows the top job of today's list (assert its id appears in the pane's subheader); the
  dataframe proto for today's list carries a `columns` config naming `score_bar` as a progress
  column; the pills exist and clearing them restores the row count. Existing tests stay green.

## Acceptance Criteria (DoD)

- [ ] Today's list renders all nine `DISPLAY` columns with a column config (asserted on the proto).
- [ ] First render selects today's top job; the pane is never the "Select a job" info box when today's list is non-empty.
- [ ] Fault and safety filters are pills; clear restores the full list.
- [ ] No hex or font literal outside `theme.py`; the two table-geometry pixel constants live in `ranking_table.py` with a docstring saying why.
- [ ] Gate green.
