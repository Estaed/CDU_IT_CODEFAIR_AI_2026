# Task-32: Visit plan page

Status: DONE

> **Execution:** agent `codex` · effort `medium`
> *Why:* Rendering over `core/visit_plan.py`; states and copy fixed in wireframes §6 and PRD §3.3.

**Lane**
- OWNS: `fair_turn/app/pages/visit_plan.py`, `tests/test_page_visit_plan.py`
- MUST NOT TOUCH: `fair_turn/core/visit_plan.py` (Task-26), `fair_turn/app/pages/workspace.py`
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-26, Task-30

## Objective

Show the signed list as crew stops in signed order with kilometres, offer the planner's
swap suggestions for acceptance with a reason, keep air and barge work visible as manual,
and record every plan decision against the batch version.

## Execution Guide

- Not signed: `st.info("Sign today's list first")` plus a button to the workspace. Signed: build `Stop`s from the signed batch's `today_job_ids` (coordinates and access from the communities table through `artefacts`, `road_factor` from the geography layer's road-access factor), `Crew`s from `constants` and `CREW_BASE_COORDS`; `plan = state.get_plan() or visit_plan.plan(...)`.
- Per crew a bordered container: header "Crew {base} ({n} jobs/day, road)", numbered stops with job id, community id, km from the previous stop, fault, "signed rank r", then "Within job-count capacity — {km} km" or "Does not fit: {k} signed jobs unplanned". "Suggested changes (not applied)" list with old/new order and saving, reason input and "Accept change" → `visit_plan.apply` + `audit.PlanDecision(action="suggestion_accept")`. "Signed work needing manual coordination" with next action and owner. Unplanned with reasons. Footer: plan status Draft / Accepted / Superseded (superseded when `plan.batch_version != current signed version`), "Accept plan", "Edit order" (a stop-number `selectbox` per row, reason required, `visit_plan.edit_order`), "Reject with reason". Each writes one `PlanDecision`. The selected stop sets `state.set_selected_job_id`.
- No hours anywhere (test greps the page text for " h " and "hours").
- Tests (AppTest with a signed fixture batch): unsigned state; stop order equals signed order per crew; a manual (barge) fixture job appears under manual and in no crew; accepting a suggestion writes one `PlanDecision` and reorders exactly two stops; a plan built on version 1 shows "Superseded" once the fixture signs version 2; page text contains no hours.

## Acceptance Criteria (DoD)

- [ ] Signed order, manual visibility and superseded state asserted.
- [ ] Every plan action writes one audit record with a reason; empty reason writes nothing.
- [ ] No hours in page text.
- [ ] Gate green.
