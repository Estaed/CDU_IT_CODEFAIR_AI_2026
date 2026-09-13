# Task-23: Phase 2 shell: five surfaces, layer rule, runtime store, human-set fields reach the ranking

Status: TODO

> **Execution:** agent `codex` · effort `medium` · plan mode **no**
> *Why:* Part 2 names every file and rule; the work is plumbing with unit and layer tests as the criterion.

**Lane**
- OWNS: `fair_turn/app/main.py`, `fair_turn/app/pages/workspace.py`, `fair_turn/app/pages/review_queue.py`, `fair_turn/app/pages/visit_plan.py`, `fair_turn/app/pages/evidence_lab.py` (stubs only), `fair_turn/app/state.py`, `fair_turn/data/runtime.py`, `fair_turn/data/artefacts.py` (`to_jobs` merge only), `.gitignore` (append `data/runtime/`), `tests/test_layers.py`, `tests/test_runtime.py`, `tests/test_app_smoke.py` (page registration and default-page assertions), `tests/conftest.py` (new: autouse fixture isolating `data/runtime/`; added by the orchestrator 2026-09-14)
- MUST NOT TOUCH: `fair_turn/app/pages/board.py`, `job_card.py`, `sign_off.py`, `feedback.py`, `audit_log.py` (retired by Task-30 and Task-34), `fair_turn/core/` (Task-24 to Task-26)
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: none

## Objective

Give Phase 2 its skeleton so later tasks own one file each: the five-surface navigation
with stub pages, the amended layer rule, the runtime store for intake reports and
human-set fields, and the fix for the Phase 1 gap where a human-set field never reached
the ranking (`BACKLOG.md`, Task-16 entry).

## Execution Guide

- `main.py`: `st.navigation` lists Workspace (default), Review queue, Visit plan, Tenant answer (`pages/tenant.py`, existing), Evidence lab. Phase 1 pages stay on disk, unregistered, until their retiring task deletes them. Each stub page: `st.title`, the provenance caption via `theme.PROVENANCE_LINE`, one `st.info("Built in Task-XX")`.
- `tests/test_layers.py`: `llm` may import `urllib`; add a third check: only `fair_turn/app/intake.py` may match `^\s*(from|import)\s+fair_turn\.llm`; any other file under `app/` that does fails with the file name.
- `data/runtime.py`: `RUNTIME_DIR = ROOT / "data" / "runtime"`; records as frozen dataclasses `HumanSetField(job_id, field, value, actor, reason, at)` and `IntakeReport(job_id, community_id, reported_on, text, extraction: dict | None, status: "extracted" | "needs_review" | "not_extracted", provider, model, prompt_version, latency_s, validation, draft_token, at)`; `append(path, record)`, `read(path) -> list`, `human_set_for(records) -> dict[job_id, dict[field, value]]`, `next_job_id(existing_ids) -> str` (`JR-2025-` plus five digits above the max). JSONL, `newline=""`, UTF-8, `_DATETIME_FIELDS` handling as in `core/audit.py`. Idempotence: `append` of an `IntakeReport` whose `draft_token` already exists in the file is a no-op returning `False`.
- `artefacts.py`: `to_jobs(art, human_set: dict | None = None, intake: list[IntakeReport] | None = None)` applies human-set values to `fault_type` / `safety_class` before building `Job` and appends intake jobs with status `extracted`. Existing callers unchanged (defaults).
- `state.py`: replace the session-only `get_human_set`/`set_human_set` with accessors over `runtime.py` (path from `get_runtime_path()`, default `RUNTIME_DIR / "runtime.jsonl"`, overridable like `audit_path`); add accessors for Phase 2: `get/set_preset`, `get/set_compare`, `get/set_batch` (opaque object, Task-25 defines it), `get/set_plan`, `get/set_intake_draft`, `get/set_review_cursor`. Every page still reads state only through this module.
- `.gitignore`: append `data/runtime/`.
- Tests: layer rule negative cases with `tmp_path` fixtures; runtime round-trip; duplicate `draft_token` is a no-op; a job with an empty `fault_type` plus a `HumanSetField` for it leaves `split_human_queue`'s queue and appears in `rank` (the BACKLOG gap); `test_main_runs_offline` asserts the default title is "Workspace".

## Acceptance Criteria (DoD)

- [ ] Layer test enforces the `app/intake.py` exception and `urllib` in `llm`.
- [ ] Runtime store round-trips, is idempotent on `draft_token`, and human-set fields move a job into the ranking (unit tests).
- [ ] AppTest opens all five registered pages with sockets refused; the provenance caption is on each.
- [ ] `data/runtime/` ignored; the committed tree contains no runtime file.
- [ ] Gate green.
