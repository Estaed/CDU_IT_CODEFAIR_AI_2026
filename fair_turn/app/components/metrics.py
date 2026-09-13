"""The board's wait metrics (PRD 3.1), shown only after today's sign-off.

``sim_inputs``, ``panel_values`` and ``formatted`` are pure, so a test can compare the panel
with ``capacity_sim.simulate`` directly.
"""

from datetime import date, timedelta
from statistics import median

import streamlit as st

from fair_turn.app import state
from fair_turn.core import capacity_sim, constants
from fair_turn.core.capacity_sim import Closure, SimResult, Site
from fair_turn.core.types import Job
from fair_turn.data.artefacts import Artefacts, to_jobs

LABELS = {
    "median_wait_remote": "Remote median wait",
    "median_wait_town": "Town median wait",
    "gap": "Gap (remote minus town)",
    "travel_cost": "Travel cost",
}
NOT_AVAILABLE = "n/a"


def sim_inputs(art: Artefacts) -> dict:
    """Jobs, closures, crews and sites for ``capacity_sim.simulate``.

    The same inputs ``ranking_table.open_jobs`` builds; it builds them inline rather than in
    a function this module could import, and that file belongs to Task-14, so they are
    rebuilt here the same way.
    """
    crews = {region: constants.CREWS_PER_REMOTE_REGION for region in constants.REMOTE_REGIONS}
    crews[constants.TOWN_REGION] = constants.CREWS_TOWN
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
        "crews_per_region": crews,
        "jobs_per_crew_day": constants.JOBS_PER_CREW_DAY,
        "travel_day_km": constants.TRAVEL_DAY_KM,
        "sites": {
            cid: Site(row["region"], float(row["km_to_base"]))
            for cid, row in art.communities.items()
        },
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
        "travel_cost": sim.travel_cost,
    }
    if region == state.ALL_REGIONS:
        return values
    end = constants.WINDOW_START + timedelta(days=len(sim.queue_length))
    remote: list[int] = []
    town: list[int] = []
    for job in jobs:
        community = communities[job.community_id]
        if community["region"] != region or job.needs_human or job.reported_on >= end:
            continue
        wait = sim.wait_days[job.job_id]
        (remote if community["is_remote"] == "True" else town).append(
            wait if wait is not None else (end - job.reported_on).days
        )
    values["median_wait_remote"] = float(median(remote)) if remote else None
    values["median_wait_town"] = float(median(town)) if town else None
    both = values["median_wait_remote"] is not None and values["median_wait_town"] is not None
    values["gap"] = values["median_wait_remote"] - values["median_wait_town"] if both else None
    return values


def _days(value: float) -> str:
    return f"{value:.1f} days"


def formatted(values: dict[str, float | None]) -> dict[str, str]:
    """Panel strings; a missing value is shown as ``n/a``."""
    return {
        key: NOT_AVAILABLE
        if value is None
        else f"{value:,.0f}"
        if key == "travel_cost"
        else _days(value)
        for key, value in values.items()
    }


def deltas(values: dict[str, float | None], baseline: dict[str, float | None]) -> dict:
    """Signed change against the efficiency-first run; ``None`` when either side is missing."""
    return {
        key: None
        if values[key] is None or baseline[key] is None
        else f"{values[key] - baseline[key]:+,.0f}"
        if key == "travel_cost"
        else f"{values[key] - baseline[key]:+.1f} days"
        for key in values
    }


def metrics_panel(today: date, region: str, lam: float) -> None:
    art = state.artefacts()
    jobs = to_jobs(art)
    values = panel_values(simulation(today, lam), jobs, art.communities, region)
    baseline = panel_values(simulation(today, 1.0), jobs, art.communities, region)
    shown = formatted(values)
    changes = deltas(values, baseline)
    travel_help = "Whole NT." if region != state.ALL_REGIONS else None
    for column, key in zip(st.columns(len(LABELS)), LABELS, strict=True):
        column.metric(
            LABELS[key],
            shown[key],
            delta=changes[key],
            delta_color="inverse",  # lower wait, gap and travel cost are better
            help=travel_help if key == "travel_cost" else "Against λ = 1.00.",
        )
