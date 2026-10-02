"""The decision log: append/read round trip with both clocks, required reasons, tolerance of
older rows, the day's latest signature, and the fixed export schema."""

import json
from datetime import date, datetime, timedelta, timezone

import pytest

from fair_turn.core import audit

DAY = date(2025, 12, 29)
DARWIN = timezone(timedelta(hours=9, minutes=30))
AT = datetime(2026, 10, 2, 9, 5, tzinfo=DARWIN)
EXPORT_COLUMNS = ["what", "planning_day", "recorded_at", "who", "reason", "detail", "hash"]


def signed(day: date = DAY, version: int = 1, **kw) -> audit.PlanSigned:
    fields = {
        "day": day,
        "version": version,
        "setting": 0.5,
        "setting_name": "Balanced",
        "signer": "R. Coordinator",
        "reason": "Proposal as it stands",
        "trips": (
            "Katherine town: 6 repairs, 2 crew-days",
            "Katherine > R-01: 4 repairs, 3 crew-days",
        ),
        "changes": ("added R-01: tenant called twice",),
        "repairs": 10,
        "overdue_left": 3,
        "added": ("R-01",),
        "dropped": (),
        "recorded_at": AT,
    }
    return audit.PlanSigned(**{**fields, **kw})


def field_set(**kw) -> audit.FieldSet:
    fields = {
        "day": DAY,
        "job_id": "JR-2025-00001",
        "field": "safety_class",
        "value": "urgent",
        "actor": "R. Coordinator",
        "reason": "Tenant confirmed by phone",
        "recorded_at": AT,
    }
    return audit.FieldSet(**{**fields, **kw})


def intake(**kw) -> audit.Intake:
    fields = {
        "day": DAY,
        "job_id": "JR-2025-00002",
        "provider": "claude",
        "model": "sonnet",
        "prompt_version": "intake-v1",
        "latency_s": 11.42,
        "validation": "verified",
        "status": "extracted",
        "recorded_at": AT,
    }
    return audit.Intake(**{**fields, **kw})


@pytest.mark.parametrize("make", [signed, field_set, intake])
def test_round_trip_each_kind_keeps_both_clocks(tmp_path, make) -> None:
    log = tmp_path / "audit" / "audit.jsonl"
    record = make()
    audit.append(log, record)
    (back,) = audit.read(log)
    assert back == record
    assert type(back.day) is date
    assert back.recorded_at == AT
    assert back.recorded_at.tzinfo is not None
    assert back.recorded_at.utcoffset() == timedelta(hours=9, minutes=30)


def test_both_clocks_are_separate_columns_in_the_file(tmp_path) -> None:
    log = tmp_path / "audit.jsonl"
    audit.append(log, field_set())
    row = json.loads(log.read_text("utf-8"))
    assert row["kind"] == "field_set"
    assert row["day"] == "2025-12-29"
    assert row["recorded_at"] == "2026-10-02T09:05:00+09:30"


def test_append_never_rewrites(tmp_path) -> None:
    log = tmp_path / "audit.jsonl"
    records = [signed(), field_set(), intake(), signed(version=2)]
    for record in records:
        audit.append(log, record)
    assert audit.read(log) == records
    assert len(log.read_text("utf-8").splitlines()) == 4


def test_recorded_at_defaults_to_an_aware_now() -> None:
    before = datetime.now().astimezone()
    record = field_set(recorded_at=None)
    assert record.recorded_at.tzinfo is not None
    assert before <= record.recorded_at <= datetime.now().astimezone()


def test_naive_recorded_at_becomes_aware() -> None:
    record = intake(recorded_at=datetime(2026, 10, 2, 9, 5))
    assert record.recorded_at.tzinfo is not None


@pytest.mark.parametrize("blank", ["", "   "])
def test_plan_signed_refuses_empty_signer_or_reason(blank) -> None:
    with pytest.raises(ValueError):
        signed(signer=blank)
    with pytest.raises(ValueError):
        signed(reason=blank)


@pytest.mark.parametrize("blank", ["", "   "])
def test_field_set_refuses_empty_reason(blank) -> None:
    with pytest.raises(ValueError):
        field_set(reason=blank)


def test_intake_refuses_unknown_status() -> None:
    with pytest.raises(ValueError):
        intake(status="maybe")


def test_read_missing_file_is_empty(tmp_path) -> None:
    assert audit.read(tmp_path / "nothing.jsonl") == []


def test_read_skips_unknown_kinds_and_old_rows(tmp_path) -> None:
    log = tmp_path / "audit.jsonl"
    audit.append(log, signed())
    old_rows = [
        # a Phase 1 kind no longer in the log
        {"kind": "sign_off", "day": "2025-12-27", "lam": 1.0, "reason": "weekly", "signer": "R"},
        # a known kind carrying a field this version does not have
        {**json.loads(log.read_text("utf-8")), "lam": 1.0},
        # a known kind with a value this version cannot parse
        {**json.loads(log.read_text("utf-8")), "day": "week 52"},
        # no kind at all
        {"day": "2025-12-29"},
    ]
    with open(log, "a", encoding="utf-8", newline="") as f:
        for row in old_rows:
            f.write(json.dumps(row) + "\n")
        f.write("\n")
    audit.append(log, field_set())
    assert audit.read(log) == [signed(), field_set()]


def test_read_skips_a_known_kind_missing_a_field(tmp_path) -> None:
    log = tmp_path / "audit.jsonl"
    row = json.loads(json.dumps(audit._to_row(field_set())))
    del row["job_id"]
    log.write_text(json.dumps(row) + "\n", encoding="utf-8", newline="")
    assert audit.read(log) == []


@pytest.mark.parametrize("clock", ["day", "recorded_at"])
def test_read_skips_a_known_kind_missing_a_clock(tmp_path, clock) -> None:
    log = tmp_path / "audit.jsonl"
    row = json.loads(json.dumps(audit._to_row(field_set())))
    del row[clock]
    log.write_text(json.dumps(row) + "\n", encoding="utf-8", newline="")
    assert audit.read(log) == []


def test_read_skips_a_truncated_line(tmp_path) -> None:
    log = tmp_path / "audit.jsonl"
    audit.append(log, field_set())
    with open(log, "a", encoding="utf-8", newline="") as f:
        f.write('{"kind": "field_set", "day": "2025-12-2\n')
    assert audit.read(log) == [field_set()]


def test_latest_signature_picks_the_last_for_the_day() -> None:
    other_day = DAY + timedelta(weeks=1)
    records = [signed(version=1), field_set(), signed(version=2), signed(other_day, version=1)]
    assert audit.latest_signature(records, DAY) == records[2]
    assert audit.latest_signature(records, other_day) == records[3]
    assert audit.latest_signature(records, DAY - timedelta(weeks=1)) is None
    assert audit.latest_signature([], DAY) is None


def test_export_rows_have_a_fixed_string_only_schema() -> None:
    rows = audit.export_rows([signed(), field_set(), intake()])
    assert len(rows) == 3
    for row in rows:
        assert list(row) == EXPORT_COLUMNS
        assert all(isinstance(value, str) for value in row.values())
        assert row["planning_day"] == "2025-12-29"
        assert row["recorded_at"] == "2026-10-02T09:05:00+09:30"
    plan, field, read = rows
    assert plan["what"] == "plan signed, version 1"
    assert plan["who"] == "R. Coordinator"
    assert plan["detail"] == (
        "Balanced: 2 trips, 10 repairs, 3 overdue left; added R-01: tenant called twice"
    )
    assert field["detail"] == "JR-2025-00001: safety_class = urgent"
    assert read["who"] == "claude (sonnet)"
    assert read["reason"] == ""
    assert read["detail"] == "JR-2025-00002: extracted (verified), 11.4 s"


def test_export_without_changes_says_so() -> None:
    (row,) = audit.export_rows([signed(changes=())])
    assert row["detail"].endswith("; no changes")


def test_export_hash_is_stable_and_tells_records_apart(tmp_path) -> None:
    records = [signed(), field_set(), intake()]
    first = [row["hash"] for row in audit.export_rows(records)]
    assert first == [row["hash"] for row in audit.export_rows(records)]
    assert all(len(h) == 12 and int(h, 16) >= 0 for h in first)
    assert len(set(first)) == 3
    log = tmp_path / "audit.jsonl"
    for record in records:
        audit.append(log, record)
    assert [row["hash"] for row in audit.export_rows(audit.read(log))] == first
    changed = audit.export_rows([signed(reason="Another reason")])[0]["hash"]
    assert changed != first[0]
