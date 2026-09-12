# Task-07: Audit log

Status: DONE

> **Execution:** agent `codex` · effort `medium` · plan mode **no**
> *Why:* append-only JSONL with a fixed record shape (PRD §3.3, §3.6); round-trip tests decide.

**Lane**
- OWNS: `fair_turn/core/audit.py`, `tests/test_audit.py`, `data/audit/.gitkeep`
- MUST NOT TOUCH: `fair_turn/app/` (Task-13 onward)
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-02

## Objective

The decision-maker's reasoning record: every sign-off, λ revision and per-job override,
with a reason, appended and exportable.

## Execution Guide

- `audit.py`: record dataclasses `SignOff` (day, lam, reason, signer, signed_at, ranked_job_ids), `Revision` (day, old_lam, new_lam, reason, at), `Override` (day, job_id, from_rank, to_rank, reason, at). `append(path, record)` writes one JSON line with a `kind` field; `read(path) -> list[record]`; `export_rows(records) -> list[dict]` flat rows for a table; `override_rate(records) -> list[(day, overrides / ranked_jobs)]`.
- Written with `newline=""` and UTF-8; never rewrites the file.
- Tests: append three kinds, read back equal; export rows have the same count; override rate on a fixture; a second append does not alter earlier lines (byte compare).

## Acceptance Criteria (DoD)

- [x] Round-trip and byte-stability tests pass.
- [x] `read` on an empty or missing file returns `[]`.
- [x] Gate green.
