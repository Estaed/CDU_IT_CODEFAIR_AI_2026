# Task-39: Empty and refusal states that show what they refuse; review queue and tenant framing

Status: DONE

> **Execution:** agent `codex` · effort `medium`
> *Why:* copy and states are fixed by the research reports and PRD 3.2-3.4; no design choice is open.

**Lane**
- OWNS: `fair_turn/app/pages/visit_plan.py`, `fair_turn/app/pages/tenant.py`, `fair_turn/app/pages/review_queue.py`, `tests/test_page_visit_plan.py`, `tests/test_page_tenant.py`, `tests/test_page_review_queue.py`
- MUST NOT TOUCH: `fair_turn/app/pages/workspace.py`, `fair_turn/app/pages/evidence_lab.py`, `fair_turn/app/components/`, `fair_turn/core/`, `fair_turn/data/`
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: 40

## Objective

The visit plan and the tenant answer open as a one-line refusal; the review queue names no
rule and shows no progress. Every empty or refusal state states its status, the cue and the
pathway (NN/g empty-state pattern, `reports/research-ui-hitl-guidance-2026-09-14.md`), and the
pages use the copy drafted there.

## Execution Guide

- Purpose lines come from `fair_turn/app/components/intro.py` (Task-40, already on main); the
  state texts below go in the page modules as named constants.
- `visit_plan.py`, before a signature: a `st.container(border=True)` holding
  `st.info("Nothing to plan yet. Sign today's batch on the workspace and the run sheet appears here.")`,
  an empty `st.dataframe` with the run sheet's columns (`stop, crew, job, community, distance km`)
  captioned "Columns of the run sheet", and `st.page_link("pages/workspace.py", label="Go to the
  workspace")` replacing the button. Keep every signed-state behaviour unchanged.
- `tenant.py`: title "Tenant answer" (matches the navigation). Under the input add
  `st.selectbox("Or try an example", options, index=None, placeholder="Pick an example job")`
  with three ids drawn from the artefacts at render time: one in today's ranked list, one in
  the backlog, one in the review queue (pick the first of each by sorted id; label each option
  "JR-... - ranked today" etc.); choosing one fills the lookup as if typed. Not-found copy:
  "We could not find that job number. Check the number on your repair receipt and try again."
  Keep the year-7 reading level check green (`core.wording.check`).
- `review_queue.py`: under the title, `st.progress(position / total, text="1 of 21 to review")`;
  a caption naming the membership rule: "Jobs arrive here when a field has no matching words
  in the report, failed the schema, or was not extracted. The system never fills a field on
  its own." For each field that needs review, above the selectbox: "No matching words in the
  report. Set this field yourself, and say why." Give the field table a `column_config` so the
  phrase column is readable (`width="large"`), `hide_index=True`, `width="stretch"`.
- Tests: AppTest offline; the visit plan before a signature renders one `page_link`-bearing
  container and an empty dataframe with five columns; the tenant page title is "Tenant answer"
  and the example selectbox has three options whose ids are open jobs; the review queue shows
  a progress element and the membership caption. Existing tests stay green.

## Acceptance Criteria (DoD)

- [ ] Visit plan refusal state: bordered container, info text, empty run-sheet columns, page link (test).
- [ ] Tenant page title "Tenant answer"; example selectbox with three ids of three states (test).
- [ ] Review queue: progress with "n of N", membership caption, per-field cue text (test).
- [ ] Wording lint green on every new string (no deficit language; FK grade at most 7 for tenant copy).
- [ ] Gate green.
