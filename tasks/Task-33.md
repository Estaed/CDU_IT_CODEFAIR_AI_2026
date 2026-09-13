# Task-33: Tenant answer: question-headed blocks, signed rank versus visit order, per-state copy

Status: DONE

> **Execution:** agent `codex` · effort `high` · plan mode **no**
> *Why:* Template work with a machine-checked reading level and factor coverage; PRD §3.4 and wireframes §7 fix every block and state.

**Lane**
- OWNS: `fair_turn/core/explain.py` (`tenant_answer` and new helpers), `fair_turn/app/pages/tenant.py`, `tests/test_explain.py`, `tests/test_page_tenant.py`
- MUST NOT TOUCH: `fair_turn/core/visit_plan.py`, `fair_turn/core/audit.py`, `fair_turn/app/pages/workspace.py`
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-26, Task-30

## Objective

The tenant reads what was understood, where the job sits and why, what happens next and
who can look it up, in year-7 English, with the signed rank and the visit order told
apart and every state answered honestly.

## Execution Guide

- `explain.tenant_answer(...)` returns a `TenantAnswer(blocks: list[Block(question, paragraphs)])` with the four questions from PRD §3.4. New inputs: `state: Literal["ranked", "review", "backlog", "unsigned", "manual", "superseded", "unknown"]`, `signed_rank`, `visit_order: tuple[int, str] | None` (position and the recorded reason), `policy: Passage | None`, `decision_version`. Rules: window stated as a policy target with source title and date, never a promised time; "We do not have a visit date yet." when none; contact block names the Community Housing Officer with no details; λ = 0 counterfactual worded as a formula comparison ("If distance did not count, your repair would be number 3."), never as a route. Per-state copy per wireframes §7; the review state says a person is checking the report and names what is missing in plain words; superseded names the version used.
- Every scored factor appears in the words (existing test extended); FK grade ≤ 7 over every state and a sample of 50 jobs; the deficit-language lint covers the new strings.
- Page: `st.container(border=True)` per block with the question as heading; empty state explains the registration number format; unknown or malformed id gets its own copy; policy source line under "What happens next".
- Tests: `TenantAnswer` for each state has the four blocks; FK ≤ 7 parametrised over states; visit-order sentence appears only when `visit_order` is set and names the reason; no digit-hour or promised-date phrasing (grep for "will arrive", "at \d"); AppTest renders the four containers for a fixture id and the unknown-id copy for a bad id.

## Acceptance Criteria (DoD)

- [ ] Four blocks in every state; FK ≤ 7 in every state (parametrised test).
- [ ] Signed rank and visit order distinguished, with the recorded reason, only when they differ.
- [ ] No promised visit time or invented contact detail (tests grep the rendered text).
- [ ] Gate green.
