"""Report tables export (Task-21 acceptance criteria)."""

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import export_report_tables as ert  # noqa: E402

pytestmark = pytest.mark.skipif(
    not (ert.BUILD / "labels.json").exists(), reason="data/build/labels.json absent"
)

FILES = (
    "extraction_vs_baseline.md",
    "span_scores.md",
    "substring_rate.md",
    "adversarial.md",
    "price_of_fairness.csv",
    "feedback_loop.csv",
    "dataset_summary.md",
)


@pytest.fixture(scope="module")
def exported(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("report")
    ert.main(out)
    return out


def test_seven_files_written(exported: Path) -> None:
    for name in FILES:
        assert (exported / name).is_file(), name


def test_rerun_is_byte_identical(exported: Path, tmp_path_factory) -> None:
    rerun = tmp_path_factory.mktemp("report_rerun")
    ert.main(rerun)
    for name in FILES:
        assert (exported / name).read_bytes() == (rerun / name).read_bytes(), name


def test_committed_files_match_a_fresh_run(exported: Path) -> None:
    committed = ROOT / "data" / "build" / "report"
    for name in FILES:
        assert (committed / name).read_bytes() == (exported / name).read_bytes(), name


def test_price_of_fairness_gap_shrinks_toward_equity(exported: Path) -> None:
    with (exported / "price_of_fairness.csv").open(newline="", encoding="utf-8") as f:
        rows = {r["lam"]: r for r in csv.DictReader(f)}
    assert set(rows) == {f"{i / 10:.1f}" for i in range(11)}
    gap_full_efficiency = float(rows["1.0"]["gap"])
    gap_full_equity = float(rows["0.0"]["gap"])
    assert gap_full_equity <= gap_full_efficiency


def test_extraction_vs_baseline_matches_eval_json(exported: Path) -> None:
    ev = json.loads((ert.BUILD / "eval.json").read_text("utf-8"))
    text = (exported / "extraction_vs_baseline.md").read_text("utf-8")
    for field in ("fault_type", "safety_class", "health_risk"):
        assert f"{ev['extractor'][field]['macro_f1']:.3f}" in text
        if field in ev["baseline"]:
            assert f"{ev['baseline'][field]['macro_f1']:.3f}" in text


def test_adversarial_counts_match_extraction_artefact(exported: Path) -> None:
    extraction = json.loads((ert.BUILD / "extraction.json").read_text("utf-8"))
    adversarial = [r for r in extraction if r["is_adversarial"]]
    text = (exported / "adversarial.md").read_text("utf-8")
    assert f"{len(adversarial)} adversarial items" in text


def test_dataset_summary_flags_provisional_values(exported: Path) -> None:
    text = (exported / "dataset_summary.md").read_text("utf-8")
    assert "*provisional*" in text
