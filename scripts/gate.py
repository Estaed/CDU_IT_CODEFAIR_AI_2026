"""The gate: `uv run python scripts/gate.py` from the repo root. Exit 0 means clean.

1. ruff check;
2. pytest;
3. replay smoke: the stub case from the replay cache with no API key in the environment, into a
   temporary runs folder, and its view.json validated against readmark/schemas/view.schema.json.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def step(name: str, cmd: list[str], env: dict | None = None) -> bool:
    print(f"== {name}: {' '.join(cmd)}", flush=True)
    code = subprocess.run(cmd, cwd=ROOT, env=env, check=False).returncode
    print(f"== {name}: {'ok' if code == 0 else f'FAILED (exit {code})'}", flush=True)
    return code == 0


def replay_smoke() -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        runs = Path(tmp)
        shutil.copytree(ROOT / "runs" / "stub" / "cache", runs / "stub" / "cache")
        env = {k: v for k, v in os.environ.items() if k != "TYPESAFE_API_KEY"}
        env["READMARK_RUNS_DIR"] = str(runs)
        ok = step("replay smoke",
                  [sys.executable, "-m", "readmark", "run", "--case", "stub", "--replay"], env)
        if not ok:
            return False
        sys.path.insert(0, str(ROOT))
        from readmark.pipeline import validate_view

        validate_view(json.loads((runs / "stub" / "view.json").read_text(encoding="utf-8")))
        print("== replay smoke: view.json matches readmark/schemas/view.schema.json", flush=True)
        return True


def main() -> int:
    results = [
        step("ruff", [sys.executable, "-m", "ruff", "check"]),
        step("pytest", [sys.executable, "-m", "pytest"]),
        replay_smoke(),
    ]
    print("GATE " + ("CLEAN" if all(results) else "FAILED"))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
