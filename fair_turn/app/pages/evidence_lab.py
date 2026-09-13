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
from fair_turn.core import audit, constants, feedback_sim
from fair_turn.core.capacity_sim import Closure, Site
from fair_turn.core.types import FaultType, HealthRiskFactor, Job, SafetyClass
from fair_turn.data import artefacts

FALLBACK_EXTRACTOR_CAPTION = "Build extractor: Claude Sonnet via claude -p (Part 2)."

# --- Tab 1: extraction quality -----------------------------------------------------------


def _load_json(path) -> dict | list:
    return json.loads(path.read_text("utf-8"))


def _cell(stats: dict, key: str) -> str:
    low, high = stats[f"{key}_ci"]
    return f"{stats[key]:.3f} [{low:.3f}, {high:.3f}]"


def field_table(ev: dict, field: str) -> pd.DataFrame:
    extractor = ev["extractor"][field]
    baseline = ev["baseline"].get(field)
    rows = []
    for label, stats in extractor["per_class"].items():
        row = {
            "class": label,
            "extractor precision": _cell(stats, "precision"),
            "extractor recall": _cell(stats, "recall"),
            "extractor f1": f"{stats['f1']:.3f}",
        }
        if baseline is not None:
            b = baseline["per_class"][label]
            row["baseline precision"] = _cell(b, "precision")
            row["baseline recall"] = _cell(b, "recall")
            row["baseline f1"] = f"{b['f1']:.3f}"
        rows.append(row)
    macro = {
        "class": "macro",
        "extractor precision": f"{extractor['macro_precision']:.3f}",
        "extractor recall": f"{extractor['macro_recall']:.3f}",
        "extractor f1": f"{extractor['macro_f1']:.3f}",
    }
    if baseline is not None:
        macro["baseline precision"] = f"{baseline['macro_precision']:.3f}"
        macro["baseline recall"] = f"{baseline['macro_recall']:.3f}"
        macro["baseline f1"] = f"{baseline['macro_f1']:.3f}"
    rows.append(macro)
    return pd.DataFrame(rows)


def render_extraction_tab() -> None:
    ev = _load_json(artefacts.BUILD_DIR / "eval.json")
    extraction_rows = _load_json(artefacts.BUILD_DIR / "extraction.json")
    st.caption(FALLBACK_EXTRACTOR_CAPTION)
    for field in ("fault_type", "safety_class", "health_risk"):
        st.subheader(field.replace("_", " "))
        st.dataframe(field_table(ev, field), hide_index=True)

    adversarial = [r for r in extraction_rows if r["is_adversarial"]]
    with_markers = sum(1 for r in adversarial if r["injection_markers"])
    substring = ev["substring_rate"]
    st.write(
        f"Adversarial subset: {len(adversarial)} items, {with_markers} carrying an injection "
        "marker in their evidence."
    )
    st.write(f"Substring verification rate: {_cell(substring, 'rate')} of {substring['n']} rows.")
    target = ", ".join(f"{f} {'met' if ok else 'not met'}" for f, ok in ev["target_met"].items())
    st.caption(f"Macro-F1 target {ev['f1_target']:.2f}: {target}.")


# --- Tab 2: feedback loop (Task-19 page body, moved) --------------------------------------

DEFAULT_LAM = 0.5
EFFICIENCY_LAM = 1.0
DEFAULT_DECAY = 0.3
CITATIONS = "Ensign et al. 2018, D'Amour et al. 2020 and Kontokosta & Hong"
DECAY_CAPTION = (
    "Decay rate is our assumption; no published estimate exists for NT housing reporting."
)
CITATION_SENTENCE = f"The mechanism follows {CITATIONS} on under-reporting."


def simulation_inputs(art: artefacts.Artefacts) -> tuple[list[Job], dict[str, Site], list[Closure]]:
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


def render_feedback_tab() -> None:
    st.write(
        "Where reports go unserved, people stop reporting. Compare efficiency-only allocation "
        "with the page's own default λ, drawn on first render: under efficiency only, remote "
        "demand looks like it dried up."
    )
    lam = st.slider(
        "λ (0 = equity first, 1 = efficiency first)",
        0.0,
        1.0,
        DEFAULT_LAM,
        0.05,
        key="evidence_lab_feedback_lam",
    )
    decay = st.slider(
        "Reporting decay when reports go unserved",
        0.0,
        1.0,
        DEFAULT_DECAY,
        0.05,
        key="evidence_lab_feedback_decay",
    )
    st.caption(DECAY_CAPTION)

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


def render_audit_tab() -> None:
    sample_path = artefacts.AUDIT_DIR / "sample.jsonl"
    records = audit.read(state.get_audit_path()) + audit.read(sample_path)
    if not records:
        st.info("No rows match the filters.")
        return

    rows = sorted(
        audit.export_rows(records),
        key=lambda r: datetime.fromisoformat(r["recorded_at"]),
        reverse=True,
    )
    signers = sorted({r["signer"] or NO_SIGNER for r in rows})
    kinds = sorted({r["kind"] for r in rows})
    days = sorted({date.fromisoformat(r["decision_day"]) for r in rows})
    min_day, max_day = days[0], days[-1]

    signer_filter = st.multiselect("Signer", signers, default=signers)
    kind_filter = st.multiselect("Kind", kinds, default=kinds)
    day_range = st.date_input(
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

    st.caption(
        f"Filters: kind {', '.join(kind_filter) or NO_SIGNER}; "
        f"signer {', '.join(signer_filter) or NO_SIGNER}; "
        f"decision day {start.isoformat()} to {end.isoformat()}."
    )
    st.caption(LOCAL_ZONE_CAPTION)

    if frame.empty:
        st.info("No rows match the filters.")
    else:
        st.dataframe(
            frame,
            hide_index=True,
            column_config={
                # Streamlit has no monospace column type; TextColumn is the closest fit,
                # a known gap (Part 2 "Deviations").
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
        st.altair_chart(chart, width="stretch")


state.artefacts()
st.title("Evidence lab")
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
