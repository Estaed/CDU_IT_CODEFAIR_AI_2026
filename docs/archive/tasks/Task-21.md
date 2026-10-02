# Task-21: Report tables and figures export

Status: DONE

> **Execution:** agent `codex` · effort `medium`
> *Why:* exports numbers already computed (eval, simulations) into the tables the report quotes; file presence and value equality are asserted. The report and slides themselves are written by hand and are not a task.

**Lane**
- OWNS: `scripts/export_report_tables.py`, `data/build/report/`, `tests/test_report_export.py`
- MUST NOT TOUCH: `fair_turn/` (earlier tasks), `data/build/eval.json` (Task-12)
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-12, Task-05

## Objective

Every number the report quotes comes from a committed file produced by one script, so a
reviewer can trace each figure to code.

## Execution Guide

- Script writes to `data/build/report/`: `extraction_vs_baseline.md` (per-field P/R/F1 with Wilson CIs, both models); `span_scores.md` (exact and partial); `substring_rate.md`; `adversarial.md` (20/20 statement); `price_of_fairness.csv` (λ from 1.0 to 0.0 step 0.1: remote median wait, town median wait, gap, travel cost from `capacity_sim` over the full window); `feedback_loop.csv` (weekly series at λ = 1.0 and λ = 0.5, decay 0.3); `dataset_summary.md` (counts by region, remote share, holdout, adversarial, human-queue count, all provisional values flagged).
- Charts for the report are screenshots of the app pages (review-visual territory, not gated); this task exports data only.
- Tests: all seven files exist after a run; `price_of_fairness.csv` gap at λ = 0.0 is at most the gap at λ = 1.0; values in `extraction_vs_baseline.md` match `eval.json`.

## Acceptance Criteria (DoD)

- [ ] Seven files committed under `data/build/report/` and reproduced byte-identically by a rerun.
- [ ] Equality with `eval.json` and the gap monotonicity assertion pass.
- [ ] Gate green.
