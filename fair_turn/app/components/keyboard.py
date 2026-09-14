"""Global keyboard shortcuts for the workspace (design/phase-2-wireframes.md keyboard path).

An invisible (zero-height) ``st.components.v2`` component: it appends nothing to the page,
only a single ``document``-level ``keydown`` listener, so it occupies no layout space. Follows
the pattern in ``cluster_map.py`` — registration happens at mount time, the registry belongs
to the running app; data (the key list) travels in through ``data``; ``AppTest`` sees a
``bidi_component`` node.

The listener ignores a keystroke held with Ctrl, Alt or Meta, and any keystroke while the
event target or ``document.activeElement`` is a text-entry element, so typing in a field never
fires a shortcut. It never reacts to ``r`` or ``c``: Streamlit's own rerun and clear-cache
keys, deliberately left out of ``KEYS``.
"""

from pathlib import Path

import streamlit as st

KEYS = ("j", "k", "a", "x")
HINT = "Keys: J next job · K previous job · A accept · X reject"
COMPONENT_NAME = "ft_keyboard"
JS_FILE = Path(__file__).parent / "keyboard.js"

_JS = JS_FILE.read_text("utf-8")


def _mount(data: dict, key: str):
    # Registered on every call, like cluster_map: the registry belongs to the running app, so
    # a registration made at import time (in another runtime, such as a test process) is not
    # found.
    component = st.components.v2.component(COMPONENT_NAME, js=_JS)
    return component(data=data, on_pressed_change=lambda: None, key=key)


def render(key: str = "workspace_keys", mount=None) -> str | None:
    """Mount the invisible listener; return the lower-case key pressed in this rerun, or
    ``None`` on every other rerun (including the one that mounts it)."""
    mount = mount or _mount
    result = mount({"keys": list(KEYS)}, key)
    pressed = getattr(result, "pressed", None)
    return pressed["key"] if pressed else None
