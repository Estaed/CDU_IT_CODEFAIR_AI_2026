"""PRD 3.3 Sign-off. The human commits today's lambda and a reason; nothing is dispatched
by this tool."""

from datetime import datetime

import streamlit as st

from fair_turn.app import state, theme
from fair_turn.app.components.ranking_table import open_jobs
from fair_turn.core import audit, scoring

state.artefacts()
st.title("Sign-off")
st.caption(theme.PROVENANCE_LINE)
st.caption("Signing off records a decision; it does not dispatch any job.")

today = state.get_today()
lam = state.get_lam()
ranked = scoring.rank(open_jobs(today), today, lam)
ranked_ids = tuple(s.job.job_id for s in ranked)

st.write(f"Day: {today.isoformat()}")
st.write(f"Lambda: {lam}")
st.write(f"Ranked job ids ({len(ranked_ids)}): {', '.join(ranked_ids)}")

if state.get_signed_today():
    st.info("Already signed off today. Signing again appends a new record.")

with st.form("sign_off_form"):
    reason = st.text_area("Reason")
    signer = st.text_input("Signer")
    submitted = st.form_submit_button("Sign off")

if submitted:
    if not reason.strip() or not signer.strip():
        st.error("A reason and a signer name are both required.")
    else:
        audit.append(
            state.get_audit_path(),
            audit.SignOff(
                day=today,
                lam=lam,
                reason=reason,
                signer=signer,
                signed_at=datetime.now(),
                ranked_job_ids=ranked_ids,
            ),
        )
        state.set_signed_today(True)
        st.success("Signed off.")
