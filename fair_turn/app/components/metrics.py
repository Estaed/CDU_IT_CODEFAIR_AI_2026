"""The workspace's wait metrics and outcome sentence (PRD 3.1), shown only after today's
sign-off.

``sim_inputs``, ``panel_values`` and ``formatted`` are pure, so a test can compare the panel
with ``capacity_sim.simulate`` directly.
"""

from collections.abc import Callable
from datetime import date, timedelta
from statistics import median

import streamlit as st

from fair_turn.app import state
from fair_turn.core import capacity_sim, constants, decisions, effect
from fair_turn.core.capacity_sim import Closure, SimResult
from fair_turn.core.types import Job, ScoredJob
from fair_turn.data import geography
from fair_turn.data.artefacts import Artefacts, to_jobs

LABELS = {
    "median_wait_remote": "Remote median wait",
    "median_wait_town": "Town median wait",
    "gap": "Gap (remote minus town)",
    "travel_km": "Road km driven",
}
NOT_AVAILABLE = "n/a"


def sim_inputs(art: Artefacts) -> dict:
    """Jobs, closures, crews and sites for ``capacity_sim.simulate``.

    The same inputs ``ranking_table.open_jobs`` builds; it builds them inline rather than in
    a function this module could import, and that file belongs to Task-14, so they are
    rebuilt here the same way.
    """
    return {
        "jobs": to_jobs(art),
        "closures": [
            Closure(
                c["community_id"],
                date.fromisoformat(c["closed_from"]),
                date.fromisoformat(c["closed_to"]),
            )
            for c in art.closures
        ],
        "crews": geography.crews(art.communities),
        "jobs_per_crew_day": constants.JOBS_PER_CREW_DAY,
        "travel_day_km": constants.TRAVEL_DAY_KM,
        "sites": geography.sim_sites(art.communities),
    }


@st.cache_data
def simulation(today: date, lam: float) -> SimResult:
    """The capacity model from the window start through ``today`` at ``lam``."""
    return capacity_sim.simulate(
        lam=lam,
        start=constants.WINDOW_START,
        days=(today - constants.WINDOW_START).days + 1,
        **sim_inputs(state.artefacts()),
    )


def panel_values(
    sim: SimResult, jobs: list[Job], communities: dict[str, dict[str, str]], region: str
) -> dict[str, float | None]:
    """The four panel numbers. For one region the medians are recomputed the way
    ``capacity_sim`` computes them (human-queue jobs out, open jobs censored at the day after
    the run); travel cost stays whole NT."""
    values = {
        "median_wait_remote": sim.median_wait_remote,
        "median_wait_town": sim.median_wait_town,
        "gap": sim.gap,
        "travel_km": sim.travel_km,
    }
    if region == state.ALL_REGIONS:
        return values
    end = constants.WINDOW_START + timedelta(days=len(sim.queue_length))
    remote: list[int] = []
    town: list[int] = []
    for job in _crew_jobs(sim, jobs, communities, region):
        wait = sim.wait_days[job.job_id]
        (remote if job.is_remote else town).append(
            wait if wait is not None else (end - job.reported_on).days
        )
    values["median_wait_remote"] = float(median(remote)) if remote else None
    values["median_wait_town"] = float(median(town)) if town else None
    both = values["median_wait_remote"] is not None and values["median_wait_town"] is not None
    values["gap"] = values["median_wait_remote"] - values["median_wait_town"] if both else None
    return values


def _crew_jobs(
    sim: SimResult, jobs: list[Job], communities: dict[str, dict[str, str]], region: str
) -> list[Job]:
    """The jobs behind the crew-wait medians, selected as ``capacity_sim`` selects them:
    reported within the run, not in the human queue, not the make-safe contractor's."""
    end = constants.WINDOW_START + timedelta(days=len(sim.queue_length))
    return [
        job
        for job in jobs
        if (region == state.ALL_REGIONS or communities[job.community_id]["region"] == region)
        and not job.needs_human
        and not decisions.is_make_safe(job)
        and job.reported_on < end
    ]


def open_counts(
    sim: SimResult, jobs: list[Job], communities: dict[str, dict[str, str]], region: str
) -> str:
    """How many of the medians' jobs are still open at the end of the run, remote and town."""
    counted = _crew_jobs(sim, jobs, communities, region)
    remote = [j for j in counted if j.is_remote]
    town = [j for j in counted if not j.is_remote]
    open_remote = sum(sim.completed_on[j.job_id] is None for j in remote)
    open_town = sum(sim.completed_on[j.job_id] is None for j in town)
    return (
        f"Still open at the end of the run: {open_remote} of {len(remote)} remote jobs, "
        f"{open_town} of {len(town)} town jobs."
    )


def _days(value: float) -> str:
    return f"{value:.1f} days"


def formatted(values: dict[str, float | None]) -> dict[str, str]:
    """Panel strings; a missing value is shown as ``n/a``."""
    return {
        key: NOT_AVAILABLE
        if value is None
        else f"{value:,.0f} km"
        if key == "travel_km"
        else _days(value)
        for key, value in values.items()
    }


SAME_AS_BASELINE = "Same as efficiency-first."


def deltas(values: dict[str, float | None], baseline: dict[str, float | None]) -> dict:
    """Signed change against the efficiency-first run; ``None`` when either side is missing or
    the two are equal (a zero delta is shown as no delta, not a red "+0.0")."""
    return {
        key: None
        if values[key] is None or baseline[key] is None or values[key] == baseline[key]
        else f"{values[key] - baseline[key]:+,.0f} km"
        if key == "travel_km"
        else f"{values[key] - baseline[key]:+.1f} days"
        for key in values
    }


def same_as_baseline(values: dict[str, float | None], baseline: dict[str, float | None]) -> dict:
    """Whether a tile's value exactly equals the baseline's (both present)."""
    return {
        key: values[key] is not None and baseline[key] is not None and values[key] == baseline[key]
        for key in values
    }


def effect_sentence(
    today: date,
    region: str,
    lam: float,
    proposed: list[ScoredJob],
    baseline_today: list[ScoredJob],
    is_remote: Callable[[str], bool],
    label: str,
) -> str:
    """The two-stage effect sentence shown above the workspace list. ``proposed`` is today's
    list after decisions (To decide + Accepted), ``baseline_today`` the first capacity-many
    jobs of the efficiency-first ranking; the two may differ in length (an accepted job is
    never dropped), so the comparison window covers both lists whole."""
    window = max(len(proposed), len(baseline_today))
    if not state.get_signed_today():
        return effect.sentence(
            "before_signature", proposed, baseline_today, window, is_remote, label
        )
    art = state.artefacts()
    jobs = to_jobs(art)
    values = panel_values(simulation(today, lam), jobs, art.communities, region)
    baseline_values = panel_values(simulation(today, 1.0), jobs, art.communities, region)
    return effect.sentence(
        "after_signature",
        proposed,
        baseline_today,
        window,
        is_remote,
        label,
        current_metrics=values,
        baseline_metrics=baseline_values,
    )


def metrics_panel(today: date, region: str, lam: float) -> None:
    """The outcome metrics, locked until today's signature (decide before reveal). The numbers
    come from the 90-day capacity simulation at ``lam`` against λ = 1.0, which reads no day's
    list, so no list is passed in."""
    if not state.get_signed_today():
        with st.container(border=True):
            st.markdown("**Outcomes appear after you sign**")
            st.caption(
                "Wait times and travel cost appear after you sign. We hide them until then so "
                "the numbers do not steer your ordering."
            )
        return
    art = state.artefacts()
    jobs = to_jobs(art)
    values = panel_values(simulation(today, lam), jobs, art.communities, region)
    baseline_values = panel_values(simulation(today, 1.0), jobs, art.communities, region)
    shown = formatted(values)
    changes = deltas(values, baseline_values)
    same = same_as_baseline(values, baseline_values)
    travel_help = "Whole NT." if region != state.ALL_REGIONS else None
    for column, key in zip(st.columns(len(LABELS)), LABELS, strict=True):
        help_text = travel_help if key == "travel_km" else "Against λ = 1.00."
        if same[key]:
            help_text = f"{help_text} {SAME_AS_BASELINE}" if help_text else SAME_AS_BASELINE
        column.metric(
            LABELS[key],
            shown[key],
            delta=changes[key],
            delta_color="inverse",  # lower wait, gap and travel cost are better
            help=help_text,
            border=True,
        )
        if same[key]:
            column.caption(SAME_AS_BASELINE)
    st.caption(
        "Baseline: efficiency-first (travel-cost weight 1.00). Simulated over the 90-day set. "
        "Days and road kilometres. A job still open at the end counts with its days open so "
        "far, so a median is a lower bound; the counts below say how many."
    )
    current_open = open_counts(simulation(today, lam), jobs, art.communities, region)
    baseline_open = open_counts(simulation(today, 1.0), jobs, art.communities, region)
    st.caption(f"This weighting: {current_open} Efficiency-first: {baseline_open}")
