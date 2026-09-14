"""The sign-off form of the workspace (PRD 3.1, wireframes §5): a read-only summary of the
frozen batch, the exact list one expander away, then signer, decision and reason, validated
inline under each field. Writing the record is the caller's ``on_submit``."""

from collections.abc import Callable

import pandas as pd
import streamlit as st

from fair_turn.core import batch

DECISIONS = {"Approve today's list": "approve", "Defer": "defer"}
SIGNER_REQUIRED = "A signer is required."
REASON_REQUIRED = "A reason is required."


def check_line(today_job_ids: tuple[str, ...], checks: dict[str, str]) -> str:
    checked = [job_id for job_id in today_job_ids if job_id in checks]
    corrected = sum(checks[job_id] == "corrected" for job_id in checked)
    return (
        f"You checked {len(checked)} of {len(today_job_ids)} jobs on today's list "
        f"and corrected {corrected}."
    )


def render(
    frozen: batch.Batch,
    status: batch.Status,
    on_submit: Callable[[str, str, str], None],
    review_count: int,
    is_remote: Callable[[str], bool],
    rows: pd.DataFrame,
    checks: dict[str, str] | None = None,
) -> None:
    """``rows`` is the frozen today's list in the workspace's columns (``community id``
    included); ``on_submit(signer, decision, reason)`` runs only with both fields filled.
    ``checks`` maps a job id checked today to ``"confirmed"`` or ``"corrected"``; it is
    reported in the summary and never a condition for signing."""
    checks = checks or {}
    today_count = len(frozen.today_job_ids)
    remote = sum(is_remote(community_id) for community_id in rows["community id"])
    with st.form("sign_off"):
        st.markdown(f"**Review and sign · {frozen.day} · batch v{frozen.version}**")
        st.markdown(
            f"Weighting {batch.preset_label(frozen.lam, frozen.preset)} "
            f"(travel-cost weight {frozen.lam:.2f})"
        )
        st.markdown(
            f"Today's list {today_count} jobs · {remote} remote · {today_count - remote} town · "
            f"Backlog {len(frozen.ranked_job_ids) - today_count}"
        )
        moves = [f"Moved by hand {len(frozen.hand_moves)}"]
        moves += [
            f'- {m.job_id} rank {m.from_rank} → {m.to_rank} "{m.reason}"' for m in frozen.hand_moves
        ]
        st.markdown("\n".join(moves))
        st.markdown(f"In review queue {review_count} (not ranked)")
        st.markdown(check_line(frozen.today_job_ids, checks))
        with st.expander("Open today's list"):
            st.dataframe(rows, hide_index=True)
        if status == "signed":
            st.caption(f"Batch v{frozen.version} is signed; a change opens a new version.")
        signer = st.text_input("Signer", key="sign_off_signer")
        signer_error = st.empty()
        decision = st.selectbox("Decision", list(DECISIONS), key="sign_off_decision")
        reason = st.text_area("Reason for today's weighting", key="sign_off_reason")
        reason_error = st.empty()
        st.caption(f"Date {frozen.day} (dataset day; recorded time is the wall clock)")
        submitted = st.form_submit_button(
            "Sign today's list", type="primary", key="sign_off_submit"
        )
    if not submitted:
        return
    if not signer.strip():
        signer_error.markdown(f":red[{SIGNER_REQUIRED}]")
    if not reason.strip():
        reason_error.markdown(f":red[{REASON_REQUIRED}]")
    if signer.strip() and reason.strip():
        on_submit(signer.strip(), DECISIONS[decision], reason.strip())
