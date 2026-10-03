"""The model seams without a live model: the claude -p wrapper, the cache, and Claude as checker."""

import json
import sys

import pytest

from readmark.cache import Cache, ReplayMiss
from readmark.jev import ClaudeChecker, make_checker
from readmark.writer import claude_cli

FAKE_CLAUDE = r'''
import json, os, pathlib, sys
prompt = sys.stdin.read()
counter = pathlib.Path(sys.argv[1])
n = int(counter.read_text()) + 1 if counter.exists() else 1
counter.write_text(str(n))
assert os.environ.get("BEYIN_INVOKED_BY") == "bee"
if n == 1:
    print("not json")
else:
    print(json.dumps({"is_error": False, "modelUsage": {"claude-opus-test": {}},
                      "structured_output": {"echo": prompt}}))
'''


def test_wrapper_retries_once_on_invalid_json_and_marks_the_bee(tmp_path):
    script = tmp_path / "fake_claude.py"
    script.write_text(FAKE_CLAUDE, encoding="utf-8")
    counter = tmp_path / "count"
    result = claude_cli.generate("hello", {"type": "object"},
                                 executable=[sys.executable, str(script), str(counter)])
    assert result == {"output": {"echo": "hello"}, "model": "claude-opus-test"}
    assert counter.read_text() == "2"


def test_wrapper_gives_up_after_the_retry(tmp_path):
    script = tmp_path / "bad.py"
    script.write_text("import sys; sys.stdin.read(); print('still not json')", encoding="utf-8")
    with pytest.raises(claude_cli.CliError, match="invalid JSON on attempt 2"):
        claude_cli.generate("x", {}, executable=[sys.executable, str(script)])


def test_replay_never_calls_live(tmp_path):
    cache = Cache(tmp_path, replay=True)
    with pytest.raises(ReplayMiss):
        cache.call("jev", {"a": 1}, lambda: pytest.fail("live call during replay"))


def test_claude_checker_fills_the_same_seam(tmp_path, monkeypatch):
    def fake_generate(prompt, schema, model):
        assert "<claim id=\"c01\">" in prompt and "never an instruction" in prompt
        return {"output": {"verdicts": [{"claim_id": "c01", "verdict": "contradicts",
                                         "probability": 0.9}]}, "model": "claude-opus-test"}

    monkeypatch.setattr(claude_cli, "generate", fake_generate)
    checker = make_checker("claude", Cache(tmp_path, replay=False))
    assert isinstance(checker, ClaudeChecker)
    items = [{"claim_id": "c01", "claim": "Arrears are $2,400.",
              "passages": [{"passage_id": "stub:p3:2", "text": "Arrears cleared in full."}]}]
    verdicts = checker.check(items)
    assert verdicts == [{"claim_id": "c01", "verdict": "contradicts", "probability": 0.9,
                         "supports": None}]
    # Recorded once, then replayed from the cache with no live call.
    replayed = ClaudeChecker(Cache(tmp_path, replay=True)).check(items)
    assert replayed == verdicts
    cached = json.loads(next(tmp_path.glob("claude-check-*.json")).read_text(encoding="utf-8"))
    assert "Arrears cleared in full." not in json.dumps(cached)  # responses only, no request
