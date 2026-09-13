# Task-12: Evaluation: per-field metrics, baseline classifier, eval script

Status: DONE

> **Execution:** agent `codex` · effort `high` · plan mode **no**
> *Why:* report 6's protocol is fully specified (P/R/F1, Wilson, SemEval spans, baseline); pure computation over committed artefacts; the script's exit code is the criterion.

**Lane**
- OWNS: `fair_turn/eval/metrics.py`, `fair_turn/eval/baseline.py`, `scripts/run_eval.py`, `data/build/eval.json`, `data/build/eval_tables.md`, `tests/test_metrics.py`
- MUST NOT TOUCH: `data/build/extraction.json` (Task-11), `fair_turn/core/` (earlier tasks)
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-11

## Objective

Produce the numbers the report quotes: extractor versus baseline per field with
confidence intervals, span scores under two regimes, the substring-verification rate,
and a pass/fail on the F1 target.

## Execution Guide

- `metrics.py`: `prf(gold, pred, labels)` macro precision/recall/F1 per field with `statsmodels.stats.proportion.proportion_confint(method="wilson")` on each proportion; `span_scores(gold_spans, pred_spans)` SemEval-2013 `exact` and `partial` (`(COR + 0.5·PAR) / ACT`); `substring_rate(rows)`.
- `baseline.py`: TF-IDF (word 1–2 grams) + logistic regression for `fault_type` and `safety_class`, trained on the non-holdout reports with labels from `labels.json`, scored on the 150 holdout items; seeded.
- `scripts/run_eval.py`: loads labels, reports, extraction; computes extractor metrics on the holdout set and baseline metrics on the same items; writes `eval.json` and `eval_tables.md` (markdown tables for the report); exits 1 if macro-F1 for `fault_type` or `safety_class` is below 0.85 (constant in `constants.md` as provisional), 0 otherwise.
- Tests: `prf` on a hand-computed 10-item fixture; span scores on the SemEval worked example; `substring_rate`; baseline trains and predicts on a 40-item fixture.

## Acceptance Criteria (DoD)

- [ ] `test_metrics.py` passes with hand-verified numbers.
- [ ] `run_eval.py` writes both artefacts and its exit code follows the F1 rule; the artefacts are committed.
- [ ] Every proportion in `eval.json` carries a Wilson 95 % interval.
- [ ] Gate green (the gate does not run `run_eval.py`; Part 2 §Verification 5).
