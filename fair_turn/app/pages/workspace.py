"""PRD 3.1 Workspace: today's list within capacity, the backlog and the map, the weighting
with its effect sentence, the selected-job pane with the coordinator's hand moves, and the
sign-off (wireframes §5, §9): a frozen batch reviewed in place, the decision state in the
header, and the metrics revealed only after the signature.

The decision state is not stored; it is derived on every rerun from what session state and
the audit log already hold: "draft" with no frozen batch, "review_open" while the frozen batch
is unsigned, "signed" when its version is signed today and its fingerprint still matches,
"changed_since_signature" when it no longer does. "saving" and "save_failed" live only inside
the rerun that submits: a failed audit write shows ``st.error`` in that rerun and the status
stays "review_open" with the batch kept, because nothing survives the rerun to say otherwise.
``batch.next_status`` validates each transition this page takes, so an impossible one raises.
"""

from datetime import datetime

import streamlit as st

from fair_turn.app import intake, state, theme
from fair_turn.app.components import (
    details_pane,
    intro,
    job_list,
    job_rows,
    metrics,
    ranking_table,
    sign_off_form,
    weighting,
    workspace_map,
)
from fair_turn.core import audit, batch, scoring
from fair_turn.data import runtime

# Decision columns first: at 1440 px the table shows about 600 px before it scrolls, so the
# class, window and score sit next to the rank and the descriptive columns come last.
DISPLAY = [
    "rank",
    "rank change",
    "job id",
    "safety class",
    "window",
    "score",
    "score_bar",
    "community id",
    "fault type",
]
TODAY_ROWS_KEY = "workspace_today"

art = state.artefacts()
today = state.get_today()
st.title("Workspace")
intro.purpose("workspace")

with st.sidebar:
    lam, label = weighting.render()
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
if state.get_selected_job_id() is None and today_list:
    state.set_selected_job_id(today_list[0].job.job_id)


def is_remote(community_id: str) -> bool:
    return art.communities[community_id]["is_remote"] == "True"


header, new_report = st.columns([4, 1])
status_slot = header.empty()  # filled at the end, once a submit in this rerun has settled
if new_report.button("New report"):
    state.set_intake_draft(intake.new_draft())
st.caption(theme.PROVENANCE_LINE)
remote_today = sum(is_remote(s.job.community_id) for s in today_list)
remote_in_baseline = sum(is_remote(s.job.community_id) for s in baseline[:cap])
today_rate = next(
    (rate for day, rate in audit.override_rate(audit.read(state.get_audit_path())) if day == today),
    0.0,
)
for column, label_text, value, delta, help_text in zip(
    st.columns(4),
    (
        "Today's list",
        "Remote households today",
        "In review",
        "Override rate today",
    ),
    (f"{len(today_list)} of {cap}", remote_today, review_count, f"{today_rate:.0%}"),
    (None, (remote_today - remote_in_baseline) or None, None, None),
    (
        "Jobs proposed within today's capacity: crews x jobs per crew per day (Part 2 constants).",
        "Change against the efficiency-first list.",
        "Jobs waiting for a person to set a field.",
        "Share of today's signed jobs moved by hand. See Evidence lab -> Audit log.",
    ),
    strict=True,
):
    column.metric(label_text, value, delta=delta, delta_color="normal", help=help_text, border=True)
effect_message = st.empty()
effect_message.info(
    "Effect: "
    + metrics.effect_sentence(today, region, lam, current, baseline, cap, is_remote, label)
)
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


def today_rows(frame, scored) -> list[dict]:
    """One dict per row of today's frame for ``job_rows.render``. Every value comes from the
    frame the table would have shown, so nothing is scored or ranked twice."""
    needs_human = {s.job.job_id: s.job.needs_human for s in scored}
    score_max = max(float(frame["score_bar"].max()), 1.0) if len(frame) else 1.0
    return [
        {
            "job_id": row["job_id"],
            "rank": int(row["rank"]),
            "rank_change": row["rank change"],
            "community_id": row["community id"],
            "is_remote": is_remote(row["community id"]),
            "fault_type": row["fault type"],
            "safety_class": row["safety class"],
            "window": row["window"],
            "score": float(row["score"]),
            "score_max": score_max,
            "human_queue": needs_human[row["job_id"]],
        }
        for _, row in frame.iterrows()
    ]


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
                current_frame = view(scored, against=baseline)
                left.dataframe(
                    current_frame,
                    hide_index=True,
                    column_config=ranking_table.column_config(current_frame),
                    width="stretch",
                    height=ranking_table.table_height(len(scored)),
                )
                right.caption("Efficiency first (λ = 1.00)")
                efficiency_frame = view(efficiency_first, other=current, table_lam=1.0)
                right.dataframe(
                    efficiency_frame,
                    hide_index=True,
                    column_config=ranking_table.column_config(efficiency_frame),
                    width="stretch",
                    height=ranking_table.table_height(len(efficiency_first)),
                )
                continue
            frame = view(scored, against=baseline)
            if name == "today":
                # A short list is read, not scanned: bordered rows with an explicit Open.
                picked = job_rows.render(today_rows(frame, scored), selected, TODAY_ROWS_KEY)
            else:
                query = st.text_input(
                    "Find in backlog",
                    placeholder="Job id or community",
                    key="workspace_backlog_search",
                )
                if query:  # display only: the ranking and the capacity split are untouched
                    frame = frame[
                        frame["job_id"].str.contains(query, case=False, regex=False)
                        | frame["community id"].str.contains(query, case=False, regex=False)
                    ]
                # The key follows the selection so a stale row pick never re-applies itself.
                event = st.dataframe(
                    frame,
                    on_select="rerun",
                    selection_mode="single-row",
                    hide_index=True,
                    column_config=ranking_table.column_config(frame),
                    key=f"workspace_{name}_{selected}",
                    width="stretch",
                    height=ranking_table.table_height(len(frame)),
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
st.markdown(
    f"Today: {len(today_list)} jobs proposed within capacity {cap} · "
    f"{remote_today} remote / {len(today_list) - remote_today} town · "
    f"Backlog {len(backlog)} · {len(state.get_hand_moves())} moved by hand · "
    f"{review_count} in review"
)

STALE = "The list changed since you opened this review; open it again."


def signed_today() -> list[audit.SignOff]:
    return [
        r
        for r in audit.read(state.get_audit_path())
        if isinstance(r, audit.SignOff) and r.day == today
    ]


human_set = runtime.human_set_for(runtime.read(state.get_runtime_path()))
current_fp = batch.fingerprint_of(
    lam, [s.job.job_id for s in current], state.get_hand_moves(), human_set
)
signed_versions = {r.batch_version for r in signed_today()}


def decision_status(frozen: batch.Batch | None, versions: set[int]) -> batch.Status:
    if frozen is None:
        return "draft"
    if state.get_signed_today() and frozen.version in versions:
        return "changed_since_signature" if batch.is_stale(frozen, current_fp) else "signed"
    return "review_open"


def open_review(status: batch.Status) -> None:
    if status == "review_open":  # a stale review is dropped before a new one opens
        status = batch.next_status(status, "change")
    batch.next_status(status, "open_review")
    preset = label if label in weighting.PRESETS else None
    frozen = batch.freeze(
        today,
        1 + len(signed_today()),
        lam,
        preset,
        current,
        cap,
        state.get_hand_moves(),
        human_set=human_set,
    )
    state.set_batch(frozen)
    st.rerun()


def on_submit(signer: str, decision: str, reason: str) -> None:
    frozen = state.get_batch()
    ok, why = batch.can_submit(frozen, current_fp, signed_versions)
    if not ok:
        st.error(why)
        return
    saving = batch.next_status(status, "submit")
    record = audit.SignOff(
        day=today,
        lam=frozen.lam,
        reason=reason,
        signer=signer,
        signed_at=datetime.now(),
        ranked_job_ids=frozen.ranked_job_ids,
        batch_version=frozen.version,
        today_job_ids=frozen.today_job_ids,
        decision=decision,
    )
    try:
        audit.append(state.get_audit_path(), record)
    except OSError as exc:
        batch.next_status(saving, "submit_fail")
        st.error(f"Could not write the audit log: {exc}")
        return
    batch.next_status(saving, "submit_ok")
    state.set_signed_today(True)
    st.success(f"Signed batch v{frozen.version}. Audit reference `{record.audit_ref}`")


status = decision_status(state.get_batch(), signed_versions)
if st.button("Review and sign", key="workspace_review_and_sign", disabled=status == "review_open"):
    open_review(status)

frozen = state.get_batch()
if frozen is not None:
    if batch.is_stale(frozen, current_fp):
        st.warning(STALE)
        if st.button("Open again", key="workspace_open_again"):
            open_review(status)
    else:
        by_id = {s.job.job_id: s for s in current}
        frozen_rows = ranking_table.rows_for(
            [by_id[job_id] for job_id in frozen.today_job_ids],
            None,
            frozen.lam,
            today,
            baseline=baseline,
        )[DISPLAY]
        sign_off_form.render(frozen, status, on_submit, review_count, is_remote, frozen_rows)

metrics.metrics_panel(today, region, lam, current, baseline, cap, is_remote, label)
effect_message.info(
    "Effect: "
    + metrics.effect_sentence(today, region, lam, current, baseline, cap, is_remote, label)
)

records = signed_today()
status = decision_status(state.get_batch(), {r.batch_version for r in records})
if status == "review_open":
    status_text = f"Review open (batch v{state.get_batch().version})"
elif status == "signed":
    latest = records[-1]
    status_text = (
        f"Signed v{latest.batch_version} {latest.recorded_at.astimezone():%H:%M} by {latest.signer}"
    )
elif status == "changed_since_signature":
    status_text = (
        f"Changed since signature (signed v{records[-1].batch_version} stays authoritative)"
    )
else:
    status_text = "Draft"
status_slot.markdown(
    f"Day {today} · Region {region} · {review_count} need review · Status: {status_text}"
)
intro.about()
