# Task-25: A calmer tier for "possibly missed": flags for problems, "worth a look" for unused pages
> **Execution:** agent `codex` · effort `high`
> *Why:* the easy example S-01 showed 5 of 5 questions flagged where 2 had a real issue. Counting on
> the stored runs (`reports/2026-10-03-easy-example.md` → *Follow-up*) shows the scan is not wrong,
> and changing it would drop A-0142's key page 51. The noise is in the presentation: unused relevant
> pages look like errors. Tarık asked the orchestrator to cut the noise (2026-10-03). Codex
> `gpt-6.1-sol`.

**Lane**
- OWNS: `web/**`, `readmark/serve.py`, `readmark/record/**`, `tests/test_screen.py`, `tests/test_home.py`, `reports/screens/2026-10-03-wave8c/**`
- MUST NOT TOUCH: `readmark/checks/**`, `readmark/gate/**`, `readmark/pipeline.py`, `readmark/checklist/**`, `readmark/ingest/**`, `readmark/jev/**`, `readmark/writer/**`, `readmark/audit/**`, `readmark/eval/**`, `readmark/schemas/**`, `runs/**`, `data/**`, `design/**`, `docs/**`, `AGENTS.md`, `notes.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: Task-24

## Goal
Two tiers on the case screen and the home screen, from the same `view.json`.

- **"Needs a look"** (today's orange "!" flag) is kept for a question with a problem in the AI's
  notes or the file:
  - a note contradicted by another page ("two pages disagree");
  - a quote not found;
  - the checker disagrees;
  - "evidence not found in the file".
- **"Worth a look (N pages)"** is for a question whose only signal is possibly-missed passages.
  - It uses a calm marker, not the orange flag: for example a blue-grey "○" with the words.
  - Its row status reads, for example, "Worth a look · 3 pages the AI did not use".
- **Required reading is unchanged.** A possibly-missed passage the gate requires stays required, and
  "Open before you sign" still lists it.
  - On a "worth a look" question it reads "Must open: a page the AI did not use".
  - The counters keep counting it.
- **"N questions look clean" stays for questions with neither tier.** The list order is: needs a
  look, then worth a look, then clean.
- **The home screen's "Flags at a glance"** counts the two tiers separately: "N need a look · M worth
  a look".
- **Words always carry the meaning, not colour alone.** The "How this works" panel explains the two
  tiers in two sentences.

## Why
The officer's attention goes first to what is wrong, and the easy example becomes readable. No check,
gate rule or frozen number changes.

## Acceptance
- [ ] `uv run python scripts/gate.py` exits 0, and `git status` shows no change after it runs.
- [ ] The A-0142, E-*, H-01 and S-01 replays and `runs/eval/` are unchanged (no `runs/` diff).
- [ ] Headless: for every question of every case in `runs/`, the tier shown matches this rule,
  computed from `view.json` in the test rather than from a pinned list. **Needs a look** applies when
  any of these holds:
  - a claim of the question is not `supported`;
  - its `contradictions` is non-empty;
  - its `missing` is non-empty;
  - its coverage is `no_evidence_in_file`.

  Otherwise it is **worth a look** if `possibly_missed` is non-empty, and **clean** if not.
  Counted on the stored runs (2026-10-03):

  | Case | Needs a look | Worth a look | Clean |
  |---|---|---|---|
  | A-0142 | 6 | 2 | 0 |
  | E-01 | 5 | 2 | 1 |
  | E-02 | 5 | 0 | 3 |
  | E-03 | 4 | 1 | 3 |
  | H-01 | 6 | 1 | 1 |
  | S-01 | 2 | 3 | 0 |
- [ ] Headless on S-01: at most 2 questions show "needs a look", and the others show "worth a look"
  or clean.
- [ ] Headless on A-0142: Debts, Residency, and every question with a contradicted or
  checker-disagrees note still show "needs a look". Required reading and counters are unchanged.
- [ ] Screenshots of S-01 and A-0142 (case list and home) at 1280 and 1440 in
  `reports/screens/2026-10-03-wave8c/`. Tests write to `.tmp/shots/`, and the delivered set is
  copied once.
- [ ] (eye) Tarık sees S-01 with most questions calm, and the real problems standing out.

## Out of scope
- Any change to the scan, the gate or the evaluation numbers.
