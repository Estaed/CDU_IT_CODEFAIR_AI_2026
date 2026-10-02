"""Reports: what the AI read from each one, and the ones a person must finish."""

from datetime import datetime

import streamlit as st

from fair_turn.app import intake, state, theme
from fair_turn.app.components import reading
from fair_turn.core import audit
from fair_turn.core.types import FaultType, SafetyClass
from fair_turn.data import runtime

CHOICES = {
    "fault_type": [f.value for f in FaultType],
    "safety_class": [s.value for s in SafetyClass],
}
REASONS = (
    "The report describes it",
    "Tenant confirmed by phone",
    "Housing officer confirmed on site",
)


def plan_line(job_id: str) -> str:
    """Where the job stands in this week's plan, in one sentence."""
    if state.done_before(job_id) is not None:
        return f"Done on {state.done_before(job_id):%d %B}."
    job = next((j for j in state.open_jobs() if j.job_id == job_id), None)
    if job is None:
        return "Not open on the planning day."
    if job.needs_human:
        return "Not in the plan yet: a person must set the missing facts first."
    if job.safety_class is SafetyClass.IMMEDIATE:
        return "Emergency: goes to the make-safe team, not the weekly plan."
    plan = state.week_plan(state.open_jobs())
    if job_id in plan.planned_job_ids():
        return f"In this week's plan: crew from {plan.trip_to(job.community_id).base}."
    waiting = plan.waiting_at(job.community_id)
    return f"Waiting this week: {waiting.reason}." if waiting else "Waiting this week."


def set_missing(r: reading.Reading) -> None:
    with st.form(f"set_{r.job_id}"):
        st.markdown("**Set the missing facts from the report.**")
        st.caption(
            "The AI's own guess is not shown: it would steer you. Read the report and decide."
        )
        values = {
            field: st.selectbox(
                reading.LABELS[field],
                CHOICES[field],
                index=None,
                format_func=lambda v: v.replace("_", " "),
                key=f"value_{r.job_id}_{field}",
            )
            for field in r.missing
        }
        why = st.radio("Why you are sure", REASONS, index=None, key=f"why_{r.job_id}")
        who = st.text_input("Your name", value=state.get_signer(), key=f"who_{r.job_id}")
        if st.form_submit_button("Save and add to the plan", type="primary"):
            if any(v is None for v in values.values()) or why is None or not who.strip():
                st.error("Set every missing fact, say why you are sure, and give your name.")
                return
            for field, value in values.items():
                runtime.append(
                    state.get_runtime_path(),
                    runtime.HumanSetField(
                        r.job_id, field, value, who.strip(), why, datetime.now().astimezone()
                    ),
                )
                audit.append(
                    state.get_audit_path(),
                    audit.FieldSet(state.today(), r.job_id, field, value, who.strip(), why),
                )
            state.set_signer(who.strip())
            st.rerun()


st.title("Reports")
st.caption(theme.PROVENANCE_LINE)
st.write(
    "The AI reads each repair report for what is broken, how urgent it is, and who lives "
    "there. Every fact must point to the tenant's own words, shown in bold. If it cannot, "
    "the fact stays empty and a person sets it. The AI never decides the plan."
)
jobs_open = state.open_jobs()
waiting_for_person = [j for j in jobs_open if j.needs_human]
tab_person, tab_look, tab_add = st.tabs(
    [f"Needs a person ({len(waiting_for_person)})", "Look up a report", "Add a new report"]
)

with tab_person:
    if not waiting_for_person:
        st.success("Every open report has been read. Nothing waits for a person.")
    else:
        job_id = st.selectbox(
            "Report",
            [j.job_id for j in waiting_for_person],
            format_func=lambda i: (
                f"{i} · {next(j.community_id for j in jobs_open if j.job_id == i)}"
            ),
        )
        r = reading.reading(job_id)
        reading.show(r)
        set_missing(r)

with tab_look:
    ids = sorted((j.job_id for j in jobs_open), reverse=True)
    job_id = st.selectbox("Report number", ids, index=None, placeholder="Type or pick a number")
    if job_id:
        st.info(plan_line(job_id))
        reading.show(reading.reading(job_id))

with tab_add:
    saved = intake.render()
    if saved:
        st.success(f"Saved as {saved}. {plan_line(saved)}")
        if st.button("Show it"):
            st.rerun()
    st.caption(
        f"New reports are dated {state.today():%d %B %Y}, the planning Monday, so they join "
        "this week's proposal."
    )
