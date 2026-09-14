# Task-41: Workspace KPI row, effect sentence in the main column, outcome tiles after signature

Status: DONE

> **Execution:** agent `codex` · effort `high` · plan mode **no**
> *Why:* the elements are fixed (dispatcher consoles open on a KPI bar, `reports/research-ui-dispatch-products-2026-09-14.md` §1; decide-before-reveal stays, `reports/research-ui-hitl-guidance-2026-09-14.md`); PRD 3.1 rules are unchanged.

**Lane**
- OWNS: `fair_turn/app/pages/workspace.py`, `fair_turn/app/components/metrics.py`, `tests/test_page_workspace.py`, `tests/test_page_workspace_signoff.py`
- MUST NOT TOUCH: `fair_turn/app/components/details_pane.py`, `fair_turn/app/components/ranking_table.py`, `fair_turn/app/components/weighting.py`, `fair_turn/core/`, `fair_turn/app/state.py`
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: 38, 40

## Objective

The coordinator reads the day's numbers before any job. Put a four-tile KPI row under the
header, move the effect sentence from the sidebar to the main column where the list is, and
render the post-signature outcomes as metric tiles with their baseline, period and units. The
decide-before-reveal rule is unchanged: before a signature the outcome panel is a locked box
that says why it is locked.

## Execution Guide

- KPI row (`workspace.py`, directly under the provenance caption, before the intake container):
  four `st.metric(..., border=True)` in `st.columns(4)`:
  1. "Today's list" value `f"{len(today_list)} of {cap}"`, help "Jobs proposed within today's
     capacity: crews x jobs per crew per day (Part 2 constants)."
  2. "Remote households today" value `remote_today`, `delta=remote_today - remote_in_baseline`
     where the baseline is the efficiency-first list (`baseline[:cap]`), `delta_color="normal"`,
     help "Change against the efficiency-first list."
  3. "In review" value `review_count`, help "Jobs waiting for a person to set a field."
  4. "Override rate today" value `f"{today_rate:.0%}"`, help "Share of today's signed jobs moved by
     hand. See Evidence lab -> Audit log." (compute `today_rate` once, before the row; it is
     currently computed at the end of the page).
- Effect sentence: remove `effect_slot` from the sidebar; render
  `st.info("Effect: ...")` directly under the KPI row with the same `effect.sentence(...)` text.
- `metrics.metrics_panel(...)`: before the first signature render one
  `st.container(border=True)` with `st.markdown("**Outcomes appear after you sign**")` and
  `st.caption("Wait times and travel cost appear after you sign. We hide them until then so the
  numbers do not steer your ordering.")`; no number, no wait or travel word beyond that caption
  (the existing signoff tests assert absence of metrics; adjust their assertions to this exact
  caption if they grep for the words "wait" or "travel"). After a signature render four
  `st.metric(border=True)` tiles in `st.columns(4)`: remote median wait, town median wait,
  the gap, total travel cost, each with `delta` against efficiency-first and one shared caption
  stating "Baseline: efficiency-first (travel-cost weight 1.00). Simulated over the 90-day set.
  Days and AUD." Keep the existing `panel_values`, `formatted`, `deltas` helpers as the source
  of the numbers.
- Tests: KPI row present with four metric nodes and the right labels; the effect sentence is a
  main-column info node and no longer in the sidebar; before a signature the outcomes box exists
  and no metric tile carries a wait or travel value; after a signature through the form four
  metric tiles exist and the caption names the baseline. Existing tests stay green.

## Acceptance Criteria (DoD)

- [ ] Four KPI tiles with the specified labels, values and help texts (test).
- [ ] Effect sentence rendered in the main column; sidebar carries weighting and filters only (test).
- [ ] Locked outcomes box before signature; four outcome tiles with baseline caption after (tests).
- [ ] No hex, size or font literal outside `theme.py`.
- [ ] Gate green.
