"""PRD 3.3 Visit plan (wireframes §6), pooled crews with reach (2026-09-14): the signed list
placed on the NT-wide crew pool. In signed order each road job takes the nearest free crew
that reaches it; distance chooses which crew goes, never which job is served; each crew
drives the shortest route over its stops; air/barge work stays manual coordination; the road
km price of today's weighting, and the jobs no crew within reach can take, are shown against
the efficiency-first list; every plan decision is written against the signed batch version.
"""

import pandas as pd
import streamlit as st
from streamlit.errors import StreamlitPageNotFoundError

from fair_turn.app import state, theme
from fair_turn.app.components import intro, ranking_table, run_sheet
from fair_turn.core import audit, scoring, visit_plan
from fair_turn.data import geography

EFFICIENCY_LAM = 1.0
RULE_SENTENCE = (
    "Distance chooses which crew goes, never which job is served. The jobs are the signed list."
)

art = state.artefacts()
today = state.get_today()
st.title("Visit plan")
intro.purpose("visit_plan")
st.caption(theme.PROVENANCE_LINE)


def _fault_label(job) -> str:
    if not job.fault_type:
        return "—"
    text = job.fault_type.value.replace("_", " ")
    return text[0].upper() + text[1:]


def _signed_km(value: float) -> str:
    sign = "+" if value >= 0 else "−"
    return f"{sign}{abs(value):,.0f} km"


def _job_label(job_id: str) -> str:
    return ranking_table.short_id(job_id)


records = audit.read(state.get_audit_path())
signoffs_today = sorted(
    (r for r in records if isinstance(r, audit.SignOff) and r.day == today),
    key=lambda r: r.batch_version,
)

if not signoffs_today:
    with st.container(border=True):
        st.info(
            "Nothing to plan yet. Sign today's batch on the workspace and the run sheet "
            "appears here."
        )
        st.caption("Columns of the run sheet")
        st.dataframe(
            pd.DataFrame(columns=("stop", "crew", "job", "community", "distance km")),
            hide_index=True,
            width="stretch",
        )
        try:
            st.page_link("pages/workspace.py", label="Go to the workspace")
        except StreamlitPageNotFoundError:
            # AppTest opens this page without the navigation registry that resolves page links.
            pass
else:
    signoff = signoffs_today[-1]
    st.markdown(f"Signed list {signoff.day} v{signoff.batch_version} by {signoff.signer}")

    open_today = ranking_table.open_jobs(today)
    jobs_by_id = {j.job_id: j for j in open_today}
    crews = geography.crews(art.communities)
    stops, no_longer_open = run_sheet.stops(signoff.today_job_ids, jobs_by_id, today)

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
        current_plan = visit_plan.plan(signoff.batch_version, stops, crews)
        state.set_plan(current_plan)

    n_open = len(stops)
    efficiency_ids = [s.job.job_id for s in scoring.rank(open_today, today, EFFICIENCY_LAM)][
        :n_open
    ]
    efficiency_plan = visit_plan.plan(
        signoff.batch_version, run_sheet.stops(efficiency_ids, jobs_by_id, today)[0], crews
    )

    st.markdown(RULE_SENTENCE)
    signed_col, efficiency_col, cost_col = st.columns(3)
    signed_col.metric("Road km, this signed list", f"{current_plan.road_km:,.0f} km", border=True)
    efficiency_col.metric(
        "Road km, efficiency-first list",
        f"{efficiency_plan.road_km:,.0f} km",
        help="The top of the list at travel-cost weight 1.00, same day, same crews, "
        "planned the same way.",
        border=True,
    )
    cost_col.metric(
        "Extra road km for today's weighting",
        _signed_km(current_plan.road_km - efficiency_plan.road_km),
        help="Positive means today's signed list drives further than the efficiency-first "
        "list. It is the travel price of the equity choice: shown, never optimised away.",
        border=True,
    )
    st.caption(
        "Jobs with no crew within reach: this signed list "
        f"{current_plan.out_of_reach}, efficiency-first list {efficiency_plan.out_of_reach}."
    )

    if no_longer_open:
        st.caption(
            f"{len(no_longer_open)} signed jobs are no longer open, so both sides compare "
            f"the {n_open} jobs still open."
        )
        st.caption(
            f"No longer open: {len(no_longer_open)} "
            f"({', '.join(_job_label(j) for j in no_longer_open)})"
        )

    for crew_plan in current_plan.crews:
        crew = crew_plan.crew
        with st.container(border=True):
            n_stops = len(crew_plan.stops)
            stops_word = "stop" if n_stops == 1 else "stops"
            st.markdown(f"**Crew {crew.crew_id}** · {n_stops} {stops_word}")
            if not crew_plan.stops:
                st.markdown("No signed road jobs for this crew")
                continue
            for index, stop in enumerate(crew_plan.stops, start=1):
                job = jobs_by_id[stop.job_id]
                leg = crew_plan.legs_km[index - 1]
                flag = " · travel day" if crew_plan.travel_day_legs[index - 1] else ""
                row_text, row_button = st.columns([6, 1])
                row_text.markdown(
                    f"{index}. {_job_label(stop.job_id)} · "
                    f"{ranking_table.community_label(stop.community_id)} · "
                    f"{_fault_label(job)} · signed rank {stop.signed_rank} · "
                    f"{leg:,.0f} km{flag}"
                )
                if row_button.button("Select", key=f"visit_select_{crew.crew_id}_{stop.job_id}"):
                    state.set_selected_job_id(stop.job_id)
            back_flag = " · travel day" if crew_plan.travel_day_legs[-1] else ""
            st.markdown(f"Back to {crew.base} · {crew_plan.legs_km[-1]:,.0f} km{back_flag}")
            st.markdown(f"Crew total: {crew_plan.km:,.0f} km")
            st.caption("Registrations: " + ", ".join(stop.job_id for stop in crew_plan.stops))

    st.subheader("Signed work needing manual coordination")
    if not current_plan.manual:
        st.markdown("No manual coordination needed.")
    for manual_item in current_plan.manual:
        st.markdown(
            f"{_job_label(manual_item.stop.job_id)}  {manual_item.stop.community_id}  "
            f"signed rank {manual_item.stop.signed_rank}  air/barge access, no road route"
        )
        st.markdown(f"Next action: {manual_item.next_action} — owner: {manual_item.owner}")
        st.caption(f"Registration: {manual_item.stop.job_id}")

    st.subheader("Signed, unplanned")
    if not current_plan.unplanned:
        st.markdown("Nothing signed is unplanned.")
    for unplanned_item in current_plan.unplanned:
        st.markdown(
            f"{_job_label(unplanned_item.stop.job_id)}  {unplanned_item.stop.community_id}  "
            f"signed rank {unplanned_item.stop.signed_rank}  "
            f"signed, unplanned: {unplanned_item.reason}"
        )
        st.caption(f"Registration: {unplanned_item.stop.job_id}")

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
                total_stops = sum(len(cp.stops) for cp in current_plan.crews)
                audit.append(
                    state.get_audit_path(),
                    audit.PlanDecision(
                        day=today,
                        batch_version=current_plan.batch_version,
                        action="accept",
                        detail=f"{total_stops} stops, {current_plan.road_km:.0f} km",
                        reason=accept_reason.strip(),
                    ),
                )
                st.rerun()

    with edit_col, st.expander("Edit order"):
        crew_ids = [cp.crew.crew_id for cp in current_plan.crews if cp.stops]
        if not crew_ids:
            st.markdown("No road stops to reorder.")
        else:
            crew_choice = st.selectbox("Crew", crew_ids, key="visit_edit_crew")
            edit_crew_plan = next(cp for cp in current_plan.crews if cp.crew.crew_id == crew_choice)
            stop_ids = [s.job_id for s in edit_crew_plan.stops]
            rank_by_id = {s.job_id: s.signed_rank for s in edit_crew_plan.stops}
            new_order = [
                st.selectbox(
                    f"Stop {position + 1}",
                    stop_ids,
                    index=position,
                    key=f"visit_edit_pos_{position}",
                    format_func=lambda jid: f"{_job_label(jid)} (signed rank {rank_by_id[jid]})",
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
                            current_plan, crew_choice, new_order, edit_reason.strip()
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

intro.about()
