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

## Progress (2026-10-04)
- **Part 1 done.** List `rules-4ffb667293fe4ebaa5a50aa7d7e34c7b` (10 questions approved, 10 of 10
  sentences found; the uploaded rule PDFs match `data/policies/nt-wwcc/policies.lock.json` by
  SHA-256). Upload `U-0f471da80da6452597aaf0f295bde79a` ran before Task-30/31.
- **Order (Tarık: "30→31→W-01 tek koşu"):** passage ids carry the case id and W-01 had no
  `case.json` loader, so the upload cannot be renamed. Task-31 §4 adds the loader; after Task-30
  and Task-31, build `data/cases/W-01/case.json` (files pointing at the existing PDFs, id W-01),
  run W-01 once live, then move list and run, measure, remove the `U-*` copies.
- **Pre-30/31 measurement of the upload** (redo on the final run):
  - 10 of 10 answer-key clause_ids map to a question (main-loop mapping; q04 bundles
    nature-gravity, relevance-to-work, victim-age and time-elapsed);
  - required 8 (cap 8), suggested 289;
  - T3 flagged: claim c57 ("five-year address history leaves out the Katherine tenancy"),
    02-p2 and 22-p1 required (checker disagrees);
  - T1 half: Claude claims c21 (police, 10-p1) and c22 (statement contradicts police, 03-p4) with
    verified quotes, but Jev's pair scan did not flag 03-p4 against 10-p1 and 03-p4 is not required.
- **Gap to report (no code change here):** "Quote not found" also covers a claim value missing
  from a found quote (c20 "March 2021", c47 "over 18"); 3 of the 8 required passages carry it.

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
