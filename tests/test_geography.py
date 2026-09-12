"""The committed community table: shape, ids, provenance, and no real names anywhere."""

import json
import re
from pathlib import Path

from _real_names import real_names

from fair_turn.core import constants
from fair_turn.data import geography

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "build" / "communities.csv"
OUTLINE = ROOT / "data" / "geo" / "nt_outline.geojson"


def _scanned_text() -> dict[str, str]:
    files = [CSV, ROOT / "docs" / "PRD.md"] + sorted((ROOT / "fair_turn" / "app").rglob("*.py"))
    return {str(f.relative_to(ROOT)): f.read_text("utf-8").upper() for f in files}


def test_no_real_community_name_leaks() -> None:
    leaks = {}
    for path, text in _scanned_text().items():
        hits = [n for n in real_names() if re.search(rf"(?<![A-Z]){re.escape(n)}(?![A-Z])", text)]
        if hits:
            leaks[path] = hits
    assert not leaks, leaks


def test_table_shape() -> None:
    df = geography.load_communities()
    assert list(df.columns) == geography.COLUMNS
    assert len(df) == 101
    assert df["community_id"].is_unique
    assert set(df["region"]) <= set(constants.REGIONS)
    assert (df.loc[df["is_remote"], "km_to_base"] > 0).all()
    assert (~df["is_remote"]).sum() == len(constants.CREW_BASES)
    assert set(df["road_access"]) <= set(geography.ROAD_FACTORS)


def test_build_is_deterministic() -> None:
    a = geography.build_communities().to_csv(index=False, lineterminator="\n")
    b = geography.build_communities().to_csv(index=False, lineterminator="\n")
    assert a == b
    assert a.encode("utf-8") == CSV.read_bytes()


def test_outline_is_one_nt_feature() -> None:
    geo = json.loads(OUTLINE.read_text("utf-8"))
    assert geo["type"] == "FeatureCollection"
    assert len(geo["features"]) == 1
    assert geo["features"][0]["properties"]["iso_3166_2"] == "AU-NT"
    assert OUTLINE.stat().st_size < 500 * 1024
