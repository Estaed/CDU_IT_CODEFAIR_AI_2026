# otopilot report, 2026-10-03: wave 4 (Task-12, Task-13)

Plan: [otopilot-2026-10-03-wave4-plan.md](otopilot-2026-10-03-wave4-plan.md). BASE_SHA `fc55bec`.
Both builders were Codex bees, `gpt-6.1-sol`/`high`, launched 16:36 ACST.

## Outcomes

| Task | Outcome | Attempts | Elapsed | Gate (exit) | Main SHA |
|---|---|---|---|---|---|
| Task-13 | green | 1 | 16:36–16:49 | bee 1 (2 eval tests need `data/heldout`, absent in its sparse lane); orchestrator, with H-01 restored in the lane: lane 0 (76 passed), main 0 (76 passed) | `cdfa35c` |
| Task-12 | green | 1 | 16:36–16:59 | bee 0 (77 passed); orchestrator: lane 0 (77 passed), main 0 (81 passed) | `34f37b2` |

**Orchestrator checks on main:**
- The A-0142 replay is byte-identical with no key and no `claude`.
- H-01's first-run numbers are unchanged under `first_run` in `runs/eval/summary.json`: 4 of 8 gold
  pages in required reading, 8 of 8 flagged or cited.

**Integration notes:**
- Task-13's bee reported BLOCKED only because its lane was cut without `data/heldout/`, while Task-10
  added eval tests that read H-01. H-01 is no longer secret, so the orchestrator restored it in the
  lane before gating.
- The wait-time CSV was being normalised to LF by the repo's `* text=auto` rule, while its README
  says it is stored verbatim. The orchestrator added `data/context/*.csv -text` to `.gitattributes`,
  inside Task-13's commit, so the file is kept byte for byte (CRLF, as downloaded).
- Task-13 and Task-12 each carry their DONE status in their own commit (Task-11's slip was not
  repeated).
- Locked pytest temp folders remain in `readmark-lanes/task-13/.tmp/` (no secrets: the `.env` copy is
  deleted). Logged in `gardener.py`. The Task-12 worktree was removed cleanly.

## What changed

**Task-12, false alarms round 2** (no new model calls):

| Measure | Before | After |
|---|---|---|
| A-0142 summary audit flags | 22 of 95 | 19 of 95 |
| H-01 summary audit flags (after changes, not held-out) | 14 of 105 | 9 of 105 |
| H-01 false alarms among the labelled flags | 9 of 14 | 4 of 9 |
| Mutation set catch rate | 20 of 21 | 20 of 21 |
| False alarms on correct mutation claims | 1 of 24 | 1 of 24 |

- The real errors stay flagged: a36 and a47 (A-0142), a52 (H-01). The 4 file-inconsistency flags on
  H-01 also stay.
- On A-0142, "quote not found" fell from 11 to 4, while "checker disagrees" rose from 11 to 15.
  Fixing the dates exposed Jev's own disagreement on the same claims. Jev's "not enough information"
  on true claims is now the main remaining source of false alarms (Task-14).
- The suggestion rule exempted 1 claim in each summary: A-0142 a92 and H-01 a101.

**Task-13:**
- **Light default.** The screen opens in light mode; a saved dark choice is kept.
- **Wait-time line on the case header.**
  - It shows Darwin/Casuarina, 2–3 bedrooms, general urban housing: 2–4 years.
  - It is labelled as NT open data, December 2020, historical and not priority-specific; the source
    has no priority figure.
  - CC BY was confirmed at the source. The data is served through `/api/context` and never enters a
    check, flag, outcome or record.
- **Record JSON.** `decision_label` and the top-level `required_reading` are gone, and the two hashes
  sit in an `integrity` block.
- **Screen tests.** They now read flagged items, statuses and counts from `view.json`. They passed
  against both the old and the new A-0142 data.

## Next
Task-14: Jev's separate "supports" score as a second signal for "checker disagrees". The threshold
comes from the SummEdits calibration (Task-08), not from our cases.
