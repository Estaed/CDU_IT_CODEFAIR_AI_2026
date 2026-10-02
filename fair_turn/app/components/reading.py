"""What the AI read from one report, every fact next to the tenant's own words.

A fact is shown only with the phrase it came from, and the phrase must be in the report. A
required fact without one is empty, and a person sets it. The model's rejected guess is
never shown: it would steer the person.
"""

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from fair_turn.app import state
from fair_turn.app.components.highlight import render, spans
from fair_turn.core import explain, verify_spans, wording
from fair_turn.data import runtime

LABELS = {
    "fault_type": "What is broken",
    "safety_class": "How urgent",
    "health_risk": "Household health risk",
    "location_mentioned": "Where in the house",
    "crew_or_access_note": "Access note",
}
STEERED = "Withheld: the report tries to instruct the AI, so a person reads it"
NOT_FOUND = "Not found: a person sets it"


@dataclass(frozen=True)
class Fact:
    field: str
    value: str
    phrase: str
    status: str


@dataclass(frozen=True)
class Reading:
    job_id: str
    community_id: str
    text: str
    facts: tuple[Fact, ...]
    missing: tuple[str, ...]  # required fields nobody has set yet
    steered: tuple[str, ...]  # instruction-like phrases found in the report
    source: str  # "test set" or the provider that read a new report


def _words(value) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value).replace("_", " ")


def reading(job_id: str) -> Reading:
    art = state.artefacts()
    set_by_hand = state.human_set(job_id)
    if job_id in art.extraction:
        row = art.extraction[job_id]
        text = art.reports[job_id]
        community = next(lb["community_id"] for lb in art.labels if lb["job_id"] == job_id)
        found = {name: (ev.value, ev.evidence) for name, ev in row.kept.items()}
        steered = tuple(row.injection_markers)
        source = "sample report, read by the AI (Claude Sonnet)"
    else:
        report = next(
            r
            for r in state.runtime_records()
            if isinstance(r, runtime.IntakeReport) and r.job_id == job_id
        )
        text, community = report.text, report.community_id
        verified = verify_spans.verify(text, report.extraction or {})
        values = {
            "fault_type": verified.fault_type,
            "safety_class": verified.safety_class,
            "location_mentioned": verified.location_mentioned,
            "crew_or_access_note": verified.crew_or_access_note,
        }
        found = {}
        for name, phrase in verified.kept.items():
            if name.startswith("health_risk:"):
                found[name] = (name.split(":", 1)[1], phrase)
            else:
                found[name] = (values[name], phrase)
        steered = tuple(wording.injection_markers(text))
        source = f"new report, read by {report.provider} ({report.model})"

    facts = []
    missing = []
    for name in verify_spans.REQUIRED_FIELDS:
        if name in set_by_hand:
            facts.append(Fact(name, _words(set_by_hand[name]), "", "Set by a person"))
        elif steered:
            facts.append(Fact(name, "", "", STEERED))
            missing.append(name)
        elif name in found:
            value, phrase = found[name]
            facts.append(Fact(name, _words(value), phrase, "Found in the report"))
        else:
            facts.append(Fact(name, "", "", NOT_FOUND))
            missing.append(name)
    for name, (value, phrase) in sorted(found.items()):
        if name in verify_spans.REQUIRED_FIELDS:
            continue
        field = "health_risk" if name.startswith("health_risk:") else name
        shown = {"location_mentioned": "mentioned", "crew_or_access_note": "noted"}.get(
            field, _words(value)
        )
        facts.append(Fact(field, shown, phrase, "Found in the report"))
    return Reading(job_id, community, text, tuple(facts), tuple(missing), steered, source)


def show(r: Reading) -> None:
    """The report with its phrases in bold, and the facts table."""
    evidence = {f"{f.field}:{i}": f.phrase for i, f in enumerate(r.facts) if f.phrase}
    with st.container(border=True):
        st.caption(f"{r.job_id} · {explain.place_name(r.community_id)} · {r.source}")
        st.markdown(render(r.text, spans(r.text, evidence)))
    if r.steered:
        st.warning(
            "This report contains words that try to give the AI instructions ("
            + ", ".join(f'"{m}"' for m in r.steered)
            + "). Its urgency and fault are not used until a person sets them."
        )
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Fact": LABELS[f.field],
                    "What the AI read": f.value,
                    "The tenant's words": f.phrase,
                    "Status": f.status,
                }
                for f in r.facts
            ]
        ),
        hide_index=True,
        width="stretch",
    )
