"""Ollama chat wrapper, the ollama intake route and the benchmark decision (Task-36)."""

import importlib
import importlib.util
import json
import urllib.error
from pathlib import Path

import pytest

from fair_turn.llm import intake, ollama

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "benchmark_provider", ROOT / "scripts" / "benchmark_provider.py"
)
assert SPEC and SPEC.loader
benchmark_provider = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark_provider)

SAMPLE_TEXT = "The ceiling wire is sparking near the baby's room and the house is hot."
VALID = {
    "fault_type": "electrical",
    "fault_type_evidence": "ceiling wire is sparking",
    "safety_class": "immediate",
    "safety_class_evidence": "wire is sparking",
    "health_risk": ["infant_or_young_child"],
    "health_risk_evidence": ["baby's room"],
    "location_mentioned": False,
    "location_evidence": "",
    "crew_or_access_note": "",
}


class _Response:
    def __init__(self, body: bytes, code: int = 200) -> None:
        self.body, self.code = body, code

    def getcode(self):
        return self.code

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _envelope(content: str) -> bytes:
    return json.dumps({"message": {"role": "assistant", "content": content}}).encode("utf-8")


def test_chat_posts_schema_and_parses_the_message(monkeypatch) -> None:
    captured = {}

    def urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _Response(_envelope(json.dumps(VALID)))

    monkeypatch.setattr(ollama.urllib.request, "urlopen", urlopen)
    schema = {"type": "object"}
    assert ollama.chat("the prompt", schema, model="qwen3:8b", timeout=7) == VALID
    assert captured == {
        "url": "http://localhost:11434/api/chat",
        "payload": {
            "model": "qwen3:8b",
            "messages": [{"role": "user", "content": "the prompt"}],
            "format": schema,
            "stream": False,
            "options": {"temperature": 0},
        },
        "timeout": 7,
    }


@pytest.mark.parametrize(
    "body",
    [
        _envelope("not json at all " + "x" * 500),
        _envelope("[1, 2]"),
        b'{"done": true}',
        b"<html>proxy error</html>",
    ],
)
def test_chat_rejects_output_that_is_not_one_object(monkeypatch, body) -> None:
    monkeypatch.setattr(ollama.urllib.request, "urlopen", lambda request, timeout: _Response(body))
    with pytest.raises(ollama.OllamaInvalidOutput) as info:
        ollama.chat("p", {}, model="qwen3:8b")
    assert len(str(info.value)) < 260  # raw text truncated to 200 characters


@pytest.mark.parametrize(
    "failure",
    [urllib.error.URLError("offline"), TimeoutError("slow"), ConnectionResetError("reset")],
)
def test_chat_wraps_connection_failures(monkeypatch, failure) -> None:
    def urlopen(request, timeout):
        raise failure

    monkeypatch.setattr(ollama.urllib.request, "urlopen", urlopen)
    with pytest.raises(ollama.OllamaUnavailable, match=r"localhost:11434/api/chat"):
        ollama.chat("p", {}, model="qwen3:8b")


def test_chat_non_200_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(
        ollama.urllib.request, "urlopen", lambda request, timeout: _Response(b"{}", code=500)
    )
    with pytest.raises(ollama.OllamaUnavailable, match="HTTP 500"):
        ollama.chat("p", {}, model="qwen3:8b")


def test_configured_accepts_ollama(monkeypatch) -> None:
    monkeypatch.setenv("FAIR_TURN_PROVIDER", "ollama")
    assert intake.configured() == "ollama"
    assert not hasattr(intake, "NotAcceptedYet")


def test_ollama_model_default_and_fallback(monkeypatch) -> None:
    assert intake.OLLAMA_EXTRACT_MODEL == "qwen3:8b"
    assert intake.MODEL_FOR["ollama"] == "qwen3:8b"
    monkeypatch.setenv("FAIR_TURN_OLLAMA_MODEL", "gemma3:4b")
    try:
        importlib.reload(intake)
        assert intake.MODEL_FOR["ollama"] == "gemma3:4b"
    finally:
        monkeypatch.delenv("FAIR_TURN_OLLAMA_MODEL")
        importlib.reload(intake)
    assert intake.MODEL_FOR["ollama"] == "qwen3:8b"


def test_default_ollama_call_routes_to_chat(monkeypatch) -> None:
    captured = {}

    def chat(prompt, schema, model, timeout):
        captured.update(model=model, timeout=timeout, has_text=SAMPLE_TEXT in prompt)
        return VALID

    monkeypatch.setattr(intake.ollama, "chat", chat)
    monkeypatch.setattr(
        intake.claude_cli, "generate", lambda *a, **k: pytest.fail("claude called for ollama")
    )
    result = intake.extract(SAMPLE_TEXT, "ollama", timeout=9)
    assert result.status == "extracted"
    assert result.provider == "ollama" and result.model == "qwen3:8b"
    assert captured == {"model": "qwen3:8b", "timeout": 9, "has_text": True}


@pytest.mark.parametrize(
    "failure",
    [ollama.OllamaUnavailable("down"), ollama.OllamaInvalidOutput("<html>")],
)
def test_ollama_failure_is_not_extracted(failure) -> None:
    def raising(prompt, schema):
        raise failure

    result = intake.extract(SAMPLE_TEXT, "ollama", call=raising)
    assert result.status == "not_extracted"
    assert result.validation == "provider error"
    assert result.verified is None


BUILD = {"fault_type": 0.9187, "safety_class": 0.5641, "health_risk": 0.9093}


def test_decide_equal_numbers_choose_ollama() -> None:
    ours = {"fault_type": 0.9187, "safety_class": 0.5641}
    default, reason = benchmark_provider.decide(ours, BUILD, 20, 20)
    assert default == "ollama"
    assert "0.5641" in reason and "20/20" in reason


def test_decide_one_field_lower_chooses_claude() -> None:
    ours = {"fault_type": 0.99, "safety_class": 0.5640}
    default, reason = benchmark_provider.decide(ours, BUILD, 20, 20)
    assert default == "claude"
    assert "safety_class" in reason and "0.5640" in reason and "0.5641" in reason


def test_decide_one_adversarial_moved_chooses_claude() -> None:
    ours = {"fault_type": 0.99, "safety_class": 0.99}
    default, reason = benchmark_provider.decide(ours, BUILD, 19, 20)
    assert default == "claude"
    assert "19/20" in reason


def _result(call) -> intake.IntakeResult:
    return intake.extract(SAMPLE_TEXT, "ollama", call=call)


def test_rank_unchanged_catches_a_changed_field() -> None:
    original = _result(lambda prompt, schema: VALID)
    same = _result(lambda prompt, schema: dict(VALID))
    downgraded = _result(
        lambda prompt, schema: {**VALID, "safety_class": "routine"}  # evidence still verifies
    )
    queued = _result(lambda prompt, schema: {**VALID, "fault_type_evidence": "not in the text"})
    assert benchmark_provider.rank_unchanged(original, same)
    assert not benchmark_provider.rank_unchanged(original, downgraded)
    assert benchmark_provider.rank_unchanged(original, queued)  # queue moves no ranked job
    assert not benchmark_provider.rank_unchanged(queued, original)  # injection got it ranked


def test_fake_run_writes_the_artefact_and_prints_a_decision(tmp_path, capsys) -> None:
    out = tmp_path / "eval_ollama.json"
    code = benchmark_provider.main(
        ["--provider", "ollama", "--model", "qwen3:8b", "--fake", "--limit", "5", "--out", str(out)]
    )
    assert code == 0
    printed = capsys.readouterr().out
    assert "decision: default = " in printed
    artefact = json.loads(out.read_text("utf-8"))
    assert set(artefact) >= {
        "provider",
        "model",
        "n_items",
        "n_adversarial",
        "fields",
        "adversarial",
        "latency_s",
        "decision",
        "build_extractor",
        "run_at",
    }
    assert (artefact["provider"], artefact["model"]) == ("ollama", "qwen3:8b")
    assert (artefact["n_items"], artefact["n_adversarial"]) == (5, 5)
    assert set(artefact["fields"]) == {"fault_type", "safety_class", "health_risk"}
    for field in ("fault_type", "safety_class"):
        assert artefact["fields"][field]["accuracy"] == 1.0  # the fake answers with gold
        assert artefact["fields"][field]["n"] == 5
    assert artefact["adversarial"] == {"unchanged": 5, "n": 5, "moved": []}
    assert set(artefact["latency_s"]) == {"p50", "p90", "max", "n"}
    assert artefact["decision"]["default"] in {"ollama", "claude"}
    assert artefact["decision"]["default"] in printed
    evaluation = json.loads((ROOT / "data/build/eval.json").read_text("utf-8"))
    assert (
        artefact["build_extractor"]["safety_class"]
        == (evaluation["extractor"]["safety_class"]["macro_f1"])
    )


def test_real_run_uses_the_named_model(tmp_path, monkeypatch) -> None:
    models = []

    def chat(prompt, schema, model, timeout):
        models.append(model)
        return VALID  # evidence absent from these reports: every item goes to the queue

    monkeypatch.setattr(benchmark_provider.ollama, "chat", chat)
    out = tmp_path / "eval.json"
    argv = ["--provider", "ollama", "--model", "gemma3:4b", "--limit", "2", "--out", str(out)]
    assert benchmark_provider.main(argv) == 0
    artefact = json.loads(out.read_text("utf-8"))
    assert models and set(models) == {"gemma3:4b"}
    assert artefact["statuses"] == {"needs_review": 2}
    assert artefact["decision"]["default"] == "claude"
