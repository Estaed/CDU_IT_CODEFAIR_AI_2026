"""``claude -p --json-schema`` as a structured model call. Build time only: results go to the
replay cache (Blueprint, Stack). Ported from the archive's ``fair_turn/llm/claude_cli.py``.

The prompt goes on stdin: a variadic flag would swallow a trailing prompt argument, and the CLI
waits then errors if stdin is open with nothing on it. The JSON result's ``structured_output``
is the schema-valid object.

A timeout kills the whole process tree: on Windows the direct child can be a shim holding a
node grandchild that outlives a plain ``proc.kill()``, so a killed process's own reap could
block forever.
"""

import json
import os
import shutil
import subprocess
import sys
import time

RETRIES = 1  # one more attempt after invalid JSON, then give up
KILL_GRACE = 30  # seconds to reap a killed tree's pipes before abandoning them


class CliError(RuntimeError):
    pass


def _kill_tree(proc: subprocess.Popen) -> None:
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
            capture_output=True,
            timeout=KILL_GRACE,
            check=False,
        )
    else:
        proc.kill()


def _model_id(result: dict, alias: str) -> str:
    """The concrete model id the CLI used, read from its usage report when present."""
    usage = result.get("modelUsage") or {}
    named = [k for k in usage if alias in k] or list(usage)
    return min(named) if named else alias


def generate(
    prompt: str,
    schema: dict,
    model: str = "opus",
    timeout: float = 900,
    executable: list[str] | None = None,
) -> dict:
    """One structured call. Returns ``{"output": <schema object>, "model": <model id>}``.

    ``executable`` overrides the resolved ``claude`` for tests."""
    claude = shutil.which("claude")
    if executable is None and claude is None:
        raise CliError("claude CLI not found on PATH; use --replay to run from the cache")
    cmd = list(executable or [claude]) + [
        "-p",
        "--model",
        model,
        "--output-format",
        "json",
        "--json-schema",
        json.dumps(schema),
    ]
    last = "no attempt made"
    for attempt in range(1, RETRIES + 2):
        started = time.monotonic()
        proc = subprocess.Popen(
            cmd,
            # Marks this as a bee for the TarikOS brain hooks, which then stay out of the
            # nested session (task contract).
            env={**os.environ, "BEYIN_INVOKED_BY": "bee"},
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        try:
            stdout, stderr = proc.communicate(prompt, timeout=timeout)
        except subprocess.TimeoutExpired:
            _kill_tree(proc)
            try:
                proc.communicate(timeout=KILL_GRACE)
            except subprocess.TimeoutExpired:
                pass  # a survivor still holds a pipe; abandon it rather than hang the run
            raise CliError(f"claude timed out after {timeout:g} s") from None
        print(f"claude: call {attempt}, {time.monotonic() - started:.1f}s", file=sys.stderr)
        if proc.returncode:
            raise CliError(f"claude exited {proc.returncode}: {stderr.strip()[:500]}")
        try:
            result = json.loads(stdout)
            if result.get("is_error"):
                raise CliError(f"claude reported an error: {result.get('result')}")
            output = result["structured_output"]
            if not isinstance(output, dict):
                raise TypeError("structured_output is not an object")
            return {"output": output, "model": _model_id(result, model)}
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as exc:
            last = f"claude returned invalid JSON on attempt {attempt}: {exc}"
    raise CliError(last)
