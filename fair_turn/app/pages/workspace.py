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
from streamlit.errors import StreamlitPageNotFoundError

from fair_turn.app import intake, state, theme
from fair_turn.app.components import (
    cluster_map,
    details_pane,
    intro,
    job_list,
    job_rows,
    metrics,
    ranking_table,
    run_sheet,
    sign_off_form,
    today_steps,
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
MAP_MODES = ["Today's list", "All open jobs"]
MAP_CAPTION = (
    "Circles group communities; zoom in or click a circle to split it. "
    "Click a dot to open its jobs."
)
NO_HUMAN_JOBS = "No jobs need a person today."
HUMAN_ROW_RATIOS = [2.2, 3.6, 1.2]  # job and community, what is missing, the Review button
DEV_EXPANDER = "DEV OPTION · Simulate incoming reports"
DEV_CAPTION = (
    "Replays a synthetic report as if a tenant just sent it. No model call; for demos and testing."
)
DEV_ADD = "Add a new report"
DEV_ADD_HUMAN = "Add one that needs a human"

art = state.artefacts()
today = state.get_today()
st.title("Workspace")
intro.purpose("workspace")
steps_slot = st.container()  # filled at the end, once a submit in this rerun has settled

with st.sidebar:
    lam, label = weighting.render()
    region, faults, safeties = weighting.filters()
    with st.expander(DEV_EXPANDER):
        st.caption(DEV_CAPTION)
        for label_text, needs_person in ((DEV_ADD, False), (DEV_ADD_HUMAN, True)):
            if st.button(label_text, key=f"workspace_dev_{int(needs_person)}", width="stretch"):
                new_id = intake.simulate_incoming(needs_person)
                state.set_selected_job_id(new_id)
                state.set_map_pick(None)
                state.set_pending_toast(new_id)
                st.rerun()

# Crews are one NT-wide pool: the ranking and the capacity split always cover every open job,
# and the sidebar region only narrows the rows and the map points shown.
jobs = ranking_table.open_jobs(today)
audit_records = audit.read(state.get_audit_path())
review_ids = ranking_table.review_requested_ids(audit_records, today)
review_reasons = {
    r.job_id: r.reason
    for r in audit_records
    if isinstance(r, audit.HumanSet)
    and r.field == ranking_table.REVIEW_REQUESTED
    and r.day == today
}
rankable = [j for j in jobs if not j.needs_human and j.job_id not in review_ids]
baseline = scoring.rank(rankable, today, 1.0)
current = ranking_table.apply_hand_moves(scoring.rank(rankable, today, lam), state.get_hand_moves())
cap = ranking_table.capacity(state.ALL_REGIONS)
today_list, backlog = current[:cap], current[cap:]
review_count = sum(1 for j in jobs if j.needs_human or j.job_id in review_ids)
checks = {
    job_id: check.decision for job_id, check in audit.latest_checks(audit_records, today).items()
}


def ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def added_message(job_id: str) -> str:
    """The toast for a replayed report: where it landed, in the words the lists use."""
    head = f"Report {ranking_table.short_id(job_id)} added"
    job = next((j for j in jobs if j.job_id == job_id), None)
    if job is not None and job.needs_human:
        missing = [
            name
            for name, value in (("fault type", job.fault_type), ("safety class", job.safety_class))
            if value is None
        ]
        return f"{head}: it needs a person ({' and '.join(missing)} not found)"
    rank = next((s.rank for s in current if s.job.job_id == job_id), None)
    if rank is None:
        return f"{head}."
    return f"{head}: it ranks {ordinal(rank)}" + ("" if rank <= cap else ", in the backlog")


if (announced := state.get_pending_toast()) is not None:
    state.set_pending_toast(None)
    st.toast(added_message(announced))


def in_view(job) -> bool:
    return region == state.ALL_REGIONS or art.communities[job.community_id]["region"] == region


shown_jobs = [j for j in jobs if in_view(j)]
today_shown = [s for s in today_list if in_view(s.job)]
backlog_shown = [s for s in backlog if in_view(s.job)]
human_jobs = sorted(
    (j for j in shown_jobs if j.needs_human or j.job_id in review_ids),
    key=lambda j: (j.reported_on, j.job_id),
)
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
    (
        f"{len(today_list)} of {cap}"
        if region == state.ALL_REGIONS
        else f"{len(today_shown)} of {len(today_list)} in {region}",
        remote_today,
        review_count,
        f"{today_rate:.0%}",
    ),
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
    + metrics.effect_sentence(
        today, state.ALL_REGIONS, lam, current, baseline, cap, is_remote, label
    )
)
st.caption(
    run_sheet.reach_line([s.job.job_id for s in today_list], {j.job_id: j for j in jobs}, today)
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
        [s for s in scored if passes(s.job) and in_view(s.job)],
        other,
        table_lam,
        today,
        baseline=against,
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
            "check": checks.get(row["job_id"]),
        }
        for _, row in frame.iterrows()
    ]


def missing_lines(job) -> list[str]:
    """What a person has to supply, in words. Only the absence is named: a value the model
    proposed and verification rejected never reaches this text (PRD 3.2)."""
    lines = [
        f"{name} not found in the report"
        for name, value in (("Fault type", job.fault_type), ("Safety class", job.safety_class))
        if value is None
    ]
    if job.job_id in review_reasons:
        lines.append(f"Sent to review: {review_reasons[job.job_id]}")
    return lines


def human_rows(human: list) -> None:
    """The "Needs a human" tab: one bordered row per job with a Review button that opens the
    review queue at that job."""
    if not human:
        st.info(NO_HUMAN_JOBS)
        return
    for job in human:
        with st.container(border=True):
            who, what, action = st.columns(HUMAN_ROW_RATIOS, vertical_alignment="center")
            who.markdown(f"**Job {ranking_table.short_id(job.job_id)}**")
            who.caption(f"{job.community_id} · reported {job.reported_on.isoformat()}")
            for line in missing_lines(job):
                what.text(line)
            if action.button("Review", key=f"workspace_review_{job.job_id}", width="stretch"):
                state.set_review_focus(job.job_id)
                try:
                    st.switch_page("pages/review_queue.py")
                except StreamlitPageNotFoundError:
                    pass  # a page run on its own (AppTest) has no navigation registry


selected = state.get_selected_job_id()
if not shown_jobs:
    st.info("No open reports for this day and region. Try widening the region.")
elif not any(in_view(s.job) for s in current):
    st.warning(f"All {len(shown_jobs)} open jobs are in the review queue ({len(human_jobs)}).")
if cap == 0:
    st.info("Capacity is zero; the list shows as backlog only.")
hidden = sum(1 for j in shown_jobs if not passes(j))
if shown_jobs and hidden == len(shown_jobs):
    st.info(f"{hidden} jobs hidden by filters.")
    st.button("Clear filters", on_click=weighting.clear_filters, key="workspace_clear_hidden")

centre, pane = st.columns([5, 3])
with centre:
    compare = st.checkbox("Compare with efficiency-first", value=state.get_compare())
    state.set_compare(compare)
    # The map sits above the lists so it needs no second click to be seen.
    map_mode = st.radio(
        "Map shows",
        MAP_MODES,
        horizontal=True,
        key="workspace_map_mode",
        label_visibility="collapsed",
    )
    rank_of = {s.job.job_id: s.rank for s in current}
    mapped_jobs = [s.job for s in today_shown] if map_mode == MAP_MODES[0] else shown_jobs
    by_community: dict[str, list] = {}
    for job in mapped_jobs:
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
    selected_community = next((j.community_id for j in jobs if j.job_id == selected), None)
    pick = cluster_map.render(points, selected_community, key="workspace_map")
    if pick is not None:
        state.set_map_pick(pick)
    map_choice = workspace_map.choice_for(state.get_map_pick(), by_community)
    if map_choice is not None and selected in map_choice[1]:
        # The pick has done its job once one of its jobs is open; a stale pick must not
        # pull the selection back after a row is opened elsewhere.
        state.set_map_pick(None)
        map_choice = None
    st.caption(MAP_CAPTION)
    tabs = st.tabs(
        [
            f"Today's list {len(today_shown)}",
            f"Needs a human {len(human_jobs)}",
            f"Backlog {len(backlog_shown)}",
        ]
    )
    with tabs[1]:
        human_rows(human_jobs)
    lists = [
        (tabs[0], "today", today_list, baseline[:cap]),
        (tabs[2], "backlog", backlog, baseline[cap:]),
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
                state.set_map_pick(None)
                st.rerun()

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
        sign_off_form.render(
            frozen, status, on_submit, review_count, is_remote, frozen_rows, checks
        )

metrics.metrics_panel(today, state.ALL_REGIONS, lam, current, baseline, cap, is_remote, label)
effect_message.info(
    "Effect: "
    + metrics.effect_sentence(
        today, state.ALL_REGIONS, lam, current, baseline, cap, is_remote, label
    )
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
signed_version = records[-1].batch_version if status == "signed" else None
plan_accepted = signed_version is not None and any(
    isinstance(r, audit.PlanDecision)
    and r.day == today
    and r.batch_version == signed_version
    and r.action == "accept"
    for r in audit.read(state.get_audit_path())
)
today_ids = [s.job.job_id for s in today_list]
with steps_slot:
    today_steps.render(
        today_steps.steps(
            review_left=review_count,
            checked=sum(job_id in checks for job_id in today_ids),
            today_total=len(today_ids),
            signed=status == "signed",
            plan_accepted=plan_accepted,
        )
    )
intro.about()
