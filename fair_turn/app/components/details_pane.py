"""The selected-job pane of the workspace (PRD 3.1, wireframes §3 and §9): why the job sits
where it does, the evidence behind each factor, the policy passages for its typed key, and
the coordinator's hand moves, each with a written reason."""

from datetime import date, datetime

import pandas as pd
import streamlit as st

from fair_turn.app import state
from fair_turn.app.components import highlight, ranking_table
from fair_turn.core import audit, explain, scoring
from fair_turn.core.batch import HandMove
from fair_turn.core.types import Job, ScoredJob
from fair_turn.data import policy, runtime
from fair_turn.data.artefacts import Artefacts

NOTHING_SELECTED = "Select a job from the list, the map, or the box above."
NO_PHRASE = "— No source phrase found"
NO_PASSAGE = "No policy passage found above the relevance threshold"
INDEX_UNAVAILABLE = "Policy index unavailable"
REASON_REQUIRED = "A reason is required."
SET_BY_COORDINATOR = "Set by coordinator"
IN_REVIEW = "In the review queue"
FIELD_FACTOR = {
    "fault_type": "safety",
    "safety_class": "safety",
    "location_mentioned": "context",
    "crew_or_access_note": "context",
}


@st.cache_resource
def _policy_index(build_dir: str) -> policy.PolicyIndex:
    """Loaded once per build folder; the argument is the cache key only."""
    return policy.load()


def _label(value: str) -> str:
    return str(value).replace("_", " ")


def _text(value: str) -> str:
    return highlight.render(value, [])


def _closed(art: Artefacts, community_id: str, today: date) -> bool:
    return any(
        c["community_id"] == community_id
        and date.fromisoformat(c["closed_from"]) <= today <= date.fromisoformat(c["closed_to"])
        for c in art.closures
    )


def _evidence(art: Artefacts, job_id: str) -> dict[str, str]:
    row = art.extraction.get(job_id)
    return {} if row is None else {field: ev.evidence for field, ev in row.kept.items()}


def _report_text(art: Artefacts, job_id: str) -> str:
    if job_id in art.reports:
        return art.reports[job_id]
    records = runtime.read(state.get_runtime_path())
    return next(
        (r.text for r in records if isinstance(r, runtime.IntakeReport) and r.job_id == job_id),
        "",
    )


def _select(options: list[str], selected: str | None) -> str | None:
    """The keyboard path into the pane: one selectbox over every open job."""
    choice = st.selectbox(
        "Select job",
        options,
        index=options.index(selected) if selected in options else None,
        placeholder="Choose a job",
    )
    if choice is not None and choice != selected:
        state.set_selected_job_id(choice)
        return choice
    return selected


def _map_choice(map_choice: tuple[str, list[str]] | None, selected: str | None) -> None:
    """Select one mapped job directly, or offer a compact chooser for several."""
    if map_choice is None:
        return
    community_id, job_ids = map_choice
    if selected in job_ids:
        return
    if len(job_ids) == 1:
        state.set_selected_job_id(job_ids[0])
        st.rerun()
    choice = st.selectbox(
        f"Choose a job at {community_id}",
        job_ids,
        index=None,
        placeholder="Pick a job",
        key=f"workspace_choose_{community_id}",
    )
    if choice is not None:
        state.set_selected_job_id(choice)
        st.rerun()


def _human_set_badges(human_set: dict[str, str]) -> None:
    for _field in sorted(human_set):
        st.badge(SET_BY_COORDINATOR, color="gray")


def _header_badges(job: Job, in_review: bool, human_set: dict[str, str]) -> None:
    """Render the non-interactive job statuses immediately below the pane heading."""
    colours = {"immediate": "red", "urgent": "orange", "routine": "gray"}
    with st.container(horizontal=True):
        if job.safety_class is not None:
            st.badge(job.safety_class.value.capitalize(), color=colours[job.safety_class.value])
        st.badge("Remote" if job.is_remote else "Town", color="gray")
        if in_review:
            st.badge("Needs a human", color="yellow")
        _human_set_badges(human_set)


def _factor_rows(
    art: Artefacts,
    job: Job,
    scored: ScoredJob | None,
    today: date,
    evidence: dict[str, str],
    human_set: dict[str, str],
) -> list[tuple[str, str, str]]:
    """Return the label, numeric value and provenance for the score summary list."""
    used = (today - job.reported_on).days
    rows = []
    if job.safety_class is None:
        rows.append(
            ("urgency", "—", "from NT window: Based on 1 of 2 fields (safety class missing)")
        )
    else:
        total = ranking_table.window_text(job, today).split(" of ", 1)[1].removesuffix(" d")
        rows.append(
            (
                "urgency",
                f"{scoring.urgency(job, today):.2f}",
                f"from NT window: {job.safety_class.value.capitalize()}, day {used} of {total}",
            )
        )

    safety_value = f"{scored.factors['safety']:.2f}" if scored is not None else "—"
    if "safety_class" in human_set:
        safety_source = _label(human_set["safety_class"])
    elif "safety_class" in evidence:
        safety_source = f'"{_text(evidence["safety_class"])}"'
    else:
        safety_source = NO_PHRASE
    rows.append(("safety", safety_value, safety_source))

    phrases = [phrase for field, phrase in sorted(evidence.items()) if field.startswith("health")]
    if phrases:
        health_source = "; ".join(f'"{_text(phrase)}"' for phrase in phrases)
    else:
        health_source = NO_PHRASE
    rows.append(("household health risk", f"{scoring.health_risk(job):.2f}", health_source))

    community = art.communities[job.community_id]
    access = "closed" if _closed(art, job.community_id, today) else "open"
    rows.append(
        (
            "logistics",
            f"{scoring.logistics(job):.2f}",
            f"from geography: {float(community['km_to_base']):.0f} km "
            f"{community['road_access']}, {access}",
        )
    )
    return rows


def _summary_list(
    art: Artefacts,
    job: Job,
    scored: ScoredJob | None,
    today: date,
    evidence: dict[str, str],
    human_set: dict[str, str],
) -> None:
    """Render the score and its factors as a scannable, bordered summary list."""
    score = f"{scored.score:.1f}" if scored is not None and scored.score is not None else "—"
    rows = [
        (
            "Score",
            score,
            "urgency + safety + household health risk - logistics",
        ),
        *_factor_rows(art, job, scored, today, evidence, human_set),
    ]
    with st.container(border=True):
        for label, value, source in rows:
            label_column, value_column, source_column = st.columns([2, 1, 4])
            label_column.markdown(f"**{label}**")
            value_column.markdown(value)
            source_column.markdown(source)


def _evidence_expander(art: Artefacts, job_id: str, human_set: dict[str, str]) -> None:
    evidence = _evidence(art, job_id)
    row = art.extraction.get(job_id)
    with st.expander("Evidence"):
        text = _report_text(art, job_id)
        st.markdown(highlight.render(text, highlight.spans(text, evidence)))
        legend = [
            f'- "{_text(phrase)}" → '
            f"{'household health risk' if field.startswith('health') else FIELD_FACTOR[field]}"
            f" → {_label(field)}"
            for field, phrase in sorted(evidence.items())
        ]
        if legend:
            st.markdown("\n".join(legend))
        fields = ["fault_type", "safety_class"]
        fields += sorted(field for field in evidence if field.startswith("health_risk:"))
        fields += ["location_mentioned", "crew_or_access_note"]
        records = []
        for field in fields:
            if field in human_set:
                value, phrase, status = _label(human_set[field]), "", SET_BY_COORDINATOR
            elif row is not None and field in row.kept:
                kept = row.kept[field]
                value, phrase, status = str(kept.value), kept.evidence, "Verified"
            elif row is not None and field in row.dropped:
                value, phrase, status = "", "", "Rejected, needs review"
            else:
                value, phrase, status = "", "", "Not found"
            records.append(
                {"field": _label(field), "value": value, "phrase": phrase, "status": status}
            )
        st.table(pd.DataFrame(records, columns=["field", "value", "phrase", "status"]))


def _policy_expander(art: Artefacts, job: Job) -> None:
    with st.expander("Policy reference"):
        index = _policy_index(str(policy.BUILD_DIR))
        if not index.available:
            st.info(INDEX_UNAVAILABLE)
            return
        passages = []
        if job.safety_class is not None:
            is_remote = art.communities[job.community_id]["is_remote"] == "True"
            passages = policy.lookup(index, job.safety_class.value, is_remote, job.fault_type)
        if not passages:
            st.caption(NO_PASSAGE)
            return
        for passage in passages:
            st.markdown(
                f"**{passage.title} — {passage.section} (effective {passage.effective_date})**"
            )
            st.markdown(_text(passage.text))


def _reason_form(key: str, label: str) -> str | None:
    """A reason field and a submit button; the reason, or None when nothing may be written."""
    with st.form(key):
        reason = st.text_input("Reason", key=f"{key}_reason")
        submitted = st.form_submit_button(label, key=f"{key}_submit")
    if not submitted:
        return None
    if not reason.strip():
        st.error(REASON_REQUIRED)
        return None
    return reason.strip()


def _actions(job: Job, current: list[ScoredJob], cap: int, today: date, in_review: bool) -> None:
    with st.container(border=True):
        st.markdown("**Actions**")
        if in_review:
            st.caption("Actions are disabled: this job is in the review queue.")
            return
        ids = [s.job.job_id for s in current]
        if job.job_id not in ids:
            st.caption("Actions are disabled: this job is not in today's ranking.")
            return
        job_id = job.job_id
        rank = ids.index(job_id) + 1
        moves = state.get_hand_moves()
        audit_path = state.get_audit_path()

        def move(to_rank: int, reason: str) -> None:
            audit.append(
                audit_path,
                audit.Override(today, job_id, rank, to_rank, reason, at=datetime.now()),
            )
            state.set_hand_moves((*moves, HandMove(job_id, rank, to_rank, reason)))
            st.rerun()

        if rank <= cap:
            if rank > 1 and (reason := _reason_form(f"move_up_{job_id}", "Move up")):
                move(rank - 1, reason)
            if rank < len(ids) and (reason := _reason_form(f"move_down_{job_id}", "Move down")):
                move(rank + 1, reason)
        elif cap > 0:
            displaced = ids[cap - 1]
            st.caption(
                f"Promoting puts this job at rank {cap} and moves {displaced} to the backlog."
            )
            if reason := _reason_form(f"promote_{job_id}", "Promote to today's list"):
                audit.append(audit_path, audit.Promotion(today, job_id, displaced, reason))
                state.set_hand_moves((*moves, HandMove(job_id, rank, cap, reason)))
                st.rerun()

        if reason := _reason_form(f"review_{job_id}", "Send to review"):
            audit.append(
                audit_path,
                audit.HumanSet(
                    day=today,
                    job_id=job_id,
                    field=ranking_table.REVIEW_REQUESTED,
                    value=reason,
                    actor="coordinator",
                    reason=reason,
                ),
            )
            state.set_hand_moves(ranking_table.without_moves_for(moves, job_id))
            st.rerun()

        if any(m.job_id == job_id for m in moves) and st.button(
            "Undo hand move", key=f"undo_{job_id}"
        ):
            state.set_hand_moves(ranking_table.without_moves_for(moves, job_id))
            st.rerun()


def render(
    art: Artefacts,
    jobs: list[Job],
    current: list[ScoredJob],
    cap: int,
    review_ids: set[str],
    today: date,
    lam: float,
    map_choice: tuple[str, list[str]] | None = None,
) -> None:
    """The pane for the selected job; ``jobs`` are the open jobs in the region, ``current``
    the ranking after hand moves, ``map_choice`` a community picked on the map."""
    by_id = {j.job_id: j for j in jobs}
    selected = _select(sorted(by_id), state.get_selected_job_id())
    _map_choice(map_choice, selected)
    if selected is None:
        st.info(NOTHING_SELECTED)
        return
    human_set = state.get_human_set(selected)
    job = by_id.get(selected)
    if job is None:
        st.subheader(selected)
        st.caption("This job is not open on this day or in this region.")
        _human_set_badges(human_set)
        return

    scored = next((s for s in current if s.job.job_id == selected), None)
    in_review = job.needs_human or selected in review_ids
    fault = _label(job.fault_type.value) if job.fault_type is not None else "—"
    safety = job.safety_class.value if job.safety_class is not None else "—"
    window = ranking_table.window_text(job, today) if job.safety_class is not None else "—"
    st.subheader(f"{selected} · {job.community_id}")
    _header_badges(job, in_review, human_set)
    st.caption(f"{fault} · {safety} · {window}")

    if in_review or scored is None:
        st.warning(IN_REVIEW)
    else:
        st.markdown("**Why it sits here.**")
        st.write(explain.why_sentence(scored, lam))
    _summary_list(art, job, scored, today, _evidence(art, selected), human_set)
    _evidence_expander(art, selected, human_set)
    _policy_expander(art, job)
    _actions(job, current, cap, today, in_review)
