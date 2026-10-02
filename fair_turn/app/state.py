"""Session state and the shared, cached world every page reads.

No page reads ``st.session_state`` directly: the keys and their defaults are defined here
once. The world (jobs, places, the simulated weeks before the planning day) is built from
the committed artefacts once per process; runtime records (new reports, fields a person
set) are laid over it on every read.
"""

from datetime import date
from pathlib import Path

import streamlit as st

from fair_turn.core import audit, constants, weekly, weeks
from fair_turn.core.types import Job
from fair_turn.data import artefacts as artefacts_module
from fair_turn.data import geography, runtime
from fair_turn.data.artefacts import Artefacts, load_all

# The backlog the coordinator meets on the planning day: what weeks of "Efficiency first"
# planning left behind, simulated from the first Monday of the synthetic window.
HISTORY_SETTING = constants.SETTINGS["Efficiency first"]
FIRST_MONDAY = weeks.FIRST_MONDAY
HISTORY_WEEKS = weeks.HISTORY_WEEKS


@st.cache_resource
def artefacts() -> Artefacts:
    """Loaded once per process: the object is immutable, so it is shared, not pickled."""
    return load_all()


@st.cache_resource
def places() -> dict[str, weekly.Place]:
    return geography.places(artefacts().communities)


@st.cache_resource
def history() -> weeks.Season:
    """The weeks before the planning day, planned efficiency first."""
    art = artefacts()
    return weeks.simulate(
        artefacts_module.to_jobs(art),
        places(),
        HISTORY_SETTING,
        FIRST_MONDAY,
        HISTORY_WEEKS,
        art.closures,
    )


def today() -> date:
    return constants.PLAN_DAY


def closed() -> set[str]:
    return weeks.closed_for_week(artefacts().closures, today())


def get_audit_path() -> Path:
    # Read at call time, not from the cached artefacts, so a test can point it elsewhere.
    return _get("audit_path", artefacts_module.AUDIT_LOG)


def set_audit_path(value: Path) -> None:
    st.session_state["audit_path"] = Path(value)


def get_runtime_path() -> Path:
    return _get("runtime_path", runtime.RUNTIME_DIR / "runtime.jsonl")


def set_runtime_path(value: Path) -> None:
    st.session_state["runtime_path"] = Path(value)


def runtime_records() -> list:
    return runtime.read(get_runtime_path())


def all_jobs() -> list[Job]:
    """Every job: the committed reports and the ones added in this app, with any field a
    person set laid over what the model read."""
    records = runtime_records()
    intake = [r for r in records if isinstance(r, runtime.IntakeReport)]
    return artefacts_module.to_jobs(artefacts(), runtime.human_set_for(records), intake)


def done_before(job_id: str) -> date | None:
    """The day a committed job was finished before the planning week, if it was."""
    done = history().completed_on.get(job_id)
    return done if done is not None and done < today() else None


def open_jobs() -> list[Job]:
    """Jobs still open on the planning day, the ones a person must read included."""
    return [j for j in all_jobs() if j.reported_on <= today() and done_before(j.job_id) is None]


def human_set(job_id: str) -> dict[str, str]:
    return runtime.human_set_for(runtime_records()).get(job_id, {})


def _get(key: str, default):
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]


# --- the coordinator's choices this week -------------------------------------------------


def get_setting() -> float:
    _restore_signature()
    setting = _get("setting", HISTORY_SETTING)
    # The two setting controls own their keys; they start from the chosen setting.
    name = weekly.setting_name(setting)
    _get("setting_pick", name if name in constants.SETTINGS else None)
    _get("setting_slider", setting)
    return setting


def set_setting(value: float) -> None:
    st.session_state["setting"] = float(value)


def get_changes() -> dict[str, tuple[str, str]]:
    """Community id -> ("add" or "drop", reason), in the order the coordinator made them."""
    _restore_signature()
    return _get("changes", {})


def set_change(community_id: str, action: str, reason: str) -> None:
    if action not in {"add", "drop"}:
        raise ValueError("a change is add or drop")
    if not reason.strip():
        raise ValueError("a change needs a reason")
    changes = dict(get_changes())
    changes[community_id] = (action, reason.strip())
    st.session_state["changes"] = changes


def undo_change(community_id: str) -> None:
    changes = dict(get_changes())
    changes.pop(community_id, None)
    st.session_state["changes"] = changes


def get_signer() -> str:
    return _get("signer", "")


def set_signer(value: str) -> None:
    st.session_state["signer"] = value


def on_pick() -> None:
    """The named-setting control changed: the slider follows it."""
    name = st.session_state.get("setting_pick")
    if name in constants.SETTINGS:
        set_setting(constants.SETTINGS[name])
        st.session_state["setting_slider"] = constants.SETTINGS[name]


def on_slide() -> None:
    """The fine-tune slider changed: the named control shows the preset it matches, if any."""
    value = float(st.session_state.get("setting_slider", get_setting()))
    set_setting(value)
    name = weekly.setting_name(value)
    st.session_state["setting_pick"] = name if name in constants.SETTINGS else None


def week_plan(
    jobs: list[Job], setting: float | None = None, with_changes: bool = True
) -> weekly.WeekPlan:
    """This week's plan for the open ``jobs`` under ``setting`` (the chosen one by default),
    with the coordinator's changes unless ``with_changes`` is False."""
    setting = get_setting() if setting is None else setting
    changes = get_changes() if with_changes else {}
    return weekly.plan(
        jobs,
        places(),
        today(),
        setting,
        closed=closed(),
        add=[cid for cid, (action, _) in changes.items() if action == "add"],
        drop=[cid for cid, (action, _) in changes.items() if action == "drop"],
    )


def signature() -> audit.PlanSigned | None:
    return audit.latest_signature(audit.read(get_audit_path()), today())


State = tuple[float, tuple[str, ...], tuple[str, ...], tuple[str, ...]]


def signed_state() -> State | None:
    """What the latest signature covered: the setting, the added and dropped ids, and the
    trips themselves, so a new report or a person's field after signing shows as a change."""
    signed = signature()
    if signed is None:
        return None
    return signed.setting, signed.added, signed.dropped, signed.job_ids


def current_state(plan: weekly.WeekPlan) -> State:
    """The same four things for the plan on screen."""
    changes = get_changes()
    return (
        plan.setting,
        tuple(
            sorted(c for c, (a, _) in changes.items() if a == "add" and c not in plan.not_fitted)
        ),
        tuple(sorted(c for c, (a, _) in changes.items() if a == "drop")),
        tuple(sorted(plan.planned_job_ids())),
    )


def published_plan(jobs: list[Job]) -> tuple[weekly.WeekPlan, audit.PlanSigned | None]:
    """The plan a tenant is told about: the signed one while it still holds, else the
    proposal under this session's setting (and no signer)."""
    signed = signature()
    if signed is not None:
        plan = weekly.plan(
            jobs,
            places(),
            today(),
            signed.setting,
            closed=closed(),
            add=signed.added,
            drop=signed.dropped,
        )
        if tuple(sorted(plan.planned_job_ids())) == signed.job_ids:
            return plan, signed
    return week_plan(jobs), None


def _restore_signature() -> None:
    """After a reload, start from what was last signed for this week, once per session."""
    if st.session_state.get("restored"):
        return
    st.session_state["restored"] = True
    signed = signature()
    if signed is None:
        return
    st.session_state["setting"] = signed.setting
    st.session_state["signer"] = signed.signer
    reasons = dict(line.split(": ", 1) for line in signed.changes if ": " in line)
    changes = {}
    for cid in signed.added:
        changes[cid] = ("add", reasons.get(f"added {cid}", "restored from the log"))
    for cid in signed.dropped:
        changes[cid] = ("drop", reasons.get(f"took out {cid}", "restored from the log"))
    st.session_state["changes"] = changes
