"""Provider and in-page intake tests for PRD sections 3.2 and 5."""

import importlib.util
import json
import socket
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from fair_turn.app import intake
from fair_turn.llm import intake as intake_llm

ROOT = Path(__file__).resolve().parent.parent
_provider_spec = importlib.util.spec_from_file_location(
    "intake_provider", ROOT / "tests/fakes/provider.py"
)
assert _provider_spec and _provider_spec.loader
_provider = importlib.util.module_from_spec(_provider_spec)
_provider_spec.loader.exec_module(_provider)
SAMPLE_TEXT = _provider.SAMPLE_TEXT
invalid_call = _provider.invalid_call
raising_call = _provider.raising_call
timeout_call = _provider.timeout_call
valid_call = _provider.valid_call
wrong_phrase_call = _provider.wrong_phrase_call


@pytest.mark.parametrize(
    ("call", "status", "validation"),
    [
        (valid_call, "extracted", "verified"),
        (wrong_phrase_call, "needs_review", "safety_class evidence not found in the report"),
        (invalid_call, "not_extracted", "schema invalid"),
        (raising_call, "not_extracted", "provider error"),
        (timeout_call, "not_extracted", "provider error"),
    ],
)
def test_extract_outcomes(call, status, validation) -> None:
    result = intake_llm.extract(SAMPLE_TEXT, "claude", call=call)
    assert result.status == status
    assert result.validation == validation


def test_rejected_value_stays_only_in_audit_extraction() -> None:
    result = intake_llm.extract(SAMPLE_TEXT, "claude", call=wrong_phrase_call)
    assert result.verified.safety_class is None
    assert result.extraction["safety_class"] == "immediate"


def test_configured_provider_states(monkeypatch) -> None:
    monkeypatch.delenv("FAIR_TURN_PROVIDER", raising=False)
    assert intake_llm.configured() is None
    monkeypatch.setenv("FAIR_TURN_PROVIDER", "claude")
    assert intake_llm.configured() == "claude"
    monkeypatch.setenv("FAIR_TURN_PROVIDER", "ollama")
    assert intake_llm.configured() == "ollama"
    monkeypatch.setenv("FAIR_TURN_PROVIDER", "junk")
    with pytest.raises(ValueError, match="junk"):
        intake_llm.configured()


def test_configured_override_wins_over_environment(monkeypatch) -> None:
    monkeypatch.setenv("FAIR_TURN_PROVIDER", "claude")
    assert intake_llm.configured(override="ollama") == "ollama"
    assert intake_llm.configured(override="none") is None
    with pytest.raises(ValueError, match="junk"):
        intake_llm.configured(override="junk")
    monkeypatch.delenv("FAIR_TURN_PROVIDER", raising=False)
    assert intake_llm.configured(override=None) is None
    assert intake_llm.configured(override="") is None


def _script(tmp_path) -> str:
    path = tmp_path / "intake_app.py"
    path.write_text(
        "import streamlit as st\n\n"
        "from fair_turn.app import intake, state\n\n"
        "state.set_audit_path(st.session_state['audit_path'])\n"
        "state.set_runtime_path(st.session_state['runtime_path'])\n"
        "if state.get_intake_draft() is None:\n"
        "    state.set_intake_draft(intake.new_draft())\n"
        "intake.render(st.container(border=True))\n",
        encoding="utf-8",
        newline="",
    )
    return str(path)


def test_provider_unset_disables_extract(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("FAIR_TURN_PROVIDER", raising=False)
    at = AppTest.from_file(_script(tmp_path))
    at.session_state["audit_path"] = tmp_path / "audit.jsonl"
    at.session_state["runtime_path"] = tmp_path / "runtime.jsonl"
    at.run(timeout=60)
    assert at.button[0].disabled
    assert "FAIR_TURN_PROVIDER" in at.info[0].value


def test_fake_submission_is_idempotent(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        socket, "socket", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError())
    )
    monkeypatch.setattr(intake, "CALL_OVERRIDE", valid_call)
    at = AppTest.from_file(_script(tmp_path))
    at.session_state["audit_path"] = tmp_path / "audit.jsonl"
    at.session_state["runtime_path"] = tmp_path / "runtime.jsonl"
    at.run(timeout=60)
    at.text_area[0].input(SAMPLE_TEXT).run(timeout=60)
    at.button[0].click().run(timeout=60)
    at.button[1].click().run(timeout=60)
    runtime_path = tmp_path / "runtime.jsonl"
    audit_path = tmp_path / "audit.jsonl"
    assert len(runtime_path.read_text("utf-8").splitlines()) == 1
    assert len(audit_path.read_text("utf-8").splitlines()) == 1

    row = json.loads(runtime_path.read_text("utf-8"))
    at.session_state["intake_draft"] = {
        **intake.new_draft(),
        "draft_token": row["draft_token"],
        "text": SAMPLE_TEXT,
        "result": intake_llm.extract(SAMPLE_TEXT, "claude", call=valid_call),
    }
    at.run(timeout=60)
    at.button[1].click().run(timeout=60)
    assert len(runtime_path.read_text("utf-8").splitlines()) == 1
    assert len(audit_path.read_text("utf-8").splitlines()) == 1


def test_provider_selectbox_and_example_pills_render(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("FAIR_TURN_PROVIDER", raising=False)
    at = AppTest.from_file(_script(tmp_path))
    at.session_state["audit_path"] = tmp_path / "audit.jsonl"
    at.session_state["runtime_path"] = tmp_path / "runtime.jsonl"
    at.run(timeout=60)
    assert at.selectbox[0].label == "Extractor"
    assert at.selectbox[0].options == ["none", "claude", "ollama"]
    assert at.button_group[0].options == list(intake.EXAMPLE_REPORTS)


def test_loading_an_example_fills_text_and_community(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("FAIR_TURN_PROVIDER", raising=False)
    at = AppTest.from_file(_script(tmp_path))
    at.session_state["audit_path"] = tmp_path / "audit.jsonl"
    at.session_state["runtime_path"] = tmp_path / "runtime.jsonl"
    at.run(timeout=60)
    label = "Cooling, Alice Springs"
    at.button_group[0].select(label).run(timeout=60)
    assert "aircon" in at.text_area[0].value
    assert at.selectbox[1].value == "Alice Springs"
    # The text stays editable after the example loads.
    at.text_area[0].input(at.text_area[0].value + " Edited.").run(timeout=60)
    assert at.text_area[0].value.endswith("Edited.")


def test_switching_provider_to_none_disables_extract(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("FAIR_TURN_PROVIDER", "claude")
    at = AppTest.from_file(_script(tmp_path))
    at.session_state["audit_path"] = tmp_path / "audit.jsonl"
    at.session_state["runtime_path"] = tmp_path / "runtime.jsonl"
    at.run(timeout=60)
    at.text_area[0].input(SAMPLE_TEXT).run(timeout=60)
    assert not at.button[0].disabled
    at.selectbox[0].select("none").run(timeout=60)
    assert at.button[0].disabled
    assert "FAIR_TURN_PROVIDER" in at.info[0].value


def test_runtime_record_carries_the_chosen_provider(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        socket, "socket", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError())
    )
    monkeypatch.setattr(intake, "CALL_OVERRIDE", valid_call)
    at = AppTest.from_file(_script(tmp_path))
    at.session_state["audit_path"] = tmp_path / "audit.jsonl"
    at.session_state["runtime_path"] = tmp_path / "runtime.jsonl"
    at.run(timeout=60)
    at.selectbox[0].select("ollama").run(timeout=60)
    at.text_area[0].input(SAMPLE_TEXT).run(timeout=60)
    at.button[0].click().run(timeout=60)
    at.button[1].click().run(timeout=60)
    row = json.loads((tmp_path / "runtime.jsonl").read_text("utf-8"))
    assert row["provider"] == "ollama"


def _replay_script(tmp_path, expr: str) -> str:
    path = tmp_path / "replay_app.py"
    path.write_text(
        "import streamlit as st\n\n"
        "from fair_turn.app import intake, state\n\n"
        "state.set_audit_path(st.session_state['audit_path'])\n"
        "state.set_runtime_path(st.session_state['runtime_path'])\n"
        f"job_id = {expr}\n"
        "st.text(f'job_id={job_id}')\n",
        encoding="utf-8",
        newline="",
    )
    return str(path)


def _run_replay(tmp_path, expr: str) -> AppTest:
    at = AppTest.from_file(_replay_script(tmp_path, expr))
    at.session_state["audit_path"] = tmp_path / "audit.jsonl"
    at.session_state["runtime_path"] = tmp_path / "runtime.jsonl"
    return at.run(timeout=60)


def _saved_job_id(at: AppTest) -> str:
    return next(t.value for t in at.text if t.value.startswith("job_id=")).removeprefix("job_id=")


@pytest.mark.parametrize("kind", ["immediate", "urgent", "routine"])
def test_simulate_incoming_replays_the_requested_safety_class(tmp_path, kind) -> None:
    at = _run_replay(tmp_path, f"intake.simulate_incoming({kind!r})")
    assert not at.exception
    job_id = _saved_job_id(at)
    row = json.loads((tmp_path / "runtime.jsonl").read_text("utf-8"))
    assert row["job_id"] == job_id
    assert row["extraction"]["safety_class"] == kind
    assert row["status"] == "extracted"


def test_simulate_incoming_needs_person_replays_a_report_missing_a_required_field(
    tmp_path,
) -> None:
    at = _run_replay(tmp_path, "intake.simulate_incoming('needs_person')")
    assert not at.exception
    row = json.loads((tmp_path / "runtime.jsonl").read_text("utf-8"))
    assert row["status"] == "needs_review"
    extraction = row["extraction"]
    assert extraction.get("fault_type") is None or extraction.get("safety_class") is None


def test_whitespace_error_keeps_text(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(intake, "CALL_OVERRIDE", valid_call)
    at = AppTest.from_file(_script(tmp_path))
    at.session_state["audit_path"] = tmp_path / "audit.jsonl"
    at.session_state["runtime_path"] = tmp_path / "runtime.jsonl"
    at.run(timeout=60)
    at.text_area[0].input("   ").run(timeout=60)
    assert "Enter the report text." in at.markdown[-1].value
    assert at.text_area[0].value == "   "
