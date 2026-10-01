"""Shared isolation for append-only runtime records and the local audit log."""

import pytest

from fair_turn.data import artefacts, runtime


@pytest.fixture(autouse=True)
def isolated_runtime(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(runtime, "RUNTIME_DIR", tmp_path / "runtime")
    # The workspace restores today's signature from the audit log, so a page test must never
    # read the developer's own data/audit/audit.jsonl.
    monkeypatch.setattr(artefacts, "AUDIT_LOG", tmp_path / "audit" / "audit.jsonl")
