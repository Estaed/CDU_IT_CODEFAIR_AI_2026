"""Synthetic ground truth drawn in code before any model writes a word (PRD section 6.2).

Build once from the repo root (the files under ``data/build/`` are what everything reads):

    venv/Scripts/python scripts/build_labels.py

Every proportion in this module is a provisional modelling choice with a row in
``constants.md``; none is an NT figure. Two of the three town/remote skew mechanisms live
here on purpose: remote under-reporting (faults are thinned before they become reports) and
wet-season closures on remote access only. The third, logistics cost, is ``communities.csv``.
"""

import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from fair_turn.core.constants import REGIONS, SEED, TOWN_REGION, WINDOW_DAYS, WINDOW_START
from fair_turn.core.types import FaultType, HealthRiskFactor, SafetyClass
from fair_turn.data.geography import load_communities

ROOT = Path(__file__).resolve().parent.parent.parent
BUILD_DIR = ROOT / "data" / "build"
WINDOW_END = WINDOW_START + timedelta(days=WINDOW_DAYS - 1)
WINDOW_MONTHS = sorted({(WINDOW_START + timedelta(days=d)).month for d in range(WINDOW_DAYS)})

# --- volume and the town/remote split (mechanism 3, static part) --------------------------
REPORT_TARGET = 1500
REMOTE_REPORT_SHARE = 0.6
REMOTE_REPORT_RATE_RATIO = 0.8  # a remote fault becomes a report with this probability
HOLDOUT_COUNT = 150
POPULATION_BAND_MIDPOINTS = {
    "under 100": 50,
    "100-249": 175,
    "250-499": 375,
    "500-999": 750,
    "1000+": 1500,
    "not recorded": 100,
}
# Town rows carry no population band, so their share of town reports is fixed here.
TOWN_REPORT_WEIGHTS = {
    "Darwin": 0.55,
    "Alice Springs": 0.20,
    "Katherine": 0.12,
    "Nhulunbuy": 0.07,
    "Tennant Creek": 0.06,
}

# --- fault mix, with the within-window heat ramp ------------------------------------------
FAULT_MIX = {
    FaultType.PLUMBING_WATER: 0.20,
    FaultType.ELECTRICAL: 0.14,
    FaultType.DOORS_LOCKS_SECURITY: 0.12,
    FaultType.COOLING: 0.10,
    FaultType.SEWER_DRAINAGE: 0.10,
    FaultType.ROOF_STRUCTURE: 0.08,
    FaultType.HOT_WATER: 0.07,
    FaultType.STOVE_COOKING: 0.07,
    FaultType.PESTS: 0.06,
    FaultType.OTHER: 0.06,
}
# Multipliers by month on the base weight; the mix is renormalised per month.
HEAT_RAMP = {
    FaultType.COOLING: {10: 1.0, 11: 1.3, 12: 1.6},
    FaultType.HOT_WATER: {10: 1.0, 11: 1.1, 12: 1.2},
}

# --- safety class conditional on fault type: P(immediate, urgent, routine) ----------------
# Shaped by the FS17 examples (exposed wires immediate, blocked toilet urgent, dripping tap
# routine); FS17 publishes no proportions, so the numbers are ours.
SAFETY_MIX_BY_FAULT = {
    FaultType.ELECTRICAL: (0.30, 0.40, 0.30),
    FaultType.PLUMBING_WATER: (0.05, 0.50, 0.45),
    FaultType.SEWER_DRAINAGE: (0.10, 0.70, 0.20),
    FaultType.COOLING: (0.02, 0.30, 0.68),
    FaultType.HOT_WATER: (0.02, 0.45, 0.53),
    FaultType.ROOF_STRUCTURE: (0.10, 0.45, 0.45),
    FaultType.DOORS_LOCKS_SECURITY: (0.05, 0.55, 0.40),
    FaultType.STOVE_COOKING: (0.10, 0.30, 0.60),
    FaultType.PESTS: (0.00, 0.15, 0.85),
    FaultType.OTHER: (0.03, 0.27, 0.70),
}
SAFETY_ORDER = (SafetyClass.IMMEDIATE, SafetyClass.URGENT, SafetyClass.ROUTINE)

# --- situational health-risk factors --------------------------------------------------------
WATER_FAULTS = (FaultType.PLUMBING_WATER, FaultType.SEWER_DRAINAGE)
NO_WATER_PROBABILITY = 0.6  # for a water fault in the immediate or urgent class

# --- wet-season closures (mechanism 2) ------------------------------------------------------
CLOSURES_PER_MONTH = {10: 0.15, 11: 0.4, 12: 0.9}  # Poisson mean per closable community
CLOSURE_DAYS = (2, 10)  # inclusive uniform range

# --- climate: BoM monthly mean-maximum normals, degrees C, one station per region -----------
# UNVERIFIED: entered from memory on 2026-09-12 because bom.gov.au returned 403 to every
# fetch; see data/raw/PROVENANCE.md. Check by hand before the report cites them.
STATION_FOR_REGION = {
    "TOP END": "Darwin Airport 014015",
    TOWN_REGION: "Darwin Airport 014015",
    "BIG RIVERS": "Tindal RAAF 014932",
    "BARKLY": "Tennant Creek Airport 015135",
    "CENTRAL AUSTRALIA": "Alice Springs Airport 015590",
    "EAST ARNHEM": "Gove Airport 014508",
}
MONTHLY_MEAN_MAX = {
    "Darwin Airport 014015": {10: 33.2, 11: 33.3, 12: 33.3},
    "Tindal RAAF 014932": {10: 38.1, 11: 37.5, 12: 36.0},
    "Tennant Creek Airport 015135": {10: 36.3, 11: 37.6, 12: 37.7},
    "Alice Springs Airport 015590": {10: 31.0, 11: 33.6, 12: 35.4},
    "Gove Airport 014508": {10: 32.3, 11: 32.8, 12: 32.4},
}
TEMP_AR_PHI = 0.6  # day-to-day persistence of the anomaly, so hot spells cluster
TEMP_ANOMALY_SD = 2.5
HEAT_WARNING_EXCESS_C = 2.0  # EHF-style relative rule: this far above the month's normal
HEAT_WARNING_DAYS = 3  # for at least this many consecutive days

# --- personas the generator is conditioned on ----------------------------------------------
REGISTERS = ("terse", "detailed", "second_language_english", "phoned_in_via_cho")
_INFANT = HealthRiskFactor.INFANT_OR_YOUNG_CHILD
_ELDERLY = HealthRiskFactor.ELDERLY
_CHRONIC = HealthRiskFactor.PREGNANCY_OR_CHRONIC_CONDITION
_CROWDED = HealthRiskFactor.OVERCROWDING
_HEAT = HealthRiskFactor.EXTREME_HEAT_EXPOSURE  # a dwelling attribute: no shade, fans only
# (register, composition, tenure years, household factors). No names, no places.
_PERSONA_ROWS = [
    ("terse", "single adult, lives alone", 3, ()),
    ("terse", "couple, no children", 7, ()),
    ("terse", "two adults, two school-age children, house gets very hot by afternoon", 5, (_HEAT,)),
    ("terse", "grandmother raising two grandchildren, youngest is four", 12, (_ELDERLY, _INFANT)),
    ("terse", "young couple with a newborn", 1, (_INFANT,)),
    ("terse", "man in his seventies, lives alone", 20, (_ELDERLY,)),
    ("terse", "three adults, one on dialysis three days a week", 9, (_CHRONIC,)),
    ("terse", "two adults, four children, extended family staying for the season", 6, (_CROWDED,)),
    ("terse", "couple, one adult uses a wheelchair", 4, (_CHRONIC,)),
    ("terse", "shift worker, lives alone, home mostly at night", 2, ()),
    (
        "detailed",
        "two adults, three children under ten, the youngest eighteen months",
        4,
        (_INFANT,),
    ),
    ("detailed", "retired couple, both in their eighties", 25, (_ELDERLY,)),
    ("detailed", "single parent with two teenagers", 8, ()),
    ("detailed", "woman seven months pregnant, partner and a toddler", 2, (_CHRONIC, _INFANT)),
    (
        "detailed",
        "eleven people across three generations in a three-bedroom house",
        10,
        (_CROWDED, _ELDERLY, _INFANT),
    ),
    ("detailed", "two adults, one with severe asthma, no children", 3, (_CHRONIC,)),
    (
        "detailed",
        "couple with an adult son who has a disability and needs daily care",
        15,
        (_CHRONIC,),
    ),
    ("detailed", "four adults sharing, all working", 1, ()),
    ("detailed", "single adult caring for an elderly parent who lives there too", 6, (_ELDERLY,)),
    (
        "detailed",
        "two adults, two children, a relative recovering from surgery staying",
        5,
        (_CHRONIC,),
    ),
    (
        "second_language_english",
        "two adults, five children, youngest under one",
        7,
        (_INFANT, _CROWDED),
    ),
    ("second_language_english", "elderly woman, lives with her adult daughter", 18, (_ELDERLY,)),
    (
        "second_language_english",
        "large family, nine people, two of them under five",
        11,
        (_CROWDED, _INFANT),
    ),
    ("second_language_english", "couple expecting their first child next month", 1, (_CHRONIC,)),
    ("second_language_english", "single man, works at the local store", 3, ()),
    (
        "second_language_english",
        "two adults, three children in primary school, tin roof and no shade trees",
        6,
        (_HEAT,),
    ),
    (
        "second_language_english",
        "grandfather with a heart condition, two grandchildren and one other adult",
        14,
        (_ELDERLY, _CHRONIC),
    ),
    (
        "second_language_english",
        "couple, one adult with diabetes, one child aged two",
        4,
        (_CHRONIC, _INFANT),
    ),
    ("second_language_english", "three generations, seven people", 9, (_CROWDED,)),
    ("second_language_english", "young couple, no children yet", 1, ()),
    ("phoned_in_via_cho", "elderly man with limited mobility, lives alone", 22, (_ELDERLY,)),
    ("phoned_in_via_cho", "mother with newborn twins and a four-year-old", 3, (_INFANT,)),
    ("phoned_in_via_cho", "family of six, one adult with kidney disease", 8, (_CHRONIC,)),
    (
        "phoned_in_via_cho",
        "eight people in a three-bedroom house, two of them infants",
        5,
        (_CROWDED, _INFANT),
    ),
    (
        "phoned_in_via_cho",
        "couple in their sixties, both retired, west-facing house with fans only",
        16,
        (_HEAT,),
    ),
    ("phoned_in_via_cho", "single adult who is deaf and speaks through the housing officer", 4, ()),
    ("phoned_in_via_cho", "pregnant woman living with her mother and two siblings", 2, (_CHRONIC,)),
    ("phoned_in_via_cho", "two adults and one child; the adults do not read or write", 6, ()),
    (
        "phoned_in_via_cho",
        "elderly couple caring for three grandchildren under six",
        19,
        (_ELDERLY, _INFANT),
    ),
    ("phoned_in_via_cho", "single adult, moved in last month", 0, ()),
]
PERSONAS = [
    {
        "persona_id": f"P-{n:02d}",
        "register": register,
        "composition": composition,
        "tenure_years": tenure,
        "household_factors": [str(f) for f in factors],
    }
    for n, (register, composition, tenure, factors) in enumerate(_PERSONA_ROWS, start=1)
]

# Independent streams per artefact, so redesigning one never reshuffles another.
_STREAM_LABELS, _STREAM_CLOSURES, _STREAM_CLIMATE, _STREAM_HOLDOUT = 1, 2, 3, 4


def _rng(seed: int, stream: int) -> np.random.Generator:
    return np.random.default_rng([seed, stream])


def _day(offset: int) -> date:
    return WINDOW_START + timedelta(days=int(offset))


# --- climate ----------------------------------------------------------------------------------


def draw_climate(seed: int = SEED) -> list[dict]:
    """One row per region per window day: max temperature and the heat-warning flag."""
    rng = _rng(seed, _STREAM_CLIMATE)
    innovation_sd = TEMP_ANOMALY_SD * (1 - TEMP_AR_PHI**2) ** 0.5
    by_station: dict[str, list[dict]] = {}
    for station, normals in MONTHLY_MEAN_MAX.items():
        anomaly = 0.0
        temps, excess = [], []
        for d in range(WINDOW_DAYS):
            anomaly = TEMP_AR_PHI * anomaly + rng.normal(0.0, innovation_sd)
            normal = normals[_day(d).month]
            temp = round(normal + anomaly, 1)
            temps.append(temp)
            excess.append(temp - normal >= HEAT_WARNING_EXCESS_C)
        warning = [False] * WINDOW_DAYS
        run = 0
        for d, hot in enumerate(excess):
            run = run + 1 if hot else 0
            if run >= HEAT_WARNING_DAYS:
                for back in range(run):
                    warning[d - back] = True
        by_station[station] = [
            {"max_temp_c": t, "heat_warning": w} for t, w in zip(temps, warning, strict=True)
        ]
    rows = []
    for d in range(WINDOW_DAYS):
        for region in REGIONS:
            rows.append(
                {"date": _day(d).isoformat(), "region": region}
                | by_station[STATION_FOR_REGION[region]][d]
            )
    return rows


# --- closures -----------------------------------------------------------------------------------


def _month_offsets(month: int) -> list[int]:
    return [d for d in range(WINDOW_DAYS) if _day(d).month == month]


def _merge(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def draw_closures(communities: pd.DataFrame, seed: int = SEED) -> list[dict]:
    """Access-closure intervals for every ``wet_season_closable`` community, rising through
    the window. Synthetic: no NT closure history exists (PRD section 6.2)."""
    rng = _rng(seed, _STREAM_CLOSURES)
    rows = []
    for community_id in communities.loc[communities["wet_season_closable"], "community_id"]:
        intervals = []
        for month, mean in CLOSURES_PER_MONTH.items():
            offsets = _month_offsets(month)
            for _ in range(int(rng.poisson(mean))):
                start = int(rng.choice(offsets))
                length = int(rng.integers(CLOSURE_DAYS[0], CLOSURE_DAYS[1] + 1))
                intervals.append((start, min(start + length - 1, WINDOW_DAYS - 1)))
        for start, end in _merge(intervals):
            rows.append(
                {
                    "community_id": community_id,
                    "closed_from": _day(start).isoformat(),
                    "closed_to": _day(end).isoformat(),
                    "source": "synthetic",
                }
            )
    return rows


# --- labels -------------------------------------------------------------------------------------


def _fault_mix_for_month(month: int) -> tuple[list[FaultType], list[float]]:
    faults = list(FAULT_MIX)
    weights = [FAULT_MIX[f] * HEAT_RAMP.get(f, {}).get(month, 1.0) for f in faults]
    total = sum(weights)
    return faults, [w / total for w in weights]


def _expected_faults(communities: pd.DataFrame) -> list[tuple[dict, float]]:
    """(community row, expected fault count) so that reports land near ``REPORT_TARGET``
    with ``REMOTE_REPORT_SHARE`` remote after remote thinning."""
    rows = communities.to_dict("records")
    remote = [r for r in rows if r["is_remote"]]
    weight = {r["community_id"]: POPULATION_BAND_MIDPOINTS[r["population_band"]] for r in remote}
    remote_faults = REPORT_TARGET * REMOTE_REPORT_SHARE / REMOTE_REPORT_RATE_RATIO
    town_reports = REPORT_TARGET * (1 - REMOTE_REPORT_SHARE)
    out = []
    for r in rows:
        if r["is_remote"]:
            out.append((r, remote_faults * weight[r["community_id"]] / sum(weight.values())))
        else:
            out.append((r, town_reports * TOWN_REPORT_WEIGHTS[r["community_id"]]))
    return out


def draw_labels(communities: pd.DataFrame, seed: int = SEED) -> list[dict]:
    """The label tuples. Faults are drawn per community, remote ones thinned by
    ``REMOTE_REPORT_RATE_RATIO``; what remains is the reports the system ever sees."""
    rng = _rng(seed, _STREAM_LABELS)
    heat_warning = {(row["region"], row["date"]): row["heat_warning"] for row in draw_climate(seed)}
    mixes = {m: _fault_mix_for_month(m) for m in WINDOW_MONTHS}
    drawn = []
    for community, expected in _expected_faults(communities):
        for _ in range(int(rng.poisson(expected))):
            if community["is_remote"] and rng.random() >= REMOTE_REPORT_RATE_RATIO:
                continue  # the unreported remote fault is the skew; it leaves no row
            offset = int(rng.integers(WINDOW_DAYS))
            faults, probs = mixes[_day(offset).month]
            fault_type = faults[int(rng.choice(len(faults), p=probs))]
            safety_class = SAFETY_ORDER[int(rng.choice(3, p=SAFETY_MIX_BY_FAULT[fault_type]))]
            persona = PERSONAS[int(rng.integers(len(PERSONAS)))]
            factors = set(persona["household_factors"])
            if (
                fault_type == FaultType.COOLING
                and heat_warning[(community["region"], _day(offset).isoformat())]
            ):
                factors.add(str(HealthRiskFactor.EXTREME_HEAT_EXPOSURE))
            if (
                fault_type in WATER_FAULTS
                and safety_class != SafetyClass.ROUTINE
                and rng.random() < NO_WATER_PROBABILITY
            ):
                factors.add(str(HealthRiskFactor.NO_WATER_OR_SANITATION))
            drawn.append(
                (
                    offset,
                    community["community_id"],
                    len(drawn),
                    {
                        "community_id": community["community_id"],
                        "reported_on": _day(offset).isoformat(),
                        "fault_type": str(fault_type),
                        "safety_class": str(safety_class),
                        "health_risk": sorted(factors),
                        "persona_id": persona["persona_id"],
                    },
                )
            )
    drawn.sort(key=lambda item: item[:3])
    labels = [
        {"job_id": f"JR-{WINDOW_START.year}-{n:05d}", **row}
        for n, (_, _, _, row) in enumerate(drawn, start=1)
    ]
    picks = _rng(seed, _STREAM_HOLDOUT).choice(len(labels), HOLDOUT_COUNT, replace=False)
    holdout = {int(i) for i in picks}
    for i, label in enumerate(labels):
        label["is_holdout"] = i in holdout
        label["is_adversarial"] = False
    return labels


# --- artefact I/O --------------------------------------------------------------------------------


def render_all(communities: pd.DataFrame, seed: int = SEED) -> dict[str, bytes]:
    """Every artefact as the exact bytes ``write_all`` writes; the determinism test compares
    these against the committed files."""
    as_json = {
        "labels.json": draw_labels(communities, seed),
        "personas.json": PERSONAS,
        "closures.json": draw_closures(communities, seed),
    }
    out = {
        name: (json.dumps(obj, indent=1) + "\n").encode("utf-8") for name, obj in as_json.items()
    }
    climate = pd.DataFrame(draw_climate(seed)).to_csv(index=False, lineterminator="\n")
    out["climate.csv"] = climate.encode("utf-8")
    return out


def write_all(build_dir: Path = BUILD_DIR, seed: int = SEED) -> list[Path]:
    communities = load_communities(build_dir / "communities.csv")
    written = []
    for name, data in render_all(communities, seed).items():
        (build_dir / name).write_bytes(data)
        written.append(build_dir / name)
    return written
