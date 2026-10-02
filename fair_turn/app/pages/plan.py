"""This week's crew plan: the coordinator's one decision, in three steps.

1. Choose what decides where crews go, and see what it costs.
2. Check the trips and who is left waiting; add or take out a trip, with a reason.
3. Sign. The signed plan, every change and its reason go to the decision log.
"""

import math

import altair as alt
import pandas as pd
import streamlit as st

from fair_turn.app import state, theme
from fair_turn.app.components import plan_map
from fair_turn.core import audit, constants, explain, scoring, weekly
from fair_turn.core.types import SafetyClass

FRONTIER_STEPS = 11  # settings 0.0, 0.1, ... 1.0 on the trade-off line


def _name(cid: str) -> str:
    return cid.title() if cid.isupper() else cid


def _count(n: int, one: str, many: str) -> str:
    return f"{n} {one if n == 1 else many}"


def _frontier(jobs) -> pd.DataFrame:
    rows = []
    for step in range(FRONTIER_STEPS):
        setting = step / (FRONTIER_STEPS - 1)
        summary = weekly.summarise(state.week_plan(jobs, setting, with_changes=False), jobs)
        name = weekly.setting_name(setting)
        rows.append(
            {
                "setting": setting,
                "name": name if name in constants.SETTINGS else "",
                "repairs": summary.repairs,
                "overdue_left": summary.overdue_left,
            }
        )
    return pd.DataFrame(rows)


def frontier_chart(frontier: pd.DataFrame, current: weekly.Summary) -> alt.Chart:
    axis_x = alt.X("repairs:Q", title="Repairs this week", scale=alt.Scale(zero=False))
    axis_y = alt.Y(
        "overdue_left:Q",
        title="Overdue repairs still waiting",
        scale=alt.Scale(zero=False),
    )
    line = (
        alt.Chart(frontier)
        .mark_line(color=theme.AXIS_LABEL, point=alt.OverlayMarkDef(color=theme.AXIS_LABEL))
        .encode(
            x=axis_x,
            y=axis_y,
            order="setting:Q",
            tooltip=[
                alt.Tooltip("setting:Q", title="Setting", format=".1f"),
                alt.Tooltip("repairs:Q", title="Repairs this week"),
                alt.Tooltip("overdue_left:Q", title="Overdue still waiting"),
            ],
        )
    )
    named = frontier[frontier["name"] != ""]
    labels = (
        alt.Chart(named)
        .mark_text(align="left", dx=8, dy=-8, fontWeight="bold")
        .encode(
            x=axis_x,
            y=axis_y,
            text="name:N",
            color=alt.Color(
                "name:N",
                scale=alt.Scale(
                    domain=list(theme.SETTING_COLOURS), range=list(theme.SETTING_COLOURS.values())
                ),
                legend=None,
            ),
        )
    )
    you = pd.DataFrame(
        [{"repairs": current.repairs, "overdue_left": current.overdue_left, "label": "Your plan"}]
    )
    marker = (
        alt.Chart(you)
        .mark_point(shape="diamond", size=260, filled=True, color=theme.HIGHLIGHT)
        .encode(x=axis_x, y=axis_y, tooltip=alt.Tooltip("label:N", title=""))
    )
    return theme.chart(alt.layer(line, labels, marker).properties(height=300))


def effect_sentence(current: weekly.Summary, base: weekly.Summary, is_base: bool) -> str:
    if is_base:
        return (
            f"This is the plan with the most repairs. {current.overdue_left} repairs past "
            f"the NT time limit still wait after this week, {current.overdue_left_remote} "
            "of them in remote communities."
        )
    fewer = base.repairs - current.repairs
    reached = base.overdue_left - current.overdue_left
    repairs = (
        f"{fewer} fewer repairs this week"
        if fewer > 0
        else f"{-fewer} more repairs this week"
        if fewer < 0
        else "the same number of repairs"
    )
    overdue = (
        f"{reached} more overdue repairs reached"
        if reached > 0
        else f"{-reached} fewer overdue repairs reached"
        if reached < 0
        else "no change in overdue repairs reached"
    )
    return f"Compared with Most repairs: {repairs}, and {overdue}."


def trips_table(plan: weekly.WeekPlan, jobs: dict) -> pd.DataFrame:
    rows = []
    for base in constants.CREW_BASES:
        town = [t for t in plan.trips if t.base == base and t.is_town]
        if town:
            ids = [j for t in town for j in t.job_ids]
            rows.append(
                {
                    "Base": base,
                    "Where": f"{base} (town)",
                    "Repairs": len(ids),
                    "Overdue": sum(scoring.is_overdue(jobs[j], plan.day) for j in ids),
                    "Driving days": 0.0,
                    "Work days": sum(t.work_days for t in town),
                    "Priority": max(t.priority for t in town),
                    "Note": "",
                }
            )
        for trip in plan.trips:
            if trip.base != base or trip.is_town:
                continue
            rows.append(
                {
                    "Base": base,
                    "Where": _name(trip.community_id),
                    "Repairs": len(trip.job_ids),
                    "Overdue": sum(scoring.is_overdue(jobs[j], plan.day) for j in trip.job_ids),
                    "Driving days": trip.travel_days,
                    "Work days": trip.work_days,
                    "Priority": trip.priority,
                    "Note": "added by you" if trip.added else "",
                }
            )
    frame = pd.DataFrame(rows)
    if not frame.empty and not frame["Note"].any():
        frame = frame.drop(columns="Note")
    return frame


def waiting_table(plan: weekly.WeekPlan, jobs: dict) -> pd.DataFrame:
    rows = []
    for waiting in plan.waiting:
        rows.append(
            {
                "Where": _name(waiting.community_id),
                "Why no crew": explain.waiting_line(waiting, plan),
                "Repairs": len(waiting.job_ids),
                "Overdue": sum(scoring.is_overdue(jobs[j], plan.day) for j in waiting.job_ids),
                "Longest wait (days)": max(
                    (plan.day - jobs[j].reported_on).days for j in waiting.job_ids
                ),
                "Base": waiting.base,
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return frame.sort_values(["Overdue", "Longest wait (days)"], ascending=False)


def run_sheet(plan: weekly.WeekPlan) -> pd.DataFrame:
    """One row per crew, one column per weekday: where the crew is."""
    rows = []
    for crew in plan.crews:
        cells: list[list[str]] = [[] for _ in explain.WEEKDAYS]
        for stop in crew.stops:
            trip = stop.trip
            out_end = stop.start + trip.travel_days / 2
            work_end = out_end + trip.work_days
            for day in range(len(explain.WEEKDAYS)):
                lo, hi = day, day + 1
                if min(hi, stop.start + trip.days) - max(lo, stop.start) <= 0:
                    continue
                if trip.is_town:
                    label = (
                        f"{trip.base} town" if trip.job_ids else f"{trip.base} town (new reports)"
                    )
                else:
                    working = min(hi, work_end) - max(lo, out_end) > 0
                    label = _name(trip.community_id) + ("" if working else " (driving)")
                if label not in cells[day]:
                    cells[day].append(label)
        rows.append(
            {
                "Crew": crew.crew_id,
                **{d: " / ".join(c) for d, c in zip(explain.WEEKDAYS, cells, strict=True)},
            }
        )
    return pd.DataFrame(rows)


st.title("This week's crew plan")
today = state.today()
jobs_open = state.open_jobs()
by_id = {j.job_id: j for j in jobs_open}
plannable = [j for j in jobs_open if weekly.in_plan(j, today)]
overdue = [j for j in plannable if scoring.is_overdue(j, today)]
crews = sum(constants.CREWS_AT_BASE.values())
st.caption(
    f"Week of Monday {today:%d %B %Y} · {crews} licensed trade crews at "
    f"{len(constants.CREW_BASES)} regional towns · "
    f"{crews * constants.CREW_DAYS_PER_WEEK} crew-days · {theme.PROVENANCE_LINE}"
)
st.write(
    "For the coordinator who schedules the licensed trades (electrical, plumbing, cooling) "
    "out of the regional towns. Fair Turn reads repair reports and proposes where your "
    "crews go this week. It shows what each choice costs and who is left waiting. Nothing "
    "goes to a crew until you sign."
)

st.info(
    f"**{len(plannable)} repairs are waiting for a crew. {len(overdue)} are past the NT time "
    f"limit, and {sum(j.is_remote for j in overdue)} of those are in remote communities.**  \n"
    f"This is what {state.HISTORY_WEEKS} weeks of planning for the most repairs left behind "
    "(simulated)."
)
needs_person = [j for j in jobs_open if j.needs_human]
emergencies = [
    j for j in jobs_open if not j.needs_human and j.safety_class is SafetyClass.IMMEDIATE
]
if needs_person or emergencies:
    left, right = st.columns(2)
    if needs_person:
        with left:
            people = _count(len(needs_person), "report needs", "reports need")
            st.warning(
                f"{people} a person before they can be planned: the AI could not find the "
                "words for what is broken or how urgent it is."
            )
            st.page_link("pages/reports.py", label="Read them in Reports", icon="➡️")
    if emergencies:
        with right:
            urgent = _count(len(emergencies), "emergency today goes", "emergencies today go")
            st.warning(
                f"{urgent} straight to the make-safe team (NT policy: safe within "
                f"{constants.MAKE_SAFE_HOURS} hours). They are not part of this plan."
            )

# --- 1. the setting ------------------------------------------------------------------------
st.subheader("1. Choose what decides where crews go")
setting = state.get_setting()
names = list(constants.SETTINGS)
current_name = weekly.setting_name(setting)
st.segmented_control(
    "What decides where crews go",
    names,
    key="setting_pick",
    on_change=state.on_pick,
    label_visibility="collapsed",
)
st.caption(
    f"**{current_name}:** "
    + explain.SETTING_MEANING.get(current_name, "between the named settings")
    + "."
)
with st.expander("Fine-tune the setting"):
    st.slider(
        "From most repairs (0) to most overdue first (1)",
        0.0,
        1.0,
        step=0.05,
        key="setting_slider",
        on_change=state.on_slide,
    )

plan = state.week_plan(jobs_open)
summary = weekly.summarise(plan, jobs_open)
base_summary = weekly.summarise(
    state.week_plan(jobs_open, constants.SETTINGS["Most repairs"], with_changes=False), jobs_open
)
is_base = math.isclose(setting, 0.0) and not state.get_changes()

m1, m2, m3, m4 = st.columns(4)
m1.metric(
    "Repairs this week",
    summary.repairs,
    delta=None if is_base else summary.repairs - base_summary.repairs,
    help="Repairs the crews fix this week under this plan.",
)
m2.metric(
    "Overdue repairs still waiting",
    summary.overdue_left,
    delta=None if is_base else summary.overdue_left - base_summary.overdue_left,
    delta_color="inverse",
    help="Repairs already past the NT time limit that get no crew this week.",
)
m3.metric(
    "Remote communities visited",
    summary.remote_trips,
    delta=None if is_base else summary.remote_trips - base_summary.remote_trips,
)
m4.metric(
    "Crew-days spent driving",
    f"{summary.driving_days:g} of {summary.crew_days:g}",
    help="Days on the road are days not spent fixing.",
)
st.markdown(f"**{effect_sentence(summary, base_summary, is_base)}**")
with st.container(border=True):
    st.markdown("**Every setting on one line: more repairs, or fewer overdue households**")
    st.altair_chart(frontier_chart(_frontier(jobs_open), summary), width="stretch")
    st.caption(
        "Each dot is one setting from Most repairs (0) to Most overdue first (1). Moving along "
        "the line trades repairs this week for overdue households reached. No point is free: "
        "the choice is yours, and it is logged when you sign."
    )

# --- 2. the trips --------------------------------------------------------------------------
st.subheader("2. Check the trips")
map_col, list_col = st.columns([5, 6])
with map_col:
    st.altair_chart(plan_map.plan_map(plan, state.places(), by_id), width="stretch")
with list_col:
    st.markdown("**Where the crews go**")
    st.dataframe(
        trips_table(plan, by_id),
        hide_index=True,
        width="stretch",
        column_config={
            "Priority": st.column_config.NumberColumn(
                format="%.1f", help="What the trip counts for, per crew-day, under the setting."
            ),
            "Driving days": st.column_config.NumberColumn(format="%g"),
            "Work days": st.column_config.NumberColumn(format="%g"),
        },
    )
    waiting = waiting_table(plan, by_id)
    st.markdown(f"**Left waiting this week** · {len(waiting)} places")
    st.dataframe(waiting, hide_index=True, width="stretch", height=260)

changes = state.get_changes()
with st.expander("Add or take out a trip", expanded=bool(changes)):
    st.caption(
        "The plan is a proposal. You know things it does not: a funeral, a ceremony, a crew "
        "already nearby. Every change needs a reason and goes to the log when you sign."
    )
    add_col, drop_col = st.columns(2)
    can_add = sorted(
        w.community_id
        for w in plan.waiting
        if not state.places()[w.community_id].is_town
        and w.reason not in (weekly.CLOSED, weekly.TRIP_FULL)
        and w.community_id not in changes
    )
    can_drop = sorted(
        t.community_id for t in plan.trips if not t.is_town and t.community_id not in changes
    )
    with add_col, st.form("add_trip", clear_on_submit=True):
        cid = st.selectbox("Add a trip to", can_add, format_func=_name, index=None)
        reason = st.text_input("Why", key="add_reason")
        if st.form_submit_button("Add trip"):
            if cid and reason.strip():
                state.set_change(cid, "add", reason)
                st.rerun()
            else:
                st.error("Choose a community and give a reason.")
    with drop_col, st.form("drop_trip", clear_on_submit=True):
        cid = st.selectbox("Take out the trip to", can_drop, format_func=_name, index=None)
        reason = st.text_input("Why", key="drop_reason")
        if st.form_submit_button("Take out"):
            if cid and reason.strip():
                state.set_change(cid, "drop", reason)
                st.rerun()
            else:
                st.error("Choose a trip and give a reason.")
    for cid, (action, reason) in changes.items():
        line, undo = st.columns([5, 1])
        verb = "Added" if action == "add" else "Took out"
        line.write(f"{verb} **{_name(cid)}**: {reason}")
        if undo.button("Undo", key=f"undo_{cid}"):
            state.undo_change(cid)
            st.rerun()

# --- 3. sign -------------------------------------------------------------------------------
st.subheader("3. Sign the plan")
signed = state.signature()
matches = signed is not None and state.signed_state() == state.current_state()
if signed is not None and matches:
    st.success(
        f"Signed by **{signed.signer}** at {signed.recorded_at:%H:%M on %d %B %Y} "
        f"(version {signed.version}). Reason: {signed.reason}"
    )
elif signed is not None:
    st.warning(
        f"You changed the plan after signing version {signed.version}. Sign again to replace "
        "it; the old version stays in the log."
    )
with st.form("sign"):
    signer = st.text_input("Your name", value=state.get_signer())
    reason = st.text_area(
        "Why this plan",
        placeholder="For example: three remote communities are two weeks past the time limit.",
    )
    pressed = st.form_submit_button("Sign this week's plan", type="primary", disabled=matches)
if pressed:
    if not signer.strip() or not reason.strip():
        st.error("Give your name and a reason. The reason is what a tenant is told.")
    else:
        version = 1 if signed is None else signed.version + 1
        added = tuple(sorted(c for c, (a, _) in changes.items() if a == "add"))
        dropped = tuple(sorted(c for c, (a, _) in changes.items() if a == "drop"))
        audit.append(
            state.get_audit_path(),
            audit.PlanSigned(
                day=today,
                version=version,
                setting=setting,
                setting_name=current_name,
                signer=signer.strip(),
                reason=reason.strip(),
                trips=weekly.trip_lines(plan),
                changes=tuple(
                    f"{'added' if a == 'add' else 'took out'} {c}: {r}"
                    for c, (a, r) in changes.items()
                ),
                repairs=summary.repairs,
                overdue_left=summary.overdue_left,
                added=added,
                dropped=dropped,
            ),
        )
        state.set_signer(signer.strip())
        st.rerun()

with st.expander("Crew run sheet, Monday to Friday", expanded=matches):
    if not matches:
        st.caption("A proposal until you sign.")
    st.dataframe(run_sheet(plan), hide_index=True, width="stretch")

with st.expander("How the plan is made"):
    st.markdown(
        f"""
- **A trip is the unit.** A crew in its own town fixes {constants.JOBS_PER_CREW_DAY} repairs
  a day. A trip to a remote community first spends days driving there and back
  ({constants.DRIVE_KM_PER_DAY} km of road a day), then fixes up to
  {constants.MAX_JOBS_PER_TRIP} repairs.
- **The setting decides what a trip is worth.** At *Most repairs* every repair counts 1 and
  driving days count in full, so the town always wins. At *Most overdue first* a repair
  counts by its need (how far past the NT time limit, how serious, who lives there) and
  driving days are not held against the trip.
- **Each base fills its crews' week** with the trips worth most per crew-day, until the days
  run out. What is left waits, with the reason shown.
- **The AI only reads the reports.** The plan is this formula, not a model. A fact the AI
  could not point to in the tenant's own words is left empty, and a person reads the report.
"""
    )
