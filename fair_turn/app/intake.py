"""New-report action embedded in the workspace flow (PRD sections 3.1, 3.2 and 5)."""

import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Literal

import numpy as np
import streamlit as st

from fair_turn.app import state
from fair_turn.app.components.ranking_table import open_jobs
from fair_turn.core import audit, constants, scoring, verify_spans
from fair_turn.core.types import FaultType, HealthRiskFactor, Job, SafetyClass
from fair_turn.data import runtime
from fair_turn.llm import intake as intake_llm

CALL_OVERRIDE: Callable | None = None

# Example ids for the intake demo (Task-48), picked by hand from the 2026-09-14 synthetic
# labels: one job whose label is a fault_type=cooling report in a town community (Alice
# Springs, is_remote=False), one fault_type=hot_water report in a remote community, and
# one fault_type=electrical report with safety_class immediate.
EXAMPLE_REPORTS = {
    "Cooling, Alice Springs": "JR-2025-00407",
    "Hot water, remote": "JR-2025-00030",
    "Electrical, immediate": "JR-2025-00011",
}


def new_draft() -> dict:
    """Return the one stateful draft that makes a retry idempotent."""
    return {
        "draft_token": uuid.uuid4().hex,
        "text": "",
        "community_id": None,
        "reported_on": None,
        "result": None,
        "loaded_example": None,
    }


def _community_for(art, job_id: str) -> str:
    return next(label["community_id"] for label in art.labels if label["job_id"] == job_id)


def _capacity_all() -> int:
    return (
        constants.CREWS_PER_REMOTE_REGION * len(constants.REMOTE_REGIONS) + constants.CREWS_TOWN
    ) * constants.JOBS_PER_CREW_DAY


def _preview_job(draft: dict, verified, community: dict[str, str]) -> Job:
    return Job(
        job_id="new-report-preview",
        community_id=draft["community_id"],
        is_remote=community["is_remote"] == "True",
        reported_on=draft["reported_on"],
        fault_type=FaultType(verified.fault_type) if verified.fault_type else None,
        safety_class=SafetyClass(verified.safety_class) if verified.safety_class else None,
        health_risk=frozenset(HealthRiskFactor(value) for value in verified.health_risk),
        logistics_factor=float(community["logistics_factor"]),
    )


def _field_rows(result: intake_llm.IntakeResult) -> list[dict[str, str]]:
    verified = result.verified
    raw = result.extraction or {}
    rows = []
    for field in ("fault_type", "safety_class"):
        value = getattr(verified, field) if verified else None
        phrase = (verified.kept if verified else {}).get(field, "")
        dropped = field in (verified.dropped if verified else {})
        rows.append(
            {
                "field": field.replace("_", " "),
                "value": value or "",
                "phrase": phrase,
                "status": "Needs review" if dropped else "Verified" if value else "Not extracted",
            }
        )
    health = ", ".join(verified.health_risk) if verified else ""
    rows.append(
        {
            "field": "health risk",
            "value": health,
            "phrase": "; ".join(
                phrase
                for name, phrase in (verified.kept.items() if verified else [])
                if name.startswith("health_risk:")
            ),
            "status": "Verified" if health else "Not extracted" if not raw else "Verified",
        }
    )
    return rows


def _save(draft: dict, result: intake_llm.IntakeResult) -> tuple[bool, str]:
    art = state.artefacts()
    existing = runtime.read(state.get_runtime_path())
    ids = {label["job_id"] for label in art.labels}
    ids.update(record.job_id for record in existing if isinstance(record, runtime.IntakeReport))
    job_id = runtime.next_job_id(ids)
    wrote = runtime.append(
        state.get_runtime_path(),
        runtime.IntakeReport(
            job_id=job_id,
            community_id=draft["community_id"],
            reported_on=draft["reported_on"],
            text=draft["text"],
            extraction=result.extraction,
            status=result.status,
            provider=result.provider,
            model=result.model,
            prompt_version=result.prompt_version,
            latency_s=result.latency_s,
            validation={"result": result.validation, "error": result.error},
            draft_token=draft["draft_token"],
            at=datetime.now().astimezone(),
        ),
    )
    if wrote:
        audit.append(
            state.get_audit_path(),
            audit.Intake(
                day=state.get_today(),
                job_id=job_id,
                provider=result.provider,
                model=result.model,
                prompt_version=result.prompt_version,
                latency_s=result.latency_s,
                validation=result.validation,
                status=result.status,
            ),
        )
    return wrote, job_id


DEV_PROVIDER = "dev-replay"
DEV_MODEL = "synthetic replay (no model call)"


def _flat_extraction(row) -> dict:
    """The schema-shaped dict of one committed extraction row, from its kept fields only."""
    kept = row.kept
    factors = sorted(name for name in kept if name.startswith("health_risk:"))
    extraction = {
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
    for field in verify_spans.REQUIRED_FIELDS:
        if field in kept:
            extraction[field] = kept[field].value
            extraction[f"{field}_evidence"] = kept[field].evidence
    return extraction


ReportKind = Literal["immediate", "urgent", "routine", "needs_person"]


def simulate_incoming(kind: ReportKind) -> str:
    """Replay one committed synthetic report as a new intake, through ``_save``; no model call.

    Candidates are the labelled reports in one fixed seeded order; the next unused one whose
    re-verified extraction has that safety class and every required field is written, or, for
    ``kind="needs_person"``, the next one missing a required field. Returns the new job id."""
    art = state.artefacts()
    ids = sorted(label["job_id"] for label in art.labels)
    order = [ids[i] for i in np.random.default_rng(constants.SEED).permutation(len(ids))]
    used = {
        record.text
        for record in runtime.read(state.get_runtime_path())
        if isinstance(record, runtime.IntakeReport) and record.provider == DEV_PROVIDER
    }
    community_of = {label["job_id"]: label["community_id"] for label in art.labels}
    for source_id in order:
        text = art.reports[source_id]
        if text in used:
            continue
        extraction = _flat_extraction(art.extraction[source_id])
        verified = verify_spans.verify(text, extraction)
        if kind == "needs_person":
            if not verified.needs_human:
                continue
        elif verified.needs_human or verified.safety_class != kind:
            continue
        failed = [f for f in verify_spans.REQUIRED_FIELDS if getattr(verified, f) is None]
        result = intake_llm.IntakeResult(
            extraction=extraction,
            verified=verified,
            status="needs_review" if failed else "extracted",
            provider=DEV_PROVIDER,
            model=DEV_MODEL,
            prompt_version=DEV_PROVIDER,
            latency_s=0.0,
            validation=f"{', '.join(failed)} evidence not found in the report"
            if failed
            else "verified",
            error=None,
        )
        draft = {
            **new_draft(),
            "text": text,
            "community_id": community_of[source_id],
            "reported_on": state.get_today(),
        }
        return _save(draft, result)[1]
    raise ValueError("no unused synthetic report left to replay")


def render(container) -> None:
    """Render and persist the current intake draft without any page-level model call."""
    draft = state.get_intake_draft()
    if draft is None:
        return
    art = state.artefacts()
    community_ids = sorted(art.communities)
    with container:
        st.subheader("New report")

        env_default = "none"
        try:
            env_default = intake_llm.configured() or "none"
        except ValueError:
            env_default = "none"
        options = ["none", "claude", "ollama"]
        provider_override = st.selectbox(
            "Extractor",
            options,
            index=options.index(st.session_state.get("intake_provider", env_default)),
            help=(
                "claude = Claude Sonnet through the logged-in claude CLI; ollama = the "
                "local model named in FAIR_TURN_OLLAMA_MODEL; none = intake disabled. "
                "The environment variable FAIR_TURN_PROVIDER sets the default."
            ),
        )
        st.session_state["intake_provider"] = provider_override

        example = st.pills("Load an example", list(EXAMPLE_REPORTS), selection_mode="single")
        if example is not None and example != draft["loaded_example"]:
            job_id = EXAMPLE_REPORTS[example]
            draft["text"] = art.reports[job_id]
            draft["community_id"] = _community_for(art, job_id)
            draft["reported_on"] = state.get_today()
            draft["result"] = None
            draft["loaded_example"] = example

        draft["text"] = st.text_area("Report text", value=draft["text"])
        selected = draft["community_id"] or community_ids[0]
        draft["community_id"] = st.selectbox(
            "Community", community_ids, index=community_ids.index(selected)
        )
        draft["reported_on"] = st.date_input(
            "Reported on",
            value=draft["reported_on"] or state.get_today(),
            help="dataset day",
        )
        st.caption("dataset day")

        error = ""
        if not draft["text"].strip():
            error = "Enter the report text."
        elif len(draft["text"]) > 4_000:
            error = "Report is over 4,000 characters."
        if error:
            st.markdown(f":red[{error}]")

        provider: str | None = None
        model = ""
        provider_reason = None
        if CALL_OVERRIDE is not None:
            # A test call takes the selected provider's name, defaulting to claude so the
            # Extract button is not blocked on the environment being unset in a test.
            provider = provider_override if provider_override != "none" else "claude"
            model = intake_llm.MODEL_FOR.get(provider, provider)
        else:
            provider = intake_llm.configured(override=provider_override)
            model = intake_llm.MODEL_FOR.get(provider, "") if provider else ""
            if provider is None:
                provider_reason = (
                    "Live intake is off: choose an extractor above (claude or ollama), or set "
                    "FAIR_TURN_PROVIDER before starting."
                )

        if provider_reason:
            st.info(provider_reason)
        extract_clicked = st.button(
            "Extract", disabled=bool(error) or provider is None or draft["result"] is not None
        )
        if extract_clicked:
            with st.status(f"Extracting with {provider} ({model})…") as status:
                result = intake_llm.extract(draft["text"], provider, call=CALL_OVERRIDE)
                draft["result"] = result
                status.update(
                    label=f"Extraction finished in {result.latency_s:.1f} s", state="complete"
                )

        result = draft["result"]
        if result is None:
            return
        st.table(_field_rows(result))
        if result.status == "not_extracted" and result.error:
            st.error(result.error)

        if result.status == "extracted":
            verified = result.verified
            community = art.communities[draft["community_id"]]
            preview = _preview_job(draft, verified, community)
            scored = scoring.rank(
                open_jobs(state.get_today()) + [preview], state.get_today(), state.get_lam()
            )
            proposed_rank = next(item.rank for item in scored if item.job.job_id == preview.job_id)
            placement = (
                "inside today's capacity" if proposed_rank <= _capacity_all() else "in the backlog"
            )
            st.caption(f"Proposed rank {proposed_rank}; {placement}.")
            action = "Add to ranked queue"
        else:
            action = "Send to review queue"
        if st.button(action):
            wrote, job_id = _save(draft, result)
            state.set_intake_draft(None)
            if wrote:
                st.success(
                    f"{job_id} added to the ranked queue."
                    if result.status == "extracted"
                    else f"{job_id} added to the review queue."
                )
            else:
                st.success("This report was already saved.")
