"""PRD 3.3 Visit plan (wireframes §6): the signed list allocated to crews in signed order,
distance used only to measure and to suggest never-silent swaps, air/barge work kept visible
as manual coordination, and every plan decision written against the signed batch version.
"""

import streamlit as st

from fair_turn.app import state, theme
from fair_turn.app.components import ranking_table
from fair_turn.core import audit, constants, scoring, visit_plan
from fair_turn.data import geography

art = state.artefacts()
today = state.get_today()
st.title("Visit plan")
st.caption(theme.PROVENANCE_LINE)


def _fault_label(job) -> str:
    return job.fault_type.value.replace("_", " ") if job.fault_type else "—"


def _stop_access(road_access: str) -> str:
    return "air" if road_access == "barge_or_air" else "road"


def _base_for_region(region: str) -> str:
    return next(row["crew_base"] for row in art.communities.values() if row["region"] == region)


def _road_factor(stop: visit_plan.Stop) -> float:
    return geography.ROAD_FACTORS[art.communities[stop.community_id]["road_access"]]


records = audit.read(state.get_audit_path())
signoffs_today = sorted(
    (r for r in records if isinstance(r, audit.SignOff) and r.day == today),
    key=lambda r: r.batch_version,
)

if not signoffs_today:
    st.info("Sign today's list first")
    if st.button("Go to the workspace", key="visit_go_to_workspace"):
        st.switch_page("pages/workspace.py")
else:
    signoff = signoffs_today[-1]
    st.markdown(f"Signed list {signoff.day} v{signoff.batch_version} by {signoff.signer}")

    jobs_by_id = {j.job_id: j for j in ranking_table.open_jobs(today)}
    stops: list[visit_plan.Stop] = []
    no_longer_open: list[str] = []
    for rank, job_id in enumerate(signoff.today_job_ids, start=1):
        job = jobs_by_id.get(job_id)
        if job is None:
            no_longer_open.append(job_id)
            continue
        community = art.communities[job.community_id]
        closed = any(
            c["community_id"] == job.community_id
            and c["closed_from"] <= today.isoformat() <= c["closed_to"]
            for c in art.closures
        )
        days_open = (today - job.reported_on).days
        stops.append(
            visit_plan.Stop(
                job_id=job.job_id,
                community_id=job.community_id,
                region=community["region"],
                lat=float(community["lat"]),
                lon=float(community["lon"]),
                access=_stop_access(community["road_access"]),
                road_open=not closed,
                signed_rank=rank,
                window_days_left=max(0, round(scoring.window_days(job) - days_open)),
            )
        )

    crews = []
    for region in constants.REGIONS:
        base = _base_for_region(region)
        lat, lon = constants.CREW_BASE_COORDS[base]
        crews.append(visit_plan.Crew(base, region, lat, lon, visit_plan.crew_capacity(region)))

    def _decisions_for(version: int) -> list[audit.PlanDecision]:
        return [
            r
            for r in records
            if isinstance(r, audit.PlanDecision) and r.day == today and r.batch_version == version
        ]

    current_plan = state.get_plan()
    accepted_current = current_plan is not None and any(
        d.action == "accept" for d in _decisions_for(current_plan.batch_version)
    )
    if current_plan is None or (
        current_plan.batch_version != signoff.batch_version and not accepted_current
    ):
        current_plan = visit_plan.plan(signoff.batch_version, stops, crews, _road_factor)
        state.set_plan(current_plan)

    if no_longer_open:
        st.caption(f"No longer open: {len(no_longer_open)} ({', '.join(no_longer_open)})")

    for crew_plan in current_plan.crews:
        crew = crew_plan.crew
        with st.container(border=True):
            st.markdown(f"**Crew {crew.base} ({crew.jobs_per_day} jobs/day, road)**")
            if not crew_plan.stops:
                st.markdown("No signed road jobs for this crew")
            else:
                for index, (stop, leg) in enumerate(
                    zip(crew_plan.stops, crew_plan.legs_km, strict=False), start=1
                ):
                    job = jobs_by_id[stop.job_id]
                    open_word = "open" if stop.road_open else "closed"
                    row_text, row_button = st.columns([6, 1])
                    row_text.markdown(
                        f"{index}. {stop.job_id}  {stop.community_id}  {leg:.0f} km road, "
                        f"{open_word}  {_fault_label(job)}  signed rank {stop.signed_rank}"
                    )
                    if row_button.button("Select", key=f"visit_select_{crew.base}_{stop.job_id}"):
                        state.set_selected_job_id(stop.job_id)
                if crew_plan.within_capacity:
                    st.markdown(f"Within job-count capacity — {crew_plan.km:.0f} km")
                else:
                    unfit = sum(
                        1
                        for item in current_plan.unplanned
                        if item.reason == "over crew capacity" and item.stop.region == crew.region
                    )
                    st.markdown(f"Does not fit: {unfit} signed jobs unplanned")

    st.subheader("Suggested changes (not applied)")
    suggested = visit_plan.suggestions(current_plan, _road_factor)
    stop_by_id = {s.job_id: s for cp in current_plan.crews for s in cp.stops}
    if not suggested:
        st.markdown("No suggested changes.")
    for position, suggestion in enumerate(suggested):
        rank_a = stop_by_id[suggestion.job_a].signed_rank
        rank_b = stop_by_id[suggestion.job_b].signed_rank
        st.markdown(
            f"Crew {suggestion.crew_base}: visit rank {rank_b} before rank {rank_a}, "
            f"saves {suggestion.saving_km:.0f} km; same day for both, windows unchanged."
        )
        reason = st.text_input("Reason", key=f"visit_suggestion_reason_{position}")
        if st.button("Accept change", key=f"visit_suggestion_accept_{position}"):
            if not reason.strip():
                st.error("A reason is required.")
            else:
                updated = visit_plan.apply(current_plan, suggestion, reason.strip(), _road_factor)
                state.set_plan(updated)
                audit.append(
                    state.get_audit_path(),
                    audit.PlanDecision(
                        day=today,
                        batch_version=current_plan.batch_version,
                        action="suggestion_accept",
                        detail=f"{suggestion.job_a} <-> {suggestion.job_b}",
                        reason=reason.strip(),
                    ),
                )
                st.rerun()

    st.subheader("Signed work needing manual coordination")
    if not current_plan.manual:
        st.markdown("No manual coordination needed.")
    for manual_item in current_plan.manual:
        st.markdown(
            f"{manual_item.stop.job_id}  {manual_item.stop.community_id}  "
            "air/barge access, no road route"
        )
        st.markdown(f"Next action: {manual_item.next_action} — owner: coordinator")

    st.subheader("Signed, unplanned")
    if not current_plan.unplanned:
        st.markdown("Nothing signed is unplanned.")
    for unplanned_item in current_plan.unplanned:
        st.markdown(
            f"{unplanned_item.stop.job_id}  {unplanned_item.stop.community_id}  "
            f"{unplanned_item.reason}"
        )

    decisions_current = _decisions_for(current_plan.batch_version)
    accepted = any(d.action == "accept" for d in decisions_current)
    superseded = current_plan.batch_version != signoff.batch_version
    status_text = "Superseded" if superseded else ("Accepted" if accepted else "Draft")
    st.markdown(f"Plan status: {status_text}")

    accept_col, edit_col, reject_col = st.columns(3)
    with accept_col:
        accept_reason = st.text_input("Reason", key="visit_accept_reason")
        if superseded:
            st.button("Accept plan", key="visit_accept_plan", disabled=True)
            st.caption(
                f"Built on v{current_plan.batch_version}; sign-off v{signoff.batch_version} "
                "supersedes it — rebuild"
            )
        elif st.button("Accept plan", key="visit_accept_plan"):
            if not accept_reason.strip():
                st.error("A reason is required.")
            else:
                total_km = sum(cp.km for cp in current_plan.crews)
                total_stops = sum(len(cp.stops) for cp in current_plan.crews)
                audit.append(
                    state.get_audit_path(),
                    audit.PlanDecision(
                        day=today,
                        batch_version=current_plan.batch_version,
                        action="accept",
                        detail=f"{total_stops} stops, {total_km:.0f} km",
                        reason=accept_reason.strip(),
                    ),
                )
                st.rerun()

    with edit_col, st.expander("Edit order"):
        crew_bases = [cp.crew.base for cp in current_plan.crews if cp.stops]
        if not crew_bases:
            st.markdown("No road stops to reorder.")
        else:
            crew_choice = st.selectbox("Crew", crew_bases, key="visit_edit_crew")
            edit_crew_plan = next(cp for cp in current_plan.crews if cp.crew.base == crew_choice)
            stop_ids = [s.job_id for s in edit_crew_plan.stops]
            rank_by_id = {s.job_id: s.signed_rank for s in edit_crew_plan.stops}
            new_order = [
                st.selectbox(
                    f"Stop {position + 1}",
                    stop_ids,
                    index=position,
                    key=f"visit_edit_pos_{position}",
                    format_func=lambda jid: f"{jid} (signed rank {rank_by_id[jid]})",
                )
                for position in range(len(stop_ids))
            ]
            edit_reason = st.text_input("Reason", key="visit_edit_reason")
            if st.button("Apply edit", key="visit_edit_apply"):
                if not edit_reason.strip():
                    st.error("A reason is required.")
                else:
                    try:
                        updated = visit_plan.edit_order(
                            current_plan, crew_choice, new_order, edit_reason.strip(), _road_factor
                        )
                    except ValueError as exc:
                        st.error(str(exc))
                    else:
                        state.set_plan(updated)
                        audit.append(
                            state.get_audit_path(),
                            audit.PlanDecision(
                                day=today,
                                batch_version=current_plan.batch_version,
                                action="edit",
                                detail=", ".join(new_order),
                                reason=edit_reason.strip(),
                            ),
                        )
                        st.rerun()

    with reject_col:
        reject_reason = st.text_input("Reason", key="visit_reject_reason")
        if st.button("Reject with reason", key="visit_reject_plan"):
            if not reject_reason.strip():
                st.error("A reason is required.")
            else:
                audit.append(
                    state.get_audit_path(),
                    audit.PlanDecision(
                        day=today,
                        batch_version=current_plan.batch_version,
                        action="reject",
                        detail="",
                        reason=reject_reason.strip(),
                    ),
                )
                st.rerun()
