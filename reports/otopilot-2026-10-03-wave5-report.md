# otopilot report, 2026-10-03: wave 5 (Task-14)

No separate plan file: wave 5 is the single task the wave 4 report named as next, launched by the
orchestrating session before its handoff (`reports/2026-10-03-handoff.md`). BASE_SHA `94afc28`.
The builder was a Codex bee, `gpt-6.1-sol`/`high`, launched 17:05 ACST with a 90-minute timebox.
Integration was done by a fresh orchestrator session after the handoff.

## Outcomes

| Task | Outcome | Attempts | Elapsed | Gate (exit) | Main SHA |
|---|---|---|---|---|---|
| Task-14 | green | 1 | 17:05–17:20 (bee), integrated 17:30 | bee 0 (85 passed); orchestrator: lane 0 (85 passed), main 0 (85 passed) | `d3247ff` |

**Orchestrator checks on main:**
- The A-0142 replay is byte-identical with no key and no `claude` (`.tmp/check_task05.py`).
- H-01's first-run numbers are unchanged: every `first_run` block in `runs/eval/summary.json` hashes
  the same as before the pick; Task-14 only adds identical copies under `jev_supports`.
- The audit and mutation numbers below were recounted from the committed stage files
  (`.tmp/check_task14.py`), not taken from the bee's report. The E-file `mutations.json` files are
  byte-unchanged.
- The six removed A-0142 flags were read against their quotes: all six are true claims.

**Integration notes:**
- The bee could not write the lane's git index (sandbox), so the orchestrator committed its
  `OWNS` changes in the lane. Every touched path is inside `OWNS`.
- The bee wrote its report to `runs/eval/task14-report.md`. It was left out of the commit (reports
  do not belong in the replay cache); its numbers are in this report.
- The bee set `PYTEST_ADDOPTS` itself, which dropped the launcher's `-p no:cacheprovider`, so a
  locked `.pytest_cache` is left in `readmark-lanes/task-14/`. No secrets remain there (the `.env`
  copy is gone). Logged in `gardener.py`.
- Main had moved to `2f930b3` (the parallel UI reference session) before the pick; no overlap.

## What changed

**The rule.** Jev backs a claim when its verdict is "supports", or when its verdict is "not enough
information" and its separate "supports" score is at least **0.10**. A "contradicts" verdict is
never rescued by the score. Code checks, contradiction pairs, the scan and required reading keep
their rules.

**Chosen on SummEdits only** (n=300; 150 consistent, 150 inconsistent):

| Rule | Balanced accuracy | n |
|---|---|---|
| Verdict alone | 0.8267 | 300 |
| Verdict or supports ≥ 0.10 | 0.8300 | 300 |

- Only 1 of 300 SummEdits verdicts is "not enough information" (s234, consistent, score 0.10), so
  the threshold rests on a single example. Every threshold from 0 to 0.10 ties; the highest was
  taken. This is calibration on the selection sample, not independent validation.

**Before and after** (H-01 numbers are after changes, not held-out):

| Measure | Before | After |
|---|---|---|
| A-0142 summary audit flags | 19 of 95 | 13 of 95 |
| A-0142 "checker disagrees" | 15 of 95 | 9 of 95 |
| H-01 summary audit flags | 9 of 105 | 9 of 105 |
| H-01 labelled flags: real error / file inconsistency / false alarm | 1 / 4 / 4 of 9 | 1 / 4 / 4 of 9 |
| Mutation set catch rate | 20 of 21 | 20 of 21 |
| False alarms on correct mutation claims | 1 of 24 | 1 of 24 |
| A-0142 gold pages in required reading | 3 of 5 | 4 of 5 (gains p58) |
| H-01 gold pages in required reading | 4 of 8 | 4 of 8 |
| E-01 / E-02 / E-03 gold pages in required reading | 2 of 4 / 3 of 4 / 3 of 5 | unchanged |

- **Removed flags (A-0142):** a24, a60, a73, a81, a87, a94. All six had "not enough information"
  with scores 0.13–0.23, and all six are true claims by their quotes.
- **Real errors kept:** a36 (contradicts, score 0.21), a47 (contradicts, 0.03), a52 on H-01
  (contradicts, 0.26). a36 and a52 sit above the threshold; they stay flagged only because
  "contradicts" is never rescued.
- **Catches lost:** none. Every mutation status is unchanged.
- **H-01:** no change. Its three "checker disagrees" are not rescued by this rule.
- The ablation's required-reading counts moved by one in two layers; the gate algorithm is the same,
  but the new statuses change which leads compete for the eight slots.

## Next
Per the handoff: freeze the numbers by 7 Oct (a one-page numbers sheet with n), the After v1
demo items in Tarık's order, then the interface rework from the chosen UI reference.

Run closed: tasks consumed
