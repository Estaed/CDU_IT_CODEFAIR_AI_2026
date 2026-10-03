# Task-04: Rewrite the Task-01 case files as real paperwork, and make the validator catch it
**Status: DONE** — verified 2026-10-03, eye check pending: 1
> **Execution:** agent `codex` · effort `high`
> *Why:* Task-01's files are thin (A-0142 averages 60 words a page, the E-files about 50) and about
> ten sentences comment on the evidence instead of being paperwork, so they hand the reader the
> traps. Tarık asked for the fix on 2026-10-03. The same family writes it (Blueprint: Codex writes
> the case files).

**Lane**
- OWNS: `data/cases/A-0142/**`, `data/cases/E-01/**`, `data/cases/E-02/**`, `data/cases/E-03/**`, `data/benchmark/DATASHEET.md`, `scripts/validate_cases.py`
- MUST NOT TOUCH: `data/cases/stub/**`, `readmark/**`, `web/**`, `tests/**`, `pyproject.toml` (Task-00); `data/heldout/**`; `design/**`; `docs/contracts.md`, `AGENTS.md`, `notes.md`
- GATE: `python scripts/validate_cases.py` (from repo root; stdlib only)
- DEPENDS ON: Task-01

## Goal
**Rewrite A-0142, E-01, E-02 and E-03** so every page reads as the real document it holds, written
by its author for their own purpose (a ledger, a form, a letter, a record, a declaration).
- **No sentence comments on the evidence**, explains a trap, addresses an assessing officer or an
  AI, or says the file is synthetic. Known examples to remove: A-0142 p. 8 "It is not a certificate
  of the balance at the date of the later housing application"; p. 51 "The letter is signed by the
  service coordinator in this synthetic file"; an intake checklist that "does not turn an absent
  document into a failed eligibility criterion"; E-02 "No approve or decline decision is
  pre-entered". Such notes belong only in `facts.csv` and `gold.json`.
- **Real page density:** give each page the content its document would have (letterheads, reference
  numbers, dates, signature blocks, form fields, ledger lines). Targets: mean at least 180 words a
  page in every file, no page under 80 words.
- **Keep what other work depends on:** the page count and page numbers, each document on its pages,
  the scenario (`notes.md` → The scenario) and every decisive passage. In A-0142 the passages on
  pp. 8, 23, 30 and 51 that `design/ab-brief.md` quotes stay word for word (the screen shows them). Every `facts.csv` quote
  stays a verbatim substring of its page; `gold.json` outcomes, decision and required reading stay
  as they are, and rationales keep citing pages that still hold the evidence. Mutation sets stay
  valid. Update `DATASHEET.md` where its numbers or text change.

**`scripts/validate_cases.py`** gets two checks for `A-0142` and `E-*` only (other case directories,
such as `stub` and `H-01`, keep today's checks):
- words per page: mean at least 180, minimum 80, printed in the per-case summary;
- meta commentary: a case-insensitive pattern list that fails on lines in `case.md` such as
  `synthetic`, `fictional`, `trap`, `Readmark`, `\bAI\b`, `assessing officer`, `the officer should`,
  `pre-entered`, `pre-filled`, `not a certificate`, naming file and line.

## Why
The demo and the mutation evaluation read these files. A file that explains its traps makes the
catch rate meaningless and fails the eye check "reads like real NT housing paperwork, not like a
test". A validator rule closes the class instead of this one instance.

## Acceptance
- [x] `python scripts/validate_cases.py` exits 0 and prints, per case, words per page (mean, min)
  next to the existing counts.
- [x] A test of the new checks: a temporary copy of a case with one page cut to 20 words, and one
  with the line "This synthetic file is for testing.", each makes the validator exit 1 naming the
  file (run by hand, reported in the notes; the copies are not committed).
- [x] A-0142 pp. 8, 23, 30 and 51 still contain the `design/ab-brief.md` passages verbatim, and
  `gold.json` is unchanged in outcomes, decision and required reading for all four files.
- [ ] (eye) Tarık skims pages 8, 23, 30, 51 and three random filler pages of A-0142. They read like
  real NT housing paperwork, not like a test.

## Out of scope
- `H-01` (held-out, written blind), the stub case, any pipeline code.
- New cases, new trap types, a release CSV.

Fixed: the formats and clause ids in `docs/contracts.md`; the case ids; page numbers of the decisive
passages.
