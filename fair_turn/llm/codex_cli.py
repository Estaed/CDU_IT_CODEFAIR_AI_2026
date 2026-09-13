"""``codex exec`` as the extractor, build time only (Part 2 stack table).

The prompt goes on stdin behind the positional ``-``: on Windows ``codex`` resolves to a
``codex.CMD`` shim that truncates a positional prompt at its first newline, and an open
stdin with nothing on it blocks forever. ``communicate(input=...)`` writes and closes it.
The object is read back from ``-o out.json``. No ``-m`` pin: the model follows the
operator's Codex config (MODELS.md rule).

A timeout kills the whole process tree: on Windows the direct child is ``cmd.exe`` running
the shim, and killing only that leaves ``node.exe``/``codex.exe`` holding the pipes, so
the read after ``subprocess.run``'s own kill blocks forever (measured 2026-09-13).
"""

import json
import shutil
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

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


def extract(
    prompt: str,
    schema: dict,
    timeout: float = 420,
    executable: list[str] | None = None,
) -> dict:
    """One structured call. ``executable`` overrides the resolved ``codex`` for tests."""
    with tempfile.TemporaryDirectory(prefix="fair_turn_codex_") as tmp:
        schema_path = Path(tmp) / "schema.json"
        out_path = Path(tmp) / "out.json"
        schema_path.write_text(json.dumps(schema), encoding="utf-8")
        cmd = list(executable or [shutil.which("codex") or "codex"]) + [
            "exec",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            "--output-schema",
            str(schema_path),
            "-o",
            str(out_path),
            "-",
        ]
        for attempt in range(1, RETRIES + 2):
            out_path.unlink(missing_ok=True)
            started = time.monotonic()
            proc = subprocess.Popen(
                cmd,
                # Marks this as a bee for TarikOS brain hooks: they exit early and do not
                # write a daily/ entry for it. Only the main loop/chef session is flushed.
                env={**os.environ, \"BEYIN_INVOKED_BY\": \"fair-turn\"},
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
            try:
                _, stderr = proc.communicate(prompt, timeout=timeout)
            except subprocess.TimeoutExpired:
                _kill_tree(proc)
                try:
                    proc.communicate(timeout=KILL_GRACE)
                except subprocess.TimeoutExpired:
                    pass  # a survivor still holds a pipe; abandon it rather than hang the run
                raise CliError(f"codex timed out after {timeout:g} s") from None
            print(f"codex: call {attempt}, {time.monotonic() - started:.1f}s", file=sys.stdout)
            if proc.returncode:
                raise CliError(f"codex exited {proc.returncode}: {stderr.strip()}")
            try:
                result = json.loads(out_path.read_text(encoding="utf-8"))
                if not isinstance(result, dict):
                    raise TypeError(f"expected an object, got {type(result).__name__}")
                return result
            except (OSError, json.JSONDecodeError, TypeError) as exc:
                last = f"codex returned invalid JSON on attempt {attempt}: {exc}"
        raise CliError(last)
