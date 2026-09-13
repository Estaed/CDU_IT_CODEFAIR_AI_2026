# Task-31: Review queue page

Status: DONE

> **Execution:** agent `codex` · effort `medium` · plan mode **no**
> *Why:* One page over existing store and audit functions; wireframes §4 and PRD §3.2 fix the copy and the states.

**Lane**
- OWNS: `fair_turn/app/pages/review_queue.py`, `tests/test_page_review_queue.py`
- MUST NOT TOUCH: `fair_turn/app/pages/workspace.py` (Task-29/30), `fair_turn/app/intake.py` (Task-28), `fair_turn/data/runtime.py` (Task-23)
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-23, Task-24, Task-28

## Objective

One job at a time, source beside fields, the missing field named with its reason, never
the rejected value; a human sets it with a reason and is told where the job landed.

## Execution Guide

- Queue = jobs with `needs_human` for the day plus runtime intake reports with status `needs_review` / `not_extracted` plus jobs sent to review (Task-29's `review_requested` records). Cursor in `state.get/set_review_cursor`; "Previous"/"Next" buttons; header "JR-… — community — k of N — fault type needs review".
- Two columns: verbatim report (`st.markdown` with highlights of the verified phrases only) and the fields table (field, value or —, phrase or reason, badge). Reason text per field: "the proposed source phrase was not found in the report" (verification failed), "the field was not extracted" (absent), "the extraction did not validate" (schema), "not extracted: {cause}" (intake failure). The model's rejected value must not appear anywhere on the page: build the table from `VerifiedExtraction` only.
- Controls: `st.selectbox` per missing required field over the enum, reason `text_input` (required), "Mark rankable" → one `runtime.HumanSetField` per set field (actor from a signer name kept in state, default "coordinator") plus one `audit.HumanSet` each; success line "JR-… is now rank R, in today's list / in the backlog" computed with `scoring.rank`, plus a button "Open in workspace" that sets the selected id and switches page via `st.switch_page`. Cursor advances. "Request clarification" writes `audit.HumanSet(field="clarification_requested", value=reason)` and the job stays. "Leave in queue" advances. Empty queue: "All reports reviewed" and a button to the workspace.
- Tests (AppTest, sockets refused, temporary runtime and audit paths): the page text never contains the enum value the fixture's extraction proposed for the failed field; marking rankable writes one runtime and one audit record and the success line names a rank; empty reason writes nothing and shows the error; the empty state renders when the fixture has no queue; previous/next wrap correctly at both ends.

## Acceptance Criteria (DoD)

- [ ] Rejected value absent from page text (fixture with a known wrong-phrase extraction).
- [ ] Human-set flow writes exactly one runtime and one audit record per field and reports the resulting rank.
- [ ] Empty state, cursor bounds and required reason tested.
- [ ] Gate green.
