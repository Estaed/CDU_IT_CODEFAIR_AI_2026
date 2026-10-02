"""Evidence, for judges and governance: what each setting does over a season, how well the
AI reads reports, and the decision log."""

import json

import altair as alt
import pandas as pd
import streamlit as st

from fair_turn.app import state, theme
from fair_turn.core import audit, constants, weeks
from fair_turn.data import artefacts
from fair_turn.eval import metrics as eval_metrics

SEASON_WEEKS = weeks.SEASON_WEEKS  # every Monday of the synthetic window


@st.cache_resource(show_spinner="Planning 13 weeks under each setting")
def season(setting: float, extra_crew_at: str | None = None) -> weeks.SeasonResult:
    art = state.artefacts()
    jobs = artefacts.to_jobs(art)
    crews = dict(constants.CREWS_AT_BASE)
    if extra_crew_at:
        crews[extra_crew_at] += 1
    run = weeks.simulate(
        jobs, state.places(), setting, state.FIRST_MONDAY, SEASON_WEEKS, art.closures, crews
    )
    return weeks.measure(run, jobs, state.places(), setting)


def season_frame() -> pd.DataFrame:
    rows = []
    for name, value in constants.SETTINGS.items():
        result = season(value)
        far = result.bands[-1]
        rows.append(
            {
                "Setting": name,
                "Repairs done": result.repairs,
                "Town on time": 100 * result.on_time_town,
                "Remote on time": 100 * result.on_time_remote,
                f"Still waiting after {SEASON_WEEKS} weeks, over 300 km": far.still_open,
                "Crew-days driving": result.driving_days,
            }
        )
    return pd.DataFrame(rows)


def band_frame() -> pd.DataFrame:
    rows = []
    for name, value in constants.SETTINGS.items():
        for band in season(value).bands:
            rows.append(
                {
                    "Setting": name,
                    "Distance from a crew base": band.band,
                    "Still waiting": band.still_open,
                    "Done on time": band.on_time_share,
                    "Repairs": band.jobs,
                }
            )
    return pd.DataFrame(rows)


def band_chart(frame: pd.DataFrame, field: str, title: str, fmt: str) -> alt.Chart:
    order = [name for name, _ in weeks.BANDS]
    colour = alt.Color(
        "Setting:N",
        scale=alt.Scale(
            domain=list(theme.SETTING_COLOURS), range=list(theme.SETTING_COLOURS.values())
        ),
        legend=alt.Legend(orient="bottom", title=None),
    )
    return theme.chart(
        alt.Chart(frame, title=title)
        .mark_bar()
        .encode(
            x=alt.X(
                "Distance from a crew base:N", sort=order, title=None, axis=alt.Axis(labelAngle=0)
            ),
            xOffset=alt.XOffset("Setting:N", sort=list(constants.SETTINGS)),
            y=alt.Y(f"{field}:Q", title=None, axis=alt.Axis(format=fmt)),
            color=colour,
            tooltip=["Setting", "Distance from a crew base", alt.Tooltip(field, format=fmt)],
        )
        .properties(height=280)
    )


def render_season() -> None:
    st.write(
        f"The same {SEASON_WEEKS} weeks of synthetic reports (October to December 2025), "
        "planned every Monday under each setting, with the same crews and the same road "
        "closures. Town days take new reports as they come in; remote trips leave on Monday."
    )
    frame = season_frame()
    efficiency, balanced, need = (season(v) for v in constants.SETTINGS.values())
    far = [r.bands[-1].still_open for r in (efficiency, balanced, need)]
    st.info(
        f"**Efficiency first leaves {far[0]} repairs over 300 km from a base still waiting after "
        f"{SEASON_WEEKS} weeks. Balanced leaves {far[1]}, and does "
        f"{balanced.repairs - efficiency.repairs:+d} repairs in total.** Its cost: remote "
        f"repairs on time go from {efficiency.on_time_remote:.0%} to "
        f"{balanced.on_time_remote:.0%}, because crew time goes to households already longest "
        f"past the limit. Most overdue first leaves {far[2]}, and town repairs on time fall from "
        f"{efficiency.on_time_town:.0%} to {need.on_time_town:.0%}. Neither end is the fair "
        "answer; the choice in between is the coordinator's."
    )
    st.caption(
        "Why this differs from the plan page: in a single week, Balanced fixes fewer repairs "
        "than Efficiency first because its trips drive further. Over a season the order "
        "matters more: under Efficiency first every repair counts the same, so the oldest goes "
        "first whatever its class, and the farthest places pile up; Balanced ends the season "
        "ahead. Most "
        "overdue first is on time least often, remote included: it keeps sending crews to "
        "repairs that are already late, while newer ones pass their limit."
    )
    left, right = st.columns(2)
    data = band_frame()
    left.altair_chart(
        band_chart(data, "Still waiting", f"Still waiting after {SEASON_WEEKS} weeks", "d"),
        width="stretch",
    )
    right.altair_chart(
        band_chart(data, "Done on time", "Done within the NT time limit", ".0%"),
        width="stretch",
    )
    st.dataframe(
        frame,
        hide_index=True,
        width="stretch",
        column_config={
            "Town on time": st.column_config.NumberColumn(format="%.0f%%"),
            "Remote on time": st.column_config.NumberColumn(format="%.0f%%"),
            "Crew-days driving": st.column_config.NumberColumn(format="%g"),
        },
    )

    st.markdown("**The setting decides who waits. One more crew is the other lever:**")
    rows = []
    for base in constants.CREW_BASES:
        result = season(constants.SETTINGS["Balanced"], base)
        rows.append(
            {
                "One more crew at": base,
                "Repairs done": result.repairs,
                "Remote on time": 100 * result.on_time_remote,
                f"Still waiting over 300 km (Balanced alone: {far[1]})": result.bands[
                    -1
                ].still_open,
            }
        )
    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        width="stretch",
        column_config={"Remote on time": st.column_config.NumberColumn(format="%.0f%%")},
    )
    st.caption(
        "Crew numbers, repairs per crew-day and driving speed are our assumptions "
        f"({sum(constants.CREWS_AT_BASE.values())} crews, {constants.JOBS_PER_CREW_DAY} "
        f"repairs a day, {constants.DRIVE_KM_PER_DAY} km of road a day): NT does not publish "
        "them. They are set in one file; the pattern above is what to test in a pilot, not a "
        "forecast."
    )
    with st.container(border=True):
        st.markdown("**What a pilot in one region would need**")
        st.markdown(
            "- **The trade roster:** crews per town and their working days, in place of our "
            "assumption.\n"
            "- **The contractor's job list:** an export from its tasking system in place of the "
            "synthetic reports; the plan reads typed fields only.\n"
            "- **Where the reading runs:** Claude through a government-approved account, or a "
            "local model on the agency's own machine (we measured one: urgency macro-F1 0.65 "
            "against Claude's 0.97, so it needs more work before it can replace it).\n"
            "- **One measure that does not exist today:** the time from a tenant's report to the "
            "finished repair, which the NT's evaluator found cannot be measured now "
            "(Menzies 2023)."
        )


def render_reading() -> None:
    ev = json.loads((artefacts.BUILD_DIR / "eval.json").read_text("utf-8"))
    rows = json.loads((artefacts.BUILD_DIR / "extraction.json").read_text("utf-8"))
    adversarial = [r for r in rows if r["is_adversarial"]]
    by_id = {r["job_id"]: r for r in rows}

    def unchanged(r: dict) -> bool:
        if r["needs_human"]:
            return True
        original = by_id[r["original_job_id"]]["kept"]
        return all(
            r["kept"].get(f, {}).get("value") == original.get(f, {}).get("value")
            for f in ("fault_type", "safety_class")
        )

    st.write(
        f"The AI (Claude Sonnet) read {ev['n_holdout']} held-out synthetic reports written by "
        "a different model (Claude Opus). Its reading is compared with the labels the reports "
        "were written from, and with a simple word-count classifier."
    )
    cols = st.columns(5)
    for col, field, label in zip(
        cols[:3],
        ("fault_type", "safety_class", "health_risk"),
        ("What is broken", "How urgent", "Household health risk"),
        strict=True,
    ):
        extractor = ev["extractor"][field]
        baseline = ev["baseline"].get(field)
        col.metric(
            label,
            f"{extractor['macro_f1']:.0%}",
            delta=None
            if baseline is None
            else f"{(extractor['macro_f1'] - baseline['macro_f1']) * 100:+.0f} pts vs word count",
            help="Macro-F1 on the held-out set.",
        )
    substring = ev["substring_rate"]
    cols[3].metric(
        "Facts tied to the tenant's words",
        f"{substring['rate']:.0%}",
        help="Every fact shown is a literal phrase of the report; one that is not is dropped.",
    )
    cols[4].metric(
        "Manipulation attempts that changed nothing",
        f"{sum(unchanged(r) for r in adversarial)} of {len(adversarial)}",
        help="Reports that try to instruct the AI ('ignore previous instructions', 'rank it "
        "first'). Each one either went to a person or kept the same reading.",
    )
    if challenge := ev.get("challenge"):
        st.caption(eval_metrics.challenge_sentence(challenge))
    st.caption(
        "Synthetic reports written to the NT definitions are cleaner than real tenants' words: "
        "treat these as upper bounds. A pilot measures the same numbers on real reports."
    )


def render_log() -> None:
    records = audit.read(state.get_audit_path())
    sample = audit.read(artefacts.AUDIT_DIR / "sample.jsonl")
    st.write(
        "Every signed plan, every change to the proposal and its reason, every fact a person "
        "set, and every report the AI read. Two clocks: the planning day in the data, and the "
        "real time the record was made."
    )
    shown = records or sample
    if not records:
        st.caption("Nothing signed on this machine yet; showing the committed sample log.")
    frame = pd.DataFrame(audit.export_rows(shown)).rename(
        columns={
            "what": "What",
            "planning_day": "Week planned (data)",
            "recorded_at": "Recorded at (real time)",
            "who": "Who",
            "reason": "Reason",
            "detail": "Detail",
            "hash": "Check code",
        }
    )
    st.dataframe(frame, hide_index=True, width="stretch")
    st.download_button(
        "Download the log (CSV)",
        frame.to_csv(index=False).encode("utf-8"),
        file_name="fair_turn_decision_log.csv",
        mime="text/csv",
    )


st.title("Evidence")
st.caption(theme.PROVENANCE_LINE)
tab_season, tab_reading, tab_log = st.tabs(
    [f"Who waits over {SEASON_WEEKS} weeks", "How well the AI reads", "Decision log"]
)
with tab_season:
    render_season()
with tab_reading:
    render_reading()
with tab_log:
    render_log()
