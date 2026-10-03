# Task-19: Case home screen: cases in progress and completed
**Status: DONE** — verified 2026-10-03, eye check pending: 1
> **Execution:** agent `codex` · effort `high`
> *Why:* Tarık wants a home screen that lists the cases, in progress and completed, with a layout
> like Claude's or Codex's session list (look only, no chat), 2026-10-03. Today the server opens one
> case, given by `--case`. Codex `gpt-6.1-sol`: the Claude weekly window stood at 91% at 22:20 on
> 3 Oct, and Tarık asked to start wave 8 straight away.

**Lane**
- OWNS: `web/**`, `readmark/serve.py`, `readmark/record/**`, `tests/test_screen.py`, `tests/test_home.py`, `reports/screens/2026-10-03-wave8/**`
- MUST NOT TOUCH: `readmark/checklist/**`, `readmark/ingest/**`, `readmark/pipeline.py`, `readmark/checks/**`, `readmark/jev/**`, `readmark/writer/**`, `readmark/audit/**`, `readmark/eval/**`, `readmark/schemas/**`, `runs/**` (except new records written by tests into temporary folders), `data/**` (Task-21), `design/**`, `docs/contracts.md`, `AGENTS.md`, `notes.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: Task-17, Task-18

## Goal
- **`python -m readmark serve` with no `--case` opens the home screen.** `--case <id>` still opens
  that case directly, as today.
- **The home screen.** In the `design/DESIGN.md` look, laid out like a session list:
  - On the left, the cases, grouped **In progress** and **Completed**. Completed means a signed
    record exists; in progress means anything else.
  - Each row shows the case name, its question list's title, its page count and, for a case in
    progress, "N of 8 decided". For a completed case it shows the decision and the date signed.
  - On the right, the selected case's summary: its documents, its question list, its flags at a
    glance, and one primary button, "Open case" or "View record".
  - A "New case" button sits at the top of the list. It is inactive until Task-20, with a short
    "coming in this build" note.
- **Which cases appear.** Every case under `runs/` that has a `view.json`, except `stub` and `eval`.
  The evaluation files (E-01 to E-03, H-01) appear in their own quiet group, "Evaluation files".
- **Each case is separate.** Its passages-opened state, outcomes, disputes and record belong to
  that case. They survive a reload and never leak into another case.
- **The case screen** gains a way back to the home screen. Its policy dialog reads the policies of
  the case's own question list (Task-18 API), not a fixed bundle.

## Why
Readmark becomes a tool with a queue of files rather than a single demo page. It is also where new
cases (Task-20) and the easy example (Task-21) live.

## Acceptance
- [x] `uv run python scripts/gate.py` exits 0, and `git status` shows no change after it runs.
- [x] The A-0142 replay is byte-identical (`runs/` shows no diff).
- [x] Headless: the home screen lists A-0142 (in progress), E-01, E-02, E-03 and H-01 (Evaluation
  files), each with its list title and page count. No console errors at 1280 or 1440.
- [x] Headless: signing A-0142 in a temporary copy moves it to Completed, with its decision and
  date.
- [x] Headless: decide two questions on A-0142, go home, open E-02. E-02 shows 0 decided, and
  going back to A-0142 still shows 2 decided.
- [x] `--case A-0142` still opens the case screen directly, and every existing screen test passes.
- [x] Screenshots of the home screen (in progress, completed and evaluation groups) at 1280 and
  1440 in `reports/screens/2026-10-03-wave8/`. Tests write to `.tmp/shots/`, and the delivered set is
  copied once.
- [ ] (eye) Tarık finds the home screen as calm as the case screen, and knows where to click
  first.

## Out of scope
- Uploading a new case (Task-20). Search (Task-23).
