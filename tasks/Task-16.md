# Task-16: Job card with source-phrase highlights and per-job override

Status: DONE

> **Execution:** agent `codex` · effort `high` · plan mode **no**
> *Why:* PRD §3.2 fully specifies the card; highlight rendering is string work over verified spans; override writes an audit record; all assertable.

**Lane**
- OWNS: `fair_turn/app/pages/job_card.py`, `fair_turn/app/components/highlight.py`, `tests/test_page_job_card.py`, `fair_turn/app/state.py` (append the human-set field accessors only; added 2026-09-13 by the orchestrator because no page may read `st.session_state` directly and Task-13 is DONE)
- MUST NOT TOUCH: `fair_turn/core/audit.py` (Task-07), `fair_turn/app/state.py` beyond the appended accessors (Task-13)
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-14

## Objective

Show one job honestly: the tenant's words, every field beside the phrase it came from,
empty where nothing verified, the factor breakdown, and a reasoned override.

## Execution Guide

- `highlight.py`: `render(report_text, spans: list[(start, end, field)]) -> str` producing Markdown with `**...**` around each verified span (non-overlapping; spans come from `verify_spans` offsets); escape Markdown control characters in the report text.
- Page: job selector (from `selected_job_id`, with a selectbox fallback); report text with highlights; a two-column table field → evidence, empty cells shown as "not found in report: fill in" with a selectbox for the coordinator to set `fault_type` / `safety_class` (kept in session only, tagged `human_set`); factor breakdown bar (Altair, theme colours) at the current λ; `why_sentence`; override form: new rank, reason (required), submit → `audit.append(Override)`; success toast.
- Tests: AppTest with a job that has a dropped field shows the "not found" cell and no invented value; highlights count equals verified spans count; submitting an override with an empty reason adds no audit line; with a reason adds exactly one line (temporary audit path via `state.audit_path`).

## Acceptance Criteria (DoD)

- [ ] Empty-field rendering and highlight count asserted.
- [ ] Override audit behaviour asserted with a temporary log file; the committed sample log is untouched by tests.
- [ ] Gate green.
