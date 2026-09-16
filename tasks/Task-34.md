# Task-34: Evidence lab: extraction quality, feedback loop, audit log with two clocks; retire the Phase 1 feedback and audit pages

Status: DONE

> **Execution:** agent `codex` · effort `medium`
> *Why:* Three existing surfaces move into tabs; the audit table's column and clock rules are fixed in PRD §3.5 and Part 2.

**Lane**
- OWNS: `fair_turn/app/pages/evidence_lab.py`, `tests/test_page_evidence_lab.py`, delete `fair_turn/app/pages/feedback.py`, `fair_turn/app/pages/audit_log.py`, `tests/test_page_feedback.py`
- MUST NOT TOUCH: `fair_turn/core/audit.py` (Task-24), `fair_turn/core/feedback_sim.py`, `fair_turn/app/pages/workspace.py` (add the override-rate caption there is Task-35)
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-24, Task-30

## Objective

Judges' and governance surface in three tabs, outside the coordinator's flow, with the
audit table as the reasoning record: two clocks, identity columns kept, newest first,
filtered export.

## Execution Guide

- Tab 1 "Extraction quality": tables from `data/build/eval.json` as the Phase 1 report export did (per-field P/R/F1 with Wilson CI, baseline beside the model, adversarial result, provider and model named from the artefact). Tab 2 "Feedback loop": the Phase 1 page body moved, with its own default λ = 0.5 (`BACKLOG.md` Task-19 entry) and both runs drawn on first render. Tab 3 "Audit log": `audit.export_rows` into `st.dataframe` with the Phase 2 column names, `recorded_at` and `decision_day` as two columns, mono for timestamp, ref, job id and hash; caption stating the local zone once; newest first; filters (signer, kind, decision-day range) restated in a caption; "Download CSV" of exactly the filtered rows; override rate by decision day as an Altair line with a daily axis.
- Unskip and adapt the tests preserved by Task-30; delete the two Phase 1 pages and the feedback test.
- Tests (AppTest, sockets refused): three tabs render; at least one Vega-Lite chart in tab 2 and tab 3; the audit frame's first row is the newest `recorded_at`; the column list equals the Part 2 export list; filtering by kind changes the CSV row count to match; the seeded sample shows `decision_day` and `recorded_at` as different values.

## Acceptance Criteria (DoD)

- [ ] Column set, ordering and two-clock assertions pass on the seeded sample.
- [ ] Filtered export row count equals the filtered frame.
- [ ] Phase 1 feedback and audit pages deleted; preserved tests unskipped and green.
- [ ] Gate green.
