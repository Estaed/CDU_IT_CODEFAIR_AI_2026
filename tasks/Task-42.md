# Task-42: Selected-job pane as a summary list with badges

Status: DONE

> **Execution:** agent `codex` · effort `high`
> *Why:* the pane's content is fixed by PRD 3.1 and wireframes §3; this task changes its form to the GOV.UK summary-list pattern (`reports/research-ui-streamlit-2026-09-14.md` §6a.2) and adds status badges.

**Lane**
- OWNS: `fair_turn/app/components/details_pane.py`, `tests/test_details_pane.py` (new)
- MUST NOT TOUCH: `fair_turn/app/pages/`, `fair_turn/app/components/ranking_table.py`, `fair_turn/app/components/highlight.py`, `fair_turn/core/`, `fair_turn/app/state.py`
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: 37, 40

## Objective

The pane reads as a run of paragraphs. Make it scan: header with badges, the why sentence,
then a label / value / source summary list for the score and its four factors, then the
evidence and policy expanders, then the actions in one bordered block. Content rules are
unchanged: an extracted factor shows its source phrase or "No source phrase found"; a computed
factor shows the policy or geography it came from; a human-set field carries the
"Set by coordinator" badge; the rejected model value never renders.

## Execution Guide

- Header: keep `st.subheader(f"{job_id} · {community_id}")`. Under it a badge row built with
  `st.badge(label, color=<named colour>)` (named colours only, no hex): the safety class
  (`immediate` red, `urgent` orange, `routine` gray), "Remote" or "Town" (gray), "Needs a
  human" (yellow) when in review, and "Set by coordinator" (gray) once per human-set field.
  Verify `st.badge`'s signature on 1.63 first; it renders as a `markdown` node in AppTest, so
  tests find it by text.
- Why sentence: `st.markdown(f"**Why it sits here.** {why}")`.
- Summary list: one `st.container(border=True)` holding five rows, each
  `st.columns([2, 1, 4])` -> label, value, source: "Score" / `f"{score:.1f}"` / "urgency +
  safety + household health risk - logistics"; then the four factors with the exact texts
  `_factor_lines` produces today (value to two decimals; source phrase in quotes for extracted
  factors, "No source phrase found" when empty, "from NT window: ..." / "from geography: ..."
  for computed ones, "Based on N of M fields" when partial). Keep colour out of it: the factor
  name is text, never coloured.
- Evidence and policy expanders unchanged. Actions: one `st.container(border=True)` titled
  "Actions" with the existing forms inside (move up/down, promote, send to review, undo), same
  keys, same reasons, same disabled states.
- Tests (`tests/test_details_pane.py`, AppTest offline, throwaway script under `tmp_path` that
  renders the pane for a known job from the committed artefacts): badge texts for a ranked job
  and for a review-queue job; the five summary rows in order; "No source phrase found" for a
  job with an empty household-health-risk field; the rejected model value string from the
  extraction audit never appears in the rendered text; existing workspace tests stay green.

## Acceptance Criteria (DoD)

- [ ] Badge row with named colours; no hex literal outside `theme.py` (test).
- [ ] Summary list rows for score and four factors, with the same source texts as before (test).
- [ ] Rejected model value never renders (test on a review-queue job).
- [ ] Actions block keeps every existing key and reason requirement (existing tests).
- [ ] Gate green.
