"""Evaluation metrics on hand-computed fixtures, the seeded baseline, and the committed
eval artefact."""

import importlib.util
import json
from pathlib import Path

import pytest

from fair_turn.eval import baseline, metrics
from fair_turn.eval.metrics import EMPTY

ROOT = Path(__file__).resolve().parent.parent
EVAL = ROOT / "data" / "build" / "eval.json"

spec = importlib.util.spec_from_file_location("run_eval", ROOT / "scripts" / "run_eval.py")
run_eval = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_eval)


def test_prf_on_ten_items_counts_empty_as_a_miss_only() -> None:
    gold = ["a", "a", "a", "a", "b", "b", "b", "c", "c", "c"]
    pred = ["a", "a", "a", "b", "b", "b", EMPTY, "c", "a", EMPTY]
    # a: TP 3 (0-2), FP 1 (8), FN 1 (3)      -> P 3/4, R 3/4, F1 6/8 = 0.75
    # b: TP 2 (4-5), FP 1 (3), FN 1 (6)      -> P 2/3, R 2/3, F1 4/6
    # c: TP 1 (7),   FP 0,     FN 2 (8, 9)   -> P 1/1, R 1/3, F1 2/4 = 0.5
    # EMPTY is no class: had it been scored as one, the macro would average four classes.
    result = metrics.prf(gold, pred, ["a", "b", "c"])
    a, b, c = (result["per_class"][k] for k in "abc")
    assert (a["precision"], a["recall"], a["f1"]) == pytest.approx((0.75, 0.75, 0.75))
    assert (b["precision"], b["recall"], b["f1"]) == pytest.approx((2 / 3, 2 / 3, 2 / 3))
    assert (c["precision"], c["recall"], c["f1"]) == pytest.approx((1.0, 1 / 3, 0.5))
    assert [a["support"], b["support"], c["support"]] == [4, 3, 3]
    assert result["macro_precision"] == pytest.approx((0.75 + 2 / 3 + 1) / 3)  # 0.8056
    assert result["macro_recall"] == pytest.approx((0.75 + 2 / 3 + 1 / 3) / 3)  # 0.5833
    assert result["macro_f1"] == pytest.approx((0.75 + 2 / 3 + 0.5) / 3)  # 0.6389
    assert result["accuracy"] == pytest.approx(0.6)  # indices 0, 1, 2, 4, 5, 7
    # Wilson 1/1, z = 1.96: centre 2.9207/4.8415 = 0.6033, half 1.9207/4.8415 = 0.3967
    assert c["precision_ci"] == pytest.approx([0.2065, 1.0], abs=1e-4)
    # Wilson 3/4: centre 1.2302/1.9604 = 0.6275, half 0.6408/1.9604 = 0.3269
    assert a["recall_ci"] == pytest.approx([0.3006, 0.9544], abs=1e-4)


def test_multilabel_prf_scores_each_factor_as_presence() -> None:
    gold = [{"x"}, {"x", "y"}, set(), {"y"}]
    pred = [{"x"}, {"x"}, {"y"}, {"y"}]
    # x: TP 2, FP 0, FN 0 -> P 1, R 1, F1 1
    # y: TP 1 (3), FP 1 (2), FN 1 (1) -> P 1/2, R 1/2, F1 1/2
    # exact set: items 0 and 3 -> 2/4
    result = metrics.multilabel_prf(gold, pred, ["x", "y"])
    assert result["per_class"]["y"]["precision"] == pytest.approx(0.5)
    assert result["per_class"]["y"]["recall"] == pytest.approx(0.5)
    assert result["macro_f1"] == pytest.approx(0.75)
    assert result["exact_set_match"] == pytest.approx(0.5)


def _span(job: str, field: str, start: int, end: int) -> dict:
    return {"job_id": job, "field": field, "start": start, "end": end}


# The six scenarios of the SemEval-2013 Task 9.1 table, one each, in document "d":
# I exact match; II spurious; III missing; IV right bounds, wrong type;
# V overlapping bounds, right type; VI overlapping bounds, wrong type.
GOLD = [
    _span("d", "fault_type", 0, 10),  # I
    _span("d", "safety_class", 70, 80),  # III
    _span("d", "safety_class", 20, 30),  # IV
    _span("d", "fault_type", 90, 100),  # V
    _span("d", "safety_class", 110, 120),  # VI
]
PRED = [
    _span("d", "fault_type", 0, 10),  # I
    _span("d", "fault_type", 50, 60),  # II
    _span("d", "fault_type", 20, 30),  # IV
    _span("d", "fault_type", 90, 105),  # V
    _span("d", "fault_type", 112, 125),  # VI
]


def test_span_scores_on_the_semeval_scenarios() -> None:
    # exact:   COR 2 (I, IV), INC 2 (V, VI), SPU 1, MIS 1; ACT 5, POS 5 -> P = R = F1 = 2/5
    # partial: COR 2, PAR 2 -> (2 + 0.5 * 2) / 5 = 3/5 for P, R and F1
    result = metrics.span_scores(GOLD, PRED)
    assert result["counts"] == {"cor": 2, "overlap": 2, "spu": 1, "mis": 1, "act": 5, "pos": 5}
    exact, partial = result["exact"], result["partial"]
    assert (exact["precision"], exact["recall"], exact["f1"]) == pytest.approx((0.4, 0.4, 0.4))
    assert (partial["precision"], partial["recall"]) == pytest.approx((0.6, 0.6))
    assert partial["f1"] == pytest.approx(0.6)


def test_span_scores_divide_precision_by_act_and_recall_by_pos() -> None:
    # One more spurious span, and one in another document at gold's bounds: ACT 7, POS 5.
    # exact P = 2/7, R = 2/5, F1 = 2PR/(P+R) = (8/35)/(24/35) = 1/3; partial P 3/7, R 3/5
    pred = [*PRED, _span("d", "fault_type", 200, 210), _span("e", "fault_type", 0, 10)]
    result = metrics.span_scores(GOLD, pred)
    assert result["exact"]["precision"] == pytest.approx(2 / 7)
    assert result["exact"]["recall"] == pytest.approx(2 / 5)
    assert result["exact"]["f1"] == pytest.approx(1 / 3)
    assert result["partial"]["precision"] == pytest.approx(3 / 7)
    assert result["partial"]["recall"] == pytest.approx(3 / 5)
    # a gold span is matched once: a second prediction at the same bounds is spurious
    twice = metrics.span_scores([GOLD[0]], [PRED[0], PRED[0]])
    assert twice["counts"] == {"cor": 1, "overlap": 0, "spu": 1, "mis": 0, "act": 2, "pos": 1}


def test_substring_rate_on_four_rows() -> None:
    rows = [{"substring_ok": ok} for ok in (True, True, False, True)]
    result = metrics.substring_rate(rows)
    assert result["rate"] == pytest.approx(0.75) and result["n"] == 4
    assert result["rate_ci"] == pytest.approx([0.3006, 0.9544], abs=1e-4)  # Wilson 3/4, above
    assert metrics.substring_rate([])["rate_ci"] == [0.0, 1.0]


def test_baseline_learns_a_forty_item_fixture_deterministically() -> None:
    words = {"electrical": "power point sparking", "pests": "cockroaches under the sink"}
    texts, labels = [], []
    for i in range(20):
        for label, phrase in words.items():
            texts.append(f"report {i} the {phrase} again")
            labels.append(label)
    unseen = ["the power point is sparking", "cockroaches everywhere under the sink"]
    first = baseline.fit_predict(texts, labels, unseen)
    assert first == ["electrical", "pests"]
    assert baseline.fit_predict(texts, labels, unseen) == first


def _proportions(node, path: str = ""):
    if isinstance(node, dict):
        for key, value in node.items():
            if key in {"precision", "recall", "accuracy", "exact_set_match", "rate"}:
                yield f"{path}.{key}", value, node.get(f"{key}_ci")
            yield from _proportions(value, f"{path}.{key}")


@pytest.mark.skipif(not EVAL.exists(), reason="data/build/eval.json not written yet")
def test_committed_eval_carries_an_interval_on_every_proportion() -> None:
    result = json.loads(EVAL.read_text("utf-8"))
    assert result["n_holdout"] == 150 and result["f1_target"] == metrics.F1_TARGET
    assert set(result["target_met"]) == {"fault_type", "safety_class"}
    assert result["notes"]
    found = list(_proportions(result))
    assert len(found) > 50
    for path, value, ci in found:
        assert isinstance(ci, list) and len(ci) == 2, path
        assert 0.0 <= ci[0] <= value <= ci[1] <= 1.0, (path, value, ci)


@pytest.mark.skipif(not EVAL.exists(), reason="data/build/eval.json not written yet")
def test_committed_eval_matches_a_fresh_run() -> None:
    assert json.loads(EVAL.read_text("utf-8")) == run_eval.evaluate()
