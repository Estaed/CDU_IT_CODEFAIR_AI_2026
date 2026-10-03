"""Evaluation parts. Each part writes ``runs/eval/<part>.json``; ``runs/eval/summary.json`` is
assembled from every part file present, so a later part is added without editing this one.
Every reported number sits in a dict beside its ``n`` (Blueprint, Verification)."""

import json
from pathlib import Path

from readmark import dumps, runs_dir

SUMMARY = "summary"


def eval_dir() -> Path:
    return runs_dir() / "eval"


def write_part(name: str, content: dict) -> Path:
    path = eval_dir() / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(content), encoding="utf-8", newline="\n")
    return path


def assemble_summary() -> Path:
    """``summary.json`` = ``{"parts": {<part>: <runs/eval/<part>.json>}}`` for every part present."""
    if (eval_dir() / 'jev_supports.json').exists():
        from readmark.eval.supports import refresh

        refresh()
    elif (eval_dir() / 'checks_round2.json').exists():
        from readmark.eval.round2 import refresh

        refresh()
    parts = {
        p.stem: json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(eval_dir().glob("*.json"))
        if p.stem != SUMMARY
    }
    return write_part(SUMMARY, {"parts": parts})
