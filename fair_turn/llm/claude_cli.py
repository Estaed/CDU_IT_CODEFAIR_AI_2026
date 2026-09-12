"""``claude -p`` as the generator, build time only (Part 2 stack table).

The prompt goes on stdin: a variadic flag would swallow a trailing prompt argument, and
the CLI waits then errors if stdin is open with nothing on it. The JSON result's
``structured_output`` is the schema-valid object.
"""

import json
import shutil
import subprocess
import sys
import time

RETRIES = 1  # one more attempt after invalid JSON, then give up


class CliError(RuntimeError):
    pass


def generate(
    prompt: str,
    schema: dict,
    model: str = "opus",
    timeout: float = 300,
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
        run = subprocess.run(
            cmd, input=prompt, capture_output=True, text=True, encoding="utf-8", timeout=timeout
        )
        print(f"claude: call {attempt}, {time.monotonic() - started:.1f}s", file=sys.stdout)
        if run.returncode:
            raise CliError(f"claude exited {run.returncode}: {run.stderr.strip()}")
        try:
            result = json.loads(run.stdout)
            if result.get("is_error"):
                raise CliError(f"claude reported an error: {result.get('result')}")
            return result["structured_output"]
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as exc:
            last = f"claude returned invalid JSON on attempt {attempt}: {exc}"
    raise CliError(last)
