# Task-11: Review screen as an answer key: the file itself, highlighted by question
**Status: DONE** — verified 2026-10-03, eye check pending: 1
> **Execution:** agent `codex` · effort `high`
> *Why:* Tarık still could not follow the wave 2 screen: too much text, all of it run together.
> His idea (2026-10-03, from IELTS answer keys) is to make the case file itself the reading
> surface, with each verified quote highlighted on its page and labelled with its question.
> Blueprint → Decisions records it. Codex `gpt-6.1-sol` at his request.

**Lane**
- OWNS: `web/**`, `readmark/serve.py`, `readmark/record/**`, `tests/test_screen.py`
- MUST NOT TOUCH: `readmark/eval/**`, `readmark/__main__.py`, `readmark/ingest/**`, `readmark/pipeline.py`, `runs/**`, `data/benchmark/**` (Task-10); `readmark/checks/**`, `readmark/jev/**`, `readmark/gate/**`, `readmark/writer/**`, `readmark/audit/**`, `readmark/schemas/**`; `data/**`, `design/**`, `docs/contracts.md`, `AGENTS.md`, `notes.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: none

## Goal
The screen gets much simpler. The officer reads the file itself, guided like an exam answer key.

- **The file is the middle of the screen.** It shows the real pages of the case file. Every
  code-verified quote is highlighted on its page, with a small label naming the question it
  answers ("Debts", "Income").
  - Flagged highlights are marked and come first; clean ones are quiet.
  - The highlight shows where the evidence sits. The AI's own sentence is one click away, never the
    main text.
- **Flagged questions first.** The left list shows the questions with something to look at, with
  the reason in a few words ("two pages disagree", "income evidence not found").
  - Questions with nothing flagged (residency, for example) fold into one line, "5 questions look
    clean". It opens on click, and the officer still sets their outcome.
- **Moving through the file.** Picking a question jumps to its first highlight. "Next flag" and
  "previous flag" move between highlights without scrolling 60 pages. A contradicting pair shows
  both pages, and a possibly-missed passage shows as a highlight with its own label.
- **Calm layout.** Boxes and space instead of dense text. Fewer words on screen at once. The look
  stays Tarik Base, design A (`web/theme.css`, `web/tokens.css`).
- **The summary tab goes.** The view's `audit` block stays in the data but is not shown.
- **What stays:**
  - the case bar with both counters and the next-step button;
  - required reading of at most 8 passages, opened before sign-off, with time in view;
  - outcomes never pre-filled; dispute with a reason;
  - the server-enforced lock; the check-your-answers summary;
  - the record and its HTML and JSON export.
- **Full page text** comes from the synthetic case file through a read-only endpoint in
  `readmark/serve.py`. Policy text stays as it is: read from the pinned PDFs on demand, only the
  short quotes shown.

## Why
The screen is what Tarık, the judges and an officer see. A view an officer cannot follow at first
sight defeats the point of a reading gate.

## Acceptance
- [x] `uv run python scripts/gate.py` exits 0.
- [x] Headless Playwright on A-0142, at 1280 and 1440 wide: no console errors and no horizontal
  overflow; the whole flow passes (open each required passage, set all 8 outcomes, locked before and
  unlocked after, sign, the record holds `opened_at` and `seconds_in_view` per passage, export HTML
  and JSON).
- [x] Headless: every verified quote of a flagged claim is highlighted in its page with its question
  label; picking a question scrolls to its first highlight; "next flag" reaches every flagged
  highlight in order.
- [x] Headless: questions with nothing flagged are folded into one line at first load, and their
  outcomes can still be set.
- [x] Headless: no summary-under-audit tab; no claim ids, model ids or the pilcrow on the main
  screen.
- [ ] (eye) Tarık opens `uv run python -m readmark serve --case A-0142`: a first-time viewer names
  the next step within 10 seconds, and the screen reads as calm, an answer key over the real file
  rather than a wall of text. Reference: Blueprint → Decisions (review screen, after the wave 2
  look), and the look of `design/direction-A.html`.

## Out of scope
- New checks or pipeline data; the look polish beyond Tarik Base; a mobile layout.
- Opening anything under `data/heldout/`.
