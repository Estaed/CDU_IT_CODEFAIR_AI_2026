"""Source-phrase verification: substring rule, whitespace normalisation, drops on failure,
and the property that no displayed field ever lacks a matching span."""

from hypothesis import given, settings
from hypothesis import strategies as st

from fair_turn.core import verify_spans

REPORT = (
    "The aircon has been dead for three\n"
    "days now and there is a baby in the house. It is the unit in the back bedroom.\n"
    "Road in is fine, the crew came last month."
)
FULL = {
    "fault_type": "cooling",
    "fault_type_evidence": "aircon has been dead",
    "safety_class": "urgent",
    "safety_class_evidence": "three days now",
    "health_risk": ["infant_or_young_child", "extreme_heat_exposure"],
    "health_risk_evidence": ["baby in the house", "aircon has been dead"],
    "location_mentioned": True,
    "location_evidence": "back bedroom",
    "crew_or_access_note": "Road in is fine",
}


def test_full_match_keeps_everything() -> None:
    v = verify_spans.verify(REPORT, FULL)
    assert v.fault_type == "cooling"
    assert v.safety_class == "urgent"
    assert v.health_risk == ("infant_or_young_child", "extreme_heat_exposure")
    assert v.location_mentioned is True
    assert v.crew_or_access_note == "Road in is fine"
    assert v.substring_ok and not v.dropped and not v.needs_human


def test_whitespace_normalisation_matches_across_a_line_break() -> None:
    v = verify_spans.verify(REPORT, {**FULL, "safety_class_evidence": "dead for three days"})
    assert v.safety_class == "urgent"
    assert verify_spans.is_span("three   days", REPORT)


def test_case_is_significant() -> None:
    assert not verify_spans.is_span("Aircon", REPORT)


def test_required_field_without_span_goes_to_human_queue() -> None:
    v = verify_spans.verify(REPORT, {**FULL, "fault_type_evidence": "the fan is broken"})
    assert v.fault_type is None
    assert v.needs_human
    assert v.dropped == {"fault_type": "the fan is broken"}
    assert not v.substring_ok


def test_failed_factor_is_dropped_and_others_kept() -> None:
    bad = {**FULL, "health_risk_evidence": ["baby in the house", "it is 45 degrees"]}
    v = verify_spans.verify(REPORT, bad)
    assert v.health_risk == ("infant_or_young_child",)
    assert v.dropped == {"health_risk:extreme_heat_exposure": "it is 45 degrees"}


def test_unverified_location_and_note_are_cleared() -> None:
    bad = {**FULL, "location_evidence": "kitchen", "crew_or_access_note": "barge only"}
    v = verify_spans.verify(REPORT, bad)
    assert v.location_mentioned is False
    assert v.crew_or_access_note == ""
    assert set(v.dropped) == {"location_mentioned", "crew_or_access_note"}


def test_empty_evidence_never_verifies() -> None:
    v = verify_spans.verify(REPORT, {**FULL, "fault_type_evidence": "   "})
    assert v.fault_type is None


def test_missing_keys_do_not_crash() -> None:
    v = verify_spans.verify(REPORT, {})
    assert v.needs_human and v.health_risk == () and v.crew_or_access_note == ""


@settings(max_examples=300)
@given(
    report=st.text(min_size=1, max_size=200),
    evidence=st.text(max_size=40),
    data=st.data(),
)
def test_displayed_fields_always_have_a_span(report: str, evidence: str, data) -> None:
    # Half the evidence strings are true slices of the report, the rest arbitrary.
    if data.draw(st.booleans()):
        start = data.draw(st.integers(0, len(report) - 1))
        end = data.draw(st.integers(start + 1, len(report)))
        evidence = report[start:end]
    v = verify_spans.verify(
        report,
        {
            "fault_type": "other",
            "fault_type_evidence": evidence,
            "safety_class": "routine",
            "safety_class_evidence": evidence,
            "health_risk": ["elderly"],
            "health_risk_evidence": [evidence],
            "location_mentioned": True,
            "location_evidence": evidence,
            "crew_or_access_note": evidence,
        },
    )
    for name, span in v.kept.items():
        assert verify_spans.is_span(span, report), name
    if v.fault_type is not None:
        assert "fault_type" in v.kept
    if v.health_risk:
        assert "health_risk:elderly" in v.kept
    if v.location_mentioned:
        assert "location_mentioned" in v.kept
    if v.crew_or_access_note:
        assert "crew_or_access_note" in v.kept
    assert v.substring_ok == (not v.dropped)
    assert set(v.kept).isdisjoint(v.dropped)
