"""The grounding rule: a field is shown only if its evidence is a literal substring of the
report (PRD section 5). Pure Python over a plain dict, so it runs on every artefact on
load and in the gate without pydantic.
"""

from dataclasses import dataclass, field

REQUIRED_FIELDS = ("fault_type", "safety_class")


@dataclass(frozen=True)
class VerifiedExtraction:
    fault_type: str | None
    safety_class: str | None
    health_risk: tuple[str, ...]
    location_mentioned: bool
    crew_or_access_note: str
    kept: dict[str, str] = field(default_factory=dict)  # field -> evidence that verified
    dropped: dict[str, str] = field(default_factory=dict)  # field -> evidence that did not
    substring_ok: bool = True  # every evidence phrase the model gave was found

    @property
    def needs_human(self) -> bool:
        return self.fault_type is None or self.safety_class is None


def normalise(text: str) -> str:
    """Whitespace-collapsed, case preserved: a phrase may wrap across a line break in the
    report and still be the same phrase."""
    return " ".join(text.split())


def is_span(evidence: str, report_text: str) -> bool:
    return bool(evidence.strip()) and normalise(evidence) in normalise(report_text)


def verify(report_text: str, extraction: dict) -> VerifiedExtraction:
    """Keep each field only if its evidence is a span of ``report_text``. A failed required
    field becomes ``None`` (the job goes to the human queue); a failed health-risk factor
    is dropped; an unverified location is not mentioned; an unverified note is emptied."""
    kept: dict[str, str] = {}
    dropped: dict[str, str] = {}

    def check(name: str, evidence: str) -> bool:
        ok = is_span(evidence, report_text)
        (kept if ok else dropped)[name] = evidence
        return ok

    values = {}
    for name in REQUIRED_FIELDS:
        value = extraction.get(name)
        ok = value is not None and check(name, str(extraction.get(f"{name}_evidence", "")))
        values[name] = str(value) if ok else None

    factors = list(extraction.get("health_risk") or [])
    evidence = list(extraction.get("health_risk_evidence") or [])
    evidence += [""] * (len(factors) - len(evidence))
    health_risk = tuple(
        str(f) for f, e in zip(factors, evidence, strict=True) if check(f"health_risk:{f}", str(e))
    )

    location = bool(extraction.get("location_mentioned")) and check(
        "location_mentioned", str(extraction.get("location_evidence", ""))
    )
    note = str(extraction.get("crew_or_access_note") or "")
    if note and not check("crew_or_access_note", note):
        note = ""

    return VerifiedExtraction(
        fault_type=values["fault_type"],
        safety_class=values["safety_class"],
        health_risk=health_risk,
        location_mentioned=location,
        crew_or_access_note=note,
        kept=kept,
        dropped=dropped,
        substring_ok=not dropped,
    )
