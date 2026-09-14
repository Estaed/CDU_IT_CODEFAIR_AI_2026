"""Evidence lab (Task-34, PRD 3.5/3.6, wireframes §8): three tabs — extraction quality, the
feedback loop moved from the retired Phase 1 page, and the audit log with its two clocks.
Network disabled as in ``tests/test_app_smoke.py``.
"""

import json
import socket
from datetime import datetime
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from fair_turn.data import artefacts

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "fair_turn" / "app" / "pages" / "evidence_lab.py"
SAMPLE_PATH = ROOT / "data" / "audit" / "sample.jsonl"
EVAL_PATH = ROOT / "data" / "build" / "eval.json"
EXTRACTION_PATH = ROOT / "data" / "build" / "extraction.json"


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


def test_what_to_do_here_list_renders(tmp_path) -> None:
    at = _run(tmp_path)
    text = "\n".join(m.value for m in at.markdown)
    assert "**What to do here**" in text
    assert "Extraction quality: how often the AI read a report correctly." in text
    assert "Feedback loop: what happens to remote reporting if only efficiency counts." in text
    assert "Audit log: every decision, who made it and when." in text


def test_empty_audit_log_says_how_rows_appear(tmp_path, monkeypatch) -> None:
    empty_dir = tmp_path / "no_sample"
    empty_dir.mkdir()
    monkeypatch.setattr(artefacts, "AUDIT_DIR", empty_dir)
    at = _run(tmp_path, audit_path=tmp_path / "missing_audit.jsonl")
    audit_tab = [tab for tab in at.tabs if tab.label == "Audit log"][0]
    assert any("Rows appear here once a report is signed" in i.value for i in audit_tab.get("info"))
    assert len(at.dataframe) == 3  # fault_type, safety_class, health_risk; no audit table


def test_three_tabs_render(tmp_path) -> None:
    at = _run(tmp_path)
    assert [t.label for t in at.tabs] == ["Extraction quality", "Feedback loop", "Audit log"]


def test_extraction_and_feedback_and_audit_each_show_a_chart(tmp_path) -> None:
    at = _run(tmp_path)
    charts = at.get("vega_lite_chart")
    # Tab 1: one macro-F1 bar chart. Tab 2: three feedback-loop line charts (reports, wait,
    # gap). Tab 3: one override-rate line.
    assert len(charts) == 5


def test_extraction_headline_metrics_read_from_eval_artefact(tmp_path) -> None:
    at = _run(tmp_path)
    ev = json.loads(EVAL_PATH.read_text("utf-8"))
    extraction_rows = json.loads(EXTRACTION_PATH.read_text("utf-8"))
    adversarial_count = sum(row["is_adversarial"] for row in extraction_rows)
    expected = {
        "Phrases verified": f"{ev['substring_rate']['rate']:.1%}",
        "Attacks resisted": f"{adversarial_count} of {adversarial_count}",
        "Fault type": f"{ev['extractor']['fault_type']['macro_f1']:.0%}",
        "Safety class": f"{ev['extractor']['safety_class']['macro_f1']:.0%}",
        "Health risk": f"{ev['extractor']['health_risk']['macro_f1']:.0%}",
    }
    metrics = {metric.label: metric for metric in at.metric}
    assert len(metrics) == 5
    assert {label: metric.value for label, metric in metrics.items()} == expected
    assert all(metric.proto.show_border for metric in metrics.values())
    rate_ci = ev["substring_rate"]["rate_ci"]
    assert metrics["Phrases verified"].help == (
        "How often a claim the AI made could be checked word-for-word against the "
        f"tenant's own report. Wilson interval: {rate_ci[0]:.1%} to {rate_ci[1]:.1%}."
    )
    field_help = (
        'Macro-F1 across classes on the 150-item held-out set. "Baseline" is a simple '
        "bag-of-words classifier used only for comparison, not the AI extractor this "
        "product uses."
    )

    def _accuracy_ci_text(field: str) -> str:
        extractor = ev["extractor"][field]
        match_key = "accuracy" if "accuracy_ci" in extractor else "exact_set_match"
        lo, hi = extractor[f"{match_key}_ci"]
        return (
            f"{field_help} The 95 % interval on {match_key.replace('_', ' ')} is {lo:.0%}–{hi:.0%}."
        )

    for field, label in (
        ("fault_type", "Fault type"),
        ("safety_class", "Safety class"),
    ):
        expected_delta = ev["extractor"][field]["macro_f1"] - ev["baseline"][field]["macro_f1"]
        assert metrics[label].delta == f"{expected_delta * 100:+.0f} pts"
        assert metrics[label].help == _accuracy_ci_text(field)
    assert metrics["Health risk"].delta == ""
    assert metrics["Health risk"].help == _accuracy_ci_text("health_risk")


def test_extraction_limitation_and_tables_are_in_expanders(tmp_path) -> None:
    at = _run(tmp_path)
    ev = json.loads(EVAL_PATH.read_text("utf-8"))
    artefact_date = datetime.fromtimestamp(EVAL_PATH.stat().st_mtime).date().isoformat()
    captions = [caption.value for caption in at.caption]
    assert (
        f"Build extractor: Claude Sonnet via claude -p (Part 2). Holdout: {ev['n_holdout']} items. "
        f"Evaluation artefact date: {artefact_date}."
    ) in captions
    assert (
        f"Target: {ev['f1_target']:.0%} on fault type and on safety class. Fault type: "
        f"{'met' if ev['target_met']['fault_type'] else 'not met'}; safety class: "
        f"{'met' if ev['target_met']['safety_class'] else 'not met'} "
        "(the model over-predicts immediate)."
    ) in captions
    expanders = [expander for expander in at.get("expander") if expander.label.endswith("by class")]
    assert [expander.label for expander in expanders] == [
        "Fault type, by class",
        "Safety class, by class",
        "Health risk, by class",
    ]
    assert len(at.dataframe) == 4  # fault_type, safety_class, health_risk, then the audit table
    field_frame = expanders[0].dataframe[0].value
    for column in (
        "class",
        "Extractor Precision",
        "Extractor Precision 95 % CI",
        "Extractor Recall",
        "Extractor Recall 95 % CI",
        "Extractor F1",
        "Baseline Precision",
        "Baseline Precision 95 % CI",
        "Baseline Recall",
        "Baseline Recall 95 % CI",
        "Baseline F1",
    ):
        assert column in field_frame.columns


def test_feedback_purpose_and_audit_chart_precede_audit_controls(tmp_path) -> None:
    at = _run(tmp_path)
    assert (
        "Replays the 90-day set twice, once efficiency-first and once at the chosen weighting, "
        "to show that an efficiency-only allocation makes remote demand look like it dried up."
    ) in [markdown.value for markdown in at.markdown]
    audit_tab = [tab for tab in at.tabs if tab.label == "Audit log"][0]
    audit_chart = at.get("vega_lite_chart")[-1]
    override_expander = [
        expander
        for expander in at.get("expander")
        if expander.label == "Override rate by decision day"
    ][0]
    assert audit_tab.children[0] is override_expander
    assert override_expander.proto.expanded is False
    assert audit_chart in override_expander.get("vega_lite_chart")


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


def test_seed_audit_signs_only_crew_jobs_and_sends_one_make_safe(tmp_path, monkeypatch) -> None:
    """Immediate jobs go to the make-safe contractor, never into a sign-off (PRD 3.1)."""
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    import seed_audit  # the script itself, not a package under fair_turn

    from fair_turn.core import audit

    monkeypatch.setattr(seed_audit, "AUDIT", tmp_path)
    seed_audit.main()
    records = audit.read(tmp_path / "sample.jsonl")
    labels = json.loads((ROOT / "data" / "build" / "labels.json").read_text("utf-8"))
    immediate = {label["job_id"] for label in labels if label["safety_class"] == "immediate"}
    sign_offs = [r for r in records if isinstance(r, audit.SignOff)]
    assert sign_offs
    for record in sign_offs:
        assert not immediate & set(record.ranked_job_ids)
        assert not immediate & set(record.today_job_ids)
    (make_safe,) = [r for r in records if isinstance(r, audit.MakeSafe)]
    assert make_safe.reason.strip()
    assert make_safe.job_id in immediate
