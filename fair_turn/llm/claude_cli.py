"""``claude -p`` as the generator, build time only (Part 2 stack table).

The prompt goes on stdin: a variadic flag would swallow a trailing prompt argument, and
the CLI waits then errors if stdin is open with nothing on it. The JSON result's
``structured_output`` is the schema-valid object.

A timeout kills the whole process tree the same way ``codex_cli`` does: on Windows the
direct child can be a shim holding a node/python grandchild that outlives a plain
``proc.kill()``, so a killed subprocess.run's own reap can block forever (measured on the
``codex`` wrapper 2026-09-13; the same mechanism is used here on principle).
"""

import json
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
        )
    else:
        proc.kill()


def generate(
    prompt: str,
    schema: dict,
    model: str = "opus",
    timeout: float = 600,
    executable: list[str] | None = None,
) -> dict:
    """One structured call. ``executable`` overrides the resolved ``claude`` for tests."""
    cmd = list(executable or [shutil.which("claude") or "claude"]) + [
        "-p",
        "--model",
        model,
        "--output-format",
        "json",
        "--json-schema",
        json.dumps(schema),
    ]
    for attempt in range(1, RETRIES + 2):
        started = time.monotonic()
        proc = subprocess.Popen(
            cmd,
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
            raise CliError(f"claude exited {proc.returncode}: {stderr.strip()}")
        try:
            result = json.loads(stdout)
            if result.get("is_error"):
                raise CliError(f"claude reported an error: {result.get('result')}")
            return result["structured_output"]
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as exc:
            last = f"claude returned invalid JSON on attempt {attempt}: {exc}"
    raise CliError(last)
