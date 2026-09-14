"""The workspace keyboard-shortcut component: KEYS, the trigger it returns, and the JS's
colour/key literals. ``AppTest`` cannot simulate a real keydown inside a v2 component, so the
trigger path is exercised with a fake mount, the same way ``test_cluster_map.py`` does."""

import re
from pathlib import Path

from streamlit.testing.v1 import AppTest

from fair_turn.app.components import keyboard

JS = Path(keyboard.__file__).with_name("keyboard.js")


def test_keys_excludes_streamlit_rerun_and_clear_cache_shortcuts() -> None:
    assert keyboard.KEYS == ("j", "k", "a", "x")
    assert "r" not in keyboard.KEYS
    assert "c" not in keyboard.KEYS


def test_js_never_reacts_to_r_or_c() -> None:
    source = JS.read_text("utf-8")
    # The key set comes only from `data.keys` (Python's KEYS); no literal key array in the JS
    # itself carries Streamlit's own rerun ("r") or clear-cache ("c") shortcuts.
    assert not re.search(r"""['"]r['"]\s*,|,\s*['"]r['"]""", source)
    assert not re.search(r"""['"]c['"]\s*,|,\s*['"]c['"]""", source)


def test_js_has_no_hex_colour_literal() -> None:
    source = JS.read_text("utf-8")
    assert not re.search(r"#[0-9a-fA-F]{3,6}\b", source)


def test_js_guards_against_a_second_listener_and_respects_modifiers_and_typing() -> None:
    source = JS.read_text("utf-8")
    assert "__ftKeyboardBound" in source
    assert "ctrlKey" in source and "altKey" in source and "metaKey" in source
    assert "activeElement" in source
    assert 'setTriggerValue("pressed"' in source
    assert "preventDefault" in source


def _script(tmp_path: Path, fake: str | None = None) -> Path:
    lines = ["import streamlit as st", "from types import SimpleNamespace"]
    lines.append("from fair_turn.app.components import keyboard")
    if fake is None:
        lines.append("result = keyboard.render()")
    else:
        lines += [
            "def fake(data, key):",
            f"    return {fake}",
            "result = keyboard.render(mount=fake)",
        ]
    lines.append("st.text(f'pressed={result}')")
    path = tmp_path / "keyboard_app.py"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="")
    return path


def test_render_returns_none_on_a_plain_run_and_mounts_one_bidi_component(tmp_path) -> None:
    at = AppTest.from_file(str(_script(tmp_path))).run(timeout=60)
    assert not at.exception
    nodes = at.get("bidi_component")
    assert len(nodes) == 1
    assert nodes[0].proto.component_name.endswith(keyboard.COMPONENT_NAME)
    assert "pressed=None" in [t.value for t in at.text]


def test_render_returns_the_pressed_key_from_a_trigger(tmp_path) -> None:
    fake = "SimpleNamespace(pressed={'key': 'j', 'nonce': 1})"
    at = AppTest.from_file(str(_script(tmp_path, fake))).run(timeout=60)
    assert not at.exception
    assert "pressed=j" in [t.value for t in at.text]


def test_hint_names_all_four_keys() -> None:
    assert "J" in keyboard.HINT and "K" in keyboard.HINT
    assert "A" in keyboard.HINT and "X" in keyboard.HINT
