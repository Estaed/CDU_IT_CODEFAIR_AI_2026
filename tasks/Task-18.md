# Task-18: Question lists: each list brings its own policies and questions
> **Execution:** agent `codex` · effort `high`
> *Why:* Tarık wants question lists per application type and an easy, non-housing example
> (2026-10-03). Today the 8 housing questions sit in one `clauses.yaml`, and the five NT policies
> are hard-coded in `readmark/ingest` (`POLICIES`). Codex `gpt-6.1-sol`: the Claude weekly window is
> at 90% until 4 Oct 21:30.

**Lane**
- OWNS: `readmark/checklist/**`, `readmark/ingest/**`, `readmark/pipeline.py`, `readmark/__init__.py`, `readmark/__main__.py`, `tests/test_checklist.py`, `tests/test_ingest.py`, `tests/test_pipeline.py`, `docs/question-lists.md`
- MUST NOT TOUCH: `web/**`, `readmark/record/**`, `readmark/serve.py`, `tests/test_screen.py` (Task-17); `readmark/checks/**`, `readmark/jev/**`, `readmark/writer/**`, `readmark/audit/**`, `readmark/eval/**`, `readmark/schemas/**`, `runs/**`, `data/**`, `design/**`, `docs/contracts.md`, `AGENTS.md`, `notes.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: none

## Goal
A **question list** is one self-contained unit. It holds:
- its id and title ("NT priority housing, urban");
- its policy bundle: each policy's key, file name and title, pinned by SHA-256;
- its approved questions, in today's clause shape: id, title, source, the verbatim policy sentence
  and what it decides.

The rules:
- **Today's 8 housing questions and 5 NT policies become the list `nt-priority-housing`.** It is
  the default.
- **A case names its list** in a small file in its case folder. A case without that file uses the
  default, so every existing case, test and command behaves as today.
- **Ingest and pipeline read the case's list** for its policies and questions. Nothing hard-codes
  the NT bundle any more.
- **A new list is added as a new folder** (or file) with no code change. It is written up in
  `docs/question-lists.md`, in short, plain sentences: the layout, how pins work, and that a person
  approves every list before use.
- **The public API** that Task-19 and Task-21 will call: list the lists, load one, and name a
  case's list. Keep it small, and document it in `docs/question-lists.md`.

## Why
The easy example (Task-21) and new cases (Task-20) need lists other than housing. The home screen
(Task-19) shows each case's list.

## Acceptance
- [ ] `uv run python scripts/gate.py` exits 0, and `git status` shows no change after it runs.
- [ ] **Nothing changes for existing cases.** `python -m readmark run --case <id> --replay` for
  A-0142, E-01, E-02, E-03 and H-01 leaves `runs/` byte-identical (`git status` clean). Every file
  under `runs/eval/` is byte-identical.
- [ ] A test builds a second, tiny list in a temporary folder: one policy text file pinned by its
  hash, and two questions. A tiny case that names that list then runs through ingest and checklist
  with a fake writer and checker. Its passages come from that policy, not from the NT bundle.
- [ ] A changed policy file in any list still fails loudly on its pin, as today.
- [ ] `docs/question-lists.md` exists, and says how to add a list in under a page.

## Out of scope
- The CDU list itself and the easy example (Task-21).
- Showing the list on screen, or serving more than one case (Task-19).

Fixed: `view.json` keeps its schema; `runs/` does not change.
