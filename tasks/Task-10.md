# Task-10: Generate the synthetic report texts

Status: DONE

> **Execution:** agent `claude` (main loop) · effort `high`
> *Why:* spends the Claude subscription window (check with `limit` first); prompt design decides text realism; the artefact validity is gated, the run itself is not.

**Lane**
- OWNS: `fair_turn/llm/prompts.py`, `scripts/generate_text.py`, `data/build/reports.json`, `tests/test_reports_artefact.py`
- MUST NOT TOUCH: `fair_turn/llm/claude_cli.py` (Task-09), `data/build/labels.json` (Task-03)
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-03, Task-09

## Objective

Give every label tuple a tenant's own words, conditioned on a household persona, written
by the generator model, 20 labels per call, resumable, and commit the result.

## Execution Guide

- `prompts.py`: the generation system text (untrusted-content rules do not apply here; this is our authoring prompt) and `generation_prompt(labels_batch, personas) -> str` listing 20 label tuples and asking for one report per tuple in the persona's register, 1–4 sentences, Australian English, no place names, no personal names; forbid the deficit terms explicitly. Output schema: `{"reports": [{"job_id": str, "text": str}]}` with `additionalProperties: false`.
- `scripts/generate_text.py`: reads labels and personas, skips job_ids already in `reports.json`, calls `claude_cli.generate` per batch, validates each item (job_id known, text 20–600 chars, `wording.check(text) == []`, no real community name), appends, writes after every batch so an interrupted run resumes. Prints calls made and elapsed.
- Run it fully once; commit `data/build/reports.json`.
- Deviation (2026-09-13): `validate` rejects deficit terms only, not `reading_level`. The FK ≤ 7 ceiling in PRD section 7 is for text the tool writes to tenants; a tenant's own report is input, and the artefact test already excluded it. The pilot batch lost 3 of 20 to it. Batches run 4 in parallel (`--workers`); the file is still written after every batch.
- `tests/test_reports_artefact.py`: every label has exactly one report; every text within length bounds; no deficit term; no real name; at least 30 distinct opening words across the set (a cheap variety check).

## Acceptance Criteria (DoD)

- [x] `data/build/reports.json` committed with one report per label in `labels.json`.
- [x] Artefact test passes.
- [x] Rerunning the script with the artefact present makes zero CLI calls (tested with the fake executable).
- [x] Gate green.
