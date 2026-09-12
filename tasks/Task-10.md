# Task-10: Generate the synthetic report texts

> **Execution:** agent `claude` (main loop) · effort `high` · plan mode **no**
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
- `tests/test_reports_artefact.py`: every label has exactly one report; every text within length bounds; no deficit term; no real name; at least 30 distinct opening words across the set (a cheap variety check).

## Acceptance Criteria (DoD)

- [ ] `data/build/reports.json` committed with one report per label in `labels.json`.
- [ ] Artefact test passes.
- [ ] Rerunning the script with the artefact present makes zero CLI calls (tested with the fake executable).
- [ ] Gate green.
