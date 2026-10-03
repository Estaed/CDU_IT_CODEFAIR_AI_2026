# Task-09: Cut the checks' false alarms: dates, the pair rule, possibly-missed duplicates
**Status: DONE** — verified 2026-10-03
> **Execution:** agent `codex` · effort `high`
> *Why:* on A-0142's summary under audit, 26 of 28 flags were false (Task-06, n=95 claims), mostly
> from a date check that misses "15 Mar" against "2026-03-15" and a pair rule that flags true
> claims. Possibly-missed lists run to 28 passages. Tarık asked for the fix on 2026-10-03, on Codex
> (`gpt-6.1-sol`) to spare the Claude pool. The evaluation numbers freeze on 7 Oct.

**Lane**
- OWNS: `readmark/checks/**`, `readmark/jev/**`, `readmark/gate/**`, `readmark/pipeline.py`, `readmark/audit/claims.py`, `tests/test_checks_and_gate.py`, `tests/test_cross.py`, `tests/test_pipeline.py`, `tests/test_audit.py`, `runs/stub/**`, `runs/A-0142/**`
- MUST NOT TOUCH: `web/**`, `readmark/serve.py`, `readmark/record/**` (Task-07); `readmark/eval/**`, `readmark/__main__.py`, `runs/eval/**` (Task-08); `readmark/audit/claude.py`, `readmark/audit/__init__.py`, `readmark/writer/**`, `readmark/schemas/**`; `data/**`, `design/**`, `docs/contracts.md`, `AGENTS.md`, `notes.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: Task-07

## Goal
Three causes of false flags are fixed in the checks, and the A-0142 run is rebuilt with **no Claude
call**: the writer, the summary and the audit's split, locate and coverage calls all replay from
the cache. New Jev calls are allowed.

- **Dates and references.** The numbers-and-dates check matches the same date in its common
  written forms: "15 Mar", "15 March 2026" and "2026-03-15"; "January 2026" against "2026-01-…".
  A reference written with or without its hyphen counts as the same ("A-0142" and "A0142"). A
  value that really is absent from every cited quote still fails.
- **The pair rule.** A claim citing one side of a contradicting pair is "contradicted" only when
  the other passage contradicts the claim itself (a Jev check of the claim against that passage).
  A true claim, such as "the March ledger shows the debt cleared", is no longer flagged. The pair
  still shows under its clause, and both passages stay in required reading.
- **Possibly-missed duplicates.** Passages that restate the same fact count once ("deduplicated
  by fact", `notes.md` → v1 scope). Each clause shows its strongest distinct passages, and only
  those compete for required reading.
- The rules are general. None names a case, page or passage. They were chosen after seeing
  A-0142's audit, so the held-out file in the evaluation wave is their honest test; say so in the
  remarks next to each rule.

## Why
The riskiest assumption is measured on precision as well as catches. A tab where 26 of 28 flags are
wrong teaches the officer to ignore flags, which is the over-trust the brief warns about.

## Acceptance
- [x] `uv run python scripts/gate.py` exits 0.
- [x] `run --case A-0142` rebuilds with `claude` off PATH (no Claude call), and `run --case A-0142
  --replay` twice gives byte-identical `view.json` with `TYPESAFE_API_KEY` unset.
- [x] Tests: "15 Mar" and "15 March 2026" match a quote holding "2026-03-15"; "A0142" matches
  "A-0142"; a date that is absent still fails.
- [x] A test: a claim citing one side of a pair, which the other passage does not contradict, is
  not `contradicted`; one that the other passage does contradict is.
- [x] A test: two possibly-missed passages that restate one fact count once.
- [x] On A-0142, the builder's report gives the audit's flag counts before and after, by status,
  with n. The two real errors Task-06 found (the "verified" eligibility heading against p48:1 and
  p58:1, and the support-worker contact sentence against p46:1) are still flagged. The p.8/p.23
  pair is still under Debts, and both passages are still required. Required reading stays at 8 or
  fewer. Possibly-missed counts per clause, before and after, with n.
- [x] `tests/test_screen.py` still passes. An assertion there that pins an A-0142 value this task
  changes may be updated, and only that one; each such line is listed in the report.

## Out of scope
- The audit's coverage call ("left out of the summary") and the sentence splitter: both are
  Claude calls.
- The screen, the evaluation wave, new clause rules.
- Opening anything under `data/heldout/`: it stays sealed until the evaluation wave.
