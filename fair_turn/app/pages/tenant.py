"""PRD 3.4 Tenant view. A tenant looks up a job by its registration number and gets a
real answer built from ``explain.tenant_answer``; this page adds only headings, no prose
of its own, so the wording lint bounds the whole page text."""

import streamlit as st

from fair_turn.app import state, theme
from fair_turn.app.components.ranking_table import open_jobs
from fair_turn.core import audit, explain, scoring

art = state.artefacts()
st.title("Tenant view")
st.caption(theme.PROVENANCE_LINE)
st.caption("Community ids shown in this project are pseudonymous, not real place names.")

job_id_input = st.text_input("Job registration number")
typed = job_id_input.strip()

if typed:
    label_ids = [label["job_id"] for label in art.labels]
    match = next((jid for jid in label_ids if jid.lower() == typed.lower()), None)

    if match is None:
        st.info("We could not find that job number. Check it and try again.")
    else:
        today = state.get_today()
        lam = state.get_lam()
        jobs = open_jobs(today)
        open_by_id = {j.job_id: j for j in jobs}

        if match not in open_by_id:
            st.subheader(f"Job {match}")
            st.write(f"This job is not open on {today.isoformat()}.")
        elif open_by_id[match].needs_human:
            st.subheader(f"Job {match}")
            st.write("A person is checking this job before it can be ranked.")
        else:
            ranked = scoring.rank(jobs, today, lam)
            scored = next(s for s in ranked if s.job.job_id == match)
            rank_at_lambda0 = next(
                s.rank for s in scoring.rank(jobs, today, 0.0) if s.job.job_id == match
            )
            window = scoring.window_days(scored.job)

            records = audit.read(state.get_audit_path())
            signoffs = [r for r in records if isinstance(r, audit.SignOff) and r.day == today]
            if signoffs:
                latest = max(signoffs, key=lambda r: r.signed_at)
                reason = latest.reason
                answer_lam = latest.lam
            else:
                reason = "The coordinator has not signed off today's setting yet."
                answer_lam = lam

            st.subheader(f"Job {match}")
            st.markdown(explain.tenant_answer(scored, rank_at_lambda0, window, reason, answer_lam))
