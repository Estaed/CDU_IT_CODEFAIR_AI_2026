"""Runtime records preserve coordinator fields and rank completed jobs (PRD 3.2)."""

from datetime import date, datetime

from fair_turn.core import constants, weekly
from fair_turn.data import artefacts, runtime


def test_round_trip_and_duplicate_intake_draft_token(tmp_path) -> None:
    path = tmp_path / "runtime.jsonl"
    field = runtime.HumanSetField(
        "JR-2025-00001", "fault_type", "electrical", "Ada", "report", datetime.now()
    )
    intake = runtime.IntakeReport(
        "JR-2025-01453",
        "C-01",
        date(2025, 10, 1),
        "The wiring sparks.",
        {"fault_type": "electrical", "safety_class": "urgent", "health_risk": []},
        "extracted",
        "claude",
        "sonnet",
        "v1",
        1.2,
        {"ok": True},
        "draft-1",
        datetime.now(),
    )

    assert runtime.append(path, field) is True
    assert runtime.append(path, intake) is True
    assert runtime.append(path, intake) is False
    assert runtime.read(path) == [field, intake]
    assert len(path.read_text("utf-8").splitlines()) == 2
    assert runtime.human_set_for(runtime.read(path)) == {
        "JR-2025-00001": {"fault_type": "electrical"}
    }


def test_read_skips_a_truncated_or_unknown_line(tmp_path) -> None:
    path = tmp_path / "runtime.jsonl"
    first = runtime.HumanSetField(
        "JR-2025-00001", "fault_type", "electrical", "Ada", "report", datetime(2025, 12, 29, 9)
    )
    last = runtime.HumanSetField(
        "JR-2025-00002", "safety_class", "urgent", "Ada", "phone", datetime(2025, 12, 29, 10)
    )
    runtime.append(path, first)
    with open(path, "a", encoding="utf-8", newline="") as f:
        f.write('{"kind": "human_set", "job_id": "JR-2025-0\n')  # cut off mid-write
        f.write('{"kind": "promotion", "job_id": "JR-2025-00003"}\n')  # an older kind
        f.write('{"kind": "human_set", "job_id": "JR-2025-00004"}\n')  # fields missing
        f.write('{"job_id": "JR-2025-00005"}\n')  # no kind
        f.write("\n")
    runtime.append(path, last)
    assert runtime.read(path) == [first, last]


def test_next_job_id_uses_highest_valid_existing_id() -> None:
    assert runtime.next_job_id([]) == "JR-2025-00001"
    assert runtime.next_job_id(["JR-2025-01452", "not-a-job", "JR-2025-00007"]) == "JR-2025-01453"


def test_human_set_field_moves_job_from_review_queue_into_the_plan() -> None:
    row = artefacts.ExtractionRow(
        job_id="JR-2025-00001",
        is_adversarial=False,
        kept={"safety_class": artefacts.Evidence(value="urgent", evidence="urgent")},
        dropped={"fault_type": "missing"},
        substring_ok=False,
        needs_human=True,
        injection_markers=[],
    )
    art = artefacts.Artefacts(
        communities={"C-01": {"is_remote": "False", "logistics_factor": "0"}},
        labels=[{"job_id": "JR-2025-00001", "community_id": "C-01", "reported_on": "2025-10-01"}],
        reports={"JR-2025-00001": "The wiring sparks."},
        extraction={"JR-2025-00001": row},
        closures=[],
        climate=[],
        audit_path=None,
    )
    today = constants.PLAN_DAY
    places = {"C-01": weekly.Place("C-01", "Darwin", True, 0.0, 0.0, 0.0)}

    (job,) = artefacts.to_jobs(art)
    assert job.needs_human and not weekly.in_plan(job, today)

    jobs = artefacts.to_jobs(art, human_set={"JR-2025-00001": {"fault_type": "electrical"}})
    assert not jobs[0].needs_human
    plan = weekly.plan(jobs, places, today, 0.0)
    assert plan.planned_job_ids() == {"JR-2025-00001"}
