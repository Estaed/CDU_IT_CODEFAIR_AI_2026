"""Read the frozen FS17 policy-passage index (PRD section 5)."""

import json
from dataclasses import dataclass
from pathlib import Path

from fair_turn.core.types import FaultType
from fair_turn.core.verify_spans import normalise
from fair_turn.data.artefacts import BUILD_DIR


@dataclass(frozen=True)
class Passage:
    section: str
    text: str
    score: float
    title: str
    effective_date: str


@dataclass(frozen=True)
class PolicyIndex:
    available: bool
    source: dict
    threshold: float
    embed_model: str
    keys: dict[str, tuple[Passage, ...]]


def key_for(safety_class: str, is_remote: bool, fault_type: FaultType | str | None) -> str:
    """Return the stable build and runtime key for a job's typed fields."""
    fault = fault_type.value if isinstance(fault_type, FaultType) else fault_type or ""
    place = "remote" if is_remote else "town"
    return f"{safety_class}|{place}|{fault}"


def load(path: Path | None = None) -> PolicyIndex:
    """Load the committed index; a missing artefact leaves policy unavailable."""
    index_path = path or BUILD_DIR / "policy_passages.json"
    if not index_path.exists():
        return PolicyIndex(False, {}, 0.0, "", {})

    raw = json.loads(index_path.read_text(encoding="utf-8"))
    source = raw["source"]
    title = str(source["title"])
    effective_date = str(source["effective_date"])
    keys = {
        key: tuple(
            Passage(
                section=str(row["section"]),
                text=str(row["text"]),
                score=float(row["score"]),
                title=title,
                effective_date=effective_date,
            )
            for row in rows
        )
        for key, rows in raw["keys"].items()
    }
    return PolicyIndex(True, source, float(raw["threshold"]), str(raw["embed_model"]), keys)


def lookup(
    index: PolicyIndex,
    safety_class: str,
    is_remote: bool,
    fault_type: FaultType | str | None,
) -> list[Passage]:
    """Use a fault-specific result when present, then the class-and-place result."""
    passages = index.keys.get(key_for(safety_class, is_remote, fault_type), ())
    if passages:
        return list(passages)
    return list(index.keys.get(key_for(safety_class, is_remote, None), ()))


def verify(index: PolicyIndex, document_text: str) -> bool:
    """Check that all stored passages remain literal spans of the source document."""
    document = normalise(document_text)
    return all(
        normalise(passage.text) in document for rows in index.keys.values() for passage in rows
    )
