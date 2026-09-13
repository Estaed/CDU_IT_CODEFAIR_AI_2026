"""PRD 3.6 Audit log. Every sign-off, revision and override, filterable and exportable,
with the override rate over time."""

import altair as alt
import pandas as pd
import streamlit as st

from fair_turn.app import state, theme
from fair_turn.core import audit
from fair_turn.data.artefacts import AUDIT_DIR

SAMPLE_PATH = AUDIT_DIR / "sample.jsonl"

state.artefacts()
st.title("Audit log")
st.caption(theme.PROVENANCE_LINE)

records = audit.read(state.get_audit_path()) + audit.read(SAMPLE_PATH)

if not records:
    st.info("No sign-offs, revisions or overrides yet.")
else:
    rows = audit.export_rows(records)
    kinds = sorted({r["kind"] for r in rows})
    days = sorted({r["day"] for r in rows})
    kind_filter = st.multiselect("Kind", kinds, default=kinds)
    day_filter = st.selectbox("Day", ["All", *days])

    filtered = [
        r
        for r in rows
        if r["kind"] in kind_filter and (day_filter == "All" or r["day"] == day_filter)
    ]
    frame = pd.DataFrame(filtered)
    st.dataframe(frame, width="stretch")
    st.download_button(
        "Download CSV", frame.to_csv(index=False), file_name="audit_log.csv", mime="text/csv"
    )

    rate = audit.override_rate(records)
    if rate:
        rate_df = pd.DataFrame(rate, columns=["day", "override_rate"])
        chart = (
            alt.Chart(rate_df)
            .mark_line(color=theme.HUMAN_QUEUE)
            .encode(x="day:T", y="override_rate:Q")
        )
        st.altair_chart(chart, width="stretch")
