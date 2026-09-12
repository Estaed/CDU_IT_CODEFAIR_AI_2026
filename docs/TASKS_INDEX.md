# Fair Turn — task index

Generated 2026-09-12 from `docs/PRD.md` and `CLAUDE.md` Part 2. Status lives here and in
each task file; `verify-task` is the only thing that ticks a box.

**Phases.** This is the whole v1 entry for 30 September 2026. The PRD's deferred decisions
(§11: key custody, Housing Reference Group role, tasking-system integration, merits review)
belong to a pilot that is deferred, not cancelled; the seams that keep it cheap are named
in Part 2 (`data/artefacts.py`, `core/audit.py`, artefact-only extraction). The report
PDF and slide deck are hand-written deliverables outside this list (Task-21 exports their
numbers).

## Tasks

- [x] Task-00: Package layout, constants, theme tokens, wording lint
- [x] Task-01: Geography layer with pseudonymous community ids
- [ ] Task-02: Core types and the ranking formula
- [ ] Task-03: Synthetic labels, personas, closures and climate table
- [ ] Task-04: Capacity simulation and wait metrics
- [ ] Task-05: Feedback-loop simulation
- [ ] Task-06: Explanation templates
- [ ] Task-07: Audit log
- [ ] Task-08: Extraction schema and source-phrase verification
- [ ] Task-09: CLI wrappers for the two subscription models
- [ ] Task-10: Generate the synthetic report texts
- [ ] Task-11: Extract typed fields from every report, plus the adversarial set
- [ ] Task-12: Evaluation: per-field metrics, baseline classifier, eval script
- [ ] Task-13: App shell, artefact loader, session state, offline smoke test
- [ ] Task-14: Triage board: ranked list, equity slider, two rankings, human queue
- [ ] Task-15: Board map and metrics panel with decide-before-reveal
- [ ] Task-16: Job card with source-phrase highlights and per-job override
- [ ] Task-17: Sign-off page and audit log page
- [ ] Task-18: Tenant view
- [ ] Task-19: Feedback-loop simulation page
- [ ] Task-20: README, reproduction steps and submission zip
- [ ] Task-21: Report tables and figures export

## Routing

Summary of each task's Execution and Lane blocks; the task file wins on disagreement.

| Task | Agent | Plan mode | Effort | Depends on |
|---|---|---|---|---|
| 00 | claude | no | medium | none |
| 01 | claude | no | high | 00 |
| 02 | codex | no | high | 00 |
| 03 | claude | yes | high | 01, 02 |
| 04 | codex | no | high | 02 |
| 05 | codex | no | high | 04 |
| 06 | codex | no | high | 02 |
| 07 | codex | no | medium | 02 |
| 08 | codex | no | high | 02 |
| 09 | claude | no | high | 08 |
| 10 | claude | no | high | 03, 09 |
| 11 | claude | no | high | 10 |
| 12 | codex | no | high | 11 |
| 13 | claude | no | high | 07, 11 |
| 14 | codex | no | high | 13 |
| 15 | codex | no | high | 14, 04 |
| 16 | codex | no | high | 14 |
| 17 | codex | no | medium | 15, 16 |
| 18 | codex | no | medium | 17 |
| 19 | codex | no | high | 13, 05 |
| 20 | claude | no | medium | 12, 19 |
| 21 | codex | no | medium | 12, 05 |

**Parallel waves** (from the dependency graph, for `otopilot`): after 00 → {01, 02}; after
02 → {04, 06, 07, 08}; then {03, 05, 09}; 10 → 11 → {12, 13}; after 13 → {14, 19}; 14 →
{15, 16} → 17 → 18; finally {20, 21}. Tasks 09, 10 and 11 spend subscription windows and
run in the main loop, one at a time.
