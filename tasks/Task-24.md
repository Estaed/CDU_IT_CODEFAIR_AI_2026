# Task-24: The case screen speaks its question list's language
> **Execution:** agent `codex` · effort `high`
> *Why:* the easy example S-01 (Task-21) is a student's extension request. Its screen still says
> "Applicant file", "Priority housing review · Darwin urban", "Delegated officer", shows the Darwin
> housing wait time, and offers "Approve priority housing". Tarık must be able to follow S-01 without
> housing words. Codex `gpt-6.1-sol`: the Claude weekly window is at 91% until 4 Oct 21:30.

**Lane**
- OWNS: `web/**`, `readmark/serve.py`, `readmark/record/**`, `tests/test_screen.py`, `tests/test_home.py`, `reports/screens/2026-10-03-wave8b/**`
- MUST NOT TOUCH: `readmark/checklist/**`, `readmark/ingest/**`, `readmark/pipeline.py`, `readmark/checks/**`, `readmark/gate/**`, `readmark/jev/**`, `readmark/writer/**`, `readmark/audit/**`, `readmark/eval/**`, `readmark/schemas/**`, `runs/**`, `data/**`, `design/**`, `docs/**`, `AGENTS.md`, `notes.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: Task-19, Task-21

## Goal
Every officer-facing word that belongs to a domain comes from the case's question list
(`load_question_list(case_question_list(case_id))`, documented in `docs/question-lists.md`):
- **`labels`:**
  - `service` names the service in the header band;
  - `case_noun` replaces "Applicant file" on the case screen, the home screen, the record and both
    exports;
  - `officer` replaces "Delegated officer".
- **`decisions`:** labels for approve, decline and request_information. They appear in the
  decision choice, the check page, the record, both exports and the home screen's completed rows.
  Record JSON keeps its keys (`approve` and the rest); only labels change.
- **The wait-time line** (NT housing open data) appears only for cases on the `nt-priority-housing`
  list.
- **A list without `labels` or `decisions`** keeps today's housing wording exactly. A-0142, E-01..03
  and H-01 look as they do now.

## Why
S-01 is how Tarık learns the system. Housing words on an extension request would confuse exactly
the person it is for.

## Acceptance
- [ ] `uv run python scripts/gate.py` exits 0, and `git status` shows no change after it runs.
- [ ] Headless on S-01 (case and home screens):
  - no "Applicant file", "Priority housing", "Delegated officer", "Darwin urban" or wait-time line;
  - "Extension request S-01", "Unit lecturer" and the CDU service name appear;
  - the decision choice offers "Approve the extension", "Decline the extension" and "Ask the
    student for more information".
- [ ] Headless: signing S-01 in a temporary copy gives a record and both exports with the extension
  labels. The record JSON's `decision` is still one of `approve`, `decline` or
  `request_information`.
- [ ] Headless on A-0142: header, identity bar, wait-time line and decision labels are unchanged.
- [ ] Tests read labels from the list files, never pin S-01's wording in a way that breaks if the
  list text changes.
- [ ] Screenshots of S-01's case screen, check page and home entry at 1280 and 1440 in
  `reports/screens/2026-10-03-wave8b/`. Tests write to `.tmp/shots/`, and the delivered set is
  copied once.
- [ ] (eye) Tarık opens S-01 and sees no housing word.

## Out of scope
- Changing what the checks flag on S-01 (the orchestrator's scan fix runs alongside).
