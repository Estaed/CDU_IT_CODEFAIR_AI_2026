# otopilot report, 2026-10-03: wave 1 (Task-00..03)

Plan: [otopilot-2026-10-03-plan.md](otopilot-2026-10-03-plan.md). BASE_SHA `5ac876e`. Orchestrator
`claude-opus-5-5` (this session). Checkpoint report: rows are appended as each lane is gated.

## Wave 1 (started 10:43 ACST)

| Task | Engine | Outcome | Attempts | Elapsed | Gate (exit) | Main SHA |
|---|---|---|---|---|---|---|
| Task-03 | main loop | green, eye check pending: 1 | 1 | 10:48–10:59 | exists check (0); `shoot.py` no console or page errors (0) | `3fed6dc` |
| Task-00 | ultracode Workflow `wf_d1625a98-101` | running | | from 10:47 | | |
| Task-01 | Codex bee `gpt-6-sol`/`high` | green, eye check pending: 1 | 1 | 10:44–11:04 (20 min) | `python scripts/validate_cases.py` lane (0), main (0) | `b84e938` |

### Task-01 notes
- Bee result `COMPLETE`, `COMMIT: NONE`: the Codex sandbox denied `index.lock` in the worktree's
  git directory (outside its workspace), as the brief anticipated. The orchestrator made the single
  commit in the lane (`95e74bd`, diff inside `OWNS` only) and integrated it with the status edits.
- Validator summary: A-0142 pages n=60, facts n=15; E-01/E-02/E-03 pages n=12 each, facts n=9/11/12,
  each with correct claims n=8 and mutations n=7 (one per type). Errors n=0.
- Gold policy quotes checked against the PDFs (`.tmp/check_gold_quotes.py`, not committed):
  n=32, not verbatim n=0. A-0142 gold matches the scenario exactly.
- `uvx ruff check scripts/validate_cases.py` reports `I001` (import block) under the user-level ruff
  config; ruff's default rules pass. Settled when Task-00's gate lands on main.
- **First look for the eye check (Tarık decides):**
  - Pages are thin: A-0142 is 24 KB for 60 pages, about 400 bytes (two short paragraphs) per page;
    the E-files about 340 bytes per page.
  - About 10 sentences across the four files comment on the evidence instead of being paperwork,
    e.g. p. 8 "It is not a certificate of the balance at the date of the later housing
    application", p. 51 "The letter is signed by the service coordinator in this synthetic file",
    an intake checklist that "does not turn an absent document into a failed eligibility
    criterion", E-02 "No approve or decline decision is pre-entered". They hand the reader the
    traps, which weakens both the "real paperwork" criterion and the evaluation numbers.
  - Because of this, Task-02's brief got one intent paragraph ("What realistic means here": no
    sentence that comments on evidence, explains a trap or addresses the officer or an AI; real
    page density). The task file is unchanged.

## Wave 2 (started 11:07 ACST)

| Task | Engine | Outcome | Attempts | Elapsed | Gate (exit) | Main SHA |
|---|---|---|---|---|---|---|
| Task-02 | Codex bee `gpt-6-sol`/`high` | running | | from 11:07 | | |

Task-02's worktree is cut from `BASE_SHA` (no `data/cases/**` in it), with main's
`scripts/validate_cases.py` copied in untracked, as the plan says.

### Task-03 notes
- Built in the main loop with the `tasarim` skill (Tarik Base, both modes). One check script for both
  directions: `design/shots/shoot.py` drives A and B through the same five states with the same clicks;
  15 screenshots in `design/shots/`.
- Verbatim check (`.tmp/check_ab_quotes.py`, not committed): 18 of 21 quoted strings in
  `design/ab-brief.md` appear verbatim in both A and B; the other 3 are the same in both and are not
  quotes (a stretch of brief prose caught by the regex, the `hh:mm:ss` format template, and the
  summary paragraph that both designs split into sentences).
- Content parity: two additions not in B were removed from A (a "Models" row in the record, a checker
  sentence in the status key).
- Launch note: the recipe's `Start-Job` died with its PowerShell tool call (no persistent session in
  this harness), so the Codex bee was relaunched detached with the same recipe body
  (`readmark-lanes/run-codex-bee.ps1`) at 10:44; first attempt never started, not counted.

## Quota
| When | Claude 5-hour | Claude weekly | Codex 5-hour | Codex weekly |
|---|---|---|---|---|
| 10:41 start | 1% | 79% | 0% | 0% |
| 10:59 | — | 79% | 6% | — |
