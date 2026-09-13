# Task-17: Sign-off page and audit log page

> **Execution:** agent `codex` · effort `medium` · plan mode **no**
> *Why:* two forms over `core.audit` with fixed records (PRD §3.3, §3.6); behaviour is asserted through the log file.

**Lane**
- OWNS: `fair_turn/app/pages/sign_off.py`, `fair_turn/app/pages/audit_log.py`, `scripts/seed_audit.py`, `data/audit/sample.jsonl`, `tests/test_pages_signoff_audit.py`, `fair_turn/app/state.py` (the revision-on-λ-change hook inside `set_lam` only; added 2026-09-13 by the orchestrator because `board.py` and `state.py` are outside this lane and Task-13 is DONE)
- MUST NOT TOUCH: `fair_turn/core/audit.py` (Task-07), `fair_turn/app/pages/board.py` (Task-14, Task-15), `fair_turn/app/state.py` beyond the revision hook (Task-13)
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-15, Task-16

## Objective

The human owns the decision: commit λ and a reason, sign, and see the record of every
day's settings, revisions and overrides with the override rate over time.

## Execution Guide

- Sign-off page: shows the current λ and the ranked job ids for the day; form with reason (required), signer name (required); submit → `audit.append(SignOff)`, `state.signed_today = True`; if already signed today, any λ change on the board calls `audit.append(Revision)` (wire through a `state` helper `on_lambda_change`). Nothing is dispatched; say so on the page in one line.
- Audit page: table from `audit.export_rows` (`st.dataframe`), filter by day and kind, download button (CSV via pandas), Altair line of `override_rate` over days in theme colours.
- `scripts/seed_audit.py`: writes `data/audit/sample.jsonl` with three signed days, one revision and two overrides so the demo has history; committed.
- Tests: submitting without a reason writes nothing; with reason writes one `SignOff` and flips `signed_today`; a λ change after signing writes a `Revision`; audit page renders one Vega-Lite chart and a dataframe with the sample's row count.

## Acceptance Criteria (DoD)

- [ ] All four behaviours asserted with a temporary log path.
- [ ] `data/audit/sample.jsonl` committed and loaded by the audit page.
- [ ] Gate green.
