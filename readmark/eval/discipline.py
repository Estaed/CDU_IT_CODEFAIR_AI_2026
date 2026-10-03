"""Pin the implementation before the single held-out run; labels belong to the scorer.

The run marker is written before any input or model call. A failed run needs an explicit,
reported crash recovery rather than a silent second attempt. No recovery is automatic.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from readmark import ROOT, dumps
from readmark.audit.claude import call_claude
from readmark.writer import WRITER_SCHEMA, ClaudeWriter, build_prompt


class EvaluationWriter(ClaudeWriter):
    """The same writer prompt and cache key, with the audit's tool-free CLI execution.

    Isolation prevents a held-out writer from opening gold with a file tool. The audit CLI
    makes one attempt, so an invalid answer cannot silently spend another writer call.
    Existing E-file responses replay unchanged; the demo and stub keep their original writer.
    """

    def write(self, case_meta: dict, case_passages: list[dict], clauses: list[dict],
              policy_by_id: dict[str, dict]) -> dict:
        prompt = build_prompt(case_meta, case_passages, clauses, policy_by_id)
        request = {"model": self.model, "prompt": prompt, "schema": WRITER_SCHEMA}
        response = self.cache.call("writer", request,
                                   lambda: call_claude(prompt, self.model, WRITER_SCHEMA))
        self.model_id = response["model"]
        return response["output"]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def implementation_files() -> list[Path]:
    return sorted([
        *[p for p in (ROOT / "readmark").rglob("*")
          if p.is_file() and p.suffix in (".py", ".yaml", ".json")
          and not any(part in (".tmp", "__pycache__") for part in p.parts)],
        ROOT / "tests" / "test_eval_cases.py",
        ROOT / "uv.lock",
    ])


def implementation_pin() -> dict:
    files = implementation_files()
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in files}


# Files that compute no H-01 result: the screen server, the officer's decision record, and this
# guard itself (it only decides whether scoring may run). Changing them after H-01 must not void
# its numbers; otherwise the repo would stay frozen for good (orchestrator integration fix,
# 2026-10-03, when the Task-11 screen landed after H-01). The H-01 view digest check below still
# proves the scored output is the frozen run's output.
NOT_RESULT_CODE = ("readmark/serve.py", "readmark/record/", "readmark/eval/discipline.py",
                   # Question-list coverage (Task-26) only advises whoever maintains a list; no
                   # case run reads it (orchestrator integration fix, 2026-10-04).
                   "readmark/checklist/coverage.py", "readmark/jev/coverage.py")


def is_coverage_file(path: str) -> bool:
    """A list's stored coverage result or its Jev cache, under readmark/checklist/lists/<id>/."""
    return path.endswith("/coverage.json") or "/coverage-cache/" in path


def result_pin(pin: dict) -> dict:
    """The part of an implementation pin that can affect H-01's results."""
    return {path: digest for path, digest in pin.items()
            if not path.startswith(NOT_RESULT_CODE) and not is_coverage_file(path)}


def save(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(record), encoding="utf-8", newline="\n")


def start_heldout(out: Path) -> None:
    """Exclusive creation makes a second live run fail before reaching a model."""
    path = out / "evaluation.json"
    if path.exists() or any((out / "cache").glob("writer-*.json")):
        raise RuntimeError("H-01 has already started; replay only. Report any crash recovery.")
    files = implementation_files()
    record = {
        "case_id": "H-01", "code_frozen_at": now(),
        "last_code_change_at": datetime.fromtimestamp(
            max(p.stat().st_mtime for p in files), timezone.utc).isoformat(),
        "implementation_sha256": implementation_pin(), "started_at": now(),
        "completed_at": None,
        "discipline": "Code, prompts and thresholds frozen before the one live run. "
                      "No held-out labels enter a model. No changes or tuning after the run.",
    }
    out.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(dumps(record))


def finish_heldout(out: Path) -> None:
    path = out / "evaluation.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    if implementation_pin() != record["implementation_sha256"]:
        raise RuntimeError("Implementation changed during H-01; report the violation.")
    record["completed_at"] = now()
    record["view_sha256"] = hashlib.sha256((out / "view.json").read_bytes()).hexdigest()
    save(path, record)


def assert_scoring_allowed(out: Path) -> dict:
    """The scorer calls this before opening SEALED.md, gold.json or facts.csv."""
    record = json.loads((out / "evaluation.json").read_text(encoding="utf-8"))
    if not record["completed_at"] or not (out / "view.json").exists():
        raise RuntimeError("H-01 labels stay sealed until its live pipeline has completed.")
    current = result_pin(implementation_pin())
    frozen = result_pin(record["implementation_sha256"])
    changed = sorted(path for path in current.keys() | frozen.keys()
                     if current.get(path) != frozen.get(path))
    digest = hashlib.sha256((out / "view.json").read_bytes()).hexdigest()
    if not changed and digest != record["view_sha256"]:
        raise RuntimeError("H-01 view differs from the completed live run.")
    # Never rewrite the single-run marker or its original view digest. Changed code is scored
    # openly as a follow-up, while the frozen first-run metrics remain alongside it in eval.
    return {**record, "scoring_label": "after changes, not held-out" if changed else "held-out",
            "changed_result_files": changed, "scored_view_sha256": digest}
