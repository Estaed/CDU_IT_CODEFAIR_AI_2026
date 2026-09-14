"""Community table: frozen BushTel and coverage snapshots in, one committed CSV out.

Build once from the repo root (the CSV under ``data/build/`` is what the app reads):

    venv/Scripts/python -m fair_turn.data.geography

Rows are the 96 BushTel Major/Minor communities under region-coded pseudonymous ids plus
the five crew-base towns under their real names. The id-to-name key is never written.
"""

import json
import math
import re
import sys
from collections.abc import Mapping
from pathlib import Path

import openpyxl
import pandas as pd

from fair_turn.core.capacity_sim import CrewBase, Site, crew_roster
from fair_turn.core.constants import CREW_BASES, REGIONS, REMOTE_REGIONS, TOWN_REGION

ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = ROOT / "data" / "raw"
BUILD_CSV = ROOT / "data" / "build" / "communities.csv"

BUSHTEL_DETAIL = "bushtel_community_detail_2026-09-12.json"
COVERAGE_XLSX = "ntgov_communities_mobile_coverage_2021.xlsx"
REMOTE_TYPES = ("Major", "Minor")

# Provisional multipliers on haversine km (constants.md). Barge/air communities have no road
# distance at all; the factor stands in for freight lead time.
ROAD_FACTORS = {"sealed": 1.0, "unsealed": 1.4, "barge_or_air": 2.5}
# Region -> crew base. Names are constants.CREW_BASES spelled as BushTel spells them.
BASE_FOR_REGION = {
    "CENTRAL AUSTRALIA": "ALICE SPRINGS",
    "BIG RIVERS": "KATHERINE",
    "BARKLY": "TENNANT CREEK",
    "TOP END": "DARWIN",
    "EAST ARNHEM": "NHULUNBUY",
    TOWN_REGION: "DARWIN",
}
POPULATION_BANDS = ((100, "under 100"), (250, "100-249"), (500, "250-499"), (1000, "500-999"))
COORD_MISMATCH_KM = 5.0

# Road-access classes read from BushTel prose. Barge/air comes from the structured
# "Accessible by road" service flag, not prose; prose only splits sealed from unsealed, and
# an unsealed signal wins because the last leg is what closes. No signal at all defaults to
# unsealed, the common case for a remote NT access road.
_UNSEALED = re.compile(
    r"\b(unsealed|dirt|gravel(led)?|4[\s-]?wd|4x4|track|impassable|cut off|not passable"
    r"|single lane|poor state|rough|corrugat\w*|rainy|check with the community)\b",
    re.I,
)
_SEALED = re.compile(
    r"\b(sealed|bitumen|all[\s-]weather|on the \w+ (highway|road)|\d+ mins?\b|minutes)\b", re.I
)

COLUMNS = [
    "community_id",
    "region",
    "is_remote",
    "lat",
    "lon",
    "population_band",
    "road_access",
    "crew_base",
    "km_to_base",
    "logistics_factor",
    "wet_season_closable",
]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dlmb = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def population_band(population: int) -> str:
    if not population:
        return "not recorded"
    for upper, label in POPULATION_BANDS:
        if population < upper:
            return label
    return "1000+"


def road_access(record: dict) -> str:
    services = record.get("Services") or []
    if any(s["ServiceType"] == "Accessible by road" and s["Status"] == "N" for s in services):
        return "barge_or_air"
    text = record.get("Description") or ""
    if _UNSEALED.search(text):
        return "unsealed"
    if _SEALED.search(text):
        return "sealed"
    return "unsealed"


def _coverage_points(raw_dir: Path) -> dict[str, tuple[float, float]]:
    wb = openpyxl.load_workbook(raw_dir / COVERAGE_XLSX, read_only=True)
    rows = wb["Communities"].iter_rows(min_row=2, values_only=True)
    return {r[0].upper(): (float(r[3]), float(r[2])) for r in rows if r[0] and r[2] and r[3]}


def build_communities(raw_dir: Path = RAW_DIR, debug: bool = False) -> pd.DataFrame:
    """Deterministic table from the frozen raw files. ``debug=True`` adds the real name and
    the road prose for inspection; that frame is never written to disk."""
    records = json.loads((raw_dir / BUSHTEL_DETAIL).read_text("utf-8"))
    by_name = {r["Name"]: r for r in records}
    bases = {
        b: (by_name[b.upper()]["Point"]["Latitude"], by_name[b.upper()]["Point"]["Longitude"])
        for b in (b.upper() for b in CREW_BASES)
    }
    coverage = _coverage_points(raw_dir)

    rows = []
    for region in REMOTE_REGIONS:
        members = [
            r
            for r in records
            if r["CommunityTypeName"] in REMOTE_TYPES and r["NTRegionName"] == region
        ]
        members.sort(key=lambda r: (-(r["Population"] or 0), r["Name"]))
        for n, r in enumerate(members, start=1):
            lat, lon = r["Point"]["Latitude"], r["Point"]["Longitude"]
            base = BASE_FOR_REGION[region]
            km = haversine_km(lat, lon, *bases[base])
            access = road_access(r)
            if r["Name"] in coverage:
                gap = haversine_km(lat, lon, *coverage[r["Name"]])
                if gap > COORD_MISMATCH_KM:
                    print(f"coverage coordinate gap {gap:.1f} km for {region} record {n}")
            rows.append(
                {
                    "community_id": f"{region} R-{n:02d}",
                    "region": region,
                    "is_remote": True,
                    "lat": round(lat, 5),
                    "lon": round(lon, 5),
                    "population_band": population_band(r["Population"] or 0),
                    "road_access": access,
                    "crew_base": base.title(),
                    "km_to_base": round(km, 1),
                    "logistics_factor": round(km * ROAD_FACTORS[access], 1),
                    "wet_season_closable": access != "sealed",
                    "name": r["Name"],
                    "road_note": (r.get("Description") or "").strip(),
                }
            )
    for base in CREW_BASES:
        r = by_name[base.upper()]
        rows.append(
            {
                "community_id": base,
                "region": r["NTRegionName"],
                "is_remote": False,
                "lat": round(r["Point"]["Latitude"], 5),
                "lon": round(r["Point"]["Longitude"], 5),
                "population_band": population_band(r["Population"] or 0),
                "road_access": "sealed",
                "crew_base": base,
                "km_to_base": 0.0,
                "logistics_factor": 0.0,
                "wet_season_closable": False,
                "name": r["Name"],
                "road_note": (r.get("Description") or "").strip(),
            }
        )
    frame = pd.DataFrame(rows)
    assert set(frame["region"]) <= set(REGIONS)
    return frame if debug else frame[COLUMNS]


def write_communities(path: Path = BUILD_CSV, raw_dir: Path = RAW_DIR) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    csv = build_communities(raw_dir).to_csv(index=False, lineterminator="\n")
    path.write_bytes(csv.encode("utf-8"))


def load_communities(path: Path = BUILD_CSV) -> pd.DataFrame:
    return pd.read_csv(path)


def sim_sites(rows: Mapping[str, Mapping[str, str]]) -> dict[str, Site]:
    """A capacity-model ``Site`` per community row of ``communities.csv`` (string values)."""
    return {
        cid: Site(
            region=r["region"],
            km_to_base=float(r["km_to_base"]),
            lat=float(r["lat"]),
            lon=float(r["lon"]),
            road_factor=ROAD_FACTORS[r["road_access"]],
        )
        for cid, r in rows.items()
    }


def crews(rows: Mapping[str, Mapping[str, str]]) -> tuple[CrewBase, ...]:
    """The NT-wide crew pool, with each region's base read from the ``crew_base`` column."""
    return crew_roster({r["region"]: r["crew_base"] for r in rows.values()})


if __name__ == "__main__":
    write_communities()
    print(f"wrote {BUILD_CSV.relative_to(ROOT)}", file=sys.stderr)
