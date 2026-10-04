# Task-29: The Ochre Card case live on the website: questions from the rules, then the file
> **Execution:** agent `main-loop` · effort `high`
> *Why:* Split from Task-28 on 2026-10-04 (Tarık: "2 ye bolelim ikincisi test zaten"). Tarık
> does this by hand on the website, as an officer would, and may do it while showing the app to
> friends. It makes live Claude calls, so it starts after the Claude reset (21:30 on 4 Oct).
> ⛔ Not for otopilot: Tarık starts it himself; the main loop helps and records.

**Lane**
- OWNS: `readmark/checklist/lists/nt-wwcc/**`, `data/cases/W-01/**`, `runs/W-01/**`, `reports/2026-10-04-ochre-questions.md`, `reports/screens/2026-10-05-wave13/**`
- MUST NOT TOUCH: everything Task-28 must not touch, and Task-28's code (`web/**`, `readmark/**` outside `nt-wwcc/`)
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: Task-28

## Goal

### 1. On the website (Tarık)
- **New question list from the rules:** upload the two rule PDFs from `data/policies/nt-wwcc/`.
  The scope sentence: the NT Screening Authority deciding whether a candidate for a Working with
  Children Clearance poses an unacceptable risk of harm or exploitation to children. Claude
  suggests; Tarık approves, edits or rejects each question. Only suggestions whose sentence is
  found in the rules can be approved.
- **New case:** upload W-01's 24 PDFs, pick that list, and run it live (Claude writer, Jev).

### 2. Make it part of the submission (main loop)
- What the website made is git-ignored (`data/question-lists/`, `data/uploads/`, `runs/U-*`).
  Move the approved list to `readmark/checklist/lists/nt-wwcc/` and the run to `runs/W-01/`, so
  W-01 opens offline with no key from the replay cache, the way A-0142 does (Blueprint, Done
  means). Its intake note comes from `data/cases/W-01/`. Remove the local `U-*` copy afterwards.
- **Measure it** in `reports/2026-10-04-ochre-questions.md`, each number with its n:
  - how many of the answer key's 10 clause_ids the approved questions cover;
  - how many suggestions failed the sentence check, and which were rejected and why;
  - required reading (8 or fewer) and flags per question;
  - whether the T1 contradiction (`03-p4` against `10-p1`) and the T3 address omission are flagged.

## Why
The pitch shows two very different NT decisions on the same engine, and Task-27 gets its first
real rulebook, used the way an officer would use it.

## Acceptance
- [ ] `uv run python scripts/gate.py` exits 0, and `git status` shows no change after it runs.
- [ ] Every evaluation number in `runs/eval/summary.json` is unchanged; A-0142's replay is unchanged.
- [ ] The home screen lists exactly A-0142 and W-01 with no uploads present.
- [ ] W-01 opens offline with no key from the replay cache, and validates like A-0142.
- [ ] The report gives the coverage of the 10 clause_ids with n, the failed sentence checks, and
  W-01's flags for T1 and T3.
- [ ] No rule PDF is committed (`git ls-files data/policies` holds only lock files).
- [ ] Screenshots of W-01's case page with its intake note at 1280 and 1440 in
  `reports/screens/2026-10-05-wave13/`.
- [ ] (eye) Tarık opens W-01: the intake note says what the file is in under ten seconds and hints
  at no outcome.

## Out of scope
- Changing the answer key or the 24 documents.
- Any code change: a gap found here is reported, and fixed in its own task.
