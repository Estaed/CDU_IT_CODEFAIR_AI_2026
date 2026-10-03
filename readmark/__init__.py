"""Readmark: an evidence map and reading gate for NT priority-housing decisions.

Each stage reads and writes JSON under ``runs/<case>/<stage>.json``; together those files and
``runs/<case>/cache/`` make up the replay cache (Blueprint, Layout).
"""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
POLICIES_DIR = DATA / "policies"
CASES_DIR = DATA / "cases"
WEB_DIR = ROOT / "web"
SCHEMAS_DIR = Path(__file__).resolve().parent / "schemas"


def runs_dir() -> Path:
    """Where stage files go. Tests point it at a temporary copy with ``READMARK_RUNS_DIR``
    so a replay never rewrites the committed run."""
    return Path(os.environ.get("READMARK_RUNS_DIR") or ROOT / "runs")


def case_run_dir(case_id: str) -> Path:
    return runs_dir() / case_id


def load_dotenv_key(name: str) -> str | None:
    """A key from the environment, else from the repo's git-ignored ``.env``."""
    if os.environ.get(name):
        return os.environ[name]
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() == name:
                return value.strip().strip('"').strip("'") or None
    return None


def dumps(obj) -> str:
    """Every stage file is written one way, so a replay is byte-identical."""
    return json.dumps(obj, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
