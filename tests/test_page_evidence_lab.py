"""The audit history page (PRD 3.6). Moved from ``tests/test_pages_signoff_audit.py`` when
the Phase 1 sign-off page was retired (Task-30); skipped until Task-34 builds the evidence lab
and points them at it."""

import socket
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
AUDIT_LOG = ROOT / "fair_turn" / "app" / "pages" / "audit_log.py"
SAMPLE_PATH = ROOT / "data" / "audit" / "sample.jsonl"


def _refuse(*args, **kwargs):
    raise RuntimeError("network disabled")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(socket, "socket", _refuse)


def _wrapper_script(page: Path, tmp_path: Path, audit_path: Path) -> Path:
    """Point the audit log at a temporary path via ``state.set_audit_path`` before running the
    real page body, so the committed ``data/audit/`` log is never touched by a test."""
    script = tmp_path / f"{page.stem}_with_temp_audit.py"
    script.write_text(
        "from pathlib import Path\n"
        "from fair_turn.app import state\n"
        f'state.set_audit_path(Path(r"{audit_path}"))\n'
        f'exec(compile(open(r"{page}", encoding="utf-8").read(), r"{page}", "exec"))\n',
        encoding="utf-8",
        newline="",
    )
    return script


@pytest.mark.skip(reason="Task-34")
def test_audit_page_with_empty_runtime_log_shows_sample_history(tmp_path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    script = _wrapper_script(AUDIT_LOG, tmp_path, audit_path)

    at = AppTest.from_file(str(script)).run(timeout=60)

    assert not at.exception
    assert len(at.get("vega_lite_chart")) == 1
    sample_lines = SAMPLE_PATH.read_text("utf-8").splitlines()
    sample_line_count = sum(1 for line in sample_lines if line.strip())
    assert len(at.dataframe[0].value) == sample_line_count


@pytest.mark.skip(reason="Task-34")
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
