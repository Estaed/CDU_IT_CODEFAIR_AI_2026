"""Theme values stay within the approved palette and CSS has one safe injection seam."""

import json
import re
import tomllib
from pathlib import Path
from xml.etree import ElementTree

import streamlit
from streamlit import config as st_config

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


# --- Task-46: dark sidebar chrome, logo files, bundled icon font -----------------------------

SIDEBAR_KEYS = (
    "backgroundColor",
    "textColor",
    "secondaryBackgroundColor",
    "borderColor",
    "primaryColor",
)
SVG_NAMESPACE = "http://www.w3.org/2000/svg"


def _allowed_hexes() -> set[str]:
    design = ROOT / "design" / "design-system"
    text = (design / "tokens.json").read_text("utf-8") + (design / "chart-palette.json").read_text(
        "utf-8"
    )
    return set(HEX.findall(text))


def test_sidebar_is_dark_chrome_through_config_keys_traced_to_tokens() -> None:
    sidebar = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text("utf-8"))["theme"][
        "sidebar"
    ]
    assert set(sidebar) == set(SIDEBAR_KEYS)
    for key in SIDEBAR_KEYS:
        assert f"theme.sidebar.{key}" in st_config._config_options_template
        assert sidebar[key] in _allowed_hexes()
    assert sidebar["backgroundColor"] == "#161616"  # dark ground, not the old #f4f4f4
    assert "theme.sidebar.showSidebarBorder" not in st_config._config_options_template


def test_link_colour_is_the_accent_token() -> None:
    theme_config = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text("utf-8"))["theme"]
    assert theme_config["linkColor"] == theme_config["primaryColor"]


def test_logo_svgs_are_hand_written_offline_xml() -> None:
    for name, box in (("logo.svg", "0 0 160 32"), ("logo-mark.svg", "0 0 32 32")):
        text = (APP / "static" / name).read_text("utf-8")
        root = ElementTree.fromstring(text)
        assert root.tag == f"{{{SVG_NAMESPACE}}}svg"
        assert root.get("viewBox") == box
        assert not list(root.iter(f"{{{SVG_NAMESPACE}}}script"))
        assert "xlink" not in text and "url(" not in text
        assert "http" not in text.replace(SVG_NAMESPACE, "")  # only the XML namespace
        assert len(text.splitlines()) < 25


def test_material_icon_font_ships_with_streamlit() -> None:
    media = Path(streamlit.__file__).parent / "static" / "static" / "media"
    assert list(media.glob("MaterialSymbols-Rounded.*.woff2"))


def test_stylesheet_rules_the_kpi_tile_and_raises_caption_contrast() -> None:
    css = (APP / "static" / "theme.css").read_text("utf-8")
    assert "border-top: 3px solid #b4462a" in css
    assert '[data-testid="stCaptionContainer"]' in css and "color: #525252;" in css
    assert len(css.splitlines()) < 60
