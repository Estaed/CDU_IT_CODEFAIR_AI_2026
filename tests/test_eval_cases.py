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
PARTS = ("cases", "mutations", "ablation", "benchmark")


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


@needs_pdfs
@pytest.mark.skipif(not complete_outputs(), reason="live evaluation has not completed yet")
def test_each_new_part_replays_twice_with_no_keys_or_claude(tmp_path):
    runs = tmp_path / "runs"
    for cid in ("A-0142", *ALL_CASES):
        shutil.copytree(ROOT / "runs" / cid, runs / cid)
    shutil.copytree(EVAL, runs / "eval")
    env = {k: v for k, v in os.environ.items() if k not in ("TYPESAFE_API_KEY", "PATH")}
    env["PATH"] = str(Path(sys.executable).parent)
    env["READMARK_RUNS_DIR"] = str(runs)
    assert shutil.which("claude", path=env["PATH"]) is None
    # Benchmark release is checked below with an isolated destination, since the CLI writes
    # the project's committed CSVs. It has no live-model code path.
    for part in ("cases", "mutations", "ablation"):
        expected = (EVAL / f"{part}.json").read_bytes()
        for _ in range(2):
            subprocess.run([sys.executable, "-m", "readmark", "eval", "--part", part, "--replay"],
                           cwd=ROOT, env=env, capture_output=True, check=True, timeout=300)
            assert (runs / "eval" / f"{part}.json").read_bytes() == expected
            for cid in ALL_CASES:
                for name in ("view", "writer", "checks", "jev", "gate", "scan", "pairs", "dedup"):
                    assert (runs / cid / f"{name}.json").read_bytes() == (
                        ROOT / "runs" / cid / f"{name}.json").read_bytes()


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
def test_full_ablation_matches_gate_and_frozen_heldout_hash():
    cases = load(EVAL / "cases.json")["cases"]
    for cid in ALL_CASES:
        coverage = cases[cid]["gold_page_coverage"]
        gold = {"required_reading": coverage["covered"] + coverage["missed"]}
        final = case_ablation(cid, gold)[-1]
        assert final["gold_page_coverage"]["count"] == coverage["count"]
    record = assert_scoring_allowed(ROOT / "runs" / "H-01")
    assert hashlib.sha256((ROOT / "runs" / "H-01" / "view.json").read_bytes()).hexdigest() == (
        record["view_sha256"])
