"""The only reader of ``data/build/`` and ``data/audit/`` the app uses (Part 2 seam).

Pure file reads: a pilot would read intake instead. Every extraction row is validated on
load, so a malformed artefact fails at startup rather than on a page.
"""

import csv
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from fair_turn.core.types import FaultType, HealthRiskFactor, Job, SafetyClass

ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = ROOT / "data" / "build"
AUDIT_DIR = ROOT / "data" / "audit"


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str | bool  # ``location_mentioned`` is the one boolean field
    evidence: str


class ExtractionRow(BaseModel):
    """One row of ``extraction.json``, exactly as ``scripts/extract.py`` writes it."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    is_adversarial: bool
    original_job_id: str | None = None
    kept: dict[str, Evidence]
    dropped: dict[str, str]  # field name -> why its evidence was rejected
    substring_ok: bool
    needs_human: bool
    injection_markers: list[str]


@dataclass(frozen=True)
class Artefacts:
    communities: dict[str, dict[str, str]]
    labels: list[dict]
    reports: dict[str, str]
    extraction: dict[str, ExtractionRow]
    closures: list[dict]
    climate: list[dict[str, str]]
    audit_path: Path


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _json(path: Path):
    return json.loads(path.read_text("utf-8"))


def load_all(build_dir: Path = BUILD_DIR, audit_dir: Path = AUDIT_DIR) -> Artefacts:
    """Every build artefact, extraction rows validated; the audit file need not exist."""
    extraction = [ExtractionRow.model_validate(r) for r in _json(build_dir / "extraction.json")]
    return Artefacts(
        communities={r["community_id"]: r for r in _csv_rows(build_dir / "communities.csv")},
        labels=_json(build_dir / "labels.json"),
        reports={r["job_id"]: r["text"] for r in _json(build_dir / "reports.json")},
        extraction={r.job_id: r for r in extraction},
        closures=_json(build_dir / "closures.json"),
        climate=_csv_rows(build_dir / "climate.csv"),
        audit_path=audit_dir / "audit.jsonl",
    )


def _job(label: dict, row: ExtractionRow, community: dict[str, str]) -> Job:
    """A row sent to the human queue yields no typed fault/safety, so ``Job.needs_human``
    matches ``row.needs_human``."""
    kept = row.kept
    fault = None if row.needs_human or "fault_type" not in kept else kept["fault_type"].value
    safety = None if row.needs_human or "safety_class" not in kept else kept["safety_class"].value
    return Job(
        job_id=label["job_id"],
        community_id=label["community_id"],
        is_remote=community["is_remote"] == "True",
        reported_on=date.fromisoformat(label["reported_on"]),
        fault_type=FaultType(fault) if fault else None,
        safety_class=SafetyClass(safety) if safety else None,
        health_risk=frozenset(
            HealthRiskFactor(k.split(":", 1)[1]) for k in kept if k.startswith("health_risk:")
        ),
        logistics_factor=float(community["logistics_factor"]),
    )


def to_jobs(art: Artefacts) -> list[Job]:
    """One job per label row; adversarial extraction rows are not jobs."""
    return [
        _job(label, art.extraction[label["job_id"]], art.communities[label["community_id"]])
        for label in art.labels
    ]


def report_text(art: Artefacts, job_id: str) -> str:
    return art.reports[job_id]


def extraction_for(art: Artefacts, job_id: str) -> ExtractionRow:
    return art.extraction[job_id]
