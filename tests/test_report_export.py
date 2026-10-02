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
    "this_week_by_setting.csv",
    "season_by_setting.csv",
    "one_more_crew.csv",
    "dataset_summary.md",
)


@pytest.fixture(scope="module")
def exported(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("report")
    ert.main(out)
    return out


def test_eight_files_written(exported: Path) -> None:
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


def _rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return {r["setting"]: r for r in csv.DictReader(f)}


def test_this_week_trades_repairs_for_overdue_households(exported: Path) -> None:
    rows = _rows(exported / "this_week_by_setting.csv")
    assert set(rows) == {f"{i / 10:.1f}" for i in range(11)}
    most, need = rows["0.0"], rows["1.0"]
    assert most["name"] == "Most repairs" and need["name"] == "Most overdue first"
    assert int(most["repairs"]) == max(int(r["repairs"]) for r in rows.values())
    assert int(need["repairs"]) < int(most["repairs"])
    assert int(need["overdue_left"]) < int(most["overdue_left"])


def test_season_most_repairs_leaves_the_farthest_waiting(exported: Path) -> None:
    rows = _rows(exported / "season_by_setting.csv")
    most, balanced = rows["0.0"], rows["0.5"]
    assert int(most["over_300_km_still_open"]) > int(balanced["over_300_km_still_open"])
    assert int(most["town_still_open"]) <= int(rows["1.0"]["town_still_open"])


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
