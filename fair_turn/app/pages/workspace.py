"""PRD 3.1 Workspace: today's list within capacity, the backlog and the map, the weighting
with its effect sentence, and the selected-job pane with the coordinator's hand moves.
Sign-off, metrics and decision states arrive in Task-30."""

import streamlit as st

from fair_turn.app import intake, state, theme
from fair_turn.app.components import (
    details_pane,
    job_list,
    ranking_table,
    weighting,
    workspace_map,
)
from fair_turn.core import audit, effect, scoring

DISPLAY = [
    "rank",
    "rank change",
    "job id",
    "community id",
    "fault type",
    "safety class",
    "window",
    "score",
    "score_bar",
]

art = state.artefacts()
today = state.get_today()
st.title("Workspace")

with st.sidebar:
    lam, label = weighting.render()
    effect_slot = st.empty()
    region, faults, safeties = weighting.filters()

jobs = ranking_table.open_jobs(today)
if region != state.ALL_REGIONS:
    jobs = [j for j in jobs if art.communities[j.community_id]["region"] == region]
review_ids = ranking_table.review_requested_ids(audit.read(state.get_audit_path()), today)
rankable = [j for j in jobs if not j.needs_human and j.job_id not in review_ids]
baseline = scoring.rank(rankable, today, 1.0)
current = ranking_table.apply_hand_moves(scoring.rank(rankable, today, lam), state.get_hand_moves())
cap = ranking_table.capacity(region)
today_list, backlog = current[:cap], current[cap:]
review_count = sum(1 for j in jobs if j.needs_human or j.job_id in review_ids)


def is_remote(community_id: str) -> bool:
    return art.communities[community_id]["is_remote"] == "True"


effect_slot.markdown(
    "Effect: " + effect.sentence("before_signature", current, baseline, cap, is_remote, label)
)

header, new_report = st.columns([4, 1])
header.markdown(f"Day {today} · Region {region} · {review_count} need review · Status: Draft")
if new_report.button("New report"):
    state.set_intake_draft(intake.new_draft())
st.caption(theme.PROVENANCE_LINE)
if state.get_intake_draft() is not None:
    intake.render(st.container(border=True))


def passes(job) -> bool:
    fault_ok = not faults or (job.fault_type is not None and job.fault_type.value in faults)
    safety_ok = not safeties or (
        job.safety_class is not None and job.safety_class.value in safeties
    )
    return fault_ok and safety_ok


def view(scored, other=None, table_lam=lam, against=None):
    frame = ranking_table.rows_for(
        [s for s in scored if passes(s.job)], other, table_lam, today, baseline=against
    )
    return frame[DISPLAY].rename(columns={"job id": "job_id"})


selected = state.get_selected_job_id()
if not jobs:
    st.info("No open reports for this day and region. Try widening the region.")
elif not rankable:
    st.warning(f"All {len(jobs)} open jobs are in the review queue ({review_count}).")
if cap == 0:
    st.info("Capacity is zero for this region; the list shows as backlog only.")
hidden = sum(1 for j in jobs if not passes(j))
if jobs and hidden == len(jobs):
    st.info(f"{hidden} jobs hidden by filters.")
    st.button("Clear filters", on_click=weighting.clear_filters, key="workspace_clear_hidden")

centre, pane = st.columns([3, 2])
with centre:
    compare = st.checkbox("Compare with efficiency-first", value=state.get_compare())
    state.set_compare(compare)
    tabs = st.tabs([f"Today's list {len(today_list)}", f"Backlog {len(backlog)}", "Map"])
    lists = [
        (tabs[0], "today", today_list, baseline[:cap]),
        (tabs[1], "backlog", backlog, baseline[cap:]),
    ]
    for tab, name, scored, efficiency_first in lists:
        with tab:
            if compare:
                left, right = st.columns(2)
                left.caption(f"Current: {label}")
                left.dataframe(view(scored, against=baseline), hide_index=True)
                right.caption("Efficiency first (λ = 1.00)")
                right.dataframe(
                    view(efficiency_first, other=current, table_lam=1.0), hide_index=True
                )
                continue
            frame = view(scored, against=baseline)
            # The key follows the selection so a stale row pick never re-applies itself.
            event = st.dataframe(
                frame,
                on_select="rerun",
                selection_mode="single-row",
                hide_index=True,
                column_config=ranking_table.column_config(frame),
                key=f"workspace_{name}_{selected}",
                width="stretch",
            )
            picked = job_list.selected_job_id(frame, event.selection.rows)
            if picked is not None and picked != selected:
                state.set_selected_job_id(picked)
                st.rerun()
    with tabs[2]:
        rank_of = {s.job.job_id: s.rank for s in current}
        by_community: dict[str, list] = {}
        for job in jobs:
            if passes(job):
                by_community.setdefault(job.community_id, []).append(job)
        points = []
        for community_id, members in sorted(by_community.items()):
            best = min(members, key=lambda j: (rank_of.get(j.job_id, len(rank_of) + 1), j.job_id))
            community = art.communities[community_id]
            points.append(
                {
                    "job_id": best.job_id,
                    "community_id": community_id,
                    "lat": float(community["lat"]),
                    "lon": float(community["lon"]),
                    "region": community["region"],
                    "open_jobs": len(members),
                }
            )
        map_pick = workspace_map.render(points, selected)
        map_choice = None
        if map_pick is not None:
            community_id = next(p["community_id"] for p in points if p["job_id"] == map_pick)
            map_choice = (community_id, sorted(j.job_id for j in by_community[community_id]))

with pane:
    details_pane.render(art, jobs, current, cap, review_ids, today, lam, map_choice)

st.divider()
remote_today = sum(is_remote(s.job.community_id) for s in today_list)
st.markdown(
    f"Today: {len(today_list)} jobs proposed within capacity {cap} · "
    f"{remote_today} remote / {len(today_list) - remote_today} town · "
    f"Backlog {len(backlog)} · {len(state.get_hand_moves())} moved by hand · "
    f"{review_count} in review"
)
st.button("Review and sign", disabled=True)
st.caption("Sign-off arrives in Task-30")
