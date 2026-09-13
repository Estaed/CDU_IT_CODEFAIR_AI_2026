"""The review queue never shows a rejected model value, writes a human-set field only with
a reason, reports the resulting rank, and its cursor wraps at both ends."""

import socket
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from fair_turn.core import audit
from fair_turn.data import artefacts, runtime

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

    while job_id not in at.header[0].value:
        at = _click_next(at)

    assert dropped_value not in _page_text(at)


# --- marking rankable --------------------------------------------------------------------------


def test_mark_rankable_writes_one_runtime_and_one_audit_record_and_reports_rank(
    art, tmp_path
) -> None:
    job_id, field, _dropped = _job_with_dropped_required_field(art)
    script = _wrapper_script(tmp_path)
    audit_path = tmp_path / "audit.jsonl"
    runtime_path = tmp_path / "runtime.jsonl"

    at = AppTest.from_file(str(script)).run(timeout=60)
    while job_id not in at.header[0].value:
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
    while job_id not in at.header[0].value:
        at = _click_next(at)

    at.selectbox(key=f"set_{field}_{job_id}").select_index(1).run(timeout=60)
    at.button(key=f"mark_{job_id}").click().run(timeout=60)
    assert not at.exception

    assert at.error
    assert runtime.read(runtime_path) == []
    assert audit.read(audit_path) == []


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
    script = _wrapper_script(tmp_path)

    at = AppTest.from_file(str(script)).run(timeout=60)
    assert not at.exception
    header = at.header[0].value
    n = int(header.split(" of ")[1].split(" — ")[0])
    if n < 2:
        pytest.skip("fewer than two committed jobs need review; wrap cannot be exercised")

    at = next(b for b in at.button if b.label == "Previous").click().run(timeout=60)
    assert f"{n} of {n}" in at.header[0].value

    at = next(b for b in at.button if b.label == "Next").click().run(timeout=60)
    assert "1 of" in at.header[0].value
