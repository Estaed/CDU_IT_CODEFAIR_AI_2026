"""The review queue never shows a rejected model value, writes a human-set field only with
a reason, reports the resulting rank, and its cursor wraps at both ends. The reason may come
from a chip, the name is remembered across jobs, and the clarification message is drafted
from a template."""

import socket
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from fair_turn.app.components import ranking_table
from fair_turn.app.intake import _flat_extraction
from fair_turn.core import audit, capacity_sim, constants, decisions, wording
from fair_turn.data import artefacts, geography, runtime

ROOT = Path(__file__).resolve().parent.parent
REVIEW_QUEUE = ROOT / "fair_turn" / "app" / "pages" / "review_queue.py"


def _refuse(*args, **kwargs):
    raise RuntimeError("network disabled")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(socket, "socket", _refuse)


@pytest.fixture(scope="module")
def art() -> artefacts.Artefacts:
    return artefacts.load_all()


def _job_with_dropped_required_field(art: artefacts.Artefacts) -> tuple[str, str, str]:
    """Return ``(job_id, field, dropped_value)`` for a committed job whose model-proposed
    value for a required field failed span verification."""
    for label in art.labels:
        job_id = label["job_id"]
        row = art.extraction[job_id]
        if row.needs_human:
            for field in ("fault_type", "safety_class"):
                if field in row.dropped:
                    return job_id, field, row.dropped[field]
    raise AssertionError("no committed job has a dropped required field")


def _open_complete_job(art: artefacts.Artefacts) -> str:
    """The first job, by id, that is still open on the default day and has both required
    fields."""
    return _open_complete_jobs(art)[0]


def _request_reviews(tmp_path: Path, art: artefacts.Artefacts, n: int) -> None:
    """Send ``n`` open jobs back for review in the temporary audit log, so the queue holds
    enough jobs to page through whatever the committed extraction left unverified."""
    for job_id in _open_complete_jobs(art)[:n]:
        audit.append(
            tmp_path / "audit.jsonl",
            audit.HumanSet(
                day=constants.WINDOW_START + timedelta(days=constants.WINDOW_DAYS),
                job_id=job_id,
                field="review_requested",
                value="review",
                actor="coordinator",
                reason="Check the evidence before dispatch.",
            ),
        )


def _open_complete_jobs(art: artefacts.Artefacts) -> list[str]:
    """Jobs, by id, still open on the default day (the same capacity run as
    ``ranking_table.open_jobs``) with both required fields."""
    jobs = artefacts.to_jobs(art)
    today = constants.WINDOW_START + timedelta(days=constants.WINDOW_DAYS)
    result = capacity_sim.simulate(
        jobs,
        1.0,
        constants.WINDOW_START,
        (today - constants.WINDOW_START).days + 1,
        [
            capacity_sim.Closure(
                c["community_id"],
                date.fromisoformat(c["closed_from"]),
                date.fromisoformat(c["closed_to"]),
            )
            for c in art.closures
        ],
        geography.crews(art.communities),
        constants.JOBS_PER_CREW_DAY,
        constants.TRAVEL_DAY_KM,
        geography.sim_sites(art.communities),
    )
    return sorted(
        j.job_id
        for j in jobs
        if not j.needs_human
        and not decisions.is_make_safe(j)
        and j.reported_on <= today
        and result.completed_on[j.job_id] is None
    )


def _wrapper_script(tmp_path: Path) -> Path:
    """Point both the audit log and the runtime store at temporary paths (same technique as
    ``tests/test_page_job_card.py``) so the committed stores are never touched."""
    audit_path = tmp_path / "audit.jsonl"
    runtime_path = tmp_path / "runtime.jsonl"
    script = tmp_path / "review_queue_with_temp_stores.py"
    script.write_text(
        "from pathlib import Path\n"
        "from fair_turn.app import state\n"
        f'state.set_audit_path(Path(r"{audit_path}"))\n'
        f'state.set_runtime_path(Path(r"{runtime_path}"))\n'
        f'exec(compile(open(r"{REVIEW_QUEUE}", encoding="utf-8").read(), '
        f'r"{REVIEW_QUEUE}", "exec"))\n',
        encoding="utf-8",
    )
    return script


def _short(job_id: str) -> str:
    return ranking_table.short_id(job_id)


def _click_next(at: AppTest) -> AppTest:
    return next(b for b in at.button if b.label == "Next").click().run(timeout=60)


def _page_text(at: AppTest) -> str:
    chunks = []
    for kind in ("markdown", "text", "caption", "header"):
        chunks += [str(el.value) for el in getattr(at, kind)]
    for frame in at.dataframe:
        chunks.append(frame.value.to_csv())
    return "\n".join(chunks)


# --- the rejected value never renders --------------------------------------------------------


def test_dropped_value_never_appears_on_the_page(art, tmp_path) -> None:
    job_id, _field, dropped_value = _job_with_dropped_required_field(art)
    script = _wrapper_script(tmp_path)

    at = AppTest.from_file(str(script)).run(timeout=60)
    assert not at.exception

    while _short(job_id) not in at.header[0].value:
        at = _click_next(at)

    assert dropped_value not in _page_text(at)


FAULT_WORDS = {
    v.replace("_", " ")
    for v in (
        "electrical",
        "plumbing_water",
        "sewer_drainage",
        "cooling",
        "hot_water",
        "roof_structure",
        "doors_locks_security",
        "stove_cooking",
        "pests",
        "other",
    )
}
SAFETY_WORDS = {"immediate", "urgent", "routine"}


def test_value_column_shows_the_verified_value_not_the_source_phrase(tmp_path) -> None:
    at = AppTest.from_file(str(_wrapper_script(tmp_path))).run(timeout=60)
    n = int(at.header[0].value.split(" of ")[1].split(" — ")[0])
    found = False
    for _ in range(n):
        frame = at.dataframe[0].value
        for _, row in frame.iterrows():
            if row["Status"] != "Verified":
                continue
            if row["Field"] == "fault type":
                assert row["Value"] in FAULT_WORDS
                found = True
            elif row["Field"] == "safety class":
                assert row["Value"] in SAFETY_WORDS
                found = True
        if found:
            break
        at = _click_next(at)
    assert found, "no verified fault type or safety class field found in the queue"


def test_report_and_table_are_full_width_not_two_columns() -> None:
    text = REVIEW_QUEUE.read_text(encoding="utf-8")
    assert "left, right = st.columns(2)" not in text
    assert 'width="stretch"' in text


def test_queue_shows_progress_membership_rule_and_field_cue(tmp_path) -> None:
    at = AppTest.from_file(str(_wrapper_script(tmp_path))).run(timeout=60)

    assert not at.exception
    assert (
        'st.progress((cursor + 1) / n, text=f"{cursor + 1} of {n} to review")'
        in REVIEW_QUEUE.read_text(encoding="utf-8")
    )
    assert any(
        "Jobs arrive here when a field has no matching words" in caption.value
        for caption in at.caption
    )
    assert any(
        "No matching words in the report. Set this field yourself, and say why." in markdown.value
        for markdown in at.markdown
    )


# --- marking rankable --------------------------------------------------------------------------


def test_mark_rankable_writes_one_runtime_and_one_audit_record_and_reports_rank(
    art, tmp_path
) -> None:
    job_id, field, _dropped = _job_with_dropped_required_field(art)
    script = _wrapper_script(tmp_path)
    audit_path = tmp_path / "audit.jsonl"
    runtime_path = tmp_path / "runtime.jsonl"

    at = AppTest.from_file(str(script)).run(timeout=60)
    while _short(job_id) not in at.header[0].value:
        at = _click_next(at)

    at.selectbox(key=f"set_{field}_{job_id}").select_index(1).run(timeout=60)
    at.text_input(key=f"reason_{job_id}").set_value("coordinator judgement").run(timeout=60)
    at.button(key=f"mark_{job_id}").click().run(timeout=60)
    assert not at.exception

    runtime_records = runtime.read(runtime_path)
    assert len(runtime_records) == 1
    assert runtime_records[0].job_id == job_id
    assert runtime_records[0].field == field

    audit_records = audit.read(audit_path)
    assert len(audit_records) == 1
    assert isinstance(audit_records[0], audit.HumanSet)
    assert audit_records[0].job_id == job_id

    assert any("is now rank" in s.value for s in at.success)


def test_mark_rankable_with_empty_reason_writes_nothing_and_shows_error(art, tmp_path) -> None:
    job_id, field, _dropped = _job_with_dropped_required_field(art)
    script = _wrapper_script(tmp_path)
    audit_path = tmp_path / "audit.jsonl"
    runtime_path = tmp_path / "runtime.jsonl"

    at = AppTest.from_file(str(script)).run(timeout=60)
    while _short(job_id) not in at.header[0].value:
        at = _click_next(at)

    at.selectbox(key=f"set_{field}_{job_id}").select_index(1).run(timeout=60)
    at.button(key=f"mark_{job_id}").click().run(timeout=60)
    assert not at.exception

    assert at.error
    assert runtime.read(runtime_path) == []
    assert audit.read(audit_path) == []


def test_review_requested_job_without_missing_fields_reports_rank(art, tmp_path) -> None:
    job_id = _open_complete_job(art)
    script = _wrapper_script(tmp_path)
    script.write_text(
        script.read_text(encoding="utf-8").replace(
            "exec(compile(", "state.set_review_cursor(-1)\nexec(compile(", 1
        ),
        encoding="utf-8",
    )
    audit_path = tmp_path / "audit.jsonl"
    audit.append(
        audit_path,
        audit.HumanSet(
            day=date(2025, 12, 30),
            job_id=job_id,
            field="review_requested",
            value="review",
            actor="coordinator",
            reason="Check the evidence before dispatch.",
        ),
    )

    at = AppTest.from_file(str(script)).run(timeout=60)
    assert _short(job_id) in at.header[0].value

    at.text_input(key=f"reason_{job_id}").set_value("Review complete.").run(timeout=60)
    at.button(key=f"mark_{job_id}").click().run(timeout=60)

    assert not at.exception
    assert any("is now rank" in message.value for message in at.success)


# --- empty state -------------------------------------------------------------------------------


def test_empty_state_renders_when_every_missing_field_is_human_set(art, tmp_path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    runtime_path = tmp_path / "runtime.jsonl"
    prefill_lines = []
    for label in art.labels:
        row = art.extraction[label["job_id"]]
        if row.needs_human:
            for field in ("fault_type", "safety_class"):
                if field not in row.kept:
                    prefill_lines.append(
                        "state.set_human_set("
                        f'"{label["job_id"]}", "{field}", "electrical" if "{field}" == '
                        '"fault_type" else "routine", "coordinator", "prefilled")'
                    )

    script = tmp_path / "review_queue_prefilled.py"
    script.write_text(
        "from pathlib import Path\n"
        "from fair_turn.app import state\n"
        f'state.set_audit_path(Path(r"{audit_path}"))\n'
        f'state.set_runtime_path(Path(r"{runtime_path}"))\n' + "\n".join(prefill_lines) + "\n"
        f'exec(compile(open(r"{REVIEW_QUEUE}", encoding="utf-8").read(), '
        f'r"{REVIEW_QUEUE}", "exec"))\n',
        encoding="utf-8",
    )

    at = AppTest.from_file(str(script)).run(timeout=60)
    assert not at.exception
    assert any("All reports reviewed" in s.value for s in at.success)


# --- cursor wraps at both ends -------------------------------------------------------------


def test_previous_and_next_wrap_at_both_ends(art, tmp_path) -> None:
    _request_reviews(tmp_path, art, 2)
    script = _wrapper_script(tmp_path)

    at = AppTest.from_file(str(script)).run(timeout=60)
    assert not at.exception
    header = at.header[0].value
    n = int(header.split(" of ")[1].split(" — ")[0])

    at = next(b for b in at.button if b.label == "Previous").click().run(timeout=60)
    assert f"{n} of {n}" in at.header[0].value

    at = next(b for b in at.button if b.label == "Next").click().run(timeout=60)
    assert "1 of" in at.header[0].value


def test_a_focus_from_the_workspace_moves_the_cursor_once(art, tmp_path) -> None:
    _request_reviews(tmp_path, art, 3)
    at = AppTest.from_file(str(_wrapper_script(tmp_path))).run(timeout=60)
    assert int(at.header[0].value.split(" of ")[1].split(" — ")[0]) >= 3
    at = _click_next(_click_next(at))
    header_prefix = at.header[0].value.split(" — ")[0]  # "Job #644 · Top End R-02"
    short = header_prefix.split(" ")[1]
    third = next(
        label["job_id"] for label in art.labels if ranking_table.short_id(label["job_id"]) == short
    )

    script = _wrapper_script(tmp_path)
    body = script.read_text(encoding="utf-8")
    focus = f'state.set_review_focus("{third}")\n'
    script.write_text(body.replace("exec(", focus + "exec(", 1), encoding="utf-8")
    focused = AppTest.from_file(str(script)).run(timeout=60)
    assert not focused.exception
    assert focused.header[0].value.startswith(f"{header_prefix} — ")
    assert focused.session_state["review_cursor"] == 2
    assert focused.session_state["review_focus"] is None


# --- less typing: reason chips, a remembered name, a drafted clarification --------------------

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
MISSING_PHRASE = {"fault_type": "what has broken", "safety_class": "how urgent it is"}


def test_reason_chips_offer_the_presets_and_the_anchoring_caption_is_shown(tmp_path) -> None:
    at = AppTest.from_file(str(_wrapper_script(tmp_path))).run(timeout=60)

    assert not at.exception
    chips = next(p for p in at.pills if p.label == "Reason")
    assert tuple(chips.options) == REASON_PRESETS
    assert any(ANCHORING_CAPTION in caption.value for caption in at.caption)


def test_chip_is_the_reason_when_the_free_text_is_empty(art, tmp_path) -> None:
    job_id, field, _dropped = _job_with_dropped_required_field(art)
    runtime_path = tmp_path / "runtime.jsonl"

    at = AppTest.from_file(str(_wrapper_script(tmp_path))).run(timeout=60)
    while _short(job_id) not in at.header[0].value:
        at = _click_next(at)

    chip = REASON_PRESETS[2]
    at.selectbox(key=f"set_{field}_{job_id}").select_index(1).run(timeout=60)
    at.pills(key=f"reason_chip_{job_id}").set_value(chip).run(timeout=60)
    at.button(key=f"mark_{job_id}").click().run(timeout=60)
    assert not at.exception

    assert [r.reason for r in runtime.read(runtime_path)] == [chip]


def test_free_text_overrides_the_chip(art, tmp_path) -> None:
    job_id, field, _dropped = _job_with_dropped_required_field(art)
    runtime_path = tmp_path / "runtime.jsonl"

    at = AppTest.from_file(str(_wrapper_script(tmp_path))).run(timeout=60)
    while _short(job_id) not in at.header[0].value:
        at = _click_next(at)

    at.selectbox(key=f"set_{field}_{job_id}").select_index(1).run(timeout=60)
    at.pills(key=f"reason_chip_{job_id}").set_value(REASON_PRESETS[0]).run(timeout=60)
    at.text_input(key=f"reason_{job_id}").set_value("Tenant called back").run(timeout=60)
    at.button(key=f"mark_{job_id}").click().run(timeout=60)
    assert not at.exception

    assert [r.reason for r in runtime.read(runtime_path)] == ["Tenant called back"]


def test_the_name_is_remembered_on_the_next_job(art, tmp_path) -> None:
    _request_reviews(tmp_path, art, 2)
    at = AppTest.from_file(str(_wrapper_script(tmp_path))).run(timeout=60)
    assert int(at.header[0].value.split(" of ")[1].split(" — ")[0]) >= 2

    name_input = next(i for i in at.text_input if i.label == "Your name")
    at = name_input.set_value("Ngaire").run(timeout=60)
    at = _click_next(at)

    assert not at.exception
    assert next(i for i in at.text_input if i.label == "Your name").value == "Ngaire"


# --- the drafted clarification ----------------------------------------------------------------


def test_request_clarification_drafts_the_message_and_sends_it_as_the_reason(art, tmp_path) -> None:
    job_id, field, _dropped = _job_with_dropped_required_field(art)
    audit_path = tmp_path / "audit.jsonl"

    at = AppTest.from_file(str(_wrapper_script(tmp_path))).run(timeout=60)
    while _short(job_id) not in at.header[0].value:
        at = _click_next(at)

    assert any(e.label == "Request clarification" for e in at.get("expander"))

    draft = at.text_area(key=f"clarify_msg_{job_id}").value
    assert job_id in draft
    assert MISSING_PHRASE[field] in draft
    assert "Community Housing Officer" in draft
    assert wording.check(draft) == []
    assert audit.read(audit_path) == [], "drafting alone must record nothing"

    at = at.button(key=f"send_clarify_{job_id}").click().run(timeout=60)
    assert not at.exception

    records = audit.read(audit_path)
    assert len(records) == 1
    assert records[0].field == "clarification_requested"
    assert records[0].reason == draft
    assert any("Clarification requested." in message.value for message in at.success)


def test_clarification_draft_falls_back_when_no_required_field_is_missing(art, tmp_path) -> None:
    """A job sent back for review has no missing required field, so the draft asks the general
    question rather than naming one."""
    job_id = _open_complete_job(art)
    script = _wrapper_script(tmp_path)
    script.write_text(
        script.read_text(encoding="utf-8").replace(
            "exec(compile(", "state.set_review_cursor(-1)\nexec(compile(", 1
        ),
        encoding="utf-8",
    )
    audit.append(
        tmp_path / "audit.jsonl",
        audit.HumanSet(
            day=date(2025, 12, 30),
            job_id=job_id,
            field="review_requested",
            value="review",
            actor="coordinator",
            reason="Check the evidence before dispatch.",
        ),
    )

    at = AppTest.from_file(str(script)).run(timeout=60)
    assert not at.exception
    assert _short(job_id) in at.header[0].value

    draft = at.text_area(key=f"clarify_msg_{job_id}").value
    assert "enough about the repair" in draft
    assert wording.check(draft) == []


# --- an intake job sent to review ----------------------------------------------------------------


def test_an_intake_job_sent_to_review_renders_from_its_runtime_record(art, tmp_path) -> None:
    today = constants.WINDOW_START + timedelta(days=constants.WINDOW_DAYS)
    source = next(label for label in art.labels if not art.extraction[label["job_id"]].needs_human)
    job_id = runtime.next_job_id(label["job_id"] for label in art.labels)
    text = art.reports[source["job_id"]]
    runtime.append(
        tmp_path / "runtime.jsonl",
        runtime.IntakeReport(
            job_id,
            source["community_id"],
            today,
            text,
            _flat_extraction(art.extraction[source["job_id"]]),
            "extracted",
            "dev-replay",
            "test",
            "dev-replay",
            0.0,
            {"ok": True},
            "draft-review-intake",
            datetime.now(),
        ),
    )
    audit.append(
        tmp_path / "audit.jsonl",
        audit.HumanSet(today, job_id, "review_requested", "check", "coordinator", "Check it."),
    )
    script = _wrapper_script(tmp_path)
    body = script.read_text(encoding="utf-8")
    script.write_text(
        body.replace("exec(", f'state.set_review_focus("{job_id}")\nexec(', 1), encoding="utf-8"
    )

    at = AppTest.from_file(str(script)).run(timeout=60)
    assert not at.exception
    assert _short(job_id) in at.header[0].value
    assert "review_requested needs review" in at.header[0].value
