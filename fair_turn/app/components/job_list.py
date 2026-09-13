"""Selectable ranked-job table for the workspace (PRD 3.1)."""

import pandas as pd
import streamlit as st


def selected_job_id(frame: pd.DataFrame, rows: list[int]) -> str | None:
    """Map the first selected row position back to the rendered job id."""
    if frame.empty or not rows:
        return None
    position = rows[0]
    if position < 0 or position >= len(frame):
        return None
    return str(frame.iloc[position]["job_id"])


def render(frame: pd.DataFrame, selected_id: str | None) -> str | None:
    """Render a selectable table.

    Streamlit dataframes cannot preselect a row, so the selected id is displayed in a
    caption rather than applied to the dataframe.
    """
    if selected_id is not None:
        st.caption(f"Selected: {selected_id}")
    event = st.dataframe(
        frame,
        on_select="rerun",
        selection_mode="single-row",
        hide_index=True,
        key="job_list",
        width="stretch",
    )
    return selected_job_id(frame, event.selection.rows)
