"""Today's list as one readable, openable row per job (PRD 3.1, wireframes §3).

Streamlit 1.63 has no row-click selection on ``st.dataframe`` and its checkbox column reads
as multi-select, so the short list a coordinator actually works through is a bordered row per
job with an explicit "Open" button. The backlog keeps the dataframe: hundreds of rows are for
scanning and filtering, not for reading.

``render`` is a pure widget function: it never touches session state and returns the job id
whose button was pressed, so the page owns the selection seam exactly as it did before.
"""

import streamlit as st

from fair_turn.app.components.ranking_table import UNCHANGED, community_label, short_id

# Row geometry: rank, job (fault type, id and community), class and window, score, the
# open button. Each cell holds at most two lines.
COLUMN_RATIOS = [0.7, 2.6, 1.6, 1.3, 1.5]
# Named Streamlit badge colours, the same map the details pane uses.
SAFETY_COLOURS = {"immediate": "red", "urgent": "orange", "routine": "gray"}
SELECTED = "Selected"
NEEDS_HUMAN = "Needs a human"
OPEN = "Open"
# A job's decision today -> (badge colour, icon, label); ``None`` is not decided yet.
DECISION_BADGES = {
    "accepted": ("green", ":material/check:", "Accepted"),
    None: ("gray", None, "Not decided"),
}


def render(rows: list[dict], selected_id: str | None, key: str) -> str | None:
    """Render one bordered row per job and return the id of the job whose button was pressed.

    Each ``rows`` item carries ``job_id, rank, rank_change, community_id, is_remote,
    fault_type, safety_class, window, score, score_max, human_queue, decision``
    (``decision`` is ``"accepted"`` or ``None``); the caller builds them
    from the ranking it already has, so nothing is scored here.
    """
    clicked = None
    for row in rows:
        job_id = row["job_id"]
        is_selected = job_id == selected_id
        with st.container(border=True):
            rank, job, urgency, score, action = st.columns(
                COLUMN_RATIOS, vertical_alignment="center"
            )
            with rank:
                st.markdown(f"**{row['rank']}**")
                if row["rank_change"] != UNCHANGED:
                    st.caption(row["rank_change"])
            with job:
                st.markdown(f"**{row['fault_type'].replace('_', ' ').capitalize()}**")
                locality = "Remote" if row["is_remote"] else "Town"
                st.caption(
                    f"Job {short_id(job_id)} · {community_label(row['community_id'])} · {locality}"
                )
            with urgency:
                with st.container(horizontal=True):
                    st.badge(
                        row["safety_class"].capitalize(),
                        color=SAFETY_COLOURS[row["safety_class"]],
                    )
                    if row["human_queue"]:
                        st.badge(NEEDS_HUMAN, color="yellow")
                st.caption(row["window"])
            with score:
                st.markdown(f"{row['score']:.1f}")
                st.progress(min(row["score"] / row["score_max"], 1.0))
            with action:
                if st.button(
                    OPEN,
                    key=f"{key}_open_{job_id}",
                    type="primary" if is_selected else "secondary",
                    width="stretch",
                ):
                    clicked = job_id
                with st.container(horizontal=True):
                    colour, icon, label = DECISION_BADGES[row["decision"]]
                    st.badge(label, icon=icon, color=colour)
                    if is_selected:
                        st.badge(SELECTED, color="orange")
    return clicked
