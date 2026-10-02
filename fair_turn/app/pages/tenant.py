"""Ask about a repair: a tenant, or the housing officer helping them, gets a real answer.

Is a crew coming this week? If not, why not, what would change it, and who decided. Every
sentence is a template over the plan; no model writes to a tenant.
"""

import streamlit as st

from fair_turn.app import state, theme
from fair_turn.core import constants, explain, weekly
from fair_turn.core.types import SafetyClass


def facts_for(job_id: str) -> explain.TenantFacts | None:
    job = next((j for j in state.all_jobs() if j.job_id == job_id), None)
    if job is None:
        return None
    place = state.places()[job.community_id]
    signed = state.signature()
    jobs_open = state.open_jobs()
    plan = state.week_plan(jobs_open)
    common = {
        "job": job,
        "today": state.today(),
        "base": place.base,
        "is_town": place.is_town,
        "setting_name": weekly.setting_name(state.get_setting()),
        "signed_by": signed.signer if signed else None,
        "signed_reason": signed.reason if signed else None,
    }
    if state.done_before(job_id) is not None:
        return explain.TenantFacts(**common, done_on=state.done_before(job_id))
    if job.needs_human:
        missing = tuple(f for f in ("fault_type", "safety_class") if getattr(job, f) is None)
        return explain.TenantFacts(**common, missing_fields=missing)
    if job.safety_class is SafetyClass.IMMEDIATE:
        return explain.TenantFacts(**common)
    trip = next((t for t in plan.trips if job_id in t.job_ids), None)
    start = None
    if trip is not None:
        start = next(s.start for c in plan.crews for s in c.stops if job_id in s.trip.job_ids)
    in_plan_under = tuple(
        name
        for name, value in constants.SETTINGS.items()
        if job_id in state.week_plan(jobs_open, value).planned_job_ids()
    )
    return explain.TenantFacts(
        **common,
        trip=trip,
        start_day=start,
        waiting=None if trip else plan.waiting_at(job.community_id),
        travel_days=weekly.travel_days(place),
        in_plan_under=in_plan_under,
    )


def examples() -> dict[str, str]:
    """Three real lookups for the demo: a remote repair with a crew coming, a remote one left
    waiting, and one a person still has to read."""
    jobs_open = state.open_jobs()
    plan = state.week_plan(jobs_open)
    planned = plan.planned_job_ids()
    remote = [j for j in jobs_open if j.is_remote and weekly.in_plan(j, state.today())]
    found = {}
    coming = next((j for j in remote if j.job_id in planned), None)
    if coming:
        found["Remote, crew coming"] = coming.job_id
    left = sorted(
        (j for j in remote if j.job_id not in planned),
        key=lambda j: j.reported_on,
    )
    if left:
        found["Remote, still waiting"] = left[0].job_id
    person = next((j for j in jobs_open if j.needs_human), None)
    if person:
        found["Report a person is reading"] = person.job_id
    return found


st.title("Ask about a repair")
st.caption(theme.PROVENANCE_LINE)
st.write(
    "For a tenant, or the housing officer helping them. Type the repair number from the "
    "report receipt. The answer says if a crew is coming this week, and if not, why not."
)
picks = examples()
choice = st.pills(
    "Or try an example",
    list(picks),
    selection_mode="single",
    default="Remote, still waiting" if "Remote, still waiting" in picks else None,
)
typed = st.text_input(
    "Repair number",
    value=picks.get(choice, "") if choice else "",
    placeholder=explain.JOB_ID_EXAMPLE,
)
job_id = typed.strip().upper()
if job_id:
    facts = facts_for(job_id)
    if facts is None:
        st.error(
            f"No repair has the number {job_id}. Numbers look like {explain.JOB_ID_EXAMPLE}. "
            "Your Community Housing Officer can help you find it."
        )
    else:
        answer = explain.tenant_answer(facts)
        with st.container(border=True):
            st.subheader(answer.headline)
            for block in answer.blocks:
                st.markdown(f"**{block.question}**")
                for paragraph in block.paragraphs:
                    st.write(paragraph)
        st.caption(f"Source for the time limits: {explain.POLICY_SOURCE}.")
