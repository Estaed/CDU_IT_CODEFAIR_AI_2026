"""The job card shows what verified, invents nothing for a missing required field, and
records an override only when a reason is given."""

import socket
from datetime import timedelta
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from fair_turn.app.components import highlight, ranking_table
from fair_turn.core import audit, constants
from fair_turn.data import artefacts

ROOT = Path(__file__).resolve().parent.parent
JOB_CARD = ROOT / "fair_turn" / "app" / "pages" / "job_card.py"
LAST_DAY = constants.WINDOW_START + timedelta(days=constants.WINDOW_DAYS)
NOT_FOUND = "not found in report: fill in"


def _refuse(*args, **kwargs):
    raise RuntimeError("network disabled")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(socket, "socket", _refuse)


@pytest.fixture(scope="module")
def art() -> artefacts.Artefacts:
    return artefacts.load_all()


def _missing_fault_type_job(art: artefacts.Artefacts) -> str:
    for label in art.labels:
        row = art.extraction[label["job_id"]]
        if row.needs_human and "fault_type" not in row.kept:
            return label["job_id"]
    raise AssertionError("no committed job is missing fault_type")


def _fully_verified_open_job(art: artefacts.Artefacts) -> str:
    open_ids = {j.job_id for j in ranking_table.open_jobs(LAST_DAY)}
    for label in art.labels:
        job_id = label["job_id"]
        row = art.extraction[job_id]
        if not row.needs_human and row.substring_ok and len(row.kept) >= 3 and job_id in open_ids:
            return job_id
    raise AssertionError("no committed open job is fully verified with 3+ kept fields")


# --- highlight.py, pure unit tests -----------------------------------------------------------


def test_spans_finds_a_phrase_wrapped_across_whitespace() -> None:
    text = "The tap in the kitchen\nhas been leaking for days."
    found = highlight.spans(text, {"fault_type": "kitchen has been leaking"})
    assert found == [(15, 39, "fault_type")]
    assert " ".join(text[15:39].split()) == "kitchen has been leaking"


def test_spans_overlap_keeps_the_earlier_longer_span() -> None:
    text = "no hot water in the bathroom"
    found = highlight.spans(text, {"a": "hot water", "b": "hot water in the bathroom"})
    assert found == [(3, 28, "b")]
    assert text[3:28] == "hot water in the bathroom"


def test_render_escapes_markdown_control_characters() -> None:
    text = "Tenant wrote *urgent* re: the [meter] box."
    spans = highlight.spans(text, {"fault_type": "[meter] box"})
    rendered = highlight.render(text, spans)
    assert rendered == r"Tenant wrote \*urgent\* re: the **\[meter\] box**."
    assert "**" not in rendered.replace("**\\[meter\\] box**", "")


def test_render_with_no_spans_only_escapes() -> None:
    assert highlight.render("plain # text", []) == r"plain \# text"


# --- the page against committed artefacts ----------------------------------------------------


def test_missing_required_field_shows_not_found_and_no_invented_value(art) -> None:
    job_id = _missing_fault_type_job(art)
    at = AppTest.from_file(str(JOB_CARD)).run(timeout=60)
    assert not at.exception
    at.selectbox[0].select(job_id).run(timeout=60)
    assert not at.exception

    table = at.table[0].value
    fault_row = table[table["Field"] == "fault type"]
    assert list(fault_row["Source phrase"]) == [NOT_FOUND]
    for fault_value in ("electrical", "plumbing_water", "cooling", "hot_water"):
        assert fault_value not in fault_row["Source phrase"].iloc[0]
    assert at.warning  # not ranked


def test_verified_job_highlight_count_matches_kept_evidence(art) -> None:
    job_id = _fully_verified_open_job(art)
    row = art.extraction[job_id]
    report_text = art.reports[job_id]
    evidence = {field: ev.evidence for field, ev in row.kept.items()}
    expected_spans = highlight.spans(report_text, evidence)

    at = AppTest.from_file(str(JOB_CARD)).run(timeout=60)
    at.selectbox[0].select(job_id).run(timeout=60)
    assert not at.exception

    rendered = at.markdown[0].value
    assert rendered.count("**") == 2 * len(expected_spans)
    assert not at.warning  # ranked, not a human-queue job


# --- override: audit only written with a non-empty reason ------------------------------------


def _wrapper_script(tmp_path: Path) -> Path:
    """AppTest runs a script top to bottom; this launcher points the audit log at a
    temporary path (via ``state.set_audit_path``) before running the real page body, so the
    committed ``data/audit/`` log is never touched by the test."""
    audit_path = tmp_path / "audit.jsonl"
    script = tmp_path / "job_card_with_temp_audit.py"
    script.write_text(
        "from pathlib import Path\n"
        "from fair_turn.app import state\n"
        f'state.set_audit_path(Path(r"{audit_path}"))\n'
        f'exec(compile(open(r"{JOB_CARD}", encoding="utf-8").read(), r"{JOB_CARD}", "exec"))\n',
        encoding="utf-8",
    )
    return script


def test_override_with_empty_reason_writes_nothing(art, tmp_path) -> None:
    job_id = _fully_verified_open_job(art)
    script = _wrapper_script(tmp_path)
    audit_path = tmp_path / "audit.jsonl"

    at = AppTest.from_file(str(script)).run(timeout=60)
    at.selectbox[0].select(job_id).run(timeout=60)
    at.text_area[0].set_value("").run(timeout=60)
    at.button[0].click().run(timeout=60)
    assert not at.exception

    assert not audit_path.exists() or audit_path.read_text("utf-8").strip() == ""
    listing_before = sorted(p.name for p in artefacts.AUDIT_DIR.glob("*"))
    assert listing_before == sorted(p.name for p in artefacts.AUDIT_DIR.glob("*"))


def test_override_with_reason_appends_one_record(art, tmp_path) -> None:
    job_id = _fully_verified_open_job(art)
    script = _wrapper_script(tmp_path)
    audit_path = tmp_path / "audit.jsonl"
    listing_before = sorted(p.name for p in artefacts.AUDIT_DIR.glob("*"))

    at = AppTest.from_file(str(script)).run(timeout=60)
    at.selectbox[0].select(job_id).run(timeout=60)
    open_today = ranking_table.open_jobs(LAST_DAY)
    n = len(open_today)
    at.number_input[0].set_value(min(n, at.number_input[0].value + 1) or 1).run(timeout=60)
    at.text_area[0].set_value("crew already on site").run(timeout=60)
    at.button[0].click().run(timeout=60)
    assert not at.exception

    records = audit.read(audit_path)
    assert len(records) == 1
    assert isinstance(records[0], audit.Override)
    assert records[0].job_id == job_id
    assert records[0].reason == "crew already on site"
    assert sorted(p.name for p in artefacts.AUDIT_DIR.glob("*")) == listing_before
