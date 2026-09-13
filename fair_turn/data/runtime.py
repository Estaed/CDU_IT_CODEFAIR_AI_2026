"""Append-only local records for intake reports and coordinator-set fields (PRD 3.2)."""

import json
import re
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = ROOT / "data" / "runtime"


@dataclass(frozen=True)
class HumanSetField:
    job_id: str
    field: str
    value: str
    actor: str
    reason: str
    at: datetime


@dataclass(frozen=True)
class IntakeReport:
    job_id: str
    community_id: str
    reported_on: date
    text: str
    extraction: dict | None
    status: Literal["extracted", "needs_review", "not_extracted"]
    provider: str
    model: str
    prompt_version: str
    latency_s: float
    validation: dict
    draft_token: str
    at: datetime


_KIND_OF = {HumanSetField: "human_set", IntakeReport: "intake"}
_CLASS_OF = {kind: cls for cls, kind in _KIND_OF.items()}
_DATETIME_FIELDS = {"at"}


def _to_row(record: HumanSetField | IntakeReport) -> dict:
    row = asdict(record)
    if "reported_on" in row:
        row["reported_on"] = row["reported_on"].isoformat()
    for name in _DATETIME_FIELDS & row.keys():
        row[name] = row[name].isoformat()
    return {"kind": _KIND_OF[type(record)], **row}


def _from_row(row: dict) -> HumanSetField | IntakeReport:
    fields = dict(row)
    cls = _CLASS_OF[fields.pop("kind")]
    if "reported_on" in fields:
        fields["reported_on"] = date.fromisoformat(fields["reported_on"])
    for name in _DATETIME_FIELDS & fields.keys():
        fields[name] = datetime.fromisoformat(fields[name])
    return cls(**fields)


def append(path: Path, record: HumanSetField | IntakeReport) -> bool:
    """Append one record, unless an intake draft token has already been stored."""
    path = Path(path)
    if isinstance(record, IntakeReport):
        if any(
            isinstance(existing, IntakeReport) and existing.draft_token == record.draft_token
            for existing in read(path)
        ):
            return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="") as f:
        f.write(json.dumps(_to_row(record)) + "\n")
    return True


def read(path: Path) -> list[HumanSetField | IntakeReport]:
    """Return records in file order, or an empty list when the store is absent."""
    path = Path(path)
    if not path.exists():
        return []
    with open(path, encoding="utf-8", newline="") as f:
        return [_from_row(json.loads(line)) for line in f if line.strip()]


def human_set_for(records: list[HumanSetField | IntakeReport]) -> dict[str, dict[str, str]]:
    """Latest coordinator-set value wins for every job field."""
    values: dict[str, dict[str, str]] = {}
    for record in records:
        if isinstance(record, HumanSetField):
            values.setdefault(record.job_id, {})[record.field] = record.value
    return values


_JOB_ID = re.compile(r"JR-2025-(\d{5})$")


def next_job_id(existing_ids) -> str:
    """Return the next identifier in the frozen 2025 job-id series."""
    numbers = [
        int(match.group(1)) for job_id in existing_ids if (match := _JOB_ID.fullmatch(job_id))
    ]
    return f"JR-2025-{max(numbers, default=0) + 1:05d}"
