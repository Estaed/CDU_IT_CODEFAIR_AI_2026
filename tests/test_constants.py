"""Region strings in constants.py must match BushTel's own spelling."""

import json
from pathlib import Path

from fair_turn.core import constants

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"


def _region_names(obj) -> set[str]:
    if isinstance(obj, dict):
        found = {obj["NTRegionName"]} if "NTRegionName" in obj else set()
        return found.union(*(_region_names(v) for v in obj.values()))
    if isinstance(obj, list):
        return set().union(*(_region_names(v) for v in obj))
    return set()


def test_regions_match_bushtel() -> None:
    raw = json.loads((RAW / "bushtel_community_detail_2026-09-12.json").read_text("utf-8"))
    names = _region_names(raw)
    assert set(constants.REMOTE_REGIONS) <= names
    assert constants.TOWN_REGION in names
    assert set(constants.REGIONS) == names


def test_windows_complete() -> None:
    assert constants.WINDOW_DAYS == 90
    days = constants.RESPONSE_BUSINESS_DAYS
    for cls in ("urgent", "routine"):
        assert days[(cls, False)] < days[(cls, True)]
