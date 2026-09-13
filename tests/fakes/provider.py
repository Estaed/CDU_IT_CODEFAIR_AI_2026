"""Fixed provider calls for Task-28's intake seam tests."""

from fair_turn.llm.claude_cli import CliError

SAMPLE_TEXT = "The ceiling wire is sparking near the baby's room and the house is hot."


def valid_call(prompt: str, schema: dict) -> dict:
    return {
        "fault_type": "electrical",
        "fault_type_evidence": "ceiling wire is sparking",
        "safety_class": "immediate",
        "safety_class_evidence": "wire is sparking",
        "health_risk": ["infant_or_young_child", "extreme_heat_exposure"],
        "health_risk_evidence": ["baby's room", "house is hot"],
        "location_mentioned": True,
        "location_evidence": "near the baby's room",
        "crew_or_access_note": "",
    }


def wrong_phrase_call(prompt: str, schema: dict) -> dict:
    value = valid_call(prompt, schema)
    value["safety_class_evidence"] = "this phrase is not in the report"
    return value


def invalid_call(prompt: str, schema: dict) -> dict:
    value = valid_call(prompt, schema)
    del value["safety_class"]
    return value


def raising_call(prompt: str, schema: dict) -> dict:
    raise CliError("fake failure")


def timeout_call(prompt: str, schema: dict) -> dict:
    raise TimeoutError("fake timeout")
