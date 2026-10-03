# Task-17: Plain AI notes, and the usability fixes
> **Execution:** agent `codex` · effort `high`
> *Why:* Tarık could not follow "AI claims · N" when he opened it. He also asked for a usability pass
> on the screen (2026-10-03: "sign olayı gri olması çık olmamış ... yeşile dönsün onaylanınca"). The
> pass is `reports/2026-10-03-usability-notes.md`. Tarık chose the 3-second rule for U6. Codex
> `gpt-6.1-sol`: the Claude weekly window is at 90% until 4 Oct 21:30.

**Lane**
- OWNS: `web/**`, `readmark/record/**`, `readmark/serve.py`, `tests/test_screen.py`, `reports/screens/2026-10-03-wave7/**`
- MUST NOT TOUCH: `readmark/checklist/**`, `readmark/ingest/**`, `readmark/pipeline.py`, `readmark/__init__.py`, `readmark/__main__.py` (Task-18); `readmark/checks/**`, `readmark/jev/**`, `readmark/writer/**`, `readmark/audit/**`, `readmark/eval/**`, `readmark/schemas/**`, `runs/**`, `data/**`, `design/**`, `docs/contracts.md`, `AGENTS.md`, `notes.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: none

## Goal
The Task-16 screen, with the AI's notes made readable and the ten usability notes fixed.

- **"What the AI noted (N)"** replaces "AI claims · N".
  - It stays closed by default: the officer reads the evidence before the AI's conclusion.
  - Opened, it shows one plain card per note:
    - the AI's sentence;
    - the quote it rests on, with page and document, and a link that opens that page in the viewer;
    - the check result in words, for example "Found in the file ✓", "The second reader is not sure",
      "Page 23 says the opposite" or "Quote not found in the file";
    - a "This note is wrong" button, which is today's dispute, with its reason box.
  - No internal ids, verdict codes or scores are shown on the card.
  - The same plain wording is used where a disputed note appears on the check page and in the
    record.
- **The usability notes U1–U9** (`reports/2026-10-03-usability-notes.md`), all of them:
  - **U1, the sign button:**
    - not ready: an outlined "Sign decision · N questions left";
    - ready: one green primary "Sign decision", and the duplicate "Next: sign decision" goes;
    - signed: a green "Signed ✓".
    - Green carries words too, never colour alone.
  - **U2, outcome icons:** one per outcome, with the word kept. Met ✓ green, Not met ✗ red, Cannot
    decide yet ⏸ amber.
  - **U3, the signed row:** a green tick or lock, with "Signed · record locked".
  - **U4, the in-page timers:** "Opened · in view N s" leaves the reading surface. The record keeps
    the times.
  - **U5, repeated tags:** the first paragraph of a run carries the full tag; the paragraphs after
    it carry a small marker.
  - **U6, what "opened" means:** a passage counts as opened once it has been in view for **3 s**,
    counted over its time in view.
    - The record keeps `opened_at` (the moment the 3 s were reached) and `seconds_in_view`.
    - The 3 s threshold is written once in the code and named in "How this works" and the record's
      footnote.
    - The record still says "opened", never "read".
  - **U7, one name per page:** "Open before you sign" and the tabs use the same page label.
  - **U8:** "Other facts" becomes "Background facts (no decision needed)".
  - **U9:** "Clause outcomes" becomes "Your answers to the questions" on the check page and in both
    exports. No officer-facing text says "clause".

## Why
These are the last things standing between a first-time viewer and the next step. Tarık's eye is
the judge.

## Acceptance
- [ ] `uv run python scripts/gate.py` exits 0, and `git status` shows no change after it runs.
- [ ] The A-0142 replay is byte-identical: run `python -m readmark run --case A-0142 --replay`, and
  `runs/` shows no diff.
- [ ] Headless on A-0142 and E-02:
  - "What the AI noted" is closed when a question opens;
  - opened, every card shows the sentence, the quote with its page, and the result in words;
  - no card shows an internal id or a raw verdict code;
  - "This note is wrong" saves a dispute that appears in the record.
- [ ] Headless: the sign button is outlined with "N questions left" while not ready, green and
  single when ready, and "Signed ✓" after signing.
- [ ] Headless: each outcome shows its own icon and its word in the question list.
- [ ] Headless (U6): a page shown for under 3 s is not counted as opened. The same page shown for
  3 s or more is counted, with `seconds_in_view` ≥ 3 in the record. Tests may shorten the clock
  through a test-only setting, but the shipped value is 3 s.
- [ ] Headless: no officer-facing text on A-0142 or E-02, the check page, or either export contains
  "clause", "claim id" or "c" followed by digits.
- [ ] Screenshots of each fix at 1280 and 1440 in `reports/screens/2026-10-03-wave7/`. Tests
  write to `.tmp/shots/`, and the delivered set is copied once.
- [ ] (eye) Tarık opens "What the AI noted" on Debts and understands every card without help.
- [ ] (eye) Tarık sees the sign button change from outlined, to green, to Signed.

## Out of scope
- What the checks flag, including E-02's income flag. The orchestrator checks that separately.
- The home screen and more than one case (Task-19).
