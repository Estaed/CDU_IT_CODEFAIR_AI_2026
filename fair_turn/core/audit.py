"""The decision-maker's reasoning record: every sign-off, lambda revision and per-job
override, appended and exportable (PRD section 3.3, 3.6). One JSON line per record; the
file is never rewritten, so an earlier line is never at risk from a later append.
"""

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path


@dataclass(frozen=True)
class SignOff:
    day: date
    lam: float
    reason: str
    signer: str
    signed_at: datetime
    ranked_job_ids: tuple[str, ...]


@dataclass(frozen=True)
class Revision:
    day: date
    old_lam: float
    new_lam: float
    reason: str
    at: datetime


@dataclass(frozen=True)
class Override:
    day: date
    job_id: str
    from_rank: int
    to_rank: int
    reason: str
    at: datetime


_KIND_OF = {SignOff: "sign_off", Revision: "revision", Override: "override"}
_CLASS_OF = {kind: cls for cls, kind in _KIND_OF.items()}
_DATETIME_FIELDS = {"signed_at", "at"}


def _to_row(record: SignOff | Revision | Override) -> dict:
    """A flat, JSON-serialisable dict for one record, with its ``kind``."""
    row = asdict(record)
    row["day"] = row["day"].isoformat()
    for name in _DATETIME_FIELDS & row.keys():
        row[name] = row[name].isoformat()
    if "ranked_job_ids" in row:
        row["ranked_job_ids"] = list(row["ranked_job_ids"])
    return {"kind": _KIND_OF[type(record)], **row}


def _from_row(row: dict) -> SignOff | Revision | Override:
    fields = dict(row)
    cls = _CLASS_OF[fields.pop("kind")]
    fields["day"] = date.fromisoformat(fields["day"])
    for name in _DATETIME_FIELDS & fields.keys():
        fields[name] = datetime.fromisoformat(fields[name])
    if "ranked_job_ids" in fields:
        fields["ranked_job_ids"] = tuple(fields["ranked_job_ids"])
    return cls(**fields)


def append(path: Path, record: SignOff | Revision | Override) -> None:
    """Append one record as a single JSON line. Never truncates or rewrites the file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="") as f:
        f.write(json.dumps(_to_row(record)) + "\n")


def read(path: Path) -> list[SignOff | Revision | Override]:
    """All records in file order. ``[]`` if the file is empty or missing."""
    path = Path(path)
    if not path.exists():
        return []
    with open(path, encoding="utf-8", newline="") as f:
        return [_from_row(json.loads(line)) for line in f if line.strip()]


def export_rows(records: list[SignOff | Revision | Override]) -> list[dict]:
    """One flat, JSON-serialisable row per record, same order, same count."""
    return [_to_row(r) for r in records]


def override_rate(records: list[SignOff | Revision | Override]) -> list[tuple[date, float]]:
    """``(day, overrides / ranked_jobs)`` for each day with a sign-off, sorted by day."""
    ranked_jobs: dict[date, int] = {}
    overrides: dict[date, int] = {}
    for r in records:
        if isinstance(r, SignOff):
            ranked_jobs[r.day] = len(r.ranked_job_ids)
        elif isinstance(r, Override):
            overrides[r.day] = overrides.get(r.day, 0) + 1
    return [
        (day, overrides.get(day, 0) / count)
        for day, count in sorted(ranked_jobs.items())
        if count > 0
    ]
