# Task-49: Map markers show their job count

Status: DONE

> **Execution:** agent `claude` · effort `medium` · plan mode **no**
> *Why:* Tarik (2026-09-14): a marker that holds many jobs looks like one job. Per-household locations do not exist (only pseudonymous community coordinates, PRD §6), so the honest fix is a count on the marker.

**Lane**
- OWNS: `fair_turn/app/components/workspace_map.py`, `tests/test_workspace_components.py`
- MUST NOT TOUCH: `fair_turn/app/pages/`, `fair_turn/app/components/details_pane.py`, `fair_turn/app/theme.py`, `fair_turn/app/components/map.py`
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: 37

## Objective

Every marker with more than one open job carries its count as a label; the tooltip names the
count too; nothing else about selection changes.

## Execution Guide

- Add a third `pdk.Layer("TextLayer", id="counts", ...)` over the same points filtered to
  `open_jobs > 1`: `get_position=["lon", "lat"]`, `get_text="label"` (a string column
  `label=str(open_jobs)`), `get_size=COUNT_FONT_PX` (named constant, 12), `size_units="'pixels'"`
  (inner quotes, the Part 2 pydeck trap), `get_color` from `theme` (white on the coloured
  marker: use `_rgb(st.get_option("theme.backgroundColor"))`), `get_text_anchor="'middle'"`,
  `get_alignment_baseline="'center'"`, `pickable=False`. Keep it last in `layers` so it draws
  on top.
- Tooltip: `"<b>{job_id}</b><br/>{community_id} · {open_jobs} open"`.
- Fallback path unchanged.
- Tests: the deck JSON has three layers with ids jobs, selected, counts; the counts layer has
  `sizeUnits == "pixels"` (no `@@=`), only points with `open_jobs > 1`, and `pickable` false;
  `picked_id` ignores a selection that only names the counts layer.

## Acceptance Criteria (DoD)

- [ ] Counts layer present with pixel units and the right subset of points (test).
- [ ] Tooltip carries the open-job count (test on the deck JSON).
- [ ] Selection behaviour and the fallback unchanged (existing tests).
- [ ] Gate green.
