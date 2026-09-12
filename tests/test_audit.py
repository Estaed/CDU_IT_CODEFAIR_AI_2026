"""Round-trip, byte-stability and override-rate tests for the audit log."""

from datetime import date, datetime
from pathlib import Path

from fair_turn.core import audit


def _sign_off(
    day: date = date(2026, 9, 1),
    ranked: tuple[str, ...] = ("job-1", "job-2", "job-3", "job-4"),
):
    return audit.SignOff(
        day=day,
        lam=1.5,
        reason="weekly sign-off",
        signer="coordinator",
        signed_at=datetime(2026, 9, 1, 9, 0),
        ranked_job_ids=ranked,
    )


def _revision(day: date = date(2026, 9, 1)):
    return audit.Revision(
        day=day,
        old_lam=1.0,
        new_lam=1.5,
        reason="fuel price rose",
        at=datetime(2026, 9, 1, 9, 5),
    )


def _override(day: date = date(2026, 9, 1), job_id: str = "job-3"):
    return audit.Override(
        day=day,
        job_id=job_id,
        from_rank=3,
        to_rank=1,
        reason="crew already on site",
        at=datetime(2026, 9, 1, 9, 10),
    )


def test_round_trip_preserves_all_three_kinds(tmp_path: Path) -> None:
    path = tmp_path / "log.jsonl"
    records = [_sign_off(), _revision(), _override()]
    for r in records:
        audit.append(path, r)
    assert audit.read(path) == records


def test_read_on_missing_file_returns_empty_list(tmp_path: Path) -> None:
    assert audit.read(tmp_path / "missing.jsonl") == []


def test_read_on_empty_file_returns_empty_list(tmp_path: Path) -> None:
    path = tmp_path / "empty.jsonl"
    path.write_text("", encoding="utf-8")
    assert audit.read(path) == []


def test_export_rows_has_same_count_and_flat_fields(tmp_path: Path) -> None:
    records = [_sign_off(), _revision(), _override()]
    rows = audit.export_rows(records)
    assert len(rows) == len(records)
    assert rows[0]["kind"] == "sign_off"
    assert rows[0]["day"] == "2026-09-01"
    assert rows[0]["ranked_job_ids"] == ["job-1", "job-2", "job-3", "job-4"]
    assert rows[2]["kind"] == "override"
    assert rows[2]["job_id"] == "job-3"


def test_override_rate_fixture() -> None:
    records = [
        _sign_off(date(2026, 9, 1)),
        _override(date(2026, 9, 1), "job-3"),
        _override(date(2026, 9, 1), "job-4"),
        _sign_off(date(2026, 9, 2), ranked=("job-5", "job-6")),
    ]
    assert audit.override_rate(records) == [
        (date(2026, 9, 1), 0.5),
        (date(2026, 9, 2), 0.0),
    ]


def test_override_rate_ignores_a_day_with_no_sign_off() -> None:
    records = [_override(date(2026, 9, 3), "job-9")]
    assert audit.override_rate(records) == []


def test_second_append_does_not_alter_earlier_lines(tmp_path: Path) -> None:
    path = tmp_path / "log.jsonl"
    audit.append(path, _sign_off())
    first_bytes = path.read_bytes()

    audit.append(path, _revision())

    assert path.read_bytes()[: len(first_bytes)] == first_bytes
