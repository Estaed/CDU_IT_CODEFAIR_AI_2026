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
from fair_turn.core.types import FaultType, Job, SafetyClass, ScoredJob
from fair_turn.data import policy, runtime
from fair_turn.data.artefacts import Artefacts

NOTHING_SELECTED = "Select a job from the list, the map, or the box above."
NO_PHRASE = "— No source phrase found"
NO_PASSAGE = "No policy passage found above the relevance threshold"
INDEX_UNAVAILABLE = "Policy index unavailable"
REASON_REQUIRED = "A reason is required."
SET_BY_COORDINATOR = "Set by coordinator"
IN_REVIEW = "In the review queue"
REPORT_CAPTION = "What the tenant reported"
FULL_PASSAGE = "Full passage"
REASON_PLACEHOLDER = "Why? e.g. crew already nearby, tenant called back"
PASSAGE_PREVIEW_CHARS = 400
CHECK_TITLE = "Check the AI's reading"
CHECK_CAPTION = "Read the report above. Are the fields the AI read from it right?"
CHECK_OK = "✓ Fields are right"
CHECK_FIX = "✗ Fix a field"
CHECK_IN_REVIEW = "This job needs a person first: open it in the Needs a human tab."
FIXABLE_FIELDS = {"fault_type": FaultType, "safety_class": SafetyClass}
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


def _select_label(job: Job) -> str:
    fault = _label(job.fault_type.value) if job.fault_type is not None else "fault type not set"
    return (
        f"{ranking_table.short_id(job.job_id)} · "
        f"{ranking_table.community_label(job.community_id)} · {fault}"
    )


def _select(options: list[str], selected: str | None, by_id: dict[str, Job]) -> str | None:
    """The keyboard path into the pane: one selectbox over every open job."""
    choice = st.selectbox(
        "Select job",
        options,
        index=options.index(selected) if selected in options else None,
        placeholder="Choose a job",
        format_func=lambda job_id: _select_label(by_id[job_id]),
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


def _report_block(art: Artefacts, job_id: str) -> None:
    """The tenant's own words first, with the source phrases highlighted and read out."""
    evidence = _evidence(art, job_id)
    with st.container(border=True):
        st.caption(REPORT_CAPTION)
        text = _report_text(art, job_id)
        st.markdown(highlight.render(text, highlight.spans(text, evidence)))
        legend = [
            f'- "{_text(phrase)}" → '
            f"{'household health risk' if field.startswith('health') else FIELD_FACTOR[field]}"
            f" → {_label(field)}"
            for field, phrase in sorted(evidence.items())
        ]
        if legend:
            st.caption("\n".join(legend))


def _check_line(check: audit.FieldCheck) -> str:
    at = f"{check.recorded_at.astimezone():%H:%M}"
    if check.decision == "confirmed":
        return f"✓ Checked by {check.actor} at {at}"
    return f"✗ Corrected {_label(check.field)} to {_label(check.value)} by {check.actor} at {at}"


def _fix_form(job_id: str, today: date) -> None:
    """The in-page correction: the field, a value from its enum, a reason and a name. Saved
    through the review queue's path (a runtime human-set field and its audit record) plus
    one ``FieldCheck``. Plain widgets, not ``st.form``, so the values follow the field."""
    with st.container(border=True):
        field = st.selectbox(
            "Field to fix", list(FIXABLE_FIELDS), format_func=_label, key=f"fieldfix_field_{job_id}"
        )
        value = st.selectbox(
            "New value",
            [e.value for e in FIXABLE_FIELDS[field]],
            format_func=_label,
            key=f"fieldfix_value_{job_id}_{field}",
        )
        reason = st.text_input("Why?", key=f"fieldfix_reason_{job_id}").strip()
        actor = st.text_input(
            "Your name", value=state.get_actor(), key=f"fieldfix_actor_{job_id}"
        ).strip()
        save, cancel = st.columns(2)
        if cancel.button("Cancel", key=f"fieldfix_cancel_{job_id}", width="stretch"):
            state.set_field_fix_job(None)
            st.rerun()
        if not save.button("Save correction", key=f"fieldfix_save_{job_id}", width="stretch"):
            return
        if not reason:
            st.error(REASON_REQUIRED)
            return
        actor = actor or "coordinator"
        state.set_actor(actor)
        state.set_human_set(job_id, field, value, actor, reason)
        path = state.get_audit_path()
        audit.append(path, audit.HumanSet(today, job_id, field, value, actor, reason))
        audit.append(
            path, audit.FieldCheck(today, job_id, "corrected", actor, reason, field, value)
        )
        state.set_field_fix_job(None)
        st.rerun()


def _check_block(job_id: str, today: date, in_review: bool) -> None:
    """✓ / ✗ on the model's reading of this job, placed after the report so the words it was
    read from are already on screen. No per-row approve and no "accept all" (PRD 3.1)."""
    with st.container(border=True):
        st.markdown(f"**{CHECK_TITLE}**")
        if in_review:
            st.caption(CHECK_IN_REVIEW)
            return
        st.caption(CHECK_CAPTION)
        ok, fix = st.columns(2)
        if ok.button(CHECK_OK, key=f"fieldcheck_ok_{job_id}", width="stretch"):
            audit.append(
                state.get_audit_path(),
                audit.FieldCheck(today, job_id, "confirmed", state.get_actor()),
            )
            state.set_field_fix_job(None)
            st.rerun()
        if fix.button(CHECK_FIX, key=f"fieldcheck_fix_{job_id}", width="stretch"):
            state.set_field_fix_job(job_id)
        if state.get_field_fix_job() == job_id:
            _fix_form(job_id, today)
        latest = audit.latest_checks(audit.read(state.get_audit_path()), today).get(job_id)
        if latest is not None:
            st.caption(_check_line(latest))


def _fields_expander(art: Artefacts, job_id: str, human_set: dict[str, str]) -> None:
    row = art.extraction.get(job_id)
    evidence = _evidence(art, job_id)
    with st.expander("Fields read from the report"):
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
                {
                    "Field": _label(field),
                    "Value": value,
                    "Source phrase": phrase,
                    "Status": status,
                }
            )
        st.table(pd.DataFrame(records, columns=["Field", "Value", "Source phrase", "Status"]))


def _preview(text: str) -> str:
    """The first ``PASSAGE_PREVIEW_CHARS`` characters, cut at a word boundary."""
    return f"{text[:PASSAGE_PREVIEW_CHARS].rsplit(' ', 1)[0]}…"


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
            with st.container(border=True):
                st.markdown(f"**{passage.title}**")
                st.caption(f"{passage.section} · effective {passage.effective_date}")
                if len(passage.text) > PASSAGE_PREVIEW_CHARS:
                    st.markdown(_text(_preview(passage.text)))
                    with st.popover(FULL_PASSAGE):
                        st.markdown(_text(passage.text))
                else:
                    st.markdown(_text(passage.text))


def _actions(job: Job, current: list[ScoredJob], cap: int, today: date, in_review: bool) -> None:
    with st.container(border=True):
        st.markdown("**Change this job's place** (every change needs a reason and is logged)")
        if in_review:
            st.caption("No changes here: this job is in the review queue.")
            return
        ids = [s.job.job_id for s in current]
        if job.job_id not in ids:
            st.caption("No changes here: this job is not in today's ranking.")
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

        actions: list[tuple[str, str, str]] = []
        displaced = None
        if rank <= cap:
            st.caption(
                "You can move this job up or down one place in today's list, "
                "or send it to the review queue."
            )
            if rank > 1:
                actions.append(("up", "↑ Up", "Move this job up one place in today's list"))
            if rank < len(ids):
                actions.append(("down", "↓ Down", "Move this job down one place in today's list"))
        elif cap > 0:
            displaced = ids[cap - 1]
            st.caption(
                "This job is in the backlog. You can promote it into today's list; "
                "the job at the last place moves to the backlog."
            )
            st.caption(
                f"Promoting puts this job at rank {cap} and moves "
                f"{ranking_table.short_id(displaced)} to the backlog."
            )
            actions.append(
                (
                    "promote",
                    "Promote",
                    "Promote this job into today's list at the last place",
                )
            )
        actions.append(("review", "To review", "Send this job to the review queue"))

        key = f"actions_{job_id}"
        with st.form(key):
            reason = st.text_input("Why?", key=f"{key}_reason", placeholder=REASON_PLACEHOLDER)
            clicked = None
            for column, (suffix, label, help_text) in zip(
                st.columns(len(actions)), actions, strict=True
            ):
                if column.form_submit_button(label, key=f"{key}_{suffix}", help=help_text):
                    clicked = suffix

        if clicked is not None and not reason.strip():
            st.error(REASON_REQUIRED)
        elif clicked == "up":
            move(rank - 1, reason.strip())
        elif clicked == "down":
            move(rank + 1, reason.strip())
        elif clicked == "promote":
            audit.append(audit_path, audit.Promotion(today, job_id, displaced, reason.strip()))
            state.set_hand_moves((*moves, HandMove(job_id, rank, cap, reason.strip())))
            st.rerun()
        elif clicked == "review":
            audit.append(
                audit_path,
                audit.HumanSet(
                    day=today,
                    job_id=job_id,
                    field=ranking_table.REVIEW_REQUESTED,
                    value=reason.strip(),
                    actor="coordinator",
                    reason=reason.strip(),
                ),
            )
            state.set_hand_moves(ranking_table.without_moves_for(moves, job_id))
            st.rerun()

        if any(m.job_id == job_id for m in moves) and st.button(
            "Undo move", key=f"undo_{job_id}", help="Undo my hand move on this job"
        ):
            state.set_hand_moves(ranking_table.without_moves_for(moves, job_id))
            st.rerun()


def _window_label(job: Job, today: date) -> str:
    """``day 3 of 5 d``; the make-safe window is hours, so it carries no day count."""
    if job.safety_class is None:
        return "—"
    window = ranking_table.window_text(job, today)
    return window if job.safety_class is SafetyClass.IMMEDIATE else f"day {window}"


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
    selected = _select(sorted(by_id), state.get_selected_job_id(), by_id)
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
    window = _window_label(job, today)
    community = ranking_table.community_label(job.community_id)
    st.subheader(f"Job {ranking_table.short_id(selected)} · {community}")
    _header_badges(job, in_review, human_set)
    st.caption(f"Registration {selected} · {fault} · {safety} · {window}")

    _report_block(art, selected)
    _check_block(selected, today, in_review)
    if in_review or scored is None:
        st.warning(IN_REVIEW)
    else:
        st.markdown("**Why it sits here.**")
        st.write(explain.why_sentence(scored, lam))
    st.caption("How the score is built")
    _summary_list(art, job, scored, today, _evidence(art, selected), human_set)
    _fields_expander(art, selected, human_set)
    _policy_expander(art, job)
    _actions(job, current, cap, today, in_review)
