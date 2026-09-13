"""Layer rule from CLAUDE.md Part 2, enforced rather than remembered.

Two halves: which third-party libraries a layer may never import, and which sibling
layers it may import. `scripts/` is outside the rule and may import anything.
"""

import re
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent / "fair_turn"

FORBIDDEN_LIBS = {
    "core": r"streamlit|anthropic|openai|subprocess|requests|urllib|httpx|socket|pandas",
    "data": r"streamlit|anthropic|openai|subprocess|requests|urllib|httpx|socket",
    "eval": r"streamlit|anthropic|openai|subprocess|requests|urllib|httpx|socket",
    "llm": r"streamlit",  # urllib is allowed here for the local Ollama wrapper.
    "app": r"anthropic|openai|subprocess|requests|urllib|httpx|socket",
}

ALLOWED_SIBLINGS = {
    "core": set(),
    "data": {"core"},
    "eval": {"core", "data"},
    "llm": {"core", "data"},
    "app": {"core", "data", "eval"},
}


def _sources(layer: str) -> list[Path]:
    folder = PKG / layer
    return sorted(folder.rglob("*.py")) if folder.exists() else []


def test_forbidden_libraries() -> None:
    assert PKG.exists()
    bad = {}
    for layer, pattern in FORBIDDEN_LIBS.items():
        rx = re.compile(rf"^\s*(import|from)\s+({pattern})\b", re.M)
        hits = [str(f.relative_to(PKG)) for f in _sources(layer) if rx.search(f.read_text("utf-8"))]
        if hits:
            bad[layer] = hits
    assert not bad, bad


def test_import_direction() -> None:
    rx = re.compile(r"^\s*(?:from|import)\s+fair_turn\.(\w+)", re.M)
    bad = {}
    for layer, allowed in ALLOWED_SIBLINGS.items():
        for f in _sources(layer):
            targets = set(rx.findall(f.read_text("utf-8"))) - {layer}
            if layer == "app" and f.name == "intake.py":
                targets -= {"llm"}  # Part 2 (2026-09-14): the one app module allowed to import llm
            if targets - allowed:
                bad[str(f.relative_to(PKG))] = sorted(targets - allowed)
    assert not bad, bad


def _llm_imports(path: Path) -> bool:
    return bool(re.search(r"^\s*(?:from|import)\s+fair_turn\.llm", path.read_text("utf-8"), re.M))


def test_only_intake_imports_llm(tmp_path) -> None:
    app_files = [path for path in (PKG / "app").rglob("*.py") if path.name != "intake.py"]
    bad = [str(path.relative_to(PKG)) for path in app_files if _llm_imports(path)]
    assert not bad, bad

    offending = tmp_path / "offending.py"
    offending.write_text("from fair_turn.llm import intake\n", encoding="utf-8", newline="")
    assert _llm_imports(offending)
