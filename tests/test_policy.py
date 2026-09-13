"""Policy-index build and runtime lookup tests (PRD section 5)."""

import importlib.util
import json
import urllib.error
from pathlib import Path

import pytest
from pypdf import PdfReader

from fair_turn.core.constants import SAFETY_CLASSES
from fair_turn.core.types import FaultType
from fair_turn.core.verify_spans import normalise
from fair_turn.data import policy
from fair_turn.llm import ollama

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "build_policy_index.py"
PDF = ROOT / "data" / "raw" / "nt_fs17_repairs_and_maintenance_2025-10.pdf"
ARTEFACT = ROOT / "data" / "build" / "policy_passages.json"
SPEC = importlib.util.spec_from_file_location("build_policy_index", SCRIPT)
assert SPEC and SPEC.loader
build_policy_index = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_policy_index)

FIXTURE_TEXT = "\n\n".join(
    (
        "Urgent repairs",
        " ".join(
            [
                "An urgent electrical repair for a fault in a remote community "
                "must be done promptly, and urgent action protects tenants."
            ]
            * 18
        ),
        "Routine repairs",
        " ".join(
            [
                "A routine plumbing water repair in a town home is recorded with the repair window "
                "and maintenance response."
            ]
            * 18
        ),
    )
)


def test_fake_build_has_complete_verified_key_set_and_is_idempotent(tmp_path) -> None:
    artefact = build_policy_index.build(
        FIXTURE_TEXT,
        build_policy_index.fake_embed,
        build_policy_index.THRESHOLD,
        embed_model="fake-hash-64",
        fetched="2026-09-14",
    )
    output = tmp_path / "policy_passages.json"
    build_policy_index.write_artefact(output, artefact)
    first = output.read_bytes()
    build_policy_index.write_artefact(output, artefact)

    index = policy.load(output)
    expected = {
        policy.key_for(safety, remote, fault)
        for safety in SAFETY_CLASSES
        for remote in (False, True)
        for fault in (*FaultType, None)
    }
    assert set(index.keys) == expected
    assert len(index.keys) == 66
    assert policy.verify(index, FIXTURE_TEXT)
    assert output.read_bytes() == first
    assert any(rows for rows in index.keys.values())
    for rows in index.keys.values():
        scores = [passage.score for passage in rows]
        assert scores == sorted(scores, reverse=True)
        assert all(score >= index.threshold for score in scores)
        assert all(normalise(passage.text) in normalise(FIXTURE_TEXT) for passage in rows)


def test_lookup_uses_full_key_before_faultless_fallback() -> None:
    fallback = policy.Passage("FS17", "fallback", 0.8, "FS17", "2025-10")
    exact = policy.Passage("FS17", "exact", 0.9, "FS17", "2025-10")
    full_key = policy.key_for("urgent", True, FaultType.ELECTRICAL)
    fallback_key = policy.key_for("urgent", True, None)
    index = policy.PolicyIndex(
        True, {}, 0.55, "fake", {full_key: (exact,), fallback_key: (fallback,)}
    )
    assert policy.lookup(index, "urgent", True, FaultType.ELECTRICAL) == [exact]

    no_exact = policy.PolicyIndex(True, {}, 0.55, "fake", {full_key: (), fallback_key: (fallback,)})
    assert policy.lookup(no_exact, "urgent", True, FaultType.ELECTRICAL) == [fallback]


def test_missing_index_is_unavailable_and_has_no_lookup(tmp_path) -> None:
    index = policy.load(tmp_path / "missing.json")
    assert not index.available
    assert policy.lookup(index, "routine", False, FaultType.PLUMBING_WATER) == []


def test_ollama_embed_posts_payload_and_wraps_connection_failure(monkeypatch) -> None:
    captured = {}

    class Response:
        def getcode(self):
            return 200

        def read(self):
            return b'{"embeddings": [[0.1, 0.2], [0.3, 0.4]]}'

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(ollama.urllib.request, "urlopen", urlopen)
    assert ollama.embed(["one", "two"], timeout=4) == [[0.1, 0.2], [0.3, 0.4]]
    assert captured == {
        "url": "http://localhost:11434/api/embed",
        "payload": {"model": "bge-m3", "input": ["one", "two"]},
        "timeout": 4,
    }

    def unavailable(*args, **kwargs):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(ollama.urllib.request, "urlopen", unavailable)
    with pytest.raises(ollama.OllamaUnavailable, match=r"localhost:11434/api/embed"):
        ollama.embed(["one"])


@pytest.mark.skipif(
    not ARTEFACT.exists() or not PDF.exists(), reason="real FS17 index is not committed yet"
)
def test_committed_index_passages_verify_against_fs17() -> None:
    document = "\n\n".join(page.extract_text() or "" for page in PdfReader(PDF).pages)
    assert policy.verify(policy.load(), document)
