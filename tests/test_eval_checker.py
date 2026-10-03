"""Checker evaluation (Task-08): the numbers on a hand-made set, the sample, every number beside
its n, and a byte-identical replay with no key and no ``claude``."""

import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from readmark import ROOT
from readmark.eval.checker import (
    agreement,
    calibration,
    claude_batches,
    confusion,
    rows_for,
    to_items,
    unsure_band,
)
from readmark.eval.summedits import SAMPLE_DIR, load_sample

EVAL = ROOT / "runs" / "eval"

# Ten hand-made pairs: (label, verdict, probability). Positive class = consistent (label 1).
HAND = [
    (1, "supports", 0.95),                # tp, bin 0.9-1.0, right
    (1, "supports", 0.85),                # tp, bin 0.8-0.9, right
    (1, "supports", 0.55),                # tp, bin 0.5-0.6, right
    (1, "not_enough_information", 0.62),  # fn, bin 0.6-0.7, wrong
    (0, "contradicts", 0.92),             # tn, bin 0.9-1.0, right
    (0, "contradicts", 0.81),             # tn, bin 0.8-0.9, right
    (0, "not_enough_information", 0.58),  # tn, bin 0.5-0.6, right
    (0, "supports", 0.97),                # fp, bin 0.9-1.0, wrong
    (0, "supports", 0.66),                # fp, bin 0.6-0.7, wrong
    (0, None, None),                      # no verdict: counts inconsistent -> tn, no probability
]


def hand_rows():
    sample = [{"sample_id": f"h{i}", "domain": "d1" if i < 5 else "d2", "label": label}
              for i, (label, _, _) in enumerate(HAND)]
    verdicts = {f"h{i}": {"claim_id": f"h{i}", "verdict": v, "probability": p}
                for i, (_, v, p) in enumerate(HAND) if v is not None}
    return rows_for(sample, verdicts)


def test_balanced_accuracy_matches_hand_count():
    # By hand: tp=3, fn=1, tn=4 (incl. no verdict), fp=2.
    # consistent recall 3/4 = 0.75; inconsistent recall 4/6 = 0.6667; balanced = 0.7083.
    c = confusion(hand_rows())
    assert (c["tp"], c["fn"], c["tn"], c["fp"]) == (3, 1, 4, 2)
    assert c["n"] == 10
    assert c["consistent_recall"] == 0.75
    assert c["inconsistent_recall"] == 0.6667
    assert c["balanced_accuracy"] == 0.7083
    assert c["accuracy"] == 0.7


def test_calibration_bins_match_hand_count():
    table = {row["bin"]: row for row in calibration(hand_rows())}
    # 0.9-1.0: 0.95 right, 0.92 right, 0.97 wrong -> n 3, accuracy 0.6667, mean 0.9467
    assert table["0.9-1.0"] == {"bin": "0.9-1.0", "n": 3, "accuracy": 0.6667,
                                "mean_probability": 0.9467}
    # 0.8-0.9: 0.85 and 0.81, both right
    assert table["0.8-0.9"] == {"bin": "0.8-0.9", "n": 2, "accuracy": 1.0,
                                "mean_probability": 0.83}
    # 0.6-0.7: 0.62 and 0.66, both wrong
    assert table["0.6-0.7"] == {"bin": "0.6-0.7", "n": 2, "accuracy": 0.0,
                                "mean_probability": 0.64}
    # 0.5-0.6: 0.55 and 0.58, both right
    assert table["0.5-0.6"] == {"bin": "0.5-0.6", "n": 2, "accuracy": 1.0,
                                "mean_probability": 0.565}
    assert table["0.0-0.1"] == {"bin": "0.0-0.1", "n": 0, "accuracy": None,
                                "mean_probability": None}
    assert table["no probability"] == {"bin": "no probability", "n": 1, "accuracy": 1.0}
    assert sum(row["n"] for row in table.values()) == 10


def test_unsure_band_and_agreement_on_hand_rows(monkeypatch):
    import readmark.eval.checker as checker

    monkeypatch.setattr(checker, "UNSURE_MIN_N", 3)
    band = unsure_band(hand_rows())
    # Target 70 %, at least 3 calls below t. Below 0.6: 2 calls (too few). Below 0.7 and 0.8:
    # 0.55 r, 0.58 r, 0.62 w, 0.66 w = 2/4 = 0.5. Below 0.9: also 0.81 r, 0.85 r = 4/6 = 0.6667,
    # still under 70 %, and the highest qualifying edge wins. Above 0.9: 0.92 r, 0.95 r, 0.97 w.
    assert band["found"] is True and band["below"] == 0.9
    assert (band["unsure_n"], band["unsure_accuracy"]) == (6, 0.6667)
    assert (band["sure_n"], band["sure_accuracy"]) == (3, 0.6667)
    by_edge = {c["below"]: c for c in band["cutoffs"]}
    assert (by_edge[0.7]["unsure_n"], by_edge[0.7]["unsure_accuracy"]) == (4, 0.5)
    assert (by_edge[0.6]["unsure_n"], by_edge[0.6]["sure_n"]) == (2, 7)

    a = {"x": {"verdict": "supports", "probability": 0.9},
         "y": {"verdict": "contradicts", "probability": 0.8}}
    b = {"x": {"verdict": "supports", "probability": 0.7},
         "y": {"verdict": "not_enough_information", "probability": 0.6}}
    ag = agreement(a, b, ["x", "y"])
    assert (ag["same_call"], ag["same_verdict"], ag["n"]) == (2, 1, 2)
    assert ag["mean_abs_probability_difference"] == 0.2


def test_sample_is_stratified_with_licence_and_citation():
    sample = load_sample()
    assert len(sample) >= 300
    strata = Counter((s["domain"], s["label"]) for s in sample)
    domains = {d for d, _ in strata}
    assert len(domains) == 10 and all(strata[(d, label)] > 0 for d in domains for label in (0, 1))
    assert len({s["sample_id"] for s in sample}) == len(sample)
    readme = (SAMPLE_DIR / "README.md").read_text(encoding="utf-8")
    assert "CC BY 4.0" in readme and "Laban" in readme and "huggingface.co" in readme


def test_claude_batches_never_pair_one_document_twice():
    items = to_items(load_sample())
    batches = claude_batches(items)
    assert sorted(i["claim_id"] for b in batches for i in b) == sorted(i["claim_id"] for i in items)
    for b in batches:
        docs = [i["passages"][0]["text"] for i in b]
        assert len(docs) == len(set(docs))


def walk(node, path="summary"):
    """Every dict holding a number also holds its n; no bare numbers in lists."""
    if isinstance(node, dict):
        numbers = [k for k, v in node.items()
                   if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if numbers:
            assert "n" in node, f"{path}: {numbers} without an n"
        for k, v in node.items():
            walk(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            assert not (isinstance(v, (int, float)) and not isinstance(v, bool)), \
                f"{path}[{i}] is a bare number"
            walk(v, f"{path}[{i}]")


def test_every_number_in_summary_sits_beside_its_n():
    summary = json.loads((EVAL / "summary.json").read_text(encoding="utf-8"))
    assert "checker" in summary["parts"]
    walk(summary)
    with pytest.raises(AssertionError):
        walk({"parts": {"x": {"accuracy": 0.5}}})


def test_replay_twice_is_byte_identical_without_key_or_claude(tmp_path):
    """The committed cache rebuilds checker.json byte for byte, twice, with no key and no claude
    on PATH (the repo's .env is the only other key source, and replay never reads a key)."""
    committed = (EVAL / "checker.json").read_bytes()
    env = {k: v for k, v in os.environ.items() if k not in ("TYPESAFE_API_KEY", "PATH")}
    env["PATH"] = str(Path(sys.executable).parent)
    assert shutil.which("claude", path=env["PATH"]) is None
    outputs = []
    for attempt in (1, 2):
        runs = tmp_path / f"runs{attempt}"
        shutil.copytree(EVAL / "cache", runs / "eval" / "cache")
        env["READMARK_RUNS_DIR"] = str(runs)
        subprocess.run([sys.executable, "-m", "readmark", "eval", "--part", "checker", "--replay"],
                       cwd=ROOT, env=env, check=True, capture_output=True)
        outputs.append((runs / "eval" / "checker.json").read_bytes())
    assert outputs[0] == outputs[1] == committed
