# Task-29: Workspace page: today's list, backlog, map, weighting, selected-job pane, overrides

Status: TODO

> **Execution:** agent `codex` · effort `high` · plan mode **no**
> *Why:* Every element is specified in PRD §3.1 and wireframes §3; the components and core functions exist by now. Visual fidelity is advisory (`review-visual` after DONE).

**Lane**
- OWNS: `fair_turn/app/pages/workspace.py`, `fair_turn/app/components/details_pane.py`, `fair_turn/app/components/weighting.py`, `fair_turn/app/components/ranking_table.py` (extend `rows_for` with delta, score and window-fraction columns), `tests/test_page_workspace.py`, `fair_turn/app/state.py` (append-only: `get_hand_moves`, `set_hand_moves`, `clear_hand_moves`; added by the orchestrator 2026-09-14 because hand moves before a signature need a session home and Task-23 defined none)
- MUST NOT TOUCH: `fair_turn/app/components/metrics.py` (Task-30), `fair_turn/app/intake.py` (Task-28), `fair_turn/app/state.py` beyond the three appended accessors (Task-23), `fair_turn/core/`
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-22, Task-23, Task-25, Task-27, Task-28

## Objective

The decision surface without its signature: what is proposed today, why, with what
evidence, and the coordinator's hand moves. Sign-off, metrics and decision states are
Task-30 on top of this file.

## Execution Guide

- Layout per wireframes §3: sidebar (weighting, filters), centre tabs "Today's list N" / "Backlog M" / "Map", right column details pane, bottom decision strip. Header: day, region, review count (jobs where `needs_human`), status placeholder text "Draft" (Task-30 replaces), "New report" button that toggles `intake.render`. Provenance caption.
- `weighting.py`: three `st.radio` presets → λ via a dict in `theme`-free code (`PRESETS = {"Efficiency first": 1.0, "Balanced": 0.5, "Need first": 0.0}` lives here, the λ values are not policy numbers); caption "Travel-cost weight 0.50. 0 ignores travel cost, 1 applies the full penalty."; `st.expander("Advanced")` with the slider labelled at both ends; slider off a preset → preset label "Custom (0.35)"; writes through `state.set_lam`/`set_preset`.
- Rankings: `current = scoring.rank(jobs, today, lam)`, `baseline = scoring.rank(jobs, today, 1.0)`; capacity from `constants` (crews for the selected region × `JOBS_PER_CREW_DAY`; "All" sums). Today's list = first `capacity` of `current` after applying hand moves from state; backlog = rest. Columns: rank, delta vs baseline (glyph + number), job id, community id, fault, safety badge text, `3 of 5 d` from `scoring.window_days`, score to one decimal, factor bar (existing Altair bar in a `column_config` image is out; use `st.column_config.ProgressColumn` for the total and keep the four factor values in the pane). "Compare with efficiency-first" checkbox → two `st.dataframe`s in `st.columns(2)` with identical columns.
- Effect sentence: `effect.sentence("before_signature", ...)` under the weighting (Task-30 switches the stage).
- `job_list.render` and `workspace_map.render` feed `state.set_selected_job_id`; the pane also has the "Select job" selectbox. Multi-job marker: the map returns a community id when a marker has several jobs; the pane then lists them as buttons.
- `details_pane.py`: header, why sentence (`explain.why_sentence`), score, four factor lines: extracted factors with phrase or "— No source phrase found"; computed factors with their source text ("from NT window: Urgent, day 3 of 5", "from geography: {km} km {access}, {open/closed}"); human-set values with `st.badge("Set by coordinator")`. Evidence expander: `highlight.render` plus a legend list (phrase → factor → field) plus the field/value/phrase/status table. Policy expander: `policy.lookup` passages with title, section, effective date; "No policy passage found above the relevance threshold" or "Policy index unavailable". Actions: move up/down (reason required) → `audit.Override`; promote from backlog (reason) → `audit.Promotion` naming the displaced job; send to review (reason) → `audit.HumanSet(field="review_requested", value=reason)`; the page treats a job with such a record for the day as `needs_human` (it leaves both frames and appears in the review queue). Undo before signing removes the hand move from state and writes nothing.
- Filters change the displayed frames only (caption says so). Decision strip: counts and a "Review and sign" button that Task-30 wires; until then disabled with the caption "Sign-off arrives in Task-30".
- Tests (AppTest, sockets refused): today's list length equals capacity for "All"; a job with `needs_human` is in no frame; the effect sentence contains no forbidden words; selecting a job through state shows its id in the pane; a promoted backlog job appears in today's list and one `Promotion` line is written to a temporary audit path; the compare checkbox renders two dataframes with identical columns; a fixture job with a human-set field shows the badge text; no hex literal in the new files.

## Acceptance Criteria (DoD)

- [ ] Capacity split, review exclusion, compare view and effect sentence asserted.
- [ ] Overrides (move, promote, send to review) each write exactly one audit record with a reason; empty reason writes nothing.
- [ ] Computed factors never render "No source phrase found"; extracted empty fields always do (fixture-based test).
- [ ] Policy passages render with title, section and date; the unavailable state renders its message.
- [ ] Gate green.
