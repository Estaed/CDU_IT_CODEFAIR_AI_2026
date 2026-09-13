"""Quality gate for Fair Turn. The only command verify-task and otopilot call.

Run from the repo root with the project interpreter:
    venv/Scripts/python scripts/gate.py
Runs lint, format check and the test suite (unit + AppTest smoke) in that order, stops at
the first failure, exits non-zero on any failure.
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV = ROOT / "venv"


def main() -> int:
    # Step 1: refuse to run under any interpreter but the project venv's.
    exe = Path(sys.executable).resolve()
    if VENV.resolve() not in exe.parents:
        print(f"gate: run with {VENV / 'Scripts' / 'python'}, not {exe}", file=sys.stderr)
        return 2
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    # Step 2: lint, format check, then the test suite, in that order (cheapest first).
    steps = [
        ("ruff check", [sys.executable, "-m", "ruff", "check", "."]),
        ("ruff format --check", [sys.executable, "-m", "ruff", "format", "--check", "."]),
        ("pytest", [sys.executable, "-m", "pytest", "-q"]),
    ]
    # Step 3: stop at the first failure and return its exit code as the verdict.
    for name, cmd in steps:
        print(f"gate: {name}")
        code = subprocess.run(cmd, cwd=ROOT, env=env).returncode
        if code:
            print(f"gate: FAILED at {name} (exit {code})", file=sys.stderr)
            return code
    print("gate: GREEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
