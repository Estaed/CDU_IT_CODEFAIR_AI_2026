"""The extraction schema: enums inline, no extra keys, no confidence, evidence per factor."""

import json

import pytest
from pydantic import ValidationError

from fair_turn.core.types import FaultType, HealthRiskFactor, SafetyClass
from fair_turn.llm import schema

VALID = {
    "fault_type": "cooling",
    "fault_type_evidence": "aircon dead",
    "safety_class": "urgent",
    "safety_class_evidence": "three days now",
    "health_risk": ["infant_or_young_child"],
    "health_risk_evidence": ["baby in the house"],
    "location_mentioned": True,
    "location_evidence": "back bedroom",
    "crew_or_access_note": "",
}


def test_schema_is_closed_and_carries_every_enum() -> None:
    s = schema.json_schema()
    assert s["additionalProperties"] is False
    assert "$defs" not in json.dumps(s)
    assert s["properties"]["fault_type"]["enum"] == [str(f) for f in FaultType]
    assert s["properties"]["safety_class"]["enum"] == [str(c) for c in SafetyClass]
    assert s["properties"]["health_risk"]["items"]["enum"] == [str(f) for f in HealthRiskFactor]
    assert set(s["required"]) == set(s["properties"])
    assert not any("confidence" in key for key in s["properties"])


def test_valid_object_round_trips() -> None:
    e = schema.Extraction.model_validate(VALID)
    assert e.fault_type is FaultType.COOLING
    assert e.model_dump(mode="json") == VALID


def test_extra_key_rejected() -> None:
    with pytest.raises(ValidationError):
        schema.Extraction.model_validate({**VALID, "confidence": 0.9})


def test_unknown_enum_value_rejected() -> None:
    with pytest.raises(ValidationError):
        schema.Extraction.model_validate({**VALID, "fault_type": "aircon"})


def test_factor_and_evidence_lengths_must_match() -> None:
    with pytest.raises(ValidationError):
        schema.Extraction.model_validate({**VALID, "health_risk_evidence": []})
