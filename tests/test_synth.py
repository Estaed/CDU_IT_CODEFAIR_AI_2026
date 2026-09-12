"""The committed synthetic artefacts: determinism, the built-in skew, shape, and no leaks."""

import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

from _real_names import real_names

from fair_turn.core import constants
from fair_turn.core.types import FaultType, HealthRiskFactor, SafetyClass
from fair_turn.data import geography, synth

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "data" / "build"
ARTEFACTS = ("labels.json", "personas.json", "closures.json", "climate.csv")

COMMUNITIES = geography.load_communities()
LABELS = json.loads((BUILD / "labels.json").read_text("utf-8"))
CLOSURES = json.loads((BUILD / "closures.json").read_text("utf-8"))
PERSONAS = json.loads((BUILD / "personas.json").read_text("utf-8"))
REMOTE_IDS = set(COMMUNITIES.loc[COMMUNITIES["is_remote"], "community_id"])


def test_build_is_deterministic() -> None:
    first = synth.render_all(COMMUNITIES)
    second = synth.render_all(COMMUNITIES)
    for name in ARTEFACTS:
        assert first[name] == second[name]
        assert first[name] == (BUILD / name).read_bytes(), f"{name} differs from committed"


def test_volume_and_remote_share() -> None:
    assert 1350 <= len(LABELS) <= 1650
    remote = sum(label["community_id"] in REMOTE_IDS for label in LABELS)
    assert 0.55 <= remote / len(LABELS) <= 0.65


def test_holdout_count_and_no_adversarial_yet() -> None:
    assert sum(label["is_holdout"] for label in LABELS) == synth.HOLDOUT_COUNT == 150
    assert not any(label["is_adversarial"] for label in LABELS)


def test_label_fields_are_typed_and_joinable() -> None:
    ids = set(COMMUNITIES["community_id"])
    personas = {p["persona_id"] for p in PERSONAS}
    faults = {str(f) for f in FaultType}
    classes = {str(c) for c in SafetyClass}
    factors = {str(f) for f in HealthRiskFactor}
    job_ids = [label["job_id"] for label in LABELS]
    assert len(set(job_ids)) == len(job_ids)
    assert job_ids == sorted(job_ids)
    for label in LABELS:
        assert re.fullmatch(r"JR-\d{4}-\d{5}", label["job_id"])
        assert label["community_id"] in ids
        assert label["persona_id"] in personas
        assert label["fault_type"] in faults
        assert label["safety_class"] in classes
        assert set(label["health_risk"]) <= factors
        day = date.fromisoformat(label["reported_on"])
        assert constants.WINDOW_START <= day <= synth.WINDOW_END


def test_every_fault_and_class_present() -> None:
    assert {label["fault_type"] for label in LABELS} == {str(f) for f in FaultType}
    assert {label["safety_class"] for label in LABELS} == {str(c) for c in SafetyClass}


def test_personas() -> None:
    assert len(PERSONAS) == 40
    assert {p["register"] for p in PERSONAS} == set(synth.REGISTERS)
    factors = {str(f) for f in HealthRiskFactor}
    for p in PERSONAS:
        assert set(p["household_factors"]) <= factors
        assert p["composition"] == p["composition"].lower()  # no capitalised names


def test_no_real_community_name_in_artefacts() -> None:
    names = real_names()
    for name in ARTEFACTS:
        text = (BUILD / name).read_text("utf-8").upper()
        hits = [n for n in names if re.search(rf"(?<![A-Z]){re.escape(n)}(?![A-Z])", text)]
        assert not hits, (name, hits)


def test_closures_remote_only_inside_window_and_rising() -> None:
    closable = set(COMMUNITIES.loc[COMMUNITIES["wet_season_closable"], "community_id"])
    assert closable <= REMOTE_IDS
    closed_days: Counter[int] = Counter()
    for row in CLOSURES:
        assert row["community_id"] in closable
        assert row["source"] == "synthetic"
        start, end = date.fromisoformat(row["closed_from"]), date.fromisoformat(row["closed_to"])
        assert constants.WINDOW_START <= start <= end <= synth.WINDOW_END
        day = start
        while day <= end:
            closed_days[day.month] += 1
            day = date.fromordinal(day.toordinal() + 1)
    assert closed_days[10] < closed_days[11] < closed_days[12]


def test_climate_shape_and_heat_flag() -> None:
    rows = (BUILD / "climate.csv").read_text("utf-8").splitlines()
    assert rows[0] == "date,region,max_temp_c,heat_warning"
    assert len(rows) - 1 == len(constants.REGIONS) * constants.WINDOW_DAYS
    flags = {r.rsplit(",", 1)[1] for r in rows[1:]}
    assert flags <= {"True", "False"}
    assert "True" in flags


def test_heat_exposure_is_from_the_dwelling_or_cooling_on_a_warning_day() -> None:
    warning = {(r["region"], r["date"]) for r in synth.draw_climate() if r["heat_warning"]}
    region = dict(zip(COMMUNITIES["community_id"], COMMUNITIES["region"], strict=True))
    heat = str(HealthRiskFactor.EXTREME_HEAT_EXPOSURE)
    carried = {p["persona_id"] for p in PERSONAS if heat in p["household_factors"]}
    situational = 0
    for label in LABELS:
        if heat in label["health_risk"] and label["persona_id"] not in carried:
            situational += 1
            assert label["fault_type"] == str(FaultType.COOLING)
            assert (region[label["community_id"]], label["reported_on"]) in warning
    assert situational > 0
