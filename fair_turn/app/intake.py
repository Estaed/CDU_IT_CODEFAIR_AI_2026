"""Adding a new report: the one app module allowed to call a model (Blueprint).

The model call happens only when the person presses Extract, with a timeout; its result is
schema-validated and every phrase checked against the text before anything is shown or
saved. With no provider set, a person can still add a test-set report with no model call.
"""

import uuid
from collections.abc import Callable
from datetime import datetime

import numpy as np
import streamlit as st

from fair_turn.app import state
from fair_turn.core import audit, constants, verify_spans
from fair_turn.data import runtime
from fair_turn.llm import intake as intake_llm

CALL_OVERRIDE: Callable | None = None  # tests put a fake model here

# Example reports for the demo, picked from the synthetic labels: a town cooling fault, a
# remote hot-water fault and a remote electrical emergency.
EXAMPLE_REPORTS = {
    "Cooling, town": "JR-2025-00407",
    "Hot water, remote": "JR-2025-00030",
    "Electrical, emergency": "JR-2025-00011",
}
REPLAY_PROVIDER = "test-set replay"
REPLAY_MODEL = "no model call: the committed reading of a test-set report"


def _draft() -> dict:
    """The one stateful draft that makes a second press save nothing twice."""
    key = "intake_draft"
    if key not in st.session_state:
        st.session_state[key] = {"token": uuid.uuid4().hex, "result": None, "example": None}
    return st.session_state[key]


def _reset_draft() -> None:
    st.session_state.pop("intake_draft", None)


def _save(text: str, community_id: str, result: intake_llm.IntakeResult, token: str) -> str:
    records = state.runtime_records()
    ids = {label["job_id"] for label in state.artefacts().labels}
    ids.update(r.job_id for r in records if isinstance(r, runtime.IntakeReport))
    job_id = runtime.next_job_id(ids)
    wrote = runtime.append(
        state.get_runtime_path(),
        runtime.IntakeReport(
            job_id=job_id,
            community_id=community_id,
            reported_on=state.today(),
            text=text,
            extraction=result.extraction,
            status=result.status,
            provider=result.provider,
            model=result.model,
            prompt_version=result.prompt_version,
            latency_s=result.latency_s,
            validation={"result": result.validation, "error": result.error},
            draft_token=token,
            at=datetime.now().astimezone(),
        ),
    )
    if not wrote:
        return next(
            r.job_id
            for r in state.runtime_records()
            if isinstance(r, runtime.IntakeReport) and r.draft_token == token
        )
    audit.append(
        state.get_audit_path(),
        audit.Intake(
            day=state.today(),
            job_id=job_id,
            provider=result.provider,
            model=result.model,
            prompt_version=result.prompt_version,
            latency_s=result.latency_s,
            validation=result.validation,
            status=result.status,
        ),
    )
    return job_id


def _flat(row) -> dict:
    """The schema-shaped dict of one committed reading, from its kept fields only."""
    kept = row.kept
    factors = sorted(name for name in kept if name.startswith("health_risk:"))
    flat = {
        "health_risk": [kept[name].value for name in factors],
        "health_risk_evidence": [kept[name].evidence for name in factors],
        "location_mentioned": "location_mentioned" in kept,
        "location_evidence": kept["location_mentioned"].evidence
        if "location_mentioned" in kept
        else "",
        "crew_or_access_note": kept["crew_or_access_note"].evidence
        if "crew_or_access_note" in kept
        else "",
    }
    for name in verify_spans.REQUIRED_FIELDS:
        if name in kept:
            flat[name] = kept[name].value
            flat[f"{name}_evidence"] = kept[name].evidence
    return flat


def replay(needs_person: bool = False) -> str:
    """Add one unused test-set report through the same save path, with no model call: its
    committed reading, re-checked against the text. Returns the new job id."""
    art = state.artefacts()
    ids = sorted(label["job_id"] for label in art.labels)
    order = [ids[i] for i in np.random.default_rng(constants.SEED).permutation(len(ids))]
    used = {
        r.text
        for r in state.runtime_records()
        if isinstance(r, runtime.IntakeReport) and r.provider == REPLAY_PROVIDER
    }
    community_of = {label["job_id"]: label["community_id"] for label in art.labels}
    for source_id in order:
        text = art.reports[source_id]
        if text in used:
            continue
        flat = _flat(art.extraction[source_id])
        verified = verify_spans.verify(text, flat)
        if verified.needs_human != needs_person:
            continue
        failed = [f for f in verify_spans.REQUIRED_FIELDS if getattr(verified, f) is None]
        result = intake_llm.IntakeResult(
            extraction=flat,
            verified=verified,
            status="needs_review" if failed else "extracted",
            provider=REPLAY_PROVIDER,
            model=REPLAY_MODEL,
            prompt_version=REPLAY_PROVIDER,
            latency_s=0.0,
            validation="verified" if not failed else f"{', '.join(failed)} not found",
            error=None,
        )
        return _save(text, community_of[source_id], result, uuid.uuid4().hex)
    raise ValueError("no unused test-set report left to replay")


def render() -> str | None:
    """The new-report form. Returns the id of a report saved on this run, if any."""
    art = state.artefacts()
    draft = _draft()
    options = ["none", "claude", "ollama"]
    try:
        default = intake_llm.configured() or "none"
    except ValueError:
        default = "none"
    chosen = st.selectbox(
        "Who reads the report",
        options,
        index=options.index(default),
        help="claude = Claude Sonnet through the logged-in claude CLI; ollama = a local "
        "model. FAIR_TURN_PROVIDER sets the default. none = no model on this machine.",
    )
    example = st.pills("Start from an example", list(EXAMPLE_REPORTS), selection_mode="single")
    if example and example != draft["example"]:
        source = EXAMPLE_REPORTS[example]
        draft.update(example=example, result=None)
        st.session_state["intake_text"] = art.reports[source]
        st.session_state["intake_community"] = next(
            lb["community_id"] for lb in art.labels if lb["job_id"] == source
        )
    text = st.text_area("Report, in the tenant's words", key="intake_text", height=140)
    communities = sorted(art.communities)
    community = st.selectbox("Community", communities, key="intake_community")

    provider = None
    if CALL_OVERRIDE is not None:
        provider = chosen if chosen != "none" else "claude"
    elif chosen != "none":
        provider = intake_llm.configured(override=chosen)
    if provider is None:
        st.info(
            "No model is set on this machine, so a report cannot be read here. Choose claude "
            "or ollama above, or add a test-set report with its committed reading below."
        )
    too_long = len(text) > 4_000
    if too_long:
        st.error("The report is over 4,000 characters.")
    pressed = st.button(
        "Read the report",
        type="primary",
        disabled=provider is None or not text.strip() or too_long,
    )
    if pressed:
        with st.status(f"Reading with {provider}…") as status:
            draft["result"] = intake_llm.extract(text, provider, call=CALL_OVERRIDE)
            status.update(label=f"Read in {draft['result'].latency_s:.1f} s", state="complete")
    saved = None
    result = draft["result"]
    if result is not None:
        if result.status == "not_extracted":
            st.error(f"The model could not read it: {result.error}. It is saved for a person.")
        elif result.status == "needs_review":
            st.warning("Some facts had no matching words in the report. A person sets them.")
        else:
            st.success("Every required fact was found in the tenant's words.")
        if st.button("Save the report"):
            saved = _save(text, community, result, draft["token"])
            _reset_draft()
    st.divider()
    left, right = st.columns(2)
    if left.button("Add a test-set report (no model)"):
        saved = replay()
    if right.button("Add one the AI could not read"):
        saved = replay(needs_person=True)
    return saved
