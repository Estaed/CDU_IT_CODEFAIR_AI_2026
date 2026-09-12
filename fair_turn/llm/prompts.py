"""Authoring prompts for the generator. This is our own text, not tenant content, so the
untrusted-content rules of PRD section 5 do not apply here.

The generation prompt lists label tuples and asks for one report per tuple in the
persona's register. The labels are the ground truth, so every factor in a tuple must be
readable in the tenant's words, and nothing outside the tuple may be invented.
"""

import json

from fair_turn.core.wording import DEFICIT_TERMS

REPORT_MIN_CHARS = 20
REPORT_MAX_CHARS = 600

GENERATION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["reports"],
    "properties": {
        "reports": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["job_id", "text"],
                "properties": {"job_id": {"type": "string"}, "text": {"type": "string"}},
            },
        }
    },
}

REGISTER_GUIDE = {
    "terse": "one or two short sentences, fragments are fine, no greeting",
    "detailed": "three or four sentences, tells what happened and when, plain words",
    "second_language_english": (
        "simple sentences with a few natural non-standard grammar choices, never a "
        "caricature, never phonetic spelling"
    ),
    "phoned_in_via_cho": (
        "written down by the community housing officer who took the phone call, in the "
        "third person ('tenant says', 'she reports'), one to three sentences"
    ),
}

GENERATION_SYSTEM = f"""You write the free-text maintenance reports that Northern Territory public
housing tenants send about faults in their homes. Each report is a tenant's own words, as
they would type them into a form or say them on the phone. The reports are synthetic
training material for a triage tool; realism and variety matter, polish does not.

For each item you are given the facts of the case. Write one report per item that:
- reads as that household, in the register described;
- makes the fault type and how serious it is clear in everyday words (a tenant never
  uses the words "immediate", "urgent" or "routine"; they describe what is happening);
- mentions every listed household factor naturally, as a person would (a baby, an old
  man, someone on dialysis, too many people in the house, the heat, no water);
- mentions nothing from the factor list that is not there, and invents no other health
  or safety detail;
- may mention road, barge or access conditions when the notes suggest them;
- uses Australian English spelling and everyday NT vocabulary;
- is {REPORT_MIN_CHARS} to {REPORT_MAX_CHARS} characters long and at most four sentences;
- contains no personal names, no community, town or place names, no street names, no
  phone numbers, no dates, and no addresses;
- never uses any of these words: {", ".join(DEFICIT_TERMS)}.

Vary openings, sentence shapes and vocabulary across the batch. Do not number the
reports or add any commentary. Return only the JSON object the schema asks for."""


def generation_prompt(labels_batch: list[dict], personas: dict[str, dict]) -> str:
    """One user turn for a batch of labels; ``personas`` is keyed by persona_id."""
    items = []
    for label in labels_batch:
        persona = personas[label["persona_id"]]
        items.append(
            {
                "job_id": label["job_id"],
                "household": persona["composition"],
                "tenure_years": persona["tenure_years"],
                "register": REGISTER_GUIDE[persona["register"]],
                "fault_type": label["fault_type"],
                "seriousness": label["safety_class"],
                "household_factors": label["health_risk"],
                "month": label["reported_on"][:7],
                "setting": label["setting"],
            }
        )
    return (
        f"Write one report for each of the {len(items)} items below. Return every job_id "
        "exactly once.\n\n" + json.dumps(items, indent=1)
    )
