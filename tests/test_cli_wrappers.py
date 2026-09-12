"""The two CLI wrappers against fake executables: no test touches a real CLI."""

import subprocess
import sys
from pathlib import Path

import pytest

from fair_turn.llm import claude_cli, codex_cli

FAKES = Path(__file__).resolve().parent / "fakes"
SCHEMA = {"title": "Probe", "type": "object", "additionalProperties": False, "properties": {}}
PROMPT = "Write the tenant's words.\nSecond line."


def fake(name: str) -> list[str]:
    return [sys.executable, str(FAKES / f"fake_{name}.py")]


def call(name: str, **kwargs):
    if name == "claude":
        return claude_cli.generate(PROMPT, SCHEMA, executable=fake("claude"), **kwargs)
    return codex_cli.extract(PROMPT, SCHEMA, executable=fake("codex"), **kwargs)


@pytest.fixture
def mode(monkeypatch, tmp_path):
    def set_mode(value: str) -> None:
        monkeypatch.setenv("FAKE_MODE", value)
        monkeypatch.setenv("FAKE_COUNTER", str(tmp_path / "counter"))

    return set_mode


@pytest.mark.parametrize("name", ["claude", "codex"])
def test_success_passes_prompt_and_schema(name, mode, capsys) -> None:
    mode("ok")
    result = call(name)
    assert result["echo"] == PROMPT
    assert result["schema_title"] == "Probe"
    assert "call 1" in capsys.readouterr().out


def test_claude_flags() -> None:
    flags = claude_cli.generate(PROMPT, SCHEMA, model="sonnet", executable=fake("claude"))["flags"]
    assert flags[:5] == ["-p", "--model", "sonnet", "--output-format", "json"]
    assert flags[5] == "--json-schema"


def test_codex_flags_and_closed_stdin() -> None:
    result = codex_cli.extract(PROMPT, SCHEMA, executable=fake("codex"))
    assert result["flags"][:4] == ["exec", "--sandbox", "read-only", "--skip-git-repo-check"]
    assert "-m" not in result["flags"]
    assert result["stdin_was_empty"] is True


@pytest.mark.parametrize("name", ["claude", "codex"])
def test_invalid_json_then_success_retries_once(name, mode, capsys) -> None:
    mode("bad_then_ok")
    assert call(name)["echo"] == PROMPT
    assert "call 2" in capsys.readouterr().out


@pytest.mark.parametrize("name", ["claude", "codex"])
def test_nonzero_exit_raises_with_stderr(name, mode) -> None:
    mode("fail")
    error = claude_cli.CliError if name == "claude" else codex_cli.CliError
    with pytest.raises(error, match="simulated failure"):
        call(name)


def test_claude_is_error_raises(mode) -> None:
    mode("is_error")
    with pytest.raises(claude_cli.CliError, match="simulated model error"):
        call("claude")


@pytest.mark.parametrize("name", ["claude", "codex"])
def test_every_subprocess_call_has_timeout_and_resolved_stdin(name, mode, monkeypatch) -> None:
    mode("ok")
    seen = []
    real_run = subprocess.run

    def spy(cmd, **kwargs):
        seen.append(kwargs)
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(subprocess, "run", spy)
    call(name, timeout=30)
    assert seen
    for kwargs in seen:
        assert kwargs["timeout"] == 30
        assert "input" in kwargs or kwargs.get("stdin") is subprocess.DEVNULL
