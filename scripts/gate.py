"""The gate: `uv run python scripts/gate.py` from the repo root. Exit 0 means clean.

1. ruff check;
2. pytest;
3. replay smoke: every committed case (the stub and the demo file A-0142) from its replay cache
   with no API key in the environment, into a temporary runs folder, and each view.json
   validated against readmark/schemas/view.schema.json (schema version 2).
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SMOKE_CASES = ("stub", "A-0142")


def step(name: str, cmd: list[str], env: dict | None = None) -> bool:
    print(f"== {name}: {' '.join(cmd)}", flush=True)
    code = subprocess.run(cmd, cwd=ROOT, env=env, check=False).returncode
    print(f"== {name}: {'ok' if code == 0 else f'FAILED (exit {code})'}", flush=True)
    return code == 0


def replay_smoke(case_id: str) -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        runs = Path(tmp)
        shutil.copytree(ROOT / "runs" / case_id / "cache", runs / case_id / "cache")
        env = {k: v for k, v in os.environ.items() if k != "TYPESAFE_API_KEY"}
        env["READMARK_RUNS_DIR"] = str(runs)
        ok = step(f"replay smoke {case_id}",
                  [sys.executable, "-m", "readmark", "run", "--case", case_id, "--replay"], env)
        if not ok:
            return False
        sys.path.insert(0, str(ROOT))
        from readmark.pipeline import validate_view

        view = json.loads((runs / case_id / "view.json").read_text(encoding="utf-8"))
        validate_view(view)
        print(f"== replay smoke {case_id}: view.json (schema version {view['schema_version']}) "
              "matches readmark/schemas/view.schema.json", flush=True)
        return True


def main() -> int:
    results = [
        step("ruff", [sys.executable, "-m", "ruff", "check"]),
        step("pytest", [sys.executable, "-m", "pytest"]),
        *(replay_smoke(case_id) for case_id in SMOKE_CASES),
    ]
    print("GATE " + ("CLEAN" if all(results) else "FAILED"))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
