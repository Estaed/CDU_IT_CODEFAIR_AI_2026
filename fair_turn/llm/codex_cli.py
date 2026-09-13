"""``codex exec`` as the extractor, build time only (Part 2 stack table).

The prompt goes on stdin behind the positional ``-``: on Windows ``codex`` resolves to a
``codex.CMD`` shim that truncates a positional prompt at its first newline, and an open
stdin with nothing on it blocks forever. ``subprocess.run(input=...)`` writes and closes it.
The object is read back from ``-o out.json``. No ``-m`` pin: the model follows the
operator's Codex config (MODELS.md rule).
"""

import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

RETRIES = 1  # one more attempt after invalid JSON, then give up


class CliError(RuntimeError):
    pass


def extract(
    prompt: str,
    schema: dict,
    timeout: float = 300,
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
            run = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=timeout,
            )
            print(f"codex: call {attempt}, {time.monotonic() - started:.1f}s", file=sys.stdout)
            if run.returncode:
                raise CliError(f"codex exited {run.returncode}: {run.stderr.strip()}")
            try:
                result = json.loads(out_path.read_text(encoding="utf-8"))
                if not isinstance(result, dict):
                    raise TypeError(f"expected an object, got {type(result).__name__}")
                return result
            except (OSError, json.JSONDecodeError, TypeError) as exc:
                last = f"codex returned invalid JSON on attempt {attempt}: {exc}"
        raise CliError(last)
