"""PRD 3.2 Review queue: one job at a time, verbatim text beside the fields table, the
missing field named with its reason (never the rejected model value); a human sets it with
a reason and is told where the job lands. The reason comes from a chip, the name is typed
once per session and the clarification message is drafted from a template, so the common
review costs three clicks and no typing."""

from dataclasses import dataclass, replace
from datetime import date
from typing import Literal

import pandas as pd
import streamlit as st

from fair_turn.app import state, theme
from fair_turn.app.components import intro, ranking_table
from fair_turn.app.components.highlight import render, spans
from fair_turn.core import audit, constants, scoring, verify_spans
from fair_turn.core.types import FaultType, HealthRiskFactor, Job, SafetyClass
from fair_turn.data import runtime
from fair_turn.data.artefacts import Artefacts, extraction_for, to_jobs

NOT_FOUND_REASON = "the proposed source phrase was not found in the report"
NOT_EXTRACTED_REASON = "the field was not extracted"
FIELD_LABELS = {
    "fault_type": "fault type",
    "safety_class": "safety class",
    "health_risk": "health risk",
    "location_mentioned": "location mentioned",
    "crew_or_access_note": "crew/access note",
}
HUMAN_SETTABLE = {"fault_type": FaultType, "safety_class": SafetyClass}
TABLE_FIELDS = (
    "fault_type",
    "safety_class",
    "health_risk",
    "location_mentioned",
    "crew_or_access_note",
)
REASON_PRESETS = (
    "Report names the appliance",
    "Report describes the fault",
    "Tenant confirmed by phone",
    "Housing officer confirmed on site",
    "Photo attached to the report",
)
ANCHORING_CAPTION = (
    "The system does not suggest a value here. Showing its rejected guess would steer you, "
    "so you set the field from the report."
)
# field -> (what the report did not say, what to ask the tenant for)
CLARIFICATION_QUESTIONS = {
    "fault_type": ("what has broken", "which part of the house or appliance is faulty"),
    "safety_class": (
        "how urgent it is",
        "whether anyone is without power, water, cooling or a safe way in",
    ),
}
CLARIFICATION_FALLBACK = ("enough about the repair", "what has broken and how urgent it is")
CLARIFY_BOX_HEIGHT = 160


@dataclass(frozen=True)
class QueueItem:
    job_id: str
    community_id: str
    text: str
    kept: dict[str, str]  # field -> verified phrase
    values: dict[str, str | bool]  # field -> verified value, for the fields in kept
    missing: dict[str, str]  # required field -> reason it is not set
    source: Literal["build", "intake", "review_requested"]


def _field_words(field: str, value: str | bool) -> str:
    """A verified value in words: an enum's underscore joined with spaces, a boolean spelled
    out, free text left as it is."""
    if isinstance(value, bool):
        return "yes" if value else "no"
    return value.replace("_", " ")


def _kept_values(row) -> dict[str, str | bool]:
    return {field: evidence.value for field, evidence in row.kept.items() if ":" not in field}


def _kept_values_intake(verified: verify_spans.VerifiedExtraction) -> dict[str, str | bool]:
    candidates = {
        "fault_type": verified.fault_type,
        "safety_class": verified.safety_class,
        "location_mentioned": verified.location_mentioned,
        "crew_or_access_note": verified.crew_or_access_note,
    }
    return {field: value for field, value in candidates.items() if field in verified.kept}


def clarification_draft(missing_fields: tuple[str, ...], job_id: str) -> str:
    """The message to the tenant, from a template over the missing required fields. No model
    call: a drafted question the coordinator edits cannot be steered by the report it asks
    about, and the text stays inside ``core.wording`` limits."""
    pairs = [CLARIFICATION_QUESTIONS[f] for f in missing_fields if f in CLARIFICATION_QUESTIONS]
    if not pairs:
        pairs = [CLARIFICATION_FALLBACK]
    what = " and ".join(pair[0] for pair in pairs)
    question = " and ".join(pair[1] for pair in pairs)
    return (
        f"Hello, this is about repair {job_id}. Your report did not say {what}. "
        f"Could you tell us {question}? "
        "Reply to this message or call your Community Housing Officer."
    )


def _reason(field: str, dropped) -> str:
    return NOT_FOUND_REASON if field in dropped else NOT_EXTRACTED_REASON


def _build_items(art: Artefacts, today: date) -> list[QueueItem]:
    items = []
    for job in ranking_table.open_jobs(today):
        if not job.needs_human or job.job_id not in art.extraction:
            continue  # an intake job is listed by ``_intake_items``
        row = extraction_for(art, job.job_id)
        kept = {field: ev.evidence for field, ev in row.kept.items()}
        human_set = state.get_human_set(job.job_id)
        missing = {
            field: _reason(field, row.dropped)
            for field in verify_spans.REQUIRED_FIELDS
            if field not in kept and field not in human_set
        }
        if not missing:
            continue
        items.append(
            QueueItem(
                job.job_id,
                job.community_id,
                art.reports[job.job_id],
                kept,
                _kept_values(row),
                missing,
                "build",
            )
        )
    return items


def _intake_items() -> list[QueueItem]:
    items = []
    for rec in runtime.read(state.get_runtime_path()):
        if not isinstance(rec, runtime.IntakeReport):
            continue
        if rec.status == "not_extracted":
            reason = f"not extracted: {rec.validation}"
            missing = dict.fromkeys(verify_spans.REQUIRED_FIELDS, reason)
            kept: dict[str, str] = {}
            values: dict[str, str | bool] = {}
        elif rec.status == "needs_review":
            verified = verify_spans.verify(rec.text, rec.extraction or {})
            kept = dict(verified.kept)
            values = _kept_values_intake(verified)
            missing = {
                field: _reason(field, verified.dropped)
                for field in verify_spans.REQUIRED_FIELDS
                if field not in kept
            }
        else:
            continue
        items.append(
            QueueItem(rec.job_id, rec.community_id, rec.text, kept, values, missing, "intake")
        )
    return items


def _review_requested_items(art: Artefacts, today: date) -> list[QueueItem]:
    items = []
    jobs_by_id = {j.job_id: j for j in ranking_table.open_jobs(today)}
    for record in audit.read(state.get_audit_path()):
        if not (
            isinstance(record, audit.HumanSet)
            and record.field == "review_requested"
            and record.day == today
        ):
            continue
        job = jobs_by_id.get(record.job_id)
        if job is None:
            continue
        row = extraction_for(art, job.job_id)
        kept = {field: ev.evidence for field, ev in row.kept.items()}
        items.append(
            QueueItem(
                job.job_id,
                job.community_id,
                art.reports[job.job_id],
                kept,
                _kept_values(row),
                {"review_requested": f"sent to review: {record.reason}"},
                "review_requested",
            )
        )
    return items


def _queue(art: Artefacts, today: date) -> list[QueueItem]:
    return _build_items(art, today) + _intake_items() + _review_requested_items(art, today)


def _capacity_all() -> int:
    return (
        constants.CREWS_PER_REMOTE_REGION * len(constants.REMOTE_REGIONS) + constants.CREWS_TOWN
    ) * constants.JOBS_PER_CREW_DAY


def _table_records(item: QueueItem, human_set: dict[str, str]) -> list[dict[str, str]]:
    records = []
    for field in TABLE_FIELDS:
        label = FIELD_LABELS[field]
        if field == "health_risk":
            factors = {k: v for k, v in item.kept.items() if k.startswith("health_risk:")}
            names = sorted(k.split(":", 1)[1].replace("_", " ") for k in factors)
            value = ", ".join(names) or "—"
            phrase = "; ".join(sorted(factors.values())) or "—"
            badge = "Verified" if factors else "—"
        elif field in item.kept:
            phrase = item.kept[field]
            value = _field_words(field, item.values.get(field, phrase))
            badge = "Verified"
        elif field in human_set:
            value, phrase, badge = human_set[field], "—", "Set by coordinator"
        elif field in item.missing:
            value, phrase, badge = "—", item.missing[field], "Needs a human"
        else:
            value, phrase, badge = "—", "—", "—"
        records.append(
            {"Field": label, "Value": value, "Phrase or reason": phrase, "Status": badge}
        )
    return records


def _job_for_rank(
    art: Artefacts, item: QueueItem, chosen: dict[str, str], today: date
) -> tuple[Job, list[Job]]:
    """The job to score for the "Mark rankable" success line, and the pool to rank it
    against: today's open jobs plus itself. ``item`` may no longer be in ``open_jobs``
    once its human-set fields make it dispatchable (PRD 3.2), so the source is looked up
    in order: today's open jobs, a runtime intake report, the build labels; the job built
    from ``item`` alone is the last resort so the page always renders."""
    open_today = ranking_table.open_jobs(today)
    jobs_by_id = {j.job_id: j for j in open_today}
    if item.job_id in jobs_by_id:
        job = jobs_by_id[item.job_id]
        if chosen:
            job = replace(job, **chosen)
        jobs = [job if j.job_id == item.job_id else j for j in open_today]
        return job, jobs

    record = next(
        (
            r
            for r in runtime.read(state.get_runtime_path())
            if isinstance(r, runtime.IntakeReport) and r.job_id == item.job_id
        ),
        None,
    )
    if record is not None:
        community = art.communities[record.community_id]
        verified = verify_spans.verify(record.text, record.extraction or {})
        fault = chosen.get("fault_type", verified.fault_type)
        safety = chosen.get("safety_class", verified.safety_class)
        job = Job(
            job_id=item.job_id,
            community_id=record.community_id,
            is_remote=community["is_remote"] == "True",
            reported_on=record.reported_on,
            fault_type=FaultType(fault) if fault else None,
            safety_class=SafetyClass(safety) if safety else None,
            health_risk=frozenset(HealthRiskFactor(v) for v in verified.health_risk),
            logistics_factor=float(community["logistics_factor"]),
        )
        return job, [*open_today, job]

    build_job = next((j for j in to_jobs(art) if j.job_id == item.job_id), None)
    if build_job is not None:
        if chosen:
            build_job = replace(build_job, **chosen)
        return build_job, [*open_today, build_job]

    fault = chosen.get("fault_type")
    safety = chosen.get("safety_class")
    job = Job(
        job_id=item.job_id,
        community_id=item.community_id,
        is_remote=False,
        reported_on=today,
        fault_type=FaultType(fault) if fault else None,
        safety_class=SafetyClass(safety) if safety else None,
        health_risk=frozenset(),
        logistics_factor=0.0,
    )
    return job, [*open_today, job]


art = state.artefacts()
st.title("Review queue")
intro.purpose("review_queue")
st.caption(theme.PROVENANCE_LINE)
st.caption(
    "Jobs arrive here when a field has no matching words in the report, failed the schema, or was "
    "not extracted. The system never fills a field on its own."
)
st.caption(ANCHORING_CAPTION)

today = state.get_today()
queue = _queue(art, today)
n = len(queue)
focus = state.get_review_focus()  # set by the workspace "Needs a human" tab
if focus is not None:
    position = next((i for i, queued in enumerate(queue) if queued.job_id == focus), None)
    if position is not None:
        state.set_review_cursor(position)
    state.clear_review_focus()

if n == 0:
    st.success("All reports reviewed")
    if st.button("Open in workspace", key="open_empty"):
        st.switch_page("pages/workspace.py")
else:
    cursor = state.get_review_cursor() % n
    state.set_review_cursor(cursor)
    item = queue[cursor]
    human_set = state.get_human_set(item.job_id)
    st.progress((cursor + 1) / n, text=f"{cursor + 1} of {n} to review")

    fields_label = ", ".join(FIELD_LABELS.get(f, f) for f in item.missing) or "fields"
    st.header(
        f"Job {ranking_table.short_id(item.job_id)} · "
        f"{ranking_table.community_label(item.community_id)}"
        f" — {cursor + 1} of {n} — {fields_label} needs review"
    )

    nav_prev, nav_next = st.columns(2)
    with nav_prev:
        if st.button("Previous"):
            state.set_review_cursor((cursor - 1) % n)
            st.rerun()
    with nav_next:
        if st.button("Next"):
            state.set_review_cursor((cursor + 1) % n)
            st.rerun()

    st.markdown(render(item.text, spans(item.text, item.kept)))
    st.dataframe(
        pd.DataFrame(_table_records(item, human_set)),
        column_config={
            "Phrase or reason": st.column_config.TextColumn("Phrase or reason", width="large")
        },
        hide_index=True,
        width="stretch",
    )

    settable_missing = [f for f in item.missing if f in HUMAN_SETTABLE]
    chosen: dict[str, str] = {}
    for field in settable_missing:
        enum_cls = HUMAN_SETTABLE[field]
        options = ["—", *[e.value for e in enum_cls]]
        st.markdown("No matching words in the report. Set this field yourself, and say why.")
        choice = st.selectbox(
            f"Set {FIELD_LABELS[field]}", options, key=f"set_{field}_{item.job_id}"
        )
        if choice != "—":
            chosen[field] = choice

    actor = st.text_input("Your name", value=state.get_actor(), key=f"actor_{item.job_id}")
    if actor.strip():
        state.set_actor(actor)

    chip = st.pills(
        "Reason", REASON_PRESETS, selection_mode="single", key=f"reason_chip_{item.job_id}"
    )
    other = st.text_input("Other reason (optional)", value="", key=f"reason_{item.job_id}")
    reason = other.strip() or (chip or "")

    col_mark, col_open, col_leave = st.columns(3)
    with col_mark:
        mark_clicked = st.button("Mark rankable", key=f"mark_{item.job_id}")
    with col_open:
        if st.button("Open in workspace", key=f"open_{item.job_id}"):
            state.set_selected_job_id(item.job_id)
            st.switch_page("pages/workspace.py")
    with col_leave:
        leave_clicked = st.button("Leave in queue", key=f"leave_{item.job_id}")

    if mark_clicked:
        missing_unfilled = [f for f in settable_missing if f not in chosen]
        if not reason.strip():
            st.error("A reason is required.")
        elif missing_unfilled:
            labels = ", ".join(FIELD_LABELS[f] for f in missing_unfilled)
            st.error(f"Set a value for {labels}.")
        else:
            for field, value in chosen.items():
                state.set_human_set(item.job_id, field, value, actor, reason)
                audit.append(
                    state.get_audit_path(),
                    audit.HumanSet(
                        day=today,
                        job_id=item.job_id,
                        field=field,
                        value=value,
                        actor=actor,
                        reason=reason,
                    ),
                )
            lam = state.get_lam()
            _job, jobs = _job_for_rank(art, item, chosen, today)
            ranked = scoring.rank(jobs, today, lam)
            scored = next((s for s in ranked if s.job.job_id == item.job_id), None)
            if scored is not None:
                in_capacity = scored.rank <= _capacity_all()
                placement = "in today's list" if in_capacity else "in the backlog"
                st.success(f"{item.job_id} is now rank {scored.rank}, {placement}")
            else:
                st.success(f"{item.job_id} recorded.")

    # An expander, not a button that reveals the box: which job has a draft open would have to
    # live in session state, and no page reads it (tests/test_app_smoke.py). The draft is
    # written on every run, so the coordinator edits rather than types.
    with st.expander("Request clarification"):
        message = st.text_area(
            "Message to the tenant",
            value=clarification_draft(tuple(item.missing), item.job_id),
            height=CLARIFY_BOX_HEIGHT,
            key=f"clarify_msg_{item.job_id}",
        )
        if st.button("Send clarification", key=f"send_clarify_{item.job_id}"):
            if not message.strip():
                st.error("A reason is required.")
            else:
                audit.append(
                    state.get_audit_path(),
                    audit.HumanSet(
                        day=today,
                        job_id=item.job_id,
                        field="clarification_requested",
                        value=message,
                        actor=actor,
                        reason=message,
                    ),
                )
                st.success("Clarification requested.")

    if leave_clicked:
        state.set_review_cursor((cursor + 1) % n)
        st.rerun()

intro.about()
