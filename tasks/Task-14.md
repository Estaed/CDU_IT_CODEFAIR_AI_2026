# Task-14: Triage board: ranked list, equity slider, two rankings, human queue

Status: DONE

> **Execution:** agent `codex` · effort `high`
> *Why:* PRD §3.1 prose is the source of truth and the smoke test plus element assertions are the criterion; no eye check is gated.

**Lane**
- OWNS: `fair_turn/app/pages/board.py`, `fair_turn/app/components/ranking_table.py`, `tests/test_page_board.py`
- MUST NOT TOUCH: `fair_turn/app/main.py` and `state.py` (Task-13), `fair_turn/app/theme.py` (Task-00), the map and metrics panel (Task-15)
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-13

## Objective

The coordinator's main screen: today's ranked jobs at the chosen λ, the efficiency
ranking beside it with rank changes highlighted, and the needs-a-human queue on top.

## Execution Guide

- Controls: date within the window (default the last day), region selectbox (all + six regions), λ slider 1.0 → 0.0 step 0.05 default 1.0, stored through `state`.
- Data: open jobs on the day from artefacts; `scoring.split_human_queue`, `scoring.rank` at λ and at 1.0; `explain.why_sentence` per row.
- Human queue: `st.warning` block listing job id, community id, missing field, with a link to the job card (sets `selected_job_id`).
- Two rankings side by side (`st.columns`): rank, community id, fault type, safety class, health-risk factors as short chips, days open, days left in window, score, factor bars (`st.progress` or a small Altair bar per row from `theme` colours), the sentence. Rank change column with arrows in the right-hand table.
- Selecting a row sets `selected_job_id` and switches to the job card (`st.switch_page`).
- Tests: AppTest at λ = 1.0 and λ = 0.0 on the committed artefacts: no exception; the two tables differ in order for at least one job; human-queue jobs appear in the warning and not in either table; every visible score equals `scoring` output for that job.

## Acceptance Criteria (DoD)

- [ ] Smoke test for the page passes with sockets blocked at both λ extremes.
- [ ] Equality of displayed scores with `scoring.rank` asserted programmatically.
- [ ] No colour or size literal in the page (theme test).
- [ ] Gate green.
