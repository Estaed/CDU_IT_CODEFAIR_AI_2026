"""Round-trip, two-clock and export-schema tests for the audit log."""

import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from fair_turn.core import audit

DARWIN = ZoneInfo("Australia/Darwin")
ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PATH = ROOT / "data" / "audit" / "sample.jsonl"
EXPORT_KEYS = [
    "kind",
    "decision_day",
    "recorded_at",
    "audit_ref",
    "job_id",
    "previous_weighting",
    "new_weighting",
    "reason",
    "signer",
    "detail",
    "hash",
]


def _sign_off(
    day: date = date(2026, 9, 1),
    ranked: tuple[str, ...] = ("job-1", "job-2", "job-3", "job-4"),
) -> audit.SignOff:
    return audit.SignOff(
        day=day,
        lam=1.5,
        reason="weekly sign-off",
        signer="coordinator",
        signed_at=datetime(2026, 9, 1, 9, 0),
        ranked_job_ids=ranked,
        today_job_ids=ranked[:2],
    )


def _revision(day: date = date(2026, 9, 1)) -> audit.Revision:
    return audit.Revision(
        day=day,
        old_lam=1.0,
        new_lam=1.5,
        reason="fuel price rose",
        at=datetime(2026, 9, 1, 9, 5),
    )


def _override(day: date = date(2026, 9, 1), job_id: str = "job-3") -> audit.Override:
    return audit.Override(
        day=day,
        job_id=job_id,
        from_rank=3,
        to_rank=1,
        reason="crew already on site",
        at=datetime(2026, 9, 1, 9, 10),
    )


def _records() -> list[audit.Record]:
    recorded_at = datetime(2026, 9, 1, 9, 15, tzinfo=DARWIN)
    return [
        _sign_off(),
        _revision(),
        _override(),
        audit.HumanSet(
            date(2026, 9, 1),
            "job-4",
            "fault_type",
            "plumbing_water",
            "coordinator",
            "checked",
            recorded_at,
        ),
        audit.Intake(
            date(2026, 9, 1),
            "job-5",
            "claude",
            "sonnet",
            "v1",
            1.2,
            "valid",
            "extracted",
            recorded_at,
        ),
        audit.Promotion(date(2026, 9, 1), "job-6", "job-7", "reason", recorded_at),
        audit.PlanDecision(date(2026, 9, 1), 2, "accept", "route accepted", "reason", recorded_at),
        audit.FieldCheck(date(2026, 9, 1), "job-8", "confirmed", "Tarik", recorded_at=recorded_at),
        audit.FieldCheck(
            date(2026, 9, 1),
            "job-9",
            "corrected",
            "Tarik",
            "report says the wiring sparks",
            "safety_class",
            "urgent",
            recorded_at,
        ),
        audit.JobDecision(date(2026, 9, 1), "job-10", "accepted", "Tarik", recorded_at=recorded_at),
        audit.JobDecision(
            date(2026, 9, 1), "job-11", "not_today", "Tarik", "tenant away", recorded_at
        ),
        audit.MakeSafe(date(2026, 9, 1), "job-12", "Tarik", "contractor booked", recorded_at),
    ]


def test_round_trip_preserves_every_kind(tmp_path: Path) -> None:
    path = tmp_path / "log.jsonl"
    records = _records()
    for record in records:
        audit.append(path, record)
    assert audit.read(path) == records


def test_recorded_at_is_timezone_aware_after_naive_phase1_input() -> None:
    for record in (_sign_off(), _revision(), _override()):
        assert record.recorded_at.tzinfo is not None
    assert _sign_off().signed_at.tzinfo is not None
    assert _revision().at.tzinfo is not None
    assert _override().at.tzinfo is not None


def test_phase1_positional_signoff_keeps_its_signature_and_gets_audit_ref() -> None:
    record = audit.SignOff(
        date(2026, 9, 1), 1.0, "reason", "signer", datetime(2026, 9, 1, 9), ("job-1",)
    )
    assert record.audit_ref == "20260901-v1"


def test_read_on_missing_or_empty_file_returns_empty_list(tmp_path: Path) -> None:
    assert audit.read(tmp_path / "missing.jsonl") == []
    assert audit.read_with_skipped(tmp_path / "missing.jsonl") == ([], 0)
    path = tmp_path / "empty.jsonl"
    path.write_bytes(b"")
    assert audit.read(path) == []


def test_unknown_kind_is_skipped_and_counted(tmp_path: Path) -> None:
    path = tmp_path / "log.jsonl"
    audit.append(path, _sign_off())
    with path.open("ab") as f:
        f.write(b'{"kind":"future_event","day":"2026-09-01"}\n')
    records, skipped = audit.read_with_skipped(path)
    assert records == [_sign_off()]
    assert skipped == 1
    assert audit.read(path) == records


def test_export_rows_has_exact_string_only_schema_and_stable_hash() -> None:
    records = _records()
    rows = audit.export_rows(records)
    assert len(rows) == len(records)
    assert all(list(row) == EXPORT_KEYS for row in rows)
    assert all(isinstance(value, str) for row in rows for value in row.values())
    assert rows[0]["audit_ref"] == "20260901-v1"
    assert rows[0]["detail"] == "approve; 2 in today's list of 4 ranked"
    assert rows[2]["detail"] == "rank 3 -> 1"
    assert rows[3]["detail"] == "fault_type = plumbing_water"
    assert rows[4]["detail"] == "claude/sonnet prompt v1: extracted (valid), 1.2 s"
    assert rows[5]["detail"] == "displaced job-7"
    assert rows[6]["detail"] == "accept v2: route accepted"
    assert rows[7]["kind"] == "field_check"
    assert (rows[7]["job_id"], rows[7]["signer"], rows[7]["detail"]) == (
        "job-8",
        "Tarik",
        "confirmed",
    )
    assert rows[8]["detail"] == "corrected safety_class = urgent"
    assert rows[8]["reason"] == "report says the wiring sparks"
    assert [row["hash"] for row in rows] == [row["hash"] for row in audit.export_rows(records)]


def test_hash_is_identical_across_two_reads(tmp_path: Path) -> None:
    path = tmp_path / "log.jsonl"
    audit.append(path, _sign_off())
    assert (
        audit.export_rows(audit.read(path))[0]["hash"]
        == audit.export_rows(audit.read(path))[0]["hash"]
    )


def test_override_rate_fixture() -> None:
    records = [
        _sign_off(date(2026, 9, 1)),
        _override(date(2026, 9, 1), "job-3"),
        _override(date(2026, 9, 1), "job-4"),
        _sign_off(date(2026, 9, 2), ranked=("job-5", "job-6")),
    ]
    # Two hand moves over a signed list of two jobs (the denominator is the signed list).
    assert audit.override_rate(records) == [(date(2026, 9, 1), 1.0), (date(2026, 9, 2), 0.0)]


def test_override_rate_ignores_a_day_with_no_sign_off() -> None:
    assert audit.override_rate([_override(date(2026, 9, 3), "job-9")]) == []


def test_second_append_does_not_alter_earlier_lines(tmp_path: Path) -> None:
    path = tmp_path / "log.jsonl"
    audit.append(path, _sign_off())
    first_bytes = path.read_bytes()
    audit.append(path, _revision())
    assert path.read_bytes()[: len(first_bytes)] == first_bytes


def test_seeded_sample_has_aware_non_midnight_recorded_timestamps() -> None:
    records = audit.read(SAMPLE_PATH)
    assert records
    for record in records:
        assert record.recorded_at.tzinfo is not None
        midnight = datetime(
            record.day.year, record.day.month, record.day.day, tzinfo=record.recorded_at.tzinfo
        )
        assert record.recorded_at != midnight


def test_decision_status_and_plan_action_are_validated() -> None:
    with pytest.raises(ValueError):
        audit.SignOff(
            date(2026, 9, 1),
            1.0,
            "reason",
            "signer",
            datetime(2026, 9, 1, 9),
            (),
            decision="invalid",
        )
    with pytest.raises(ValueError):
        audit.Intake(date(2026, 9, 1), "job", "provider", "model", "v1", 1.0, "valid", "unknown")
    with pytest.raises(ValueError):
        audit.PlanDecision(date(2026, 9, 1), 1, "invalid", "detail", "reason")


# --- field checks (PRD 3.1, "Checking the AI's reading") ---------------------------------------


def test_field_check_round_trip_keeps_both_clocks(tmp_path: Path) -> None:
    path = tmp_path / "log.jsonl"
    day = date(2025, 12, 30)  # the dataset day, far from the wall clock
    before = datetime.now().astimezone()
    record = audit.FieldCheck(day, "job-1", "confirmed", "Tarik")
    audit.append(path, record)
    (read_back,) = audit.read(path)
    assert read_back == record
    assert read_back.day == day
    assert read_back.recorded_at.tzinfo is not None
    assert read_back.recorded_at >= before
    row = audit.export_rows([read_back])[0]
    assert row["kind"] == "field_check"
    assert row["decision_day"] == "2025-12-30"
    assert row["recorded_at"] == read_back.recorded_at.isoformat()
    assert row["decision_day"] != row["recorded_at"][:10]


def test_field_check_decision_and_correction_reason_are_validated() -> None:
    with pytest.raises(ValueError):
        audit.FieldCheck(date(2026, 9, 1), "job-1", "approved", "Tarik")
    with pytest.raises(ValueError):
        audit.FieldCheck(date(2026, 9, 1), "job-1", "corrected", "Tarik", " ", "fault_type", "roof")
    audit.FieldCheck(date(2026, 9, 1), "job-1", "confirmed", "Tarik", reason="")


def test_latest_checks_keeps_the_newest_per_job_on_that_day() -> None:
    day = date(2026, 9, 1)
    first = audit.FieldCheck(day, "job-1", "confirmed", "A")
    second = audit.FieldCheck(day, "job-1", "corrected", "B", "why", "fault_type", "roof")
    other_day = audit.FieldCheck(date(2026, 9, 2), "job-2", "confirmed", "A")
    assert audit.latest_checks([first, second, other_day, _sign_off()], day) == {"job-1": second}


# --- job decisions (PRD 3.1, accept or reject per job) -----------------------------------------


def test_job_decision_round_trip_keeps_both_clocks(tmp_path: Path) -> None:
    path = tmp_path / "log.jsonl"
    day = date(2025, 12, 30)  # the dataset day, far from the wall clock
    before = datetime.now().astimezone()
    record = audit.JobDecision(day, "job-1", "not_today", "Tarik", "tenant away")
    audit.append(path, record)
    (read_back,) = audit.read(path)
    assert read_back == record
    assert read_back.day == day
    assert read_back.recorded_at.tzinfo is not None
    assert read_back.recorded_at >= before
    row = audit.export_rows([read_back])[0]
    assert row["kind"] == "job_decision"
    assert (row["job_id"], row["signer"], row["detail"]) == ("job-1", "Tarik", "not_today")
    assert row["reason"] == "tenant away"
    assert row["decision_day"] == "2025-12-30"
    assert row["recorded_at"] == read_back.recorded_at.isoformat()
    assert row["decision_day"] != row["recorded_at"][:10]


def test_job_decision_values_and_reasons_are_validated() -> None:
    day = date(2026, 9, 1)
    with pytest.raises(ValueError):
        audit.JobDecision(day, "job-1", "approved", "Tarik")
    for decision in ("not_today", "needs_person"):
        with pytest.raises(ValueError):
            audit.JobDecision(day, "job-1", decision, "Tarik", "  ")
    audit.JobDecision(day, "job-1", "accepted", "Tarik")
    audit.JobDecision(day, "job-1", "undone", "Tarik")


def test_latest_decisions_keeps_the_newest_per_job_on_that_day() -> None:
    day = date(2026, 9, 1)
    records = [
        audit.JobDecision(day, "job-1", "accepted", "A"),
        audit.JobDecision(day, "job-1", "undone", "A"),
        audit.JobDecision(day, "job-2", "not_today", "A", "why"),
        audit.JobDecision(date(2026, 9, 2), "job-3", "accepted", "A"),
        _sign_off(),
    ]
    assert audit.latest_decisions(records, day) == {"job-1": "undone", "job-2": "not_today"}


# --- make-safe lane (PRD 3.1 and 6.3, amended 2026-09-15) ----------------------------------------


def test_make_safe_round_trip_keeps_both_clocks_and_exports_its_row(tmp_path: Path) -> None:
    path = tmp_path / "log.jsonl"
    day = date(2025, 12, 30)  # the dataset day, far from the wall clock
    before = datetime.now().astimezone()
    record = audit.MakeSafe(day, "job-1", "Tarik", "contractor booked by phone")
    audit.append(path, record)
    assert '"kind": "make_safe"' in path.read_text("utf-8")
    (read_back,) = audit.read(path)
    assert read_back == record
    assert isinstance(read_back, audit.MakeSafe)
    assert read_back.day == day
    assert read_back.recorded_at.tzinfo is not None
    assert read_back.recorded_at >= before
    row = audit.export_rows([read_back])[0]
    assert list(row) == EXPORT_KEYS
    assert row["kind"] == "make_safe"
    assert (row["job_id"], row["signer"], row["reason"]) == (
        "job-1",
        "Tarik",
        "contractor booked by phone",
    )
    assert row["detail"] == "sent to make-safe contractor"
    assert row["decision_day"] == "2025-12-30"
    assert row["recorded_at"] == read_back.recorded_at.isoformat()
    assert row["decision_day"] != row["recorded_at"][:10]


def test_make_safe_is_frozen_and_needs_a_reason() -> None:
    day = date(2026, 9, 1)
    for reason in ("", "   ", "\t\n"):
        with pytest.raises(ValueError):
            audit.MakeSafe(day, "job-1", "Tarik", reason)
    record = audit.MakeSafe(day, "job-1", "Tarik", "booked")
    with pytest.raises(AttributeError):
        record.reason = "changed"  # type: ignore[misc]
    naive = audit.MakeSafe(day, "job-1", "Tarik", "booked", datetime(2026, 9, 1, 9, 0))
    assert naive.recorded_at.tzinfo is not None


def test_make_safe_sent_keeps_the_newest_per_job_on_any_day() -> None:
    first = audit.MakeSafe(date(2026, 9, 1), "job-1", "A", "first call")
    second = audit.MakeSafe(date(2026, 9, 2), "job-1", "B", "second call")
    other = audit.MakeSafe(date(2026, 8, 30), "job-2", "A", "booked")
    records = [
        first,
        _sign_off(),
        audit.JobDecision(date(2026, 9, 1), "job-3", "accepted", "A"),
        other,
        second,
    ]
    assert audit.make_safe_sent(records) == {"job-1": second, "job-2": other}
    assert audit.make_safe_sent([second, first]) == {"job-1": first}  # file order wins
    assert audit.make_safe_sent([_sign_off(), _revision()]) == {}


def _immediate_label_ids() -> set[str]:
    labels = json.loads((ROOT / "data" / "build" / "labels.json").read_text("utf-8"))
    return {label["job_id"] for label in labels if label["safety_class"] == "immediate"}


def _assert_sample_signs_crew_jobs_and_sends_one_make_safe(records) -> None:
    immediate = _immediate_label_ids()
    sign_offs = [r for r in records if isinstance(r, audit.SignOff)]
    assert sign_offs
    for record in sign_offs:
        assert not immediate & set(record.ranked_job_ids)
        assert not immediate & set(record.today_job_ids)
    (make_safe,) = [r for r in records if isinstance(r, audit.MakeSafe)]
    assert make_safe.reason.strip()
    assert make_safe.job_id in immediate


def test_seeded_sample_signs_only_crew_jobs_and_sends_one_make_safe() -> None:
    _assert_sample_signs_crew_jobs_and_sends_one_make_safe(audit.read(SAMPLE_PATH))
