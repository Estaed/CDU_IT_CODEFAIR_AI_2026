"""Hand-counted rates, seal enforcement, cumulative layers and offline repeatability."""

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import needs_pdfs

from readmark import ROOT
from readmark.cache import Cache
from readmark.eval.cases import (
    ALL_CASES,
    case_ablation,
    load,
    mutation_ablation,
    mutation_metrics,
    page_coverage,
    release_benchmark,
    trap_touches,
)
from readmark.eval.discipline import (
    EvaluationWriter,
    assert_scoring_allowed,
    finish_heldout,
    start_heldout,
)
from readmark.writer import ClaudeWriter

EVAL = ROOT / "runs" / "eval"
PARTS = ("cases", "mutations", "ablation", "benchmark", "audit_labels", "checks_round2",
         "jev_supports")


def test_six_claim_catch_and_false_alarm_rates_by_hand():
    rows = [
        {"label": "contradicted", "mutation_type": "number_swap", "status": "quote_not_found"},
        {"label": "contradicted", "mutation_type": "number_swap", "status": "supported"},
        {"label": "unsupported", "mutation_type": "stale_value", "status": "contradicted"},
        {"label": "contradicted", "mutation_type": "negation", "status": "checker_disagrees"},
        {"label": "supported", "mutation_type": "none", "status": "supported"},
        {"label": "supported", "mutation_type": "none", "status": "quote_not_found"},
    ]
    result = mutation_metrics(rows)
    assert result["catch_rate"] == {"count": 3, "n": 4, "rate": 0.75}
    assert result["false_alarm_rate"] == {"count": 1, "n": 2, "rate": 0.5}
    assert result["by_mutation_type"]["number_swap"] == {"count": 1, "n": 2, "rate": 0.5}
    assert result["by_mutation_type"]["stale_value"] == {"count": 1, "n": 1, "rate": 1.0}
    assert mutation_metrics([])["catch_rate"] == {"count": 0, "n": 0, "rate": None}


def test_ablation_adds_only_the_layer_that_flags_a_claim():
    labels = [{"label": "contradicted", "mutation_type": kind} for kind in
              ("number_swap", "negation", "stale_value")]
    citations = [{"passage_id": "x:p1:1", "quote_found": True}]
    claims = [
        {"claim_id": "m01", "citations": citations, "values_missing": ["42"],
         "checker": {"verdict": "supports"}, "contradicted_by": []},
        {"claim_id": "m02", "citations": citations, "values_missing": [],
         "checker": {"verdict": "contradicts"}, "contradicted_by": []},
        {"claim_id": "m03", "citations": citations, "values_missing": [],
         "checker": {"verdict": "supports"}, "contradicted_by": ["x:p2:1"]},
    ]
    outputs = mutation_ablation({"labels": labels, "claims": claims})
    assert [r["catch_rate"]["count"] for r in outputs] == [0, 1, 2, 3, 3]
    assert [r["new_errors_caught"]["count"] for r in outputs] == [0, 1, 1, 1, 0]


def test_trap_touch_requires_the_fact_quote_and_its_clause():
    passages = {"x:p1:1": {"page": 1, "text": "Balance $10."},
                "x:p1:2": {"page": 1, "text": "Something unrelated."}}
    view = {"required_reading": [{"passage_id": "x:p1:2", "clause_ids": ["debt"]}],
            "suggested_reading": [{"passage_id": "x:p1:1", "clause_ids": ["debt"]}],
            "clauses": [{"clause_id": "income", "missing": [{"statement": "No income"}],
                         "coverage": "no_evidence_in_file"}]}
    facts = [
        {"fact_id": "f1", "trap": "stale_value", "clause_id": "debt", "page": "1",
         "quote": "Balance $10.", "role": "stale"},
        {"fact_id": "f2", "trap": "missing_doc", "clause_id": "income", "page": "",
         "quote": "", "role": "missing"},
    ]
    touches = trap_touches(view, facts, passages)
    assert touches[0]["required"] == [] and touches[0]["suggested"] == ["x:p1:1"]
    assert touches[1]["missing_evidence_flag"] and touches[1]["touched"]
    assert page_coverage([{"passage_id": "x:p1:1"}, {"passage_id": "x:p1:2"}],
                         ["p1", "p2"])["count"] == 1


def test_heldout_marker_blocks_second_run_and_premature_scoring(tmp_path):
    start_heldout(tmp_path)
    with pytest.raises(RuntimeError, match="already started"):
        start_heldout(tmp_path)
    with pytest.raises(RuntimeError, match="stay sealed"):
        assert_scoring_allowed(tmp_path)
    (tmp_path / "view.json").write_text("{}\n", encoding="utf-8")
    finish_heldout(tmp_path)
    record = assert_scoring_allowed(tmp_path)
    assert record["last_code_change_at"] <= record["code_frozen_at"] <= record["started_at"]
    (tmp_path / "view.json").write_text('{"changed": true}\n', encoding="utf-8")
    with pytest.raises(RuntimeError, match="view differs"):
        assert_scoring_allowed(tmp_path)


def test_changed_result_code_is_reported_without_rewriting_the_first_run(tmp_path, monkeypatch):
    import readmark.eval.discipline as discipline

    start_heldout(tmp_path)
    (tmp_path / 'view.json').write_text('{}\n', encoding='utf-8')
    finish_heldout(tmp_path)
    first_bytes = (tmp_path / 'evaluation.json').read_bytes()
    first = load(tmp_path / 'evaluation.json')
    changed = {**first['implementation_sha256'], 'readmark/checks/__init__.py': 'changed'}
    monkeypatch.setattr(discipline, 'implementation_pin', lambda: changed)
    (tmp_path / 'view.json').write_text('{"after": true}\n', encoding='utf-8')
    followup = assert_scoring_allowed(tmp_path)
    assert followup['scoring_label'] == 'after changes, not held-out'
    assert followup['changed_result_files'] == ['readmark/checks/__init__.py']
    assert followup['view_sha256'] == first['view_sha256']
    assert followup['scored_view_sha256'] != first['view_sha256']
    assert (tmp_path / 'evaluation.json').read_bytes() == first_bytes


def test_isolated_writer_keeps_the_original_prompt_and_cache_key(tmp_path, monkeypatch):
    import readmark.eval.discipline as discipline

    calls = []

    def fixed_call(prompt, model, schema):
        calls.append((prompt, model, schema))
        return {"model": "fixed", "output": {"facts": []}}

    monkeypatch.setattr(discipline, "call_claude", fixed_call)
    meta = {"case_id": "test", "pages": 1}
    EvaluationWriter(Cache(tmp_path, replay=False)).write(meta, [], [], {})
    # The standard writer finds the same response, even with its live executable disabled.
    assert ClaudeWriter(Cache(tmp_path, replay=True)).write(meta, [], [], {}) == {"facts": []}
    assert len(calls) == 1 and calls[0][1] == "opus"


def walk_numbers(node, path="summary"):
    if isinstance(node, dict):
        numbers = [k for k, v in node.items() if isinstance(v, (int, float))
                   and not isinstance(v, bool)]
        if numbers:
            assert "n" in node, f"{path}: {numbers} need n"
        for k, v in node.items():
            walk_numbers(v, f"{path}.{k}")
    elif isinstance(node, list):
        for v in node:
            assert not isinstance(v, (int, float)) or isinstance(v, bool)
            walk_numbers(v, path)


def test_every_summary_number_has_a_denominator():
    walk_numbers(load(EVAL / "summary.json"))
    with pytest.raises(AssertionError):
        walk_numbers({"required": 8})


def complete_outputs():
    return all((EVAL / f"{part}.json").exists() for part in PARTS)


def assert_replay_unchanged(actual, expected):
    """Only H-01's implementation list may lose the two deleted CDU source paths."""
    if actual.name not in {"cases.json", "summary.json"}:
        assert actual.read_bytes() == expected.read_bytes()
        return
    replay, baseline = load(actual), load(expected)
    replay_cases = replay["parts"]["cases"] if actual.name == "summary.json" else replay
    baseline_cases = baseline["parts"]["cases"] if actual.name == "summary.json" else baseline
    replay_pin = replay_cases["cases"]["H-01"]["heldout_discipline"]
    baseline_pin = baseline_cases["cases"]["H-01"]["heldout_discipline"]
    retired = {"readmark/checklist/lists/cdu-extension/clauses.yaml",
               "readmark/checklist/lists/cdu-extension/list.yaml"}
    assert replay_pin["changed_result_files"] == [p for p in baseline_pin["changed_result_files"]
                                                 if p not in retired]
    baseline_pin["changed_result_files"] = replay_pin["changed_result_files"]
    # Every other field, including every number and denominator, must remain exactly equal.
    assert replay == baseline


@needs_pdfs
@pytest.mark.skipif(not complete_outputs(), reason="live evaluation has not completed yet")
def test_each_new_part_replays_twice_with_no_keys_or_claude(tmp_path):
    runs = tmp_path / "runs"
    for cid in ALL_CASES:
        shutil.copytree(ROOT / "runs" / cid, runs / cid)
    shutil.copytree(EVAL, runs / "eval")
    env = {k: v for k, v in os.environ.items() if k not in ("TYPESAFE_API_KEY", "PATH")}
    env["PATH"] = str(Path(sys.executable).parent)
    env["READMARK_RUNS_DIR"] = str(runs)
    assert shutil.which("claude", path=env["PATH"]) is None
    # Benchmark release is checked below with an isolated destination, since the CLI writes
    # the project's committed CSVs. It has no live-model code path.
    for part in ("cases", "mutations", "ablation", None):
        name = part or 'audit_labels'  # summary assembly also rebuilds the labelled comparison
        expected = EVAL / f"{name}.json"
        for _ in range(2):
            command = [sys.executable, '-m', 'readmark', 'eval', '--replay']
            if part:
                command += ['--part', part]
            subprocess.run(command,
                           cwd=ROOT, env=env, capture_output=True, check=True, timeout=300)
            assert_replay_unchanged(runs / "eval" / f"{name}.json", expected)
            for cid in ALL_CASES:
                stages = ['view', 'writer', 'checks', 'jev', 'gate', 'scan', 'pairs', 'dedup']
                if cid in ('A-0142', 'H-01'):
                    stages += ['audit']
                if cid.startswith('E-'):
                    stages += ['mutations']
                for stage in stages:
                    assert (runs / cid / f"{stage}.json").read_bytes() == (
                        ROOT / "runs" / cid / f"{stage}.json").read_bytes()
    assert_replay_unchanged(runs / 'eval' / 'summary.json', EVAL / 'summary.json')
    assert (runs / 'eval' / 'checks_round2.json').read_bytes() == (
        EVAL / 'checks_round2.json').read_bytes()
    assert (runs / 'eval' / 'jev_supports.json').read_bytes() == (
        EVAL / 'jev_supports.json').read_bytes()


@pytest.mark.skipif(not complete_outputs(), reason="live evaluation has not completed yet")
def test_benchmark_csvs_rebuild_twice_and_match_sources(tmp_path, monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.setenv("PATH", str(Path(sys.executable).parent))
    assert shutil.which("claude") is None
    monkeypatch.setenv("READMARK_RUNS_DIR", str(tmp_path / "runs"))
    shutil.copytree(ROOT / "runs" / "H-01", tmp_path / "runs" / "H-01")
    for cid in ("A-0142", "E-01", "E-02", "E-03"):
        destination = tmp_path / "runs" / cid
        destination.mkdir(parents=True)
        shutil.copyfile(ROOT / "runs" / cid / "view.json", destination / "view.json")
    for attempt in ("first", "second"):
        release_benchmark(tmp_path / attempt)
        for name in ("facts.csv", "gold.csv", "mutations.csv"):
            assert (tmp_path / attempt / name).read_bytes() == (
                ROOT / "data" / "benchmark" / name).read_bytes()
    assert (tmp_path / "runs" / "eval" / "benchmark.json").read_bytes() == (
        EVAL / "benchmark.json").read_bytes()


@pytest.mark.skipif(not complete_outputs(), reason="live evaluation has not completed yet")
def test_full_ablation_matches_gate_and_records_the_current_heldout_hash():
    cases = load(EVAL / "cases.json")["cases"]
    for cid in ALL_CASES:
        coverage = cases[cid]["gold_page_coverage"]
        gold = {"required_reading": coverage["covered"] + coverage["missed"]}
        final = case_ablation(cid, gold)[-1]
        assert final["gold_page_coverage"]["count"] == coverage["count"]
    record = assert_scoring_allowed(ROOT / "runs" / "H-01")
    assert hashlib.sha256((ROOT / "runs" / "H-01" / "view.json").read_bytes()).hexdigest() == (
        record["scored_view_sha256"])
    assert record['scoring_label'] == 'after changes, not held-out'
    assert cases['H-01']['first_run'] == (
        load(EVAL / 'checks_round2.json')['before']['parts']['cases']['cases']['H-01'])
    assert cases['H-01']['first_run']['summary_audit']['flags'] == {
        'count': 14, 'n': 105, 'rate': 0.1333}


def test_round2_keeps_the_real_errors_and_labels_every_exempted_suggestion():
    comparison = load(EVAL / 'checks_round2.json')
    for claims in comparison['real_errors'].values():
        assert all(c['remains_flagged'] for c in claims)
    assert comparison['new_model_calls']['claude']['count'] == 0
    assert comparison['new_model_calls']['jev']['count'] == 0
    assert not any(c['lost_catch'] for c in comparison['mutation_changes'])
    labels = load(EVAL / 'audit_labels.json')
    assert labels['after_changes']['retained_by_label'] == {
        'real_summary_error': {'count': 1, 'n': 1, 'rate': 1.0},
        'file_inconsistency': {'count': 4, 'n': 4, 'rate': 1.0},
        'false_alarm': {'count': 4, 'n': 9, 'rate': 0.4444},
    }
    for cid, suggestions in comparison['suggestions'].items():
        audit = load(ROOT / 'runs' / cid / 'audit.json')
        assert suggestions['n'] == len(audit['claims'])
        assert suggestions['count'] == len(suggestions['claims'])
        for suggestion in suggestions['claims']:
            claim = next(c for c in audit['claims'] if c['claim_id'] == suggestion['claim_id'])
            assert claim['status'] == 'supported' and claim['checker']['verdict'] is None


def test_supports_comparison_keeps_baselines_and_reports_every_lost_catch():
    comparison = load(EVAL / 'jev_supports.json')
    first = load(EVAL / 'checks_round2.json')['before']['parts']['cases']['cases']['H-01']
    cases = load(EVAL / 'cases.json')['cases']
    labels = load(EVAL / 'audit_labels.json')
    assert comparison['first_run_h01'] == cases['H-01']['first_run'] == first
    assert labels['first_run'] == comparison['before']['audit_labels']['first_run']
    assert comparison['response_cache']['unchanged']
    assert comparison['response_cache']['new_model_calls']['count'] == 0
    for cid, old_rows in comparison['before']['mutations'].items():
        new = load(ROOT / 'runs' / cid / 'mutations.json')['claims']
        lost = {c['claim_id'] for old, c in zip(old_rows, new, strict=True)
                if old['label'] != 'supported' and old['status'] != 'supported'
                and c['status'] == 'supported'}
        reported = {c['claim_id'] for c in comparison['mutation_changes']
                    if c['case'] == cid and c['lost_catch']}
        assert lost == reported
    for cid, rows in comparison['real_errors'].items():
        audit = {c['claim_id']: c for c in load(ROOT / 'runs' / cid / 'audit.json')['claims']}
        for row in rows:
            claim = audit[row['claim_id']]
            assert row['remains_flagged'] == (claim['status'] != 'supported')
            assert {k: v for k, v in row['checker'].items() if k != 'n'} == claim['checker']
