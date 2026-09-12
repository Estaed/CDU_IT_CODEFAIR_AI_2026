"""The generated report texts: one per label, bounded, clean, varied; and the generation
script's resume behaviour against the fake CLI (no real call in the gate)."""

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest
from _real_names import real_names

from fair_turn.core import wording
from fair_turn.llm import prompts

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "data" / "build"
REPORTS = BUILD / "reports.json"
FAKE = [sys.executable, str(ROOT / "tests" / "fakes" / "fake_claude.py")]

spec = importlib.util.spec_from_file_location(
    "generate_text", ROOT / "scripts" / "generate_text.py"
)
generate_text = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_text)

LABELS = json.loads((BUILD / "labels.json").read_text("utf-8"))


def _build_copy(tmp_path: Path, keep: int) -> Path:
    """A build dir with the first ``keep`` labels only, so the fake batches stay small."""
    for name in ("personas.json", "communities.csv"):
        (tmp_path / name).write_bytes((BUILD / name).read_bytes())
    (tmp_path / "labels.json").write_text(json.dumps(LABELS[:keep]), "utf-8")
    return tmp_path


def test_rerun_with_complete_artefact_makes_zero_calls(tmp_path, monkeypatch) -> None:
    build = _build_copy(tmp_path, keep=5)
    (build / "reports.json").write_text(
        json.dumps([{"job_id": label["job_id"], "text": "x" * 30} for label in LABELS[:5]]), "utf-8"
    )
    monkeypatch.setenv("FAKE_MODE", "fail")  # any call would raise CliError
    summary = generate_text.run(build, executable=FAKE, names=[])
    assert summary == {"calls": 0, "written": 0, "rejected": [], "missing": 0}


def test_fake_generation_fills_missing_and_resumes(tmp_path, monkeypatch) -> None:
    build = _build_copy(tmp_path, keep=7)
    monkeypatch.setenv("FAKE_MODE", "reports")
    first = generate_text.run(build, executable=FAKE, batch_size=5, limit=1, names=[])
    assert first["calls"] == 1 and first["written"] == 5 and first["missing"] == 2
    second = generate_text.run(build, executable=FAKE, batch_size=5, names=[])
    assert second["calls"] == 1 and second["written"] == 2 and second["missing"] == 0
    reports = json.loads((build / "reports.json").read_text("utf-8"))
    assert [r["job_id"] for r in reports] == [label["job_id"] for label in LABELS[:7]]


def test_validate_rejects_bad_items() -> None:
    wanted = {"JR-2025-00001"}
    ok = {"job_id": "JR-2025-00001", "text": "The tap in the kitchen leaks all day and night."}
    assert generate_text.validate(ok, wanted, ["Someplace"]) is None
    assert generate_text.validate({**ok, "job_id": "JR-2025-99999"}, wanted, []) is not None
    assert generate_text.validate({**ok, "text": "short"}, wanted, []) is not None
    assert generate_text.validate({**ok, "text": ok["text"] + " We are vulnerable."}, wanted, [])
    assert generate_text.validate(
        {**ok, "text": "We live at Someplace and the tap leaks."}, wanted, ["Someplace"]
    )


def test_prompt_lists_every_tuple_and_forbids_deficit_terms() -> None:
    personas = {
        p["persona_id"]: p for p in json.loads((BUILD / "personas.json").read_text("utf-8"))
    }
    batch = [{**label, "setting": "a town house"} for label in LABELS[:3]]
    text = prompts.generation_prompt(batch, personas)
    for label in batch:
        assert label["job_id"] in text and label["fault_type"] in text
    for term in wording.DEFICIT_TERMS:
        assert term in prompts.GENERATION_SYSTEM
    assert prompts.GENERATION_SCHEMA["additionalProperties"] is False


# --- the committed artefact (active once Task-10's run has been made) ----------------------

needs_artefact = pytest.mark.skipif(
    not REPORTS.exists(), reason="data/build/reports.json not generated yet (Task-10 run pending)"
)


@needs_artefact
def test_one_report_per_label_within_bounds() -> None:
    reports = json.loads(REPORTS.read_text("utf-8"))
    assert sorted(r["job_id"] for r in reports) == sorted(label["job_id"] for label in LABELS)
    for r in reports:
        assert prompts.REPORT_MIN_CHARS <= len(r["text"]) <= prompts.REPORT_MAX_CHARS, r["job_id"]


@needs_artefact
def test_reports_are_clean_and_varied() -> None:
    reports = json.loads(REPORTS.read_text("utf-8"))
    joined = "\n".join(r["text"] for r in reports)
    assert [t for t in wording.check(joined) if t != wording.READING_LEVEL] == []
    upper = joined.upper()
    leaks = [n for n in real_names() if re.search(rf"(?<![A-Z]){re.escape(n)}(?![A-Z])", upper)]
    assert not leaks, leaks
    openings = {r["text"].split()[0].strip(".,!").lower() for r in reports if r["text"].split()}
    assert len(openings) >= 30, len(openings)
