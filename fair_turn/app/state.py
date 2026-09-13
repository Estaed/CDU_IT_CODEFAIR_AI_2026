"""Typed accessors for session state. No page reads ``st.session_state`` directly: the keys
and their defaults are defined here once."""

from datetime import date, datetime, timedelta
from pathlib import Path

import streamlit as st

from fair_turn.core import audit, constants
from fair_turn.data.artefacts import Artefacts, load_all

ALL_REGIONS = "All"


@st.cache_resource
def artefacts() -> Artefacts:
    """Loaded once per process: the object is immutable, so it is shared, not pickled."""
    return load_all()


def _get(key: str, default):
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]


def get_today() -> date:
    return _get("today", constants.WINDOW_START + timedelta(days=constants.WINDOW_DAYS))


def set_today(value: date) -> None:
    st.session_state["today"] = value


def get_region() -> str:
    return _get("region", ALL_REGIONS)


def set_region(value: str) -> None:
    if value != ALL_REGIONS and value not in constants.REGIONS:
        raise ValueError(f"unknown region: {value}")
    st.session_state["region"] = value


def get_lam() -> float:
    return _get("lam", 1.0)  # PRD 3.1: starts at efficiency first


def set_lam(value: float) -> None:
    """A board lambda change after today's sign-off is a revision, not a silent edit."""
    value = float(value)
    if get_signed_today() and value != get_lam():
        audit.append(
            get_audit_path(),
            audit.Revision(
                day=get_today(),
                old_lam=get_lam(),
                new_lam=value,
                reason="lambda changed on the board after sign-off",
                at=datetime.now(),
            ),
        )
    st.session_state["lam"] = value


def get_signed_today() -> bool:
    return _get("signed_today", False)


def set_signed_today(value: bool) -> None:
    st.session_state["signed_today"] = value


def get_selected_job_id() -> str | None:
    return _get("selected_job_id", None)


def set_selected_job_id(value: str | None) -> None:
    st.session_state["selected_job_id"] = value


def get_audit_path() -> Path:
    return _get("audit_path", artefacts().audit_path)


def set_audit_path(value: Path) -> None:
    st.session_state["audit_path"] = Path(value)


def get_human_set(job_id: str) -> dict[str, str]:
    return _get("human_set", {}).get(job_id, {})


def set_human_set(job_id: str, field: str, value: str) -> None:
    all_human_set = _get("human_set", {})
    all_human_set.setdefault(job_id, {})[field] = value
