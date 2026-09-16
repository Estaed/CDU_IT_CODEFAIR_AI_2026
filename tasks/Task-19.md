# Task-19: Feedback-loop simulation page

Status: DONE

> **Execution:** agent `codex` · effort `high`
> *Why:* charts over `feedback_sim.run` output (PRD §3.5); the assumption slider and the three charts are fully specified; chart presence and data equality are asserted.

**Lane**
- OWNS: `fair_turn/app/pages/feedback.py`, `tests/test_page_feedback.py`
- MUST NOT TOUCH: `fair_turn/core/feedback_sim.py` (Task-05), `fair_turn/app/theme.py` (Task-00)
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-13, Task-05

## Objective

Replay 90 days at λ = 1.0 and at a chosen λ with a labelled decay assumption, and show
remote reports drying up under efficiency-only allocation.

## Execution Guide

- Controls: λ slider (default 0.5), decay slider 0.0–1.0 (default 0.3) with a caption stating it is our assumption and no published estimate exists (report 6 wording); a "Run" button so the simulation is not recomputed on every widget move; results cached by (λ, decay).
- Charts (Altair, theme colours, `width="stretch"`): reports per week town/remote for both runs; median wait town/remote for both runs; the gap for both runs. One sentence under the charts naming the three citations (Ensign 2018, D'Amour 2020, Kontokosta & Hong) from a constant string in the page.
- Tests: AppTest: pressing Run renders three Vega-Lite charts; the plotted gap series for the λ = 1.0 run equals `feedback_sim.run` output computed in the test; with decay 0 the two report series are identical.

## Acceptance Criteria (DoD)

- [ ] Three charts present and data equality asserted.
- [ ] Simulation not re-run without pressing Run (call counter through monkeypatch).
- [ ] Gate green.
