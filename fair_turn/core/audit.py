"""The decision log: who decided what, why, and when.

Each append is one JSON line, so a later decision cannot rewrite an earlier one. Two clocks,
never written as one: ``week`` / ``day`` is the dataset's planning day, ``recorded_at`` the
real, timezone-aware wall-clock time the record was made.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path


def _now() -> datetime:
    return datetime.now().astimezone()


def _aware(value: datetime | None) -> datetime:
    if value is None:
        return _now()
    return value.astimezone() if value.tzinfo is None else value


@dataclass(frozen=True)
class PlanSigned:
    """A coordinator signed one week's crew plan. Every change they made to the proposal is
    in ``changes`` with its reason, so the log shows what the formula proposed and what the
    person decided."""

    day: date  # the planning Monday
    version: int
    setting: float
    setting_name: str
    signer: str
    reason: str
    trips: tuple[str, ...]  # "base > community: n repairs", in plan order
    changes: tuple[str, ...]  # "added C: reason" / "took out C: reason"
    repairs: int
    overdue_left: int
    job_ids: tuple[str, ...] = ()  # every planned job, sorted: what the signature covers
    added: tuple[str, ...] = ()  # community ids the coordinator put in
    dropped: tuple[str, ...] = ()  # community ids the coordinator took out
    recorded_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.signer.strip():
            raise ValueError("a signed plan needs the signer's name")
        if not self.reason.strip():
            raise ValueError("a signed plan needs a reason")
        object.__setattr__(self, "recorded_at", _aware(self.recorded_at))


@dataclass(frozen=True)
class FieldSet:
    """A person set a field the model could not read from the report."""

    day: date
    job_id: str
    field: str
    value: str
    actor: str
    reason: str
    recorded_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError("a field set by hand needs a reason")
        object.__setattr__(self, "recorded_at", _aware(self.recorded_at))


@dataclass(frozen=True)
class Intake:
    """A new report went through the extractor."""

    day: date
    job_id: str
    provider: str
    model: str
    prompt_version: str
    latency_s: float
    validation: str
    status: str
    recorded_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.status not in {"extracted", "needs_review", "not_extracted"}:
            raise ValueError("status must be extracted, needs_review or not_extracted")
        object.__setattr__(self, "recorded_at", _aware(self.recorded_at))


Record = PlanSigned | FieldSet | Intake

_KIND_OF = {PlanSigned: "plan_signed", FieldSet: "field_set", Intake: "intake"}
_CLASS_OF = {kind: cls for cls, kind in _KIND_OF.items()}
_TUPLES = ("trips", "changes", "job_ids", "added", "dropped")


def _to_row(record: Record) -> dict:
    row = asdict(record)
    row["day"] = row["day"].isoformat()
    row["recorded_at"] = row["recorded_at"].isoformat()
    for name in _TUPLES:
        if name in row:
            row[name] = list(row[name])
    return {"kind": _KIND_OF[type(record)], **row}


def _from_row(row: dict) -> Record:
    fields = dict(row)
    cls = _CLASS_OF[fields.pop("kind")]
    fields["day"] = date.fromisoformat(fields["day"])
    fields["recorded_at"] = datetime.fromisoformat(fields["recorded_at"])
    for name in _TUPLES:
        if name in fields:
            fields[name] = tuple(fields[name])
    return cls(**fields)


def append(path: Path, record: Record) -> None:
    """Append one record as a single JSON line. Never truncates or rewrites the file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="") as f:
        f.write(json.dumps(_to_row(record)) + "\n")


def read(path: Path) -> list[Record]:
    """Records in file order. A line of an older or unknown kind, or one cut off mid-write,
    is skipped: one bad line never hides the rest of the log."""
    path = Path(path)
    if not path.exists():
        return []
    records: list[Record] = []
    with open(path, encoding="utf-8", newline="") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                if isinstance(row, dict) and row.get("kind") in _CLASS_OF:
                    records.append(_from_row(row))
            except (TypeError, ValueError, KeyError):  # JSONDecodeError is a ValueError
                continue
    return records


def latest_signature(records: list[Record], day: date) -> PlanSigned | None:
    signed = [r for r in records if isinstance(r, PlanSigned) and r.day == day]
    return signed[-1] if signed else None


def _hash(record: Record) -> str:
    canonical = json.dumps(_to_row(record), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:12]


def export_rows(records: list[Record]) -> list[dict[str, str]]:
    """Readable rows with one fixed, string-only column schema."""
    rows = []
    for record in records:
        row = {
            "what": "",
            "planning_day": record.day.isoformat(),
            "recorded_at": record.recorded_at.isoformat(timespec="seconds"),
            "who": "",
            "reason": getattr(record, "reason", ""),
            "detail": "",
            "hash": _hash(record),
        }
        if isinstance(record, PlanSigned):
            row["what"] = f"plan signed, version {record.version}"
            row["who"] = record.signer
            changes = "; ".join(record.changes) if record.changes else "no changes"
            row["detail"] = (
                f"{record.setting_name}: {len(record.trips)} trips, {record.repairs} repairs, "
                f"{record.overdue_left} overdue left; {changes}"
            )
        elif isinstance(record, FieldSet):
            row["what"] = "field set by hand"
            row["who"] = record.actor
            label = {"fault_type": "what is broken", "safety_class": "urgency"}.get(
                record.field, record.field.replace("_", " ")
            )
            row["detail"] = f"{record.job_id}: {label} set to {record.value.replace('_', ' ')}"
        else:
            row["what"] = "report read"
            row["who"] = f"{record.provider} ({record.model})"
            row["detail"] = (
                f"{record.job_id}: {record.status} ({record.validation}), {record.latency_s:.1f} s"
            )
        rows.append(row)
    return rows
