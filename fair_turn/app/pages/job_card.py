"""PRD 3.2 Job card: the tenant's words with source-phrase highlights, every field beside
the phrase it came from (empty where nothing verified), the factor breakdown at the
current lam, and a per-job rank override."""

from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st

from fair_turn.app import state, theme
from fair_turn.app.components import ranking_table
from fair_turn.app.components.highlight import render, spans
from fair_turn.core import audit, explain, scoring
from fair_turn.core.types import FaultType, SafetyClass
from fair_turn.data.artefacts import to_jobs

NOT_FOUND = "not found in report: fill in"
FIELD_LABELS = {
    "fault_type": "fault type",
    "safety_class": "safety class",
    "location_mentioned": "location mentioned",
    "crew_or_access_note": "crew/access note",
}
HUMAN_SETTABLE = {"fault_type": FaultType, "safety_class": SafetyClass}

art = state.artefacts()
st.title("Job card")
st.caption(theme.PROVENANCE_LINE)


@st.cache_data
def _jobs_by_id() -> dict:
    return {j.job_id: j for j in to_jobs(art)}


jobs_by_id = _jobs_by_id()

options = sorted(jobs_by_id)
default_id = state.get_selected_job_id()
default_index = options.index(default_id) if default_id in jobs_by_id else 0
job_id = st.selectbox("Job", options, index=default_index)
state.set_selected_job_id(job_id)

job = jobs_by_id[job_id]
row = art.extraction[job_id]
report_text = art.reports[job_id]
human_set = state.get_human_set(job_id)

evidence = {field: ev.evidence for field, ev in row.kept.items()}
st.markdown(render(report_text, spans(report_text, evidence)))

st.subheader("Fields")
fields = ["fault_type", "safety_class"]
fields += sorted(k for k in row.kept if k.startswith("health_risk:"))
fields += ["location_mentioned", "crew_or_access_note"]
records = []
for field in fields:
    label = FIELD_LABELS.get(field, field.split(":", 1)[-1].replace("_", " "))
    if field in row.kept:
        value = row.kept[field].evidence
    elif field in human_set:
        value = f"{human_set[field]} (human_set)"
    else:
        value = NOT_FOUND
    records.append({"Field": label, "Source phrase": value})
st.table(pd.DataFrame(records, columns=["Field", "Source phrase"]))

for field, enum_cls in HUMAN_SETTABLE.items():
    if field in row.kept:
        continue
    options = ["", *[e.value for e in enum_cls]]
    current = human_set.get(field, "")
    choice = st.selectbox(
        f"Set {FIELD_LABELS[field]} (missing)",
        options,
        index=options.index(current) if current in options else 0,
        key=f"human_{field}_{job_id}",
    )
    if choice and choice != current:
        state.set_human_set(job_id, field, choice)
        st.rerun()

today = state.get_today()
lam = state.get_lam()
open_today = ranking_table.open_jobs(today)
ranked = scoring.rank(open_today, today, lam)
scored = next((s for s in ranked if s.job.job_id == job_id), None)

st.subheader("Factor breakdown")
if job.needs_human:
    st.warning("This job is not ranked until the missing fields are filled.")
else:
    factors = scored.factors if scored is not None else scoring.score_job(job, today, lam).factors
    factor_names = list(factors)
    chart_df = pd.DataFrame({"factor": factor_names, "value": [factors[n] for n in factor_names]})
    chart = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X("value:Q"),
            y=alt.Y("factor:N", sort=None),
            color=alt.Color(
                "factor:N",
                scale=alt.Scale(
                    domain=list(theme.FACTOR_COLOURS.keys()),
                    range=list(theme.FACTOR_COLOURS.values()),
                ),
                legend=None,
            ),
        )
    )
    st.altair_chart(chart, width="stretch")
    if scored is not None:
        st.write(explain.why_sentence(scored, lam))

st.subheader("Override rank")
disabled = scored is None
with st.form("override_form"):
    n = len(ranked)
    new_rank = st.number_input(
        "New rank",
        min_value=1,
        max_value=max(n, 1),
        value=scored.rank if scored is not None else 1,
        disabled=disabled,
    )
    reason = st.text_area("Reason", disabled=disabled)
    submitted = st.form_submit_button("Submit override", disabled=disabled)

if disabled:
    st.caption("This job is not in today's open ranked set; the rank cannot be overridden.")
elif submitted:
    if not reason.strip():
        st.error("A reason is required.")
    else:
        audit.append(
            state.get_audit_path(),
            audit.Override(
                day=today,
                job_id=job_id,
                from_rank=scored.rank,
                to_rank=int(new_rank),
                reason=reason,
                at=datetime.now(),
            ),
        )
        st.success("Override recorded.")
