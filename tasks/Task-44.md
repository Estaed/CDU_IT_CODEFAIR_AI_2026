# Task-44: Evidence lab headline tiles and expanders

Status: DONE

> **Execution:** agent `codex` · effort `medium`
> *Why:* the numbers exist in `eval.json`; the change is presentation (KPI tiles first, tables behind expanders, limitations beside the numbers per NIST MEASURE 2.9 in `reports/research-ui-hitl-guidance-2026-09-14.md`).

**Lane**
- OWNS: `fair_turn/app/pages/evidence_lab.py`, `tests/test_page_evidence_lab.py`
- MUST NOT TOUCH: `fair_turn/app/components/`, `fair_turn/core/`, `fair_turn/data/`, `scripts/`, `data/build/`
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: 40

## Objective

The extraction tab is a wall of three tables. Lead with the five numbers a judge needs, state
the limitation next to them, and put the tables behind expanders. Give the feedback-loop tab
a one-sentence purpose above its controls and the audit tab its override-rate chart first.

## Execution Guide

- Extraction tab, top: five `st.metric(border=True)` tiles in `st.columns(5)`:
  "Verified source phrases" (substring verification rate as a percentage with the Wilson
  interval in `help`), "Adversarial items, rank unchanged" (`"20 of 20"` from the artefact),
  "Fault type macro-F1", "Safety class macro-F1", "Household health risk macro-F1" (each with
  `delta` against the baseline classifier where a baseline exists, `delta_color="normal"`).
  Directly under the tiles: `st.caption` naming the extractor, the item count and the artefact
  date, then the existing target sentence rewritten as a limitation next to the numbers:
  "Macro-F1 target 0.85: fault type met; safety class not met (the extractor over-predicts
  `immediate`)." Read every number from `eval.json`; no literal.
- The three per-field tables move into `st.expander(f"{field} by class")`, collapsed.
  (`st.expander` emits a `status` node in AppTest; find it through `at.get("status")`.)
- Feedback-loop tab: one sentence above the controls: "Replays the 90-day set twice, once
  efficiency-first and once at the chosen weighting, to show that an efficiency-only
  allocation makes remote demand look like it dried up." Keep the charts and the decay slider.
- Audit tab: render the override-rate-by-day chart before the filters and the table; keep the
  two clocks as two columns, the export and the filters unchanged.
- Tests: five metric nodes with the specified labels and values equal to the artefact's; the
  limitation caption present; three status/expander nodes; the feedback sentence present; the
  audit tab's first chart precedes its dataframe. Existing tests stay green.

## Acceptance Criteria (DoD)

- [ ] Five headline tiles read from `eval.json`, with baseline deltas (test).
- [ ] Limitation sentence next to the tiles; per-field tables behind expanders (test).
- [ ] Feedback purpose sentence; audit override chart first (test).
- [ ] No hex, size or font literal outside `theme.py`.
- [ ] Gate green.
