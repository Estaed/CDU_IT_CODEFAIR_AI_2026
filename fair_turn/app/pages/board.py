"""PRD 3.1 Triage board: the needs-a-human queue, then the ranking at the chosen lam beside
the efficiency-first ranking at lam = 1.0."""

from datetime import timedelta

import streamlit as st

from fair_turn.app import state, theme
from fair_turn.app.components import map as nt_map_component
from fair_turn.app.components import metrics, ranking_table
from fair_turn.core import constants, scoring

JOB_CARD = "pages/job_card.py"
MISSING = {"fault_type": "fault type", "safety_class": "safety class"}

art = state.artefacts()
st.title("Triage board")
st.caption(theme.PROVENANCE_LINE)

day_col, region_col, lam_col = st.columns(3)
today = day_col.date_input(
    "Day",
    value=state.get_today(),
    min_value=constants.WINDOW_START,
    max_value=constants.WINDOW_START + timedelta(days=constants.WINDOW_DAYS),
    key="board_today",
)
state.set_today(today)
regions = [state.ALL_REGIONS, *constants.REGIONS]
region = region_col.selectbox(
    "Region", regions, index=regions.index(state.get_region()), key="board_region"
)
state.set_region(region)
lam = lam_col.slider(
    "Equity setting λ (1.0 efficiency first, 0.0 need only)",
    min_value=0.0,
    max_value=1.0,
    value=state.get_lam(),
    step=0.05,
    key="board_lam",
)
state.set_lam(lam)

jobs = ranking_table.open_jobs(today)
if region != state.ALL_REGIONS:
    jobs = [j for j in jobs if art.communities[j.community_id]["region"] == region]
_, human_queue = scoring.split_human_queue(jobs)


def _open_job_card(job_id: str) -> None:
    state.set_selected_job_id(job_id)
    st.switch_page(JOB_CARD)


if human_queue:
    lines = [f"**Needs a human: {len(human_queue)} job(s) are not ranked.**"]
    for job in human_queue:
        missing = ", ".join(
            label for field, label in MISSING.items() if getattr(job, field) is None
        )
        lines.append(f"- {job.job_id} · community {job.community_id} · missing {missing}")
    st.warning("\n".join(lines))
    queue_col, button_col = st.columns([3, 1])
    queued = queue_col.selectbox("Queued job", [j.job_id for j in human_queue])
    if button_col.button("Open job card"):
        _open_job_card(queued)
else:
    st.success("No job needs a human today.")

at_lam = scoring.rank(jobs, today, lam)
at_one = scoring.rank(jobs, today, 1.0)
tables = [
    (f"Ranking at λ = {lam:.2f}", "board_rank_lam", at_lam, None, lam),
    ("Efficiency first, λ = 1.00", "board_rank_one", at_one, at_lam, 1.0),
]
for column, (heading, key, scored, other, table_lam) in zip(st.columns(2), tables, strict=True):
    with column:
        st.subheader(heading)
        frame = ranking_table.rows_for(scored, other, table_lam, today)
        event = st.dataframe(
            frame,
            hide_index=True,
            column_config=ranking_table.column_config(frame),
            on_select="rerun",
            selection_mode="single-row",
            key=key,
        )
        if event.selection.rows:
            _open_job_card(frame.iloc[event.selection.rows[0]]["job id"])

st.subheader("Map")
open_counts: dict[str, int] = {}
for job in jobs:
    open_counts[job.community_id] = open_counts.get(job.community_id, 0) + 1
st.altair_chart(nt_map_component.nt_map(art.communities, open_counts, region), width="stretch")

st.subheader("Wait metrics")
if state.get_signed_today():
    metrics.metrics_panel(today, region, lam)
else:
    st.info("Wait metrics appear after today's sign-off (decide before reveal).")
