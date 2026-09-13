"""New-report action embedded in the workspace flow (PRD sections 3.1, 3.2 and 5)."""

import uuid
from collections.abc import Callable
from datetime import datetime

import streamlit as st

from fair_turn.app import state
from fair_turn.app.components.ranking_table import open_jobs
from fair_turn.core import audit, constants, scoring
from fair_turn.core.types import FaultType, HealthRiskFactor, Job, SafetyClass
from fair_turn.data import runtime
from fair_turn.llm import intake as intake_llm

CALL_OVERRIDE: Callable | None = None


def new_draft() -> dict:
    """Return the one stateful draft that makes a retry idempotent."""
    return {
        "draft_token": uuid.uuid4().hex,
        "text": "",
        "community_id": None,
        "reported_on": None,
        "result": None,
    }


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


def render(container) -> None:
    """Render and persist the current intake draft without any page-level model call."""
    draft = state.get_intake_draft()
    if draft is None:
        return
    art = state.artefacts()
    community_ids = sorted(art.communities)
    with container:
        st.subheader("New report")
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
            provider, model = "fake", "fake"
        else:
            provider = intake_llm.configured()
            model = intake_llm.MODEL_FOR.get(provider, "") if provider else ""
            if provider is None:
                provider_reason = (
                    "Live intake is off: set FAIR_TURN_PROVIDER=claude and restart to enable it."
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
