# Task-45: Today's list as readable job rows with one-click open

Status: DONE

> **Execution:** agent `claude` · effort `high` · plan mode **no**
> *Why:* Tarik (2026-09-14): the checkbox column reads as multi-select and the dataframe is hard for a person to scan; Streamlit 1.63 has no row-click selection on `st.dataframe`, so today's list becomes a list of bordered rows (GOV.UK task-list / MOJ card pattern, `reports/research-ui-dispatch-products-2026-09-14.md` §1, `reports/research-ui-hitl-guidance-2026-09-14.md`).

**Lane**
- OWNS: `fair_turn/app/components/job_rows.py` (new), `fair_turn/app/pages/workspace.py`, `tests/test_job_rows.py` (new), `tests/test_page_workspace.py`
- MUST NOT TOUCH: `fair_turn/app/components/ranking_table.py`, `fair_turn/app/components/details_pane.py`, `fair_turn/app/components/intake.py`, `fair_turn/app/intake.py`, `fair_turn/app/state.py`, `fair_turn/app/theme.py`, `.streamlit/config.toml`, `fair_turn/core/`
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: 38, 41, 42

## Objective

Today's list (at most capacity rows, usually 14) renders as one bordered row per job that a
person can read top to bottom and open with one click. The backlog (hundreds of rows) and the
compare view keep the dataframe. The selected job is shared exactly as before (state seam).

## Execution Guide

- `components/job_rows.py`: `render(rows: list[dict], selected_id: str | None, key: str) -> str | None`.
  Each `rows` item carries `job_id, rank, rank_change, community_id, is_remote, fault_type,
  safety_class, window, score, score_max, human_queue` (build the dicts in `workspace.py` from
  the same `ScoredJob`s and `ranking_table.rows_for` output the table uses; do not recompute
  scores). Each row is `st.container(border=True)` with `st.columns([0.7, 1.6, 2.2, 1.6, 1.6, 0.9],
  vertical_alignment="center")`:
  1. rank as `st.markdown(f"**{rank}**")` and, when `rank_change` is not the unchanged glyph,
     a caption with it;
  2. job id in code style (`st.markdown(f"`{job_id}`")`) and a caption with the fault type label;
  3. community id and a `st.badge("Remote" | "Town", color="gray")`;
  4. safety class badge (`immediate` red, `urgent` orange, `routine` gray, same map as
     `details_pane`) and a caption with the window text ("6 of 2 d");
  5. score to one decimal and `st.progress(min(score / score_max, 1.0))` (no text);
  6. a button labelled "Open" (`type="primary"` when this row is the selected job, else
     `"secondary"`; `key=f"{key}_open_{job_id}"`), which returns the job id when clicked.
  The selected row also carries `st.badge("Selected", color="orange")` next to the rank. Return
  the clicked id or `None`; never touch session state inside the component.
- `workspace.py`: in the "Today's list" tab, when `compare` is off, call `job_rows.render(...)`
  instead of the dataframe; on a returned id call `state.set_selected_job_id` and `st.rerun()`.
  The backlog tab keeps the dataframe (with its `column_config`, `single-row` selection and
  `table_height`); above it add `st.text_input("Find in backlog", placeholder="Job id or
  community")` that filters the backlog frame by substring on job id and community id
  (display only; never changes ranking or capacity). Compare mode is unchanged (two frames).
  Keep the first-render auto-selection of the top job.
- Named constants for the column ratios and the badge colour map live in `job_rows.py`; no
  hex literals.
- Tests: `tests/test_job_rows.py` (AppTest offline over a throwaway script): 3 rows render 3
  bordered containers, 3 "Open" buttons, the selected row's button is primary and carries the
  "Selected" badge text; clicking the second "Open" makes `render` return that id (simulate by
  `at.button[...].click().run()` and asserting the script's stored return value in session
  state written by the throwaway script, not by the component). `tests/test_page_workspace.py`:
  today's tab has no dataframe and `cap` "Open" buttons when compare is off; the backlog tab
  still has one dataframe; the backlog search narrows the frame; existing tests updated where
  they counted today's dataframe.

## Acceptance Criteria (DoD)

- [ ] Today's list renders as bordered rows with rank, id, community, class badge, window, score bar and an Open button (tests).
- [ ] Clicking Open selects the job; the pane and the map highlight follow (state seam unchanged).
- [ ] Backlog keeps the dataframe and gains a display-only search (test).
- [ ] No hex, size or font literal outside `theme.py`.
- [ ] Gate green.
