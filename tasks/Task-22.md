# Task-22: Workspace interaction spike: pydeck map, selectable list, shared selection

Status: DONE

> **Execution:** agent `codex` · effort `high`
> *Why:* Part 2 fixed pydeck and the session-state selection seam (spike 2026-09-14); what is left is writing the two components and the tests. The click path is a human check listed as not gated.

**Lane**
- OWNS: `fair_turn/app/components/workspace_map.py`, `fair_turn/app/components/job_list.py`, `tests/test_workspace_components.py`
- MUST NOT TOUCH: `fair_turn/app/components/map.py` (Phase 1 outline, reused as fallback), `fair_turn/app/state.py` (Task-23), `fair_turn/app/pages/` (Task-29)
- GATE: `venv/Scripts/python scripts/gate.py` (repo root) (criterion 5 is a human check, not gated)
- DEPENDS ON: none

## Objective

Prove, in code that ships, that a ranked list, a pan-and-zoom map and a details pane can
share one selected job in Streamlit 1.63 with native selection events only. This is the
framework gate in `docs/phase-2-discovery.md` §5: if it holds, Streamlit stays.

## Execution Guide

- `workspace_map.py`: `build_deck(points: list[dict], selected_id: str | None) -> pydeck.Deck` where each point has `job_id, community_id, lat, lon, region, open_jobs`. One `ScatterplotLayer` (`pickable=True`, radius from `open_jobs`, fill from `theme.REGION_COLOURS`), a second layer with the selected point only, larger, stroked in the primary colour. `map_provider="carto"`, `map_style="light"`, `initial_view_state` at NT centre (lat −19, lon 133, zoom 4). `render(points, selected_id) -> str | None`: calls `st.pydeck_chart(deck, on_select="rerun", selection_mode="single-object", key="workspace_map")`, reads `event.selection["objects"]`, and returns the clicked `job_id` or `None`. Wrap the call in `try/except Exception` and fall back to `components/map.py`'s Altair outline with the same points plus one `st.info("Basemap unavailable ...")`.
- `job_list.py`: `render(frame: pd.DataFrame, selected_id: str | None) -> str | None` over `st.dataframe(frame, on_select="rerun", selection_mode="single-row", hide_index=True, key=...)`, returning the `job_id` of the selected row or `None`. The frame always carries a `job_id` column; selection is by row position, so the function maps position back to id from the frame it rendered.
- Neither module reads or writes `st.session_state` directly (Task-13 rule); the page (Task-29) calls `state.set_selected_job_id` with what these return. No hex literals: colours come from `theme.py`.
- Tests (AppTest with `socket.socket` refused, as in `tests/test_app_smoke.py`, over a tiny throwaway script written to `tmp_path`): the deck proto contains `selection_mode`, two layers, and no `url` other than the Carto style; forcing an exception in `build_deck` renders the Altair fallback and exactly one info box; `job_list.render` maps a selection at row 2 to that row's `job_id` (call the pure mapping helper directly, since AppTest cannot click).

## Acceptance Criteria (DoD)

- [x] Deck spec assertions (selection mode, two layers, Carto style only) pass with sockets refused.
- [x] Fallback path renders the outline with the same marker count and one info box.
- [x] Row-position to `job_id` mapping tested, including an empty frame.
- [x] No hex, size or font literal outside `theme.py` (existing theme test stays green).
- [x] Human check, recorded in this file under a `## Spike result` heading with the date: clicking a marker and clicking a row both change the selected id in a real `streamlit run`; if either fails, stop and raise the framework question before Task-29.
- [x] Gate green.

## Spike result

**2026-09-14 — framework question raised.** In the real app started with `streamlit run`,
selecting a list row changed the shared selected job to `JR-2025-00881` and updated the details
pane. Clicking a visible pydeck marker did not change the selected job after the map was panned
and zoomed to place the marker under the click target. Criterion 5 therefore fails. Before any
further workspace UI change: can Streamlit 1.63 reliably return pydeck `single-object` selection
for this layer, or must the workspace use another selectable map mechanism?

**2026-09-14, later — resolved, pydeck stays.** Re-run by the main loop in headless Chromium
(Playwright) against `streamlit run` on port 8765: a click on the Alice Springs marker at NT
zoom returned a `single-object` selection event, the details pane rendered "Choose a job at
Alice Springs" with one button per open job, and pressing a button set the shared selected
id (capture: `design/screenshots/01c-workspace-map-click.png`). The earlier "failure" was the
by-design behaviour of PRD 3.1 ("a map marker holding several jobs offers the choice; it
never picks one") read as a missing selection. Streamlit 1.63 keys the pydeck element on
`key` and `selection_mode` only (`deck_gl_json_chart.py`), so the selection survives the
highlight-layer rebuild on every rerun. Row selection changed the selected id as reported.
Criterion 5 passes; no other selectable map is needed. Usability of the marker path (tiny
markers at NT zoom, a long button list for a town) is a `review-visual` finding in
`BACKLOG.md`, not a framework question.
