"""Sign-off writes a record only with both fields present, a lambda change after sign-off
writes a revision, and the audit page renders the sample history."""

import socket
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from fair_turn.core import audit

ROOT = Path(__file__).resolve().parent.parent
SIGN_OFF = ROOT / "fair_turn" / "app" / "pages" / "sign_off.py"
AUDIT_LOG = ROOT / "fair_turn" / "app" / "pages" / "audit_log.py"
SAMPLE_PATH = ROOT / "data" / "audit" / "sample.jsonl"


def _refuse(*args, **kwargs):
    raise RuntimeError("network disabled")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(socket, "socket", _refuse)


def _wrapper_script(page: Path, tmp_path: Path, audit_path: Path) -> Path:
    """Same technique as ``tests/test_page_job_card.py``: point the audit log at a temporary
    path via ``state.set_audit_path`` before running the real page body, so the committed
    ``data/audit/`` log is never touched by a test."""
    script = tmp_path / f"{page.stem}_with_temp_audit.py"
    script.write_text(
        "from pathlib import Path\n"
        "from fair_turn.app import state\n"
        f'state.set_audit_path(Path(r"{audit_path}"))\n'
        f'exec(compile(open(r"{page}", encoding="utf-8").read(), r"{page}", "exec"))\n',
        encoding="utf-8",
    )
    return script


# --- sign-off page ------------------------------------------------------------------------


def test_sign_off_with_empty_fields_writes_nothing(tmp_path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    script = _wrapper_script(SIGN_OFF, tmp_path, audit_path)

    at = AppTest.from_file(str(script)).run(timeout=60)
    at.text_area[0].set_value("").run(timeout=60)
    at.text_input[0].set_value("").run(timeout=60)
    at.button[0].click().run(timeout=60)

    assert not at.exception
    assert at.error
    assert not audit_path.exists() or audit_path.read_text("utf-8").strip() == ""


def test_sign_off_with_reason_and_signer_writes_one_record_and_flips_signed_today(
    tmp_path,
) -> None:
    audit_path = tmp_path / "audit.jsonl"
    script = _wrapper_script(SIGN_OFF, tmp_path, audit_path)

    at = AppTest.from_file(str(script)).run(timeout=60)
    at.text_area[0].set_value("weekly sign-off").run(timeout=60)
    at.text_input[0].set_value("R. Coordinator").run(timeout=60)
    at.button[0].click().run(timeout=60)

    assert not at.exception
    records = audit.read(audit_path)
    assert len(records) == 1
    assert isinstance(records[0], audit.SignOff)
    assert records[0].reason == "weekly sign-off"
    assert records[0].signer == "R. Coordinator"

    # session_state persists across reruns of the same AppTest instance, so re-running the
    # same session (not a new AppTest) is what re-executes the page with signed_today=True.
    at.run(timeout=60)
    assert any("Already signed off" in i.value for i in at.info)


def _wrapper_script_with_lambda_trigger(tmp_path: Path, audit_path: Path) -> Path:
    """Sign-off page plus a test-only button that calls ``state.set_lam`` afterwards, in the
    same script so the interaction happens inside one AppTest session (session_state, and
    therefore ``signed_today``, does not carry over between separate AppTest instances)."""
    script = tmp_path / "sign_off_with_lambda_trigger.py"
    script.write_text(
        "from pathlib import Path\n"
        "import streamlit as st\n"
        "from fair_turn.app import state\n"
        f'state.set_audit_path(Path(r"{audit_path}"))\n'
        f'exec(compile(open(r"{SIGN_OFF}", encoding="utf-8").read(), r"{SIGN_OFF}", "exec"))\n'
        'if st.button("test: change lambda"):\n'
        "    state.set_lam(0.5)\n",
        encoding="utf-8",
    )
    return script


def test_lambda_change_after_sign_off_writes_one_revision(tmp_path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    script = _wrapper_script_with_lambda_trigger(tmp_path, audit_path)

    at = AppTest.from_file(str(script)).run(timeout=60)
    at.text_area[0].set_value("weekly sign-off").run(timeout=60)
    at.text_input[0].set_value("R. Coordinator").run(timeout=60)
    at.button[0].click().run(timeout=60)  # the sign-off form's submit button
    assert len(audit.read(audit_path)) == 1  # the sign-off only, so far

    at.button[1].click().run(timeout=60)  # the test-only lambda-change trigger

    records = audit.read(audit_path)
    revisions = [r for r in records if isinstance(r, audit.Revision)]
    assert len(revisions) == 1
    assert revisions[0].old_lam == 1.0
    assert revisions[0].new_lam == 0.5


# --- audit log page ------------------------------------------------------------------------


def test_audit_page_with_empty_runtime_log_shows_sample_history(tmp_path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    script = _wrapper_script(AUDIT_LOG, tmp_path, audit_path)

    at = AppTest.from_file(str(script)).run(timeout=60)

    assert not at.exception
    assert len(at.get("vega_lite_chart")) == 1
    sample_lines = SAMPLE_PATH.read_text("utf-8").splitlines()
    sample_line_count = sum(1 for line in sample_lines if line.strip())
    assert len(at.dataframe[0].value) == sample_line_count


def test_seed_audit_script_is_idempotent(tmp_path, monkeypatch) -> None:
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    import seed_audit  # the script itself, not a package under fair_turn

    monkeypatch.setattr(seed_audit, "AUDIT", tmp_path)
    seed_audit.main()
    first = (tmp_path / "sample.jsonl").read_bytes()
    seed_audit.main()
    second = (tmp_path / "sample.jsonl").read_bytes()
    assert first == second
