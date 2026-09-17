"""The extraction contract: one pydantic model that emits the JSON Schema both CLIs are
constrained to and validates every object they return (PRD section 5, Blueprint).

Every categorical field is an enum from ``core.types``; every displayed field carries an
evidence phrase that ``core.verify_spans`` checks against the report text. There is no
confidence field and there never will be (Blueprint Key Constraints).
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

from fair_turn.core.types import FaultType, HealthRiskFactor, SafetyClass


class Extraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fault_type: FaultType
    fault_type_evidence: str
    safety_class: SafetyClass
    safety_class_evidence: str
    health_risk: list[HealthRiskFactor]
    health_risk_evidence: list[str]
    location_mentioned: bool
    location_evidence: str
    crew_or_access_note: str  # empty allowed; anything else must be a quote from the report

    @model_validator(mode="after")
    def _evidence_matches_factors(self) -> "Extraction":
        if len(self.health_risk) != len(self.health_risk_evidence):
            raise ValueError("health_risk and health_risk_evidence must have the same length")
        return self


def _inline_refs(node: Any, defs: dict[str, Any]) -> Any:
    """Replace every ``$ref`` with its definition so the schema is one self-contained
    object: the CLIs' schema flags were spiked with inline enums, not ``$defs``."""
    if isinstance(node, dict):
        if "$ref" in node:
            name = node["$ref"].rsplit("/", 1)[-1]
            return _inline_refs({k: v for k, v in defs[name].items() if k != "title"}, defs)
        return {k: _inline_refs(v, defs) for k, v in node.items() if k != "$defs"}
    if isinstance(node, list):
        return [_inline_refs(v, defs) for v in node]
    return node


def json_schema() -> dict[str, Any]:
    """The schema handed to ``claude -p --json-schema`` and ``codex exec --output-schema``."""
    raw = Extraction.model_json_schema()
    schema = _inline_refs(raw, raw.get("$defs", {}))
    assert schema["additionalProperties"] is False
    for enum in (FaultType, SafetyClass, HealthRiskFactor):
        assert [str(m) for m in enum] in _enums(schema), enum
    return schema


def _enums(node: Any) -> list[list[str]]:
    if isinstance(node, dict):
        found = [node["enum"]] if "enum" in node else []
        for v in node.values():
            found.extend(_enums(v))
        return found
    if isinstance(node, list):
        return [e for v in node for e in _enums(v)]
    return []
