"""Theme values stay within the approved palette and CSS has one safe injection seam."""

import json
import re
import tomllib
from pathlib import Path

from fair_turn.app import theme
from fair_turn.core import constants

APP = Path(__file__).resolve().parent.parent / "fair_turn" / "app"
ROOT = APP.parent.parent
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


def test_config_and_stylesheet_colours_are_design_tokens() -> None:
    config = (ROOT / ".streamlit" / "config.toml").read_text("utf-8")
    tomllib.loads(config)
    css = (APP / "static" / "theme.css").read_text("utf-8")
    tokens = json.loads((ROOT / "design" / "design-system" / "tokens.json").read_text("utf-8"))
    palette = json.loads(
        (ROOT / "design" / "design-system" / "chart-palette.json").read_text("utf-8")
    )
    allowed = set(HEX.findall(json.dumps(tokens))) | set(HEX.findall(json.dumps(palette)))
    assert set(HEX.findall(config + css)) <= allowed


def test_only_theme_injects_styles_and_stylesheet_is_self_contained() -> None:
    style_hits = []
    for path in APP.rglob("*.py"):
        text = path.read_text("utf-8")
        if path.name != "theme.py" and ("<style" in text or "unsafe_allow_html" in text):
            style_hits.append(str(path.relative_to(APP)))
    css = (APP / "static" / "theme.css").read_text("utf-8")
    assert not style_hits, style_hits
    assert "url(" not in css
    assert "@import" not in css
