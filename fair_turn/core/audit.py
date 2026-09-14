"""The decision-maker's reasoning record (PRD sections 3.1 and 3.5).

Each append is one JSON line, so a later decision cannot rewrite an earlier one. ``day`` is
the dataset decision day; ``recorded_at`` is the real, timezone-aware wall-clock timestamp.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path


def _aware(value: datetime) -> datetime:
    """Return ``value`` in the local timezone when a Phase 1 caller supplied it as naive."""
    return value.astimezone() if value.tzinfo is None else value


@dataclass(frozen=True)
class SignOff:
    day: date
    lam: float
    reason: str
    signer: str
    signed_at: datetime
    ranked_job_ids: tuple[str, ...]
    recorded_at: datetime | None = None
    batch_version: int = 1
    today_job_ids: tuple[str, ...] = ()
    decision: str = "approve"
    audit_ref: str = ""

    def __post_init__(self) -> None:
        if self.decision not in {"approve", "defer"}:
            raise ValueError("decision must be approve or defer")
        recorded_at = _aware(self.signed_at if self.recorded_at is None else self.recorded_at)
        object.__setattr__(self, "recorded_at", recorded_at)
        if self.signed_at.tzinfo is None:
            object.__setattr__(self, "signed_at", recorded_at)
        if not self.audit_ref:
            object.__setattr__(self, "audit_ref", f"{self.day:%Y%m%d}-v{self.batch_version}")


@dataclass(frozen=True)
class Revision:
    day: date
    old_lam: float
    new_lam: float
    reason: str
    at: datetime
    recorded_at: datetime | None = None

    def __post_init__(self) -> None:
        recorded_at = _aware(self.at if self.recorded_at is None else self.recorded_at)
        object.__setattr__(self, "recorded_at", recorded_at)
        if self.at.tzinfo is None:
            object.__setattr__(self, "at", recorded_at)


@dataclass(frozen=True)
class Override:
    day: date
    job_id: str
    from_rank: int
    to_rank: int
    reason: str
    at: datetime
    recorded_at: datetime | None = None

    def __post_init__(self) -> None:
        recorded_at = _aware(self.at if self.recorded_at is None else self.recorded_at)
        object.__setattr__(self, "recorded_at", recorded_at)
        if self.at.tzinfo is None:
            object.__setattr__(self, "at", recorded_at)


@dataclass(frozen=True)
class HumanSet:
    day: date
    job_id: str
    field: str
    value: str
    actor: str
    reason: str
    recorded_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "recorded_at",
            datetime.now().astimezone() if self.recorded_at is None else _aware(self.recorded_at),
        )


@dataclass(frozen=True)
class Intake:
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
        object.__setattr__(
            self,
            "recorded_at",
            datetime.now().astimezone() if self.recorded_at is None else _aware(self.recorded_at),
        )


@dataclass(frozen=True)
class Promotion:
    day: date
    job_id: str
    displaced_job_id: str
    reason: str
    recorded_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "recorded_at",
            datetime.now().astimezone() if self.recorded_at is None else _aware(self.recorded_at),
        )


@dataclass(frozen=True)
class PlanDecision:
    day: date
    batch_version: int
    action: str
    detail: str
    reason: str
    recorded_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.action not in {"accept", "edit", "reject", "suggestion_accept"}:
            raise ValueError("action must be accept, edit, reject or suggestion_accept")
        object.__setattr__(
            self,
            "recorded_at",
            datetime.now().astimezone() if self.recorded_at is None else _aware(self.recorded_at),
        )


@dataclass(frozen=True)
class FieldCheck:
    """A reviewer's check of the fields the model read from one job's report (PRD 3.1).

    ``confirmed`` needs no reason; ``corrected`` names the field, the new value and why."""

    day: date
    job_id: str
    decision: str
    actor: str
    reason: str = ""
    field: str = ""
    value: str = ""
    recorded_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.decision not in {"confirmed", "corrected"}:
            raise ValueError("decision must be confirmed or corrected")
        if self.decision == "corrected" and not (self.reason.strip() and self.field and self.value):
            raise ValueError("a correction needs a field, a value and a reason")
        object.__setattr__(
            self,
            "recorded_at",
            datetime.now().astimezone() if self.recorded_at is None else _aware(self.recorded_at),
        )


JOB_DECISIONS = ("accepted", "not_today", "needs_person", "undone")


@dataclass(frozen=True)
class JobDecision:
    """A coordinator's decision on one job for the decision ``day`` (PRD 3.1): accept it for
    today, leave it for another day, send it to a person, or undo the previous decision.

    ``not_today`` and ``needs_person`` need a reason; ``accepted`` and ``undone`` do not."""

    day: date
    job_id: str
    decision: str
    actor: str
    reason: str = ""
    recorded_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.decision not in JOB_DECISIONS:
            raise ValueError("decision must be accepted, not_today, needs_person or undone")
        if self.decision in {"not_today", "needs_person"} and not self.reason.strip():
            raise ValueError(f"{self.decision} needs a reason")
        object.__setattr__(
            self,
            "recorded_at",
            datetime.now().astimezone() if self.recorded_at is None else _aware(self.recorded_at),
        )


Record = (
    SignOff
    | Revision
    | Override
    | HumanSet
    | Intake
    | Promotion
    | PlanDecision
    | FieldCheck
    | JobDecision
)

_KIND_OF = {
    SignOff: "sign_off",
    Revision: "revision",
    Override: "override",
    HumanSet: "human_set",
    Intake: "intake",
    Promotion: "promotion",
    PlanDecision: "plan_decision",
    FieldCheck: "field_check",
    JobDecision: "job_decision",
}
_CLASS_OF = {kind: cls for cls, kind in _KIND_OF.items()}
_DATETIME_FIELDS = {"signed_at", "at", "recorded_at"}


def _to_row(record: Record) -> dict:
    """A flat, JSON-serialisable dict for one record, with its ``kind``."""
    row = asdict(record)
    row["day"] = row["day"].isoformat()
    for name in _DATETIME_FIELDS & row.keys():
        row[name] = row[name].isoformat()
    for name in ("ranked_job_ids", "today_job_ids"):
        if name in row:
            row[name] = list(row[name])
    return {"kind": _KIND_OF[type(record)], **row}


def _from_row(row: dict) -> Record:
    fields = dict(row)
    cls = _CLASS_OF[fields.pop("kind")]
    fields["day"] = date.fromisoformat(fields["day"])
    for name in _DATETIME_FIELDS & fields.keys():
        fields[name] = datetime.fromisoformat(fields[name])
    for name in ("ranked_job_ids", "today_job_ids"):
        if name in fields:
            fields[name] = tuple(fields[name])
    return cls(**fields)


def append(path: Path, record: Record) -> None:
    """Append one record as a single JSON line. Never truncates or rewrites the file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="") as f:
        f.write(json.dumps(_to_row(record)) + "\n")


def read_with_skipped(path: Path) -> tuple[list[Record], int]:
    """Return records in file order and the number with an unrecognised ``kind``."""
    path = Path(path)
    if not path.exists():
        return [], 0
    records: list[Record] = []
    skipped = 0
    with open(path, encoding="utf-8", newline="") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("kind") not in _CLASS_OF:
                skipped += 1
                continue
            records.append(_from_row(row))
    return records, skipped


def read(path: Path) -> list[Record]:
    """All recognised records in file order. ``[]`` if the file is empty or missing."""
    records, _ = read_with_skipped(path)
    return records


def _hash(record: Record) -> str:
    canonical = json.dumps(_to_row(record), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:12]


def export_rows(records: list[Record]) -> list[dict]:
    """Readable CSV-ready rows with a fixed, string-only column schema."""
    rows = []
    for record in records:
        row = {
            "kind": _KIND_OF[type(record)],
            "decision_day": record.day.isoformat(),
            "recorded_at": record.recorded_at.isoformat(),
            "audit_ref": record.audit_ref if isinstance(record, SignOff) else "",
            "job_id": "",
            "previous_weighting": "",
            "new_weighting": "",
            "reason": getattr(record, "reason", ""),
            "signer": "",
            "detail": "",
            "hash": _hash(record),
        }
        if isinstance(record, SignOff):
            row["new_weighting"] = str(record.lam)
            row["signer"] = record.signer
            row["detail"] = (
                f"{record.decision}; {len(record.today_job_ids)} in today's list of "
                f"{len(record.ranked_job_ids)} ranked"
            )
        elif isinstance(record, Revision):
            row["previous_weighting"] = str(record.old_lam)
            row["new_weighting"] = str(record.new_lam)
        elif isinstance(record, Override):
            row["job_id"] = record.job_id
            row["detail"] = f"rank {record.from_rank} -> {record.to_rank}"
        elif isinstance(record, HumanSet):
            row["job_id"] = record.job_id
            row["signer"] = record.actor
            row["detail"] = f"{record.field} = {record.value}"
        elif isinstance(record, Intake):
            row["job_id"] = record.job_id
            row["detail"] = (
                f"{record.provider}/{record.model} prompt {record.prompt_version}: "
                f"{record.status} ({record.validation}), {record.latency_s:.1f} s"
            )
        elif isinstance(record, Promotion):
            row["job_id"] = record.job_id
            row["detail"] = f"displaced {record.displaced_job_id}"
        elif isinstance(record, PlanDecision):
            row["detail"] = f"{record.action} v{record.batch_version}: {record.detail}"
        elif isinstance(record, FieldCheck):
            row["job_id"] = record.job_id
            row["signer"] = record.actor
            row["detail"] = (
                f"corrected {record.field} = {record.value}"
                if record.decision == "corrected"
                else "confirmed"
            )
        elif isinstance(record, JobDecision):
            row["job_id"] = record.job_id
            row["signer"] = record.actor
            row["detail"] = record.decision
        rows.append(row)
    return rows


def latest_checks(records: list[Record], day: date) -> dict[str, FieldCheck]:
    """The newest field check per job on the decision ``day``, in file order."""
    return {r.job_id: r for r in records if isinstance(r, FieldCheck) and r.day == day}


def latest_decisions(records: list[Record], day: date) -> dict[str, str]:
    """The newest job decision per job on the decision ``day``, in file order."""
    return {r.job_id: r.decision for r in records if isinstance(r, JobDecision) and r.day == day}


def override_rate(records: list[Record]) -> list[tuple[date, float]]:
    """``(day, overrides / ranked_jobs)`` for each sign-off day, sorted by decision day."""
    ranked_jobs: dict[date, int] = {}
    overrides: dict[date, int] = {}
    for record in records:
        if isinstance(record, SignOff):
            ranked_jobs[record.day] = len(record.ranked_job_ids)
        elif isinstance(record, Override):
            overrides[record.day] = overrides.get(record.day, 0) + 1
    return [
        (day, overrides.get(day, 0) / count)
        for day, count in sorted(ranked_jobs.items())
        if count > 0
    ]
