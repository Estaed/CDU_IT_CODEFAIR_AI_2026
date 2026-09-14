"""PRD 3.4 Tenant answer (wireframes §7). A tenant looks up a job by its registration number
and reads four question-headed blocks built by ``explain.tenant_answer``. This page only
resolves which state the job is in (unknown, review, manual, unsigned, ranked, backlog or
superseded) from the open jobs, the audit log and the visit plan; the prose is the
template's, so the wording lint bounds the answer text."""

import streamlit as st

from fair_turn.app import state, theme
from fair_turn.app.components import intro
from fair_turn.app.components.ranking_table import (
    apply_hand_moves,
    capacity,
    open_jobs,
    review_requested_ids,
    short_id,
)
from fair_turn.core import audit, explain, scoring
from fair_turn.data import policy

REQUIRED_FIELDS = ("fault_type", "safety_class")
EXAMPLE_HINT = "Not sure of the number? Pick an example above instead."
WINDOW_CAPTION = (
    '"NT window" is the amount of time policy allows to fix this kind of repair once it '
    "is reported."
)
LAMBDA_CAPTION = (
    '"If distance did not count" compares your place in line today with where you would '
    "be if travel cost were left out of the sum (that comparison is written as λ = 0)."
)


@st.cache_resource
def policy_index() -> policy.PolicyIndex:
    return policy.load()


art = state.artefacts()
st.title("Tenant answer")
intro.purpose("tenant")
st.markdown(
    "**What to do here**\n\n"
    "1. Type the job number from the tenant's receipt, or pick an example.\n"
    "2. Read the answer to the tenant. It says where the repair sits and why."
)
st.caption(theme.PROVENANCE_LINE)
st.caption("Community ids shown in this project are pseudonymous, not real place names.")

today = state.get_today()
jobs = open_jobs(today)
records = audit.read(state.get_audit_path())
review_ids = review_requested_ids(records, today)
rankable = [j for j in jobs if not j.needs_human and j.job_id not in review_ids]
ranked = apply_hand_moves(scoring.rank(rankable, today, state.get_lam()), state.get_hand_moves())
today_capacity = capacity(state.ALL_REGIONS)
example_ids = [
    sorted(s.job.job_id for s in ranked[:today_capacity])[0],
    sorted(s.job.job_id for s in ranked[today_capacity:])[0],
    sorted(j.job_id for j in jobs if j.needs_human or j.job_id in review_ids)[0],
]
example_labels = {
    example_ids[0]: f"{short_id(example_ids[0])} · on today's list",
    example_ids[1]: f"{short_id(example_ids[1])} · waiting in the backlog",
    example_ids[2]: f"{short_id(example_ids[2])} · needs a person first",
}


typed = st.text_input(
    "Job registration number",
    help=f"Starts with {explain.JOB_ID_PREFIX} and ends with five digits, like "
    f"{explain.JOB_ID_EXAMPLE}. Find it on the tenant's report receipt.",
).strip()
example = st.selectbox(
    "Or try an example",
    example_ids,
    index=None,
    placeholder="Pick an example job",
    format_func=example_labels.__getitem__,
    help="A sample job in each state, so you can see what a tenant would be told.",
)
typed = example or typed


def visit_order_for(job_id: str, version: int) -> tuple[int, str] | None:
    """``(visit position, reason)`` when the plan for ``version`` visits the job in a
    different place from its signed order among the same crew's stops."""
    plan = state.get_plan()
    if plan is None or plan.batch_version != version:
        return None
    for crew_plan in plan.crews:
        ids = [stop.job_id for stop in crew_plan.stops]
        if job_id not in ids:
            continue
        signed = sorted(crew_plan.stops, key=lambda stop: stop.signed_rank)
        position = ids.index(job_id) + 1
        if position == [stop.job_id for stop in signed].index(job_id) + 1:
            return None
        change = next((c for c in reversed(plan.changes) if job_id in c.job_ids), None)
        return position, change.reason if change is not None else ""
    return None


def render(answer: explain.TenantAnswer) -> None:
    for block in answer.blocks:
        with st.container(border=True):
            st.subheader(block.question)
            for paragraph in block.paragraphs:
                st.markdown(paragraph)


if not typed:
    st.info(
        f"Type the job registration number from your report receipt. It starts with "
        f"{explain.JOB_ID_PREFIX} and ends with five digits, like {explain.JOB_ID_EXAMPLE}."
    )
    intro.about()
    st.stop()

open_by_id = {j.job_id.lower(): j for j in jobs}
known = {label["job_id"].lower() for label in art.labels} | set(open_by_id)

if typed.lower() not in known:
    render(explain.tenant_answer(state="unknown"))
    st.caption(EXAMPLE_HINT)
    intro.about()
    st.stop()

job = open_by_id.get(typed.lower())
if job is None:
    st.info("This job is not open on the selected day, so it is not in the queue.")
    st.stop()

st.caption(f"Job {job.job_id}")
lam = state.get_lam()
passages = (
    []
    if job.safety_class is None
    else policy.lookup(policy_index(), job.safety_class.value, job.is_remote, job.fault_type)
)
source = passages[0] if passages else None

if job.needs_human or job.job_id in review_ids:
    row = art.extraction.get(job.job_id)
    missing = tuple(
        f for f in REQUIRED_FIELDS if getattr(job, f) is None and (row is None or f not in row.kept)
    )
    render(
        explain.tenant_answer(
            state="review",
            scored=scoring.score_job(job, today, lam),
            policy=source,
            missing_fields=missing,
        )
    )
    st.stop()

if art.communities[job.community_id]["road_access"] == "barge_or_air":
    render(
        explain.tenant_answer(
            state="manual", scored=scoring.score_job(job, today, lam), policy=source
        )
    )
    st.caption(WINDOW_CAPTION)
    st.stop()

rankable = [j for j in jobs if not j.needs_human and j.job_id not in review_ids]
rank_at_lambda0 = next(
    s.rank for s in scoring.rank(rankable, today, 0.0) if s.job.job_id == job.job_id
)
signoffs = [
    r
    for r in records
    if isinstance(r, audit.SignOff) and r.day == today and r.decision == "approve"
]

if not signoffs:
    draft = apply_hand_moves(scoring.rank(rankable, today, lam), state.get_hand_moves())
    render(
        explain.tenant_answer(
            state="unsigned",
            scored=next(s for s in draft if s.job.job_id == job.job_id),
            rank_at_lambda0=rank_at_lambda0,
            lam=lam,
            policy=source,
        )
    )
    st.caption(WINDOW_CAPTION)
    st.caption(LAMBDA_CAPTION)
    st.stop()

latest = max(signoffs, key=lambda r: (r.batch_version, r.recorded_at))
scored = next(s for s in scoring.rank(rankable, today, latest.lam) if s.job.job_id == job.job_id)
common = dict(
    scored=scored,
    rank_at_lambda0=rank_at_lambda0,
    lam=latest.lam,
    coordinator_reason=latest.reason,
    policy=source,
)

if job.job_id not in latest.today_job_ids:
    signed_rank = (
        latest.ranked_job_ids.index(job.job_id) + 1 if job.job_id in latest.ranked_job_ids else None
    )
    render(explain.tenant_answer(state="backlog", signed_rank=signed_rank, **common))
    st.caption(WINDOW_CAPTION)
    st.caption(LAMBDA_CAPTION)
    st.stop()

superseded = any(
    isinstance(r, audit.PlanDecision) and r.day == today and r.batch_version < latest.batch_version
    for r in records
)
render(
    explain.tenant_answer(
        state="superseded" if superseded else "ranked",
        signed_rank=latest.today_job_ids.index(job.job_id) + 1,
        visit_order=visit_order_for(job.job_id, latest.batch_version),
        decision_version=latest.batch_version,
        **common,
    )
)
st.caption(WINDOW_CAPTION)
st.caption(LAMBDA_CAPTION)
intro.about()
