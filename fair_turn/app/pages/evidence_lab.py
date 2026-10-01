"""PRD 3.5 Evidence lab: extraction quality, the feedback-loop simulation and the audit
log with its two clocks, in three tabs for judges and governance, outside the coordinator's
flow (wireframes §8).

Build artefacts are read through the ``artefacts`` module's directory constants rather than a
literal path, per the loader-only rule enforced in ``tests/test_app_smoke.py``.
"""

import json
from datetime import date, datetime

import altair as alt
import pandas as pd
import streamlit as st

from fair_turn.app import state, theme
from fair_turn.app.components import intro
from fair_turn.core import audit, constants, feedback_sim
from fair_turn.core.capacity_sim import Closure, CrewBase, Site
from fair_turn.core.types import FaultType, HealthRiskFactor, Job, SafetyClass
from fair_turn.data import artefacts, geography

FALLBACK_EXTRACTOR_CAPTION = "Build extractor: Claude Sonnet via claude -p (Blueprint)."
NO_RECORDS_MESSAGE = (
    "No decisions logged yet. Rows appear here once a report is signed, a visit plan is "
    "accepted or rejected, or a coordinator makes an override."
)

# --- Tab 1: extraction quality -----------------------------------------------------------


def _load_json(path) -> dict | list:
    return json.loads(path.read_text("utf-8"))


def _ci_span(stats: dict, key: str) -> str:
    low, high = stats[f"{key}_ci"]
    return f"{low:.0%}–{high:.0%}"


NUMBER_COLUMNS = [
    "Extractor Precision",
    "Extractor Recall",
    "Extractor F1",
    "Baseline Precision",
    "Baseline Recall",
    "Baseline F1",
]


def field_table(ev: dict, field: str) -> pd.DataFrame:
    extractor = ev["extractor"][field]
    baseline = ev["baseline"].get(field)
    rows = []
    for label, stats in extractor["per_class"].items():
        row = {
            "class": label,
            "Extractor Precision": stats["precision"] * 100,
            "Extractor Precision 95 % CI": _ci_span(stats, "precision"),
            "Extractor Recall": stats["recall"] * 100,
            "Extractor Recall 95 % CI": _ci_span(stats, "recall"),
            "Extractor F1": stats["f1"] * 100,
        }
        if baseline is not None:
            b = baseline["per_class"][label]
            row["Baseline Precision"] = b["precision"] * 100
            row["Baseline Precision 95 % CI"] = _ci_span(b, "precision")
            row["Baseline Recall"] = b["recall"] * 100
            row["Baseline Recall 95 % CI"] = _ci_span(b, "recall")
            row["Baseline F1"] = b["f1"] * 100
        rows.append(row)
    macro = {
        "class": "macro",
        "Extractor Precision": extractor["macro_precision"] * 100,
        "Extractor Precision 95 % CI": "",
        "Extractor Recall": extractor["macro_recall"] * 100,
        "Extractor Recall 95 % CI": "",
        "Extractor F1": extractor["macro_f1"] * 100,
    }
    if baseline is not None:
        macro["Baseline Precision"] = baseline["macro_precision"] * 100
        macro["Baseline Precision 95 % CI"] = ""
        macro["Baseline Recall"] = baseline["macro_recall"] * 100
        macro["Baseline Recall 95 % CI"] = ""
        macro["Baseline F1"] = baseline["macro_f1"] * 100
    rows.append(macro)
    return pd.DataFrame(rows)


def macro_f1_chart(ev: dict, fields: tuple[str, ...]) -> alt.Chart:
    """Macro-F1 per field, extractor vs baseline, grouped bars."""
    rows = []
    labels = {
        "fault_type": "Fault type",
        "safety_class": "Safety class",
        "health_risk": "Health risk",
    }
    for field in fields:
        extractor = ev["extractor"][field]
        rows.append(
            {"field": labels[field], "model": "Extractor", "macro_f1": extractor["macro_f1"]}
        )
        baseline = ev["baseline"].get(field)
        if baseline is not None:
            rows.append(
                {"field": labels[field], "model": "Baseline", "macro_f1": baseline["macro_f1"]}
            )
    data = pd.DataFrame(rows)
    colour = alt.Color(
        "model:N",
        scale=alt.Scale(domain=["Extractor", "Baseline"], range=[theme.TOWN, theme.REMOTE]),
        title="Model",
    )
    return (
        alt.Chart(data, title="Read correctly, by field")
        .mark_bar()
        .encode(
            x=alt.X("model:N", title=None, axis=None),
            y=alt.Y("macro_f1:Q", title="Read correctly", axis=alt.Axis(format="%")),
            color=colour,
            column=alt.Column("field:N", title=None),
        )
        .configure_axis(
            gridColor=theme.GRIDLINE, labelColor=theme.AXIS_LABEL, titleColor=theme.AXIS_LABEL
        )
        .configure_title(color=theme.AXIS_LABEL)
    )


def render_extraction_tab() -> None:
    eval_path = artefacts.BUILD_DIR / "eval.json"
    ev = _load_json(eval_path)
    extraction_rows = _load_json(artefacts.BUILD_DIR / "extraction.json")
    substring = ev["substring_rate"]
    adversarial = [r for r in extraction_rows if r["is_adversarial"]]
    interval = f"{substring['rate_ci'][0]:.1%} to {substring['rate_ci'][1]:.1%}"
    st.write(
        "The percent of reports read correctly out of 150 held-out synthetic reports, "
        "compared with a bag-of-words baseline. Higher is better."
    )
    st.caption(
        "Share of the 150 held-out reports read correctly; the attack count is the 20 "
        "adversarial reports that left the ranking unchanged."
    )
    metrics = st.columns(5)
    metrics[0].metric(
        "Phrases verified",
        f"{substring['rate']:.1%}",
        border=True,
        help=(
            "How often a claim the AI made could be checked word-for-word against the "
            f"tenant's own report. Wilson interval: {interval}."
        ),
    )
    metrics[1].metric(
        "Attacks resisted",
        f"{len(adversarial)} of {len(adversarial)}",
        border=True,
        help=(
            '"Attacks" are reports written on purpose to trick the system into a wrong '
            "answer. Every one of them still leaves the ranking unchanged; the gate asserts "
            "this on the committed artefact (tests/test_extraction_artefact.py), so the "
            "count is the size of the adversarial set."
        ),
    )
    field_help = (
        'Macro-F1 across classes on the 150-item held-out set. "Baseline" is a simple '
        "bag-of-words classifier used only for comparison, not the AI extractor this "
        "product uses."
    )
    for column, field, label in zip(
        metrics[2:],
        ("fault_type", "safety_class", "health_risk"),
        (
            "Fault type",
            "Safety class",
            "Health risk",
        ),
        strict=True,
    ):
        extractor = ev["extractor"][field]
        baseline = ev["baseline"].get(field)
        delta = None if baseline is None else extractor["macro_f1"] - baseline["macro_f1"]
        match_key = "accuracy" if "accuracy_ci" in extractor else "exact_set_match"
        interval = _ci_span(extractor, match_key)
        column.metric(
            label,
            f"{extractor['macro_f1']:.0%}",
            delta=None if delta is None else f"{delta * 100:+.0f} pts",
            delta_color="normal",
            border=True,
            help=f"{field_help} The 95 % interval on {match_key.replace('_', ' ')} is {interval}.",
        )
    artefact_date = datetime.fromtimestamp(eval_path.stat().st_mtime).date().isoformat()
    st.caption(
        f"{FALLBACK_EXTRACTOR_CAPTION} Holdout: {ev['n_holdout']} items. "
        f"Evaluation artefact date: {artefact_date}."
    )
    st.caption(
        f"Target: {ev['f1_target']:.0%} on fault type and on safety class. Fault type: "
        f"{'met' if ev['target_met']['fault_type'] else 'not met'}; safety class: "
        f"{'met' if ev['target_met']['safety_class'] else 'not met'} "
        "(the model over-predicts immediate)."
    )
    st.altair_chart(
        macro_f1_chart(ev, ("fault_type", "safety_class", "health_risk")), width="stretch"
    )
    number_config = {
        column: st.column_config.NumberColumn(format="%.0f%%") for column in NUMBER_COLUMNS
    }
    field_labels = {
        "fault_type": "Fault type, by class",
        "safety_class": "Safety class, by class",
        "health_risk": "Health risk, by class",
    }
    for field, expander_label in field_labels.items():
        with st.expander(expander_label):
            st.dataframe(field_table(ev, field), hide_index=True, column_config=number_config)


# --- Tab 2: feedback loop (Task-19 page body, moved) --------------------------------------

DEFAULT_LAM = 0.5
EFFICIENCY_LAM = 1.0
DEFAULT_DECAY = 0.3
CITATIONS = "Ensign et al. 2018, D'Amour et al. 2020 and Kontokosta & Hong"
DECAY_CAPTION = (
    "Decay rate is our assumption; no published estimate exists for NT housing reporting."
)
CITATION_SENTENCE = f"The mechanism follows {CITATIONS} on under-reporting."


def simulation_inputs(
    art: artefacts.Artefacts,
) -> tuple[list[Job], dict[str, Site], tuple[CrewBase, ...], list[Closure]]:
    """Jobs from the label rows, a site per community, the NT-wide crew pool and the closures."""
    rows = art.communities
    sites = geography.sim_sites(rows)
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
    return jobs, sites, geography.crews(rows), closures


@st.cache_data(show_spinner="Replaying 90 days")
def weekly_series(lam: float, decay: float) -> feedback_sim.WeeklySeries:
    jobs, sites, crews, closures = simulation_inputs(state.artefacts())
    return feedback_sim.run(jobs, sites, crews, lam, decay, constants.SEED, closures)


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


def window_share_chart(rows: pd.DataFrame, runs: list[str]) -> alt.Chart:
    return (
        alt.Chart(rows, title="Share of reports made that were completed within their NT window")
        .mark_bar()
        .encode(
            x=alt.X("run:N", sort=runs, title="Run"),
            xOffset=alt.XOffset("locality:N"),
            y=alt.Y("value:Q", title="Share", axis=alt.Axis(format=".0%")),
            color=alt.Color(
                "locality:N",
                scale=alt.Scale(domain=["town", "remote"], range=[theme.TOWN, theme.REMOTE]),
                title="Locality",
            ),
        )
        .configure_axis(
            gridColor=theme.GRIDLINE, labelColor=theme.AXIS_LABEL, titleColor=theme.AXIS_LABEL
        )
        .configure_title(color=theme.AXIS_LABEL)
    )


def render_feedback_tab() -> None:
    st.write(
        "Replays the 90-day set twice, once efficiency-first and once at the chosen weighting. "
        "Moving towards equity serves more remote reports within their NT window and leaves fewer "
        "never served; the price is paid in town waits and kilometres. Crew capacity caps how far "
        "any weighting can go: a second crew per remote region does more than any setting."
    )
    st.write(
        "Reporting fades wherever reports go unserved, under both runs. The decay rate is a "
        "labelled assumption on the slider, not a measured one."
    )
    lam = st.slider(
        "λ (0 = equity first, 1 = efficiency first)",
        0.0,
        1.0,
        DEFAULT_LAM,
        0.05,
        key="evidence_lab_feedback_lam",
        help="How much travel cost is subtracted from need when ordering jobs: 0 ignores travel, "
        "1 subtracts it at full weight. Need (urgency, safety, household health risk) always "
        "counts.",
    )
    decay = st.slider(
        "Reporting decay when reports go unserved",
        0.0,
        1.0,
        DEFAULT_DECAY,
        0.05,
        key="evidence_lab_feedback_decay",
        help="How much less often a community reports a repair after being left "
        "unserved: 0 means reporting never drops, 1 means it stops almost at once.",
    )
    st.caption(DECAY_CAPTION)

    runs = {run_label(EFFICIENCY_LAM): weekly_series(EFFICIENCY_LAM, decay)}
    runs[run_label(lam)] = weekly_series(lam, decay)
    order = list(runs)
    rows = chart_rows(runs)
    jobs, *_ = simulation_inputs(state.artefacts())
    window_rows = []
    for run, series in runs.items():
        remote, town = feedback_sim.served_within_window(series.sim, jobs)
        for locality, value in (("town", town), ("remote", remote)):
            if value is not None:
                window_rows.append({"run": run, "locality": locality, "value": value})
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
    st.altair_chart(window_share_chart(pd.DataFrame(window_rows), order), width="stretch")
    st.caption(CITATION_SENTENCE)


# --- Tab 3: audit log -----------------------------------------------------------------------

AUDIT_COLUMNS = [
    "kind",
    "decision_day",
    "recorded_at",
    "audit_ref",
    "job_id",
    "previous_weighting",
    "new_weighting",
    "reason",
    "signer",
    "detail",
    "hash",
]
LOCAL_ZONE_CAPTION = (
    "Times are shown in the local zone of the machine that recorded them (ISO 8601 with offset)."
)
NO_SIGNER = "(none)"
KIND_LABELS = {
    "sign_off": "List signed",
    "revision": "Weighting revised",
    "override": "Rank changed by coordinator",
    "human_set": "Field set by coordinator",
    "intake": "Report received",
    "promotion": "Job promoted",
    "plan_decision": "Visit plan decision",
    "field_check": "Field checked",
    "job_decision": "Job decision",
    "make_safe": "Sent to make-safe contractor",
}


def render_audit_tab() -> None:
    sample_path = artefacts.AUDIT_DIR / "sample.jsonl"
    records = audit.read(state.get_audit_path()) + audit.read(sample_path)
    if not records:
        st.info(NO_RECORDS_MESSAGE)
        return

    rows = sorted(
        audit.export_rows(records),
        key=lambda r: datetime.fromisoformat(r["recorded_at"]),
        reverse=True,
    )
    signers = sorted({r["signer"] or NO_SIGNER for r in rows})
    kinds = sorted({r["kind"] for r in rows})
    kind_options = {KIND_LABELS[kind]: kind for kind in kinds}
    days = sorted({date.fromisoformat(r["decision_day"]) for r in rows})
    min_day, max_day = days[0], days[-1]

    rate = audit.override_rate(records)
    if rate:
        rate_df = pd.DataFrame(rate, columns=["day", "override_rate"])
        chart = (
            alt.Chart(rate_df, title="Override rate by decision day")
            .mark_line(color=theme.HUMAN_QUEUE, strokeWidth=theme.STROKE_WIDTH)
            .encode(
                x=alt.X("day:T", title="Decision day"),
                y=alt.Y("override_rate:Q", title="Override rate"),
            )
            .configure_axis(
                gridColor=theme.GRIDLINE, labelColor=theme.AXIS_LABEL, titleColor=theme.AXIS_LABEL
            )
            .configure_title(color=theme.AXIS_LABEL)
        )
        with st.expander("Override rate by decision day", expanded=False):
            st.altair_chart(chart, width="stretch")

    filter_columns = st.columns(3)
    signer_filter = filter_columns[0].multiselect("Signer", signers, default=signers)
    kind_labels = list(kind_options)
    kind_filter_labels = filter_columns[1].multiselect("Kind", kind_labels, default=kind_labels)
    kind_filter = [kind_options[label] for label in kind_filter_labels]
    day_range = filter_columns[2].date_input(
        "Decision day range", value=(min_day, max_day), min_value=min_day, max_value=max_day
    )
    start, end = (
        day_range
        if isinstance(day_range, tuple) and len(day_range) == 2
        else (
            day_range,
            day_range,
        )
    )

    filtered = [
        r
        for r in rows
        if (r["signer"] or NO_SIGNER) in signer_filter
        and r["kind"] in kind_filter
        and start <= date.fromisoformat(r["decision_day"]) <= end
    ]
    frame = pd.DataFrame(filtered, columns=AUDIT_COLUMNS)
    display_frame = frame.assign(kind=frame["kind"].map(KIND_LABELS))

    st.caption(
        f"Showing {len(filtered)} of {len(rows)} rows · kind "
        f"{', '.join(kind_filter_labels) or NO_SIGNER}; "
        f"signer {', '.join(signer_filter) or NO_SIGNER}; "
        f"decision day {start.isoformat()} to {end.isoformat()}."
    )
    st.caption(LOCAL_ZONE_CAPTION)
    st.caption(
        '"Decision day" is the day inside the dataset the decision belongs to; '
        '"recorded at" is the real clock time it was logged. They are not always '
        "the same day."
    )

    if frame.empty:
        st.info("No rows match the filters.")
    else:
        st.dataframe(
            display_frame,
            hide_index=True,
            column_config={
                # Streamlit has no monospace column type; TextColumn is the closest fit,
                # a known gap (Blueprint "Deviations").
                "recorded_at": st.column_config.TextColumn("Recorded at"),
                "audit_ref": st.column_config.TextColumn("Audit ref"),
                "job_id": st.column_config.TextColumn("Job id"),
                "hash": st.column_config.TextColumn("Hash"),
            },
        )
    st.download_button(
        "Download CSV",
        frame.to_csv(index=False),
        file_name="audit_log.csv",
        mime="text/csv",
    )


state.artefacts()
st.title("Evidence lab")
intro.purpose("evidence_lab")
st.markdown(
    "This page is for checking the system, not for daily work.\n\n"
    "**What to do here**\n\n"
    "1. Extraction quality: how often the AI read a report correctly.\n"
    "2. Feedback loop: what the weighting costs, and what it cannot buy without crews.\n"
    "3. Audit log: every decision, who made it and when."
)
st.caption(theme.PROVENANCE_LINE)

extraction_tab, feedback_tab, audit_tab = st.tabs(
    ["Extraction quality", "Feedback loop", "Audit log"]
)
with extraction_tab:
    render_extraction_tab()
with feedback_tab:
    render_feedback_tab()
with audit_tab:
    render_audit_tab()
intro.about()
