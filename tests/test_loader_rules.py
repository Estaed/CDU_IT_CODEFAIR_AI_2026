"""The artefact loader never ranks a job the extractor sent to a person."""

from datetime import date

from fair_turn.data import artefacts

COMMUNITY = {"is_remote": "True", "logistics_factor": "40"}
LABEL = {"job_id": "JR-1", "community_id": "c1", "reported_on": "2025-10-06"}


def _row(needs_human: bool, markers: list[str]) -> artefacts.ExtractionRow:
    return artefacts.ExtractionRow(
        job_id="JR-1",
        is_adversarial=False,
        kept={
            "fault_type": {"value": "electrical", "evidence": "power out"},
            "safety_class": {"value": "immediate", "evidence": "sparking"},
            "health_risk:elderly": {"value": "elderly", "evidence": "nan is 80"},
        },
        dropped={},
        substring_ok=True,
        needs_human=needs_human,
        injection_markers=markers,
    )


def test_a_row_marked_for_a_person_is_not_ranked() -> None:
    job = artefacts._job(LABEL, _row(True, ["rank it first"]), COMMUNITY)
    assert job.needs_human
    assert job.reported_on == date(2025, 10, 6)
    assert {f.value for f in job.health_risk} == {"elderly"}


def test_a_coordinator_value_still_ranks_a_row_marked_for_a_person() -> None:
    values = {"fault_type": "electrical", "safety_class": "urgent"}
    job = artefacts._job(LABEL, _row(True, ["rank it first"]), COMMUNITY, values)
    assert not job.needs_human
    assert job.safety_class.value == "urgent"


def test_a_clean_row_is_ranked() -> None:
    assert not artefacts._job(LABEL, _row(False, []), COMMUNITY).needs_human
