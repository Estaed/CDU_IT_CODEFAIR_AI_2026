"""PRD 3.5 Feedback-loop simulation: the 90-day replay at λ = 1.0 against a chosen λ, with
reporting that decays where reports went unserved. Simulated on the label rows (ground
truth), behind a Run button and cached by (λ, decay)."""

from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

from fair_turn.app import state, theme
from fair_turn.core import constants, feedback_sim
from fair_turn.core.capacity_sim import Closure, Site
from fair_turn.core.types import FaultType, HealthRiskFactor, Job, SafetyClass
from fair_turn.data.artefacts import Artefacts

EFFICIENCY_LAM = 1.0
DEFAULT_DECAY = 0.3
CITATIONS = "Ensign et al. 2018, D'Amour et al. 2020 and Kontokosta & Hong"
DECAY_CAPTION = (
    "Decay rate is our assumption; no published estimate exists for NT housing reporting."
)
CITATION_SENTENCE = f"The mechanism follows {CITATIONS} on under-reporting."


def simulation_inputs(art: Artefacts) -> tuple[list[Job], dict[str, Site], list[Closure]]:
    """Jobs from the label rows, a site per community and the closures."""
    rows = art.communities
    sites = {cid: Site(r["region"], float(r["km_to_base"])) for cid, r in rows.items()}
    jobs = [
        Job(
            job_id=label["job_id"],
            community_id=label["community_id"],
            is_remote=rows[label["community_id"]]["is_remote"] == "True",
            reported_on=date.fromisoformat(label["reported_on"]),
            fault_type=FaultType(label["fault_type"]),
            safety_class=SafetyClass(label["safety_class"]),
            health_risk=frozenset(HealthRiskFactor(h) for h in label["health_risk"]),
            logistics_factor=float(rows[label["community_id"]]["logistics_factor"]),
        )
        for label in art.labels
    ]
    closures = [
        Closure(
            c["community_id"],
            date.fromisoformat(c["closed_from"]),
            date.fromisoformat(c["closed_to"]),
        )
        for c in art.closures
    ]
    return jobs, sites, closures


@st.cache_data(show_spinner="Replaying 90 days")
def weekly_series(lam: float, decay: float) -> feedback_sim.WeeklySeries:
    jobs, sites, closures = simulation_inputs(state.artefacts())
    return feedback_sim.run(jobs, sites, lam, decay, constants.SEED, closures)


def run_label(lam: float) -> str:
    return "Efficiency only (λ = 1.0)" if lam == EFFICIENCY_LAM else f"Chosen (λ = {lam:g})"


def chart_rows(runs: dict[str, feedback_sim.WeeklySeries]) -> dict[str, pd.DataFrame]:
    """Long-form rows per chart; a week with no median is dropped, not plotted as 0."""
    reports, waits, gaps = [], [], []
    for run, s in runs.items():
        for i, week in enumerate(s.week_start):
            base = {"week": week.isoformat(), "run": run}
            reports.append({**base, "locality": "town", "value": s.reports_town[i]})
            reports.append({**base, "locality": "remote", "value": s.reports_remote[i]})
            for locality, value in (
                ("town", s.median_wait_town[i]),
                ("remote", s.median_wait_remote[i]),
            ):
                if value is not None:
                    waits.append({**base, "locality": locality, "value": value})
            if s.gap[i] is not None:
                gaps.append({**base, "value": s.gap[i]})
    return {
        "reports": pd.DataFrame(reports),
        "wait": pd.DataFrame(waits),
        "gap": pd.DataFrame(gaps),
    }


def line_chart(rows: pd.DataFrame, title: str, y_title: str, runs: list[str]) -> alt.Chart:
    run_dash = alt.StrokeDash("run:N", scale=alt.Scale(domain=runs), title="Run")
    base = alt.Chart(rows, title=title).encode(
        x=alt.X("week:T", title="Week reported"),
        y=alt.Y("value:Q", title=y_title),
        strokeDash=run_dash,
    )
    if "locality" in rows.columns:
        colour = alt.Color(
            "locality:N",
            scale=alt.Scale(domain=["town", "remote"], range=[theme.TOWN, theme.REMOTE]),
            title="Locality",
        )
        layers = [
            base.transform_filter(alt.datum.run == run)
            .mark_line(point=True, strokeWidth=theme.STROKE_WIDTH)
            .encode(color=colour, detail="locality:N")
            for run in runs
        ]
    else:
        layers = [
            base.transform_filter(alt.datum.run == run).mark_line(
                point=True, strokeWidth=theme.STROKE_WIDTH, color=theme.REMOTE
            )
            for run in runs
        ]
    return (
        alt.layer(*layers)
        .configure_axis(
            gridColor=theme.GRIDLINE, labelColor=theme.AXIS_LABEL, titleColor=theme.AXIS_LABEL
        )
        .configure_title(color=theme.AXIS_LABEL)
    )


state.artefacts()
st.title("Feedback loop")
st.caption(theme.PROVENANCE_LINE)
st.write(
    "Where reports go unserved, people stop reporting. Compare efficiency-only allocation "
    "with a chosen λ: under efficiency only, remote demand looks like it dried up."
)

lam = st.slider("λ (0 = equity first, 1 = efficiency first)", 0.0, 1.0, state.get_lam(), 0.05)
state.set_lam(lam)
decay = st.slider("Reporting decay when reports go unserved", 0.0, 1.0, DEFAULT_DECAY, 0.05)
st.caption(DECAY_CAPTION)

if st.button("Run"):
    runs = {run_label(EFFICIENCY_LAM): weekly_series(EFFICIENCY_LAM, decay)}
    runs[run_label(lam)] = weekly_series(lam, decay)
    order = list(runs)
    rows = chart_rows(runs)
    st.altair_chart(
        line_chart(rows["reports"], "Reports per week", "Reports", order), width="stretch"
    )
    st.altair_chart(
        line_chart(rows["wait"], "Median wait by week reported", "Days", order), width="stretch"
    )
    st.altair_chart(
        line_chart(rows["gap"], "Gap: remote minus town median wait", "Days", order),
        width="stretch",
    )
    st.caption(CITATION_SENTENCE)
