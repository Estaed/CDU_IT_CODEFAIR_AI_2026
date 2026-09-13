# Task-30: Sign-off form, decision states, metrics reveal; retire the Phase 1 board, job card and sign-off pages

Status: DONE

> **Execution:** agent `codex` · effort `high` · plan mode **no**
> *Why:* `core/batch.py` carries the rules; this task is the form, the header status and the wiring, all assertable through AppTest.

**Lane**
- OWNS: `fair_turn/app/pages/workspace.py` (sign-off section, header status, strip button), `fair_turn/app/components/sign_off_form.py`, `fair_turn/app/components/metrics.py`, `tests/test_page_workspace_signoff.py`, delete `fair_turn/app/pages/board.py`, `job_card.py`, `sign_off.py`, `tests/test_page_board.py`, `tests/test_page_job_card.py`, `tests/test_board_map_metrics.py`, `tests/test_pages_signoff_audit.py` (move the audit-page tests to Task-34's file first: see guide)
- MUST NOT TOUCH: `fair_turn/app/pages/evidence_lab.py` (Task-34), `fair_turn/core/`
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-29

## Objective

The signature: a frozen batch reviewed in place, invalidated by any change, written with
an audit reference; the metrics and the outcome sentence appear only after it; the header
shows the decision state. The three Phase 1 pages this replaces are deleted.

## Execution Guide

- `sign_off_form.py`: `render(batch: Batch, status, on_submit)` as a bordered `st.form` per wireframes §5: read-only summary (weighting with number, counts, hand moves with reasons, review count), `st.expander("Open today's list")` with the frozen batch rows in the workspace's columns, signer `text_input`, decision `selectbox` (Approve today's list / Defer), reason `text_area`, date caption "dataset day; recorded time is the wall clock", single primary button "Sign today's list". Inline validation (red text under the field, no modal). On success `st.success` with `audit_ref` in mono.
- Workspace wiring: "Review and sign" → `batch.freeze(...)` into `state.set_batch`, status `review_open`; every rerun computes the current fingerprint and, if `is_stale`, replaces the summary with the "list changed" message and a "Open again" button; submit → `can_submit` → `audit.SignOff(... batch_version, today_job_ids, decision, audit_ref)` → status `signed`, `state.set_signed_today(True)`; failure writing → `st.error`, status `save_failed`. Later λ change or hand move → `audit.Revision`/`Override` as today and status `changed_since_signature`; the header text reads "Signed v1 10:42 by A. Coordinator" / "Changed since signature (signed v1 stays authoritative)".
- `metrics.py`: keep `simulation`/`panel_values`; `metrics_panel` renders only when `state.get_signed_today()`; add the outcome sentence through `effect.sentence("after_signature", ...)` from the same values. Move the panel from the board into the workspace below the strip.
- Deletions: the three pages and their tests. Before deleting `tests/test_pages_signoff_audit.py`, copy its audit-page assertions into `tests/test_page_evidence_lab.py` as skipped tests (`pytest.mark.skip(reason="Task-34")`) so nothing is lost; Task-34 unskips them.
- Tests: before signing, no element text contains "median wait" or "travel cost"; opening the form then changing λ shows the stale message and the submit path is refused; a valid submit writes one `SignOff` with `batch_version == 1` and `audit_ref` matching the format, and the metrics panel then renders; a second identical submit is refused; a λ change after signing writes a `Revision` and the header shows "Changed since signature"; every page in `pages/` still opens.

## Acceptance Criteria (DoD)

- [ ] Decide-before-reveal asserted on element text before and after a signature.
- [ ] Stale review, duplicate version and save failure each surface as specified and write nothing.
- [ ] Phase 1 board, job card and sign-off pages and tests deleted; the audit-page tests preserved as skipped in the evidence-lab test file.
- [ ] Gate green.
