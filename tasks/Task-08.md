# Task-08: Extraction schema and source-phrase verification

Status: DONE

> **Execution:** agent `claude` (main loop) · effort `high` · plan mode **no**
> *Why:* 2026-09-12 — rerouted from `codex` and done in the main loop: Codex is held back until the Claude window renews, and this task gates 09, 10 and 11 which spend that window. Original reason: the schema is the contract both CLIs receive and the substring rule is the grounding invariant; both fully specified in PRD §5 and Part 2.

**Lane**
- OWNS: `fair_turn/llm/schema.py`, `fair_turn/core/verify_spans.py`, `tests/test_schema.py`, `tests/test_verify_spans.py`
- MUST NOT TOUCH: `fair_turn/core/types.py` (Task-02), `fair_turn/llm/claude_cli.py` and `codex_cli.py` (Task-09)
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-02

## Objective

One pydantic model that emits the JSON Schema the extractor is constrained to and that
validates every returned object, plus the Python rule that decides whether a field may
be shown at all.

## Execution Guide

- `schema.py`: `Extraction(BaseModel)` with `model_config = ConfigDict(extra="forbid")`; fields `fault_type: FaultType`, `fault_type_evidence: str`, `safety_class: SafetyClass`, `safety_class_evidence: str`, `health_risk: list[HealthRiskFactor]`, `health_risk_evidence: list[str]` (same length), `location_mentioned: bool`, `location_evidence: str`, `crew_or_access_note: str` (empty allowed). No confidence field, ever. `json_schema() -> dict` from `model_json_schema()` with enums and `additionalProperties: false` asserted present.
- `verify_spans.py` (core, pure): `verify(report_text, extraction_dict) -> VerifiedExtraction`: each field kept only if its evidence is a literal substring of `report_text` (case-sensitive, whitespace-normalised on both sides); a failed required field (fault_type, safety_class) becomes `None`, a failed health-risk factor is dropped; returns the kept fields, the dropped ones, and `substring_ok: bool`.
- Tests: schema has the enums and `additionalProperties` false; extra key rejected; evidence that is not a substring drops the field; whitespace normalisation keeps a match across a line break; full-match input keeps everything.

## Acceptance Criteria (DoD)

- [x] `json_schema()` contains `"additionalProperties": false` at the top level and every enum.
- [x] `verify` never returns a displayed field without a matching span (tested with hypothesis over random substrings and non-substrings).
- [x] Gate green.
