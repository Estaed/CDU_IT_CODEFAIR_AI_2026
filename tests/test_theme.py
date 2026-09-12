"""Colour literals live in theme.py only; the palette covers every region and factor."""

import re
from pathlib import Path

from fair_turn.app import theme
from fair_turn.core import constants

APP = Path(__file__).resolve().parent.parent / "fair_turn" / "app"
HEX = re.compile(r"#[0-9a-fA-F]{6}")


def test_no_hex_outside_theme() -> None:
    hits = [
        str(f.relative_to(APP))
        for f in APP.rglob("*.py")
        if f.name != "theme.py" and HEX.search(f.read_text("utf-8"))
    ]
    assert not hits, hits


def test_palette_covers_regions_and_factors() -> None:
    assert set(theme.REGION_COLOURS) == set(constants.REGIONS)
    assert set(theme.FACTOR_COLOURS) == {"urgency", "safety", "health_risk", "logistics"}
    assert len(set(theme.REGION_COLOURS.values())) == len(theme.REGION_COLOURS)
