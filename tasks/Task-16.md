# Task-16: Polish the final look: four small screen fixes
> **Execution:** agent `codex` · effort `high`
> *Why:* the wave 6 screen review left four small gaps below the fix threshold, and Tarık asked for
> them to be fixed on Codex (2026-10-03). The fourth showed up on E-02. Codex `gpt-6.1-sol`.

**Lane**
- OWNS: `web/**`, `tests/test_screen.py`, `reports/screens/2026-10-03-wave6b/**`
- MUST NOT TOUCH: `readmark/**`, `runs/**`, `data/**`, `design/**`, `docs/contracts.md`, `AGENTS.md`, `notes.md`, `reports/screens/2026-10-03-wave6/**`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: none

## Goal
The Task-15 screen with four rough edges smoothed. Nothing else changes.

1. **One word for questions.** The sign-off list says "Finish these 8 clauses". Everywhere the
   officer reads, the word is "question", as in the rest of the screen. Internal names stay.
2. **The identity bar stays tidy.** At 1440 the wait-time line wraps onto a third line when the
   primary button reads "Next: set your outcome". At 1440 it fits on one line. At 1280 it wraps at
   most once, cleanly, and the button never squeezes it.
3. **"More pages" opens without an inner scroll box.** Its list opens in place, at full height,
   above the page viewer. Both groups ("Cited by the AI's claims", "Possibly missed") are visible
   without scrolling inside a box.
4. **Several page pairs in the warning box.** On E-02, Urgent-need category, the warning box runs
   three links together: "Compare pages 2 and 9 ⇆Compare pages 1 and 9 ⇆Compare pages 1 and 9".
   - Each pair is its own line, and no pair is listed twice.
   - The sentence above names every page involved, not only the first pair.

## Why
These are the last visible rough edges before Tarık's eye check and the pitch.

## Acceptance
- [ ] `uv run python scripts/gate.py` exits 0, and `git status` shows no changes after it runs.
- [ ] Headless: no officer-facing text on A-0142 or E-02 contains "clause".
- [ ] Headless at 1440, on every question of A-0142: the wait-time line has the height of one line.
  At 1280 it is at most two lines.
- [ ] Headless: after "More pages" opens, the list's `scrollHeight` equals its `clientHeight` (no
  inner scroll), on every question of A-0142 that has the control.
- [ ] Headless on E-02, Urgent-need category: each disagreeing pair is one link on its own line,
  with no duplicates.
- [ ] The tests that need E-02 read it from `runs/E-02/view.json`.
- [ ] Screenshots of the four fixes at 1280 and 1440 in `reports/screens/2026-10-03-wave6b/`. Tests
  write to `.tmp/shots/`, and the delivered set is copied once.
- [ ] (eye) Tarık sees the same calm page as Task-15, with these four fixed.

## Out of scope
- What the checks flag, including E-02's "Income evidence not found" while its page 5 holds an
  income statement. The orchestrator looks at that separately.
- Any other layout or colour change.
