# Task-02: Held-out case H-01, written blind
> **Execution:** agent `codex` · effort `high`
> *Why:* it answers "you planted the traps your own system finds" (pre-Blueprint review #10). The
> author sees no other case, no pipeline and no gold.

**Lane**
- OWNS: `data/heldout/H-01/**`
- MUST NOT TOUCH: everything else. In particular, do not open or read `data/cases/**`, `runs/**`,
  `readmark/**` or `notes.md`.
- GATE: `python scripts/validate_cases.py data/heldout/H-01` (from repo root)
- DEPENDS ON: Task-01 (its `scripts/validate_cases.py`)

## Goal
One urban priority-housing applicant file, 15–20 pages, in the `docs/contracts.md` format, with its
own `facts.csv` and `gold.json`.
- **Sources:** `docs/contracts.md` and the five policies (`data/policies/*.pdf` or the r.jina.ai
  fallback). Nothing else in the repo.
- **The author chooses** the applicant, the urgent-need category, the decisive facts, and 2–4 traps
  of any contract trap types, placed anywhere.
- **The right outcome follows from the real policy text,** cited verbatim in each rationale.
- **Write the facts table first,** then the documents, then the gold.
- **A sealed copy:** `data/heldout/H-01/SEALED.md` names the traps and where they are, with the
  first line "Do not open before the pipeline has run on H-01".

## Why
Wave 2 runs the pipeline on H-01 and reports its catch rate next to the other files. A file whose
traps nobody on the Claude side chose is the honest number.

## Acceptance
- [ ] `python scripts/validate_cases.py data/heldout/H-01` exits 0.
- [ ] Every rationale in `gold.json` quotes a policy sentence verbatim.
- [ ] Every person and organisation is invented.

## Out of scope
- Any other file, any pipeline run, and any mutation set.

Fixed: the formats and clause ids in `docs/contracts.md`; the case id H-01.
