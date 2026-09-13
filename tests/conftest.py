"""Shared isolation for append-only runtime records."""

import pytest

from fair_turn.data import runtime


@pytest.fixture(autouse=True)
def isolated_runtime(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(runtime, "RUNTIME_DIR", tmp_path / "runtime")
