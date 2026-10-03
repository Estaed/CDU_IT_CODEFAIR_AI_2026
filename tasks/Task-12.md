# Task-12: False alarms, round 2: values in the passage, date ranges, suggestions; H-01 after changes
> **Execution:** agent `codex` · effort `high`
> *Why:* after labelling H-01's summary audit, 9 of its 14 flags were false alarms, and 5 of the 9
> had the value in the cited passage or the document header rather than in the short quote. Tarık
> approved the Blueprint change and asked for the fix before the numbers freeze (2026-10-03).
> Codex `gpt-6.1-sol` at his request.

**Lane**
- OWNS: `readmark/checks/**`, `readmark/audit/claims.py`, `readmark/eval/**`, `readmark/pipeline.py`, `tests/test_checks_and_gate.py`, `tests/test_audit.py`, `tests/test_eval_cases.py`, `tests/test_cross.py`, `tests/test_pipeline.py`, `runs/**`
- MUST NOT TOUCH: `web/**`, `readmark/serve.py`, `readmark/record/**`, `tests/test_screen.py`, `data/context/**` (Task-13); `readmark/jev/**`, `readmark/writer/**`, `readmark/audit/claude.py`, `readmark/audit/__init__.py`, `readmark/schemas/**`, `readmark/ingest/**`; `data/**`, `design/**`, `docs/contracts.md`, `AGENTS.md`, `notes.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: none

## Goal
- **Values beyond the quote.** The numbers-and-dates check passes a value that appears in a cited
  quote, in that quote's whole passage, or in the passage's document header (its title and date).
  Blueprint → Layout states this rule, changed on 2026-10-03. A value found nowhere in those still
  fails.
- **Date ranges.** "21–27 February 2026" matches "21 February to 27 February 2026" and the ISO
  forms. A wrong range still fails.
- **Suggestions are not facts.** A summary claim that only suggests or hedges is shown as "nothing
  to check" and is not flagged. Example: "the answer … may also need checking". A factual claim
  that merely contains such a word is still checked. Report every claim the rule exempts, with n.
- **H-01 after changes.**
  - H-01's first-run numbers stay frozen, exactly as committed, and stay reported as the held-out
    result.
  - Numbers computed on H-01 after this task are labelled "after changes, not held-out", side by
    side with the first-run numbers.
  - The held-out guard in `readmark/eval/discipline.py` records the change instead of refusing to
    score.
- **Re-measure everything from the cache.**
  - Cases: A-0142, E-01..E-03, H-01.
  - Parts: mutations, cases, ablation, audit labels.
  - No Claude call; new Jev calls only if a check needs them, counted.
  - `summary.json` carries before and after for each headline number, each with n.

## Why
A summary audit that is mostly false alarms teaches the officer to ignore flags. This fixes the
causes the labels showed, without touching the checker or the writer.

## Acceptance
- [ ] `uv run python scripts/gate.py` exits 0.
- [ ] Tests:
  - a date only in the document header passes;
  - an amount only elsewhere in the cited passage passes;
  - a value found nowhere still fails;
  - "21–27 February 2026" matches its long form;
  - a suggestion claim is exempted;
  - a factual claim containing "should" is still checked.
- [ ] Every rebuilt run replays twice with `TYPESAFE_API_KEY` unset and `claude` off PATH and gives
  byte-identical output.
- [ ] The mutation set's catch rate is reported before and after (it was 20 of 21). Any drop is named,
  claim by claim.
- [ ] For H-01, per label class (real summary error, file inconsistency, false alarm), how many
  flags remain after the change, with n. a52, the real error, must stay flagged; if it does not,
  say why.
- [ ] For A-0142, the audit's flags before and after, by status, with n. Its two real errors (a36,
  a47) must stay flagged; if one does not, say why.
- [ ] `runs/eval/summary.json` shows H-01's first-run numbers unchanged beside the "after changes"
  numbers.

## Out of scope
- The checker (Jev), the writer and its prompts, the screen.
- A new held-out file: another time.

Fixed: the parts seam (`runs/eval/<part>.json`, `summary.json` assembled from all); the stage file
names; the CLI verbs and flags. Screen tests in `tests/test_screen.py` belong to Task-13. If your
data change breaks one, report it rather than editing it.
