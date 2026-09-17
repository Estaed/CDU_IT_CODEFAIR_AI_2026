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
    keyboard,
    metrics,
    ranking_table,
    run_sheet,
    sign_off_form,
    today_steps,
    weighting,
    workspace_map,
)
from fair_turn.core import audit, batch, constants, decisions, scoring
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
DEV_KINDS = {
    "Immediate": "immediate",
    "Urgent": "urgent",
    "Routine": "routine",
    "Needs a person": "needs_person",
}
KEY_SIGNED = "Today's list is signed."
KEY_NOT_TO_DECIDE = "This job is not in To decide."
KEY_NOT_READ = "Tick 'I have read the report' first."
MAKE_SAFE_CAPTION = (
    "Immediate jobs go to the emergency make-safe contractor, who makes them safe within "
    f"{constants.MAKE_SAFE_HOURS} hours. The weighting does not move them and they take no "
    "crew place."
)
NO_MAKE_SAFE = "No Immediate job is waiting."

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
        dev_kind = st.selectbox("Kind of report", list(DEV_KINDS), key="workspace_dev_kind")
        if st.button("Add report", key="workspace_dev_add", width="stretch"):
            new_id = intake.simulate_incoming(DEV_KINDS[dev_kind])
            state.set_selected_job_id(new_id)
            state.set_map_pick(None)
            audit_length = len(audit.read(state.get_audit_path()))
            state.set_added_report((new_id, DEV_KINDS[dev_kind], audit_length))
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
sent = audit.make_safe_sent(audit_records)
# Immediate jobs go to the make-safe contractor, never into the ranking or the crew places.
rankable = [
    j
    for j in jobs
    if not j.needs_human and j.job_id not in review_ids and not decisions.is_make_safe(j)
]
make_safe = sorted(
    (
        j
        for j in jobs
        if decisions.is_make_safe(j) and j.job_id not in review_ids and j.job_id not in sent
    ),
    key=lambda j: (j.reported_on, j.job_id),
)
baseline = scoring.rank(rankable, today, 1.0)
current = ranking_table.apply_hand_moves(scoring.rank(rankable, today, lam), state.get_hand_moves())
cap = ranking_table.capacity(state.ALL_REGIONS)
# Today's per-job decisions split the ranking: accepted jobs stay, the free places go to the
# best-ranked undecided jobs (To decide), and a job rejected as not today joins the backlog.
latest_decisions = audit.latest_decisions(audit_records, today)
standing = {job_id: d for job_id, d in latest_decisions.items() if d != "undone"}
day_split = decisions.split([s.job.job_id for s in current], latest_decisions, cap)
on_today = set(day_split.accepted) | set(day_split.to_decide)
today_list = [s for s in current if s.job.job_id in on_today]
to_decide = [s for s in today_list if s.job.job_id not in standing]
accepted = [s for s in today_list if s.job.job_id in standing]
backlog = [s for s in current if s.job.job_id not in on_today]
review_count = sum(1 for j in jobs if j.needs_human or j.job_id in review_ids)


def ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def added_message(job_id: str, kind: str) -> str:
    """Where a replayed report landed, from the same split the tabs use."""
    head = f"Report {ranking_table.short_id(job_id)} added"
    job = next((j for j in jobs if j.job_id == job_id), None)
    if job is not None and (job.needs_human or job_id in review_ids):
        return f"{head}. It needs a person: open the Needs a human tab."
    if job is not None and decisions.is_make_safe(job):
        return f"{head} ({kind}). It is in Make safe now: send it to the make-safe contractor."
    rank = next((s.rank for s in current if s.job.job_id == job_id), None)
    if rank is None:
        return f"{head}."
    head = f"{head} ({kind}). It ranks {ordinal(rank)}"
    if job_id in day_split.to_decide:
        return f"{head}: it is in To decide."
    why = (
        "a new routine repair has most of its NT window left"
        if kind == "routine"
        else "today's list is already full of higher-ranked jobs"
    )
    return f"{head}: it waits in the Backlog, because {why}."


# The message stays until the next action: the audit log grows or the selection moves.
added_text = None
if (added := state.get_added_report()) is not None:
    added_id, added_kind, added_length = added
    if len(audit_records) == added_length and state.get_selected_job_id() == added_id:
        added_text = added_message(added_id, added_kind)
    else:
        state.set_added_report(None)


def in_view(job) -> bool:
    return region == state.ALL_REGIONS or art.communities[job.community_id]["region"] == region


shown_jobs = [j for j in jobs if in_view(j)]
today_shown = [s for s in today_list if in_view(s.job)]
to_decide_shown = [s for s in to_decide if in_view(s.job)]
accepted_shown = [s for s in accepted if in_view(s.job)]
backlog_shown = [s for s in backlog if in_view(s.job)]
human_jobs = sorted(
    (j for j in shown_jobs if j.needs_human or j.job_id in review_ids),
    key=lambda j: (j.reported_on, j.job_id),
)
if state.get_selected_job_id() is None and today_list:
    state.set_selected_job_id((to_decide or today_list)[0].job.job_id)


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
        "Jobs proposed within today's capacity: crews x jobs per crew per day (Blueprint).",
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
        today, state.ALL_REGIONS, lam, today_list, baseline[:cap], is_remote, label
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


make_safe_shown = [j for j in make_safe if in_view(j) and passes(j)]


def make_safe_rows(waiting: list) -> None:
    """The "Make safe now" lane above the tabs: one bordered row per Immediate job with an
    Open button; sending it to the contractor happens in the pane."""
    st.markdown(f"**Make safe now {len(waiting)}**")
    st.caption(MAKE_SAFE_CAPTION)
    if not waiting:
        st.caption(NO_MAKE_SAFE)
        return
    for job in waiting:
        with st.container(border=True):
            who, what, action = st.columns(HUMAN_ROW_RATIOS, vertical_alignment="center")
            who.markdown(f"**Job {ranking_table.short_id(job.job_id)}**")
            fault = job.fault_type.value.replace("_", " ") if job.fault_type is not None else "—"
            what.caption(f"{job.community_id} · {fault} · reported {job.reported_on.isoformat()}")
            if action.button("Open", key=f"workspace_make_safe_open_{job.job_id}", width="stretch"):
                state.set_selected_job_id(job.job_id)
                state.set_map_pick(None)
                st.rerun()


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
            "decision": "accepted" if standing.get(row["job_id"]) == "accepted" else None,
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

STALE = "The list changed since you opened this review; open it again."


def signed_today() -> list[audit.SignOff]:
    return [
        r
        for r in audit.read(state.get_audit_path())
        if isinstance(r, audit.SignOff) and r.day == today
    ]


human_set = runtime.human_set_for(runtime.read(state.get_runtime_path()))
current_fp = batch.fingerprint_of(
    lam, [s.job.job_id for s in current], state.get_hand_moves(), human_set, standing
)
signed_versions = {r.batch_version for r in signed_today()}


def decision_status(frozen: batch.Batch | None, versions: set[int]) -> batch.Status:
    if frozen is None:
        return "draft"
    if state.get_signed_today() and frozen.version in versions:
        return "changed_since_signature" if batch.is_stale(frozen, current_fp) else "signed"
    return "review_open"


status = decision_status(state.get_batch(), signed_versions)


def signed_banner() -> None:
    """The signed state at the top of To decide, with the way on to the visit plan."""
    latest = signed_today()[-1]
    st.success(
        f"Today's list is signed (v{latest.batch_version}): "
        f"{len(latest.today_job_ids)} jobs accepted."
    )
    st.caption(f"Audit reference `{latest.audit_ref}`")
    if st.button("Open the visit plan", key="workspace_open_visit_plan", type="primary"):
        try:
            st.switch_page("pages/visit_plan.py")
        except StreamlitPageNotFoundError:
            pass  # a page run on its own (AppTest) has no navigation registry


def handle_key(pressed: str | None) -> None:
    """J/K walk To decide as the tab shows it; A accepts only an unsigned, read job in To
    decide, through the Accept button's own function; X opens the reject form. No key signs."""
    if pressed is None:
        return
    order = [s.job.job_id for s in to_decide_shown if passes(s.job)]
    if pressed in ("j", "k"):
        if not order:
            return
        if selected in order:
            step = 1 if pressed == "j" else -1
            target = order[(order.index(selected) + step) % len(order)]
        else:
            target = order[0] if pressed == "j" else order[-1]
        state.set_selected_job_id(target)
        state.set_map_pick(None)
        st.rerun()
    elif pressed == "a":
        if status == "signed":
            st.toast(KEY_SIGNED)
        elif selected not in day_split.to_decide:
            st.toast(KEY_NOT_TO_DECIDE)
        elif not state.get_read(selected):
            st.toast(KEY_NOT_READ)
        else:
            details_pane.accept_for_today(selected, today)
            st.rerun()
    elif pressed == "x" and selected is not None:
        state.set_reject_job(selected)
        st.rerun()


handle_key(keyboard.render())

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
    st.caption(keyboard.HINT)
    if added_text is not None:
        st.success(added_text)
    make_safe_rows(make_safe_shown)
    tabs = st.tabs(
        [
            f"To decide {len(to_decide_shown)}",
            f"Accepted {len(accepted_shown)}",
            f"Needs a human {len(human_jobs)}",
            f"Backlog {len(backlog_shown)}",
        ]
    )
    with tabs[0]:
        if status == "signed":
            signed_banner()
        elif not to_decide_shown:
            st.info("Nothing left to decide here.")
    with tabs[1]:
        if not accepted_shown:
            st.info("No job accepted yet: open a job in To decide and read it to the bottom.")
    with tabs[2]:
        human_rows(human_jobs)
    # In the compare view To decide shows the whole of today's list against efficiency-first.
    lists = [
        (tabs[0], "today", to_decide, today_list, baseline[:cap]),
        (tabs[1], "accepted", accepted, None, None),
        (tabs[3], "backlog", backlog, backlog, baseline[cap:]),
    ]
    for tab, name, rows_scored, compared, efficiency_first in lists:
        with tab:
            if compare and compared is not None:
                scored = compared
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
            frame = view(rows_scored, against=baseline)
            if name in ("today", "accepted"):
                # A short list is read, not scanned: bordered rows with an explicit Open.
                picked = job_rows.render(today_rows(frame, rows_scored), selected, TODAY_ROWS_KEY)
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
    details_pane.render(
        art,
        jobs,
        current,
        cap,
        review_ids,
        today,
        lam,
        map_choice,
        job_split=day_split,
        signed=status == "signed",
    )

st.divider()
st.markdown(
    f"Today: {len(today_list)} jobs on today's list within capacity {cap} · "
    f"{len(accepted)} accepted · {len(to_decide)} to decide · "
    f"{remote_today} remote / {len(today_list) - remote_today} town · "
    f"Backlog {len(backlog)} · {len(state.get_hand_moves())} moved by hand · "
    f"{review_count} in review"
)


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
        today_job_ids=day_split.accepted,
        decisions=standing,
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
    st.rerun()  # the page shows the signed state: the banner in To decide, decisions closed


ready = not day_split.to_decide and bool(day_split.accepted)
if st.button(
    "Review and sign",
    key="workspace_review_and_sign",
    disabled=status == "review_open" or not ready,
):
    open_review(status)
if day_split.to_decide:
    st.caption(f"Decide the {len(day_split.to_decide)} jobs left in To decide first.")
elif not day_split.accepted:
    st.caption("Accept at least one job before you sign.")

frozen = state.get_batch()
if frozen is not None:
    if batch.is_stale(frozen, current_fp):
        st.warning(STALE)
        if st.button("Open again", key="workspace_open_again", disabled=not ready):
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
        fixed = sum(
            check.decision == "corrected"
            for check in audit.latest_checks(audit_records, today).values()
        )
        counts = (
            sum(d == "not_today" for d in standing.values()),
            sum(d == "needs_person" for d in standing.values()),
            fixed,
        )
        sign_off_form.render(
            frozen, status, on_submit, review_count, is_remote, frozen_rows, counts
        )

metrics.metrics_panel(today, state.ALL_REGIONS, lam)
effect_message.info(
    "Effect: "
    + metrics.effect_sentence(
        today, state.ALL_REGIONS, lam, today_list, baseline[:cap], is_remote, label
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
with steps_slot:
    today_steps.render(
        today_steps.steps(
            review_left=review_count,
            to_decide=len(day_split.to_decide),
            signed=status == "signed",
            plan_accepted=plan_accepted,
        )
    )
intro.about()
