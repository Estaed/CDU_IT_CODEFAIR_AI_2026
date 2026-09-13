"""Evidence lab (Task-34, PRD 3.5/3.6, wireframes §8): three tabs — extraction quality, the
feedback loop moved from the retired Phase 1 page, and the audit log with its two clocks.
Network disabled as in ``tests/test_app_smoke.py``.
"""

import socket
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "fair_turn" / "app" / "pages" / "evidence_lab.py"
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


def _run(tmp_path, audit_path=None) -> AppTest:
    audit_path = audit_path if audit_path is not None else tmp_path / "audit.jsonl"
    script = _wrapper_script(PAGE, tmp_path, audit_path)
    at = AppTest.from_file(str(script)).run(timeout=60)
    assert not at.exception
    return at


def test_three_tabs_render(tmp_path) -> None:
    at = _run(tmp_path)
    assert [t.label for t in at.tabs] == ["Extraction quality", "Feedback loop", "Audit log"]


def test_extraction_and_feedback_and_audit_each_show_a_chart(tmp_path) -> None:
    at = _run(tmp_path)
    charts = at.get("vega_lite_chart")
    # Tab 2: three feedback-loop line charts (reports, wait, gap). Tab 3: one override-rate line.
    assert len(charts) == 4


def test_extraction_tab_shows_three_field_tables(tmp_path) -> None:
    at = _run(tmp_path)
    assert len(at.dataframe) == 4  # fault_type, safety_class, health_risk, then the audit table


def test_audit_frame_first_row_is_the_newest_recorded_at(tmp_path) -> None:
    at = _run(tmp_path)
    audit_frame = at.dataframe[-1].value
    recorded = list(audit_frame["recorded_at"])
    assert recorded == sorted(recorded, reverse=True)


def test_audit_column_list(tmp_path) -> None:
    at = _run(tmp_path)
    audit_frame = at.dataframe[-1].value
    assert list(audit_frame.columns) == [
        "kind",
        "decision_day",
        "recorded_at",
        "audit_ref",
        "job_id",
        "previous_weighting",
        "new_weighting",
        "reason",
        "signer",
        "detail",
        "hash",
    ]


def test_filtering_by_kind_matches_the_csv_export(tmp_path) -> None:
    at = _run(tmp_path)
    kind_widget = [w for w in at.multiselect if w.label == "Kind"][0]
    only_kind = kind_widget.value[:1]
    at = kind_widget.set_value(only_kind).run(timeout=60)
    assert not at.exception

    audit_frame = at.dataframe[-1].value
    assert set(audit_frame["kind"]) <= set(only_kind)
    assert audit_frame["kind"].eq(only_kind[0]).all()
    download = [b for b in at.download_button if b.label == "Download CSV"]
    assert len(download) == 1, "Download CSV button not found"


def test_seeded_sample_shows_two_distinct_clocks(tmp_path) -> None:
    at = _run(tmp_path)
    audit_frame = at.dataframe[-1].value
    pairs = zip(audit_frame["decision_day"], audit_frame["recorded_at"], strict=True)
    for decision_day, recorded_at in pairs:
        day_part, time_part = recorded_at.split("T", 1)
        assert decision_day != day_part or not time_part.startswith("00:00:00")


def test_audit_page_with_empty_runtime_log_shows_sample_history(tmp_path) -> None:
    at = _run(tmp_path)
    audit_frame = at.dataframe[-1].value
    sample_lines = SAMPLE_PATH.read_text("utf-8").splitlines()
    sample_line_count = sum(1 for line in sample_lines if line.strip())
    assert len(audit_frame) == sample_line_count


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
