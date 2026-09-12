# Task-18: Tenant view

> **Execution:** agent `codex` · effort `medium` · plan mode **no**
> *Why:* one lookup form over `explain.tenant_answer` (PRD §3.4); wording lint and equality with the counterfactual rank decide.

**Lane**
- OWNS: `fair_turn/app/pages/tenant.py`, `tests/test_page_tenant.py`
- MUST NOT TOUCH: `fair_turn/core/explain.py` (Task-06), `fair_turn/app/pages/board.py` (Task-14)
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-17

## Objective

A tenant types a job registration number and gets a real answer, including where the
job would sit if distance were ignored and why the coordinator chose today's setting.

## Execution Guide

- Page: text input for job id; unknown id → plain message, no stack trace; known id → `tenant_answer` with `rank_at_lambda0` from `scoring.rank(open_jobs, today, 0.0)`, the day's `SignOff` reason and λ from the audit log (latest for that day; if none, say the day is not yet signed), the NT window from `constants`. Year-7 wording is the template's job; the page adds nothing but headings.
- Provenance line and a one-line note that community ids are pseudonymous.
- Tests: AppTest with a known id: the rendered text contains the job id, the λ = 0 rank computed independently in the test, and passes `wording.check`; unknown id renders the plain message and no exception.

## Acceptance Criteria (DoD)

- [ ] Counterfactual rank on the page equals the test's independent `scoring.rank` at λ = 0.
- [ ] Page text passes `wording.check` for five sampled jobs.
- [ ] Gate green.
