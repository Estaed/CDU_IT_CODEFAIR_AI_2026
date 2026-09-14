# Fair Turn — task index

Generated 2026-09-12 from `docs/PRD.md` and `CLAUDE.md` Part 2; Phase 2 tasks appended
2026-09-14 from the amended PRD and Part 2. Status lives here and in each task file;
`verify-task` is the only thing that ticks a box.

## Phases

| Phase | Tasks | State | Owns it |
|---|---|---|---|
| **Phase 1** — six screens from committed artefacts, offline | 00–21 | DONE 2026-09-13 | PRD at `2d8c349` |
| **Phase 2** — one coordinator workspace, live intake, cited policy passages, visit plan, network allowed | 22–36 | in progress | `docs/PRD.md` (amended 2026-09-14), `design/phase-2-wireframes.md`, Part 2 |
| **Pilot** — key custody, Housing Reference Group role, tasking-system integration, merits review, hosted deployment | none | deferred, not cancelled | PRD §11 |

The pilot's seams are already in Part 2: `data/artefacts.py` plus `data/runtime.py` (intake
would replace the runtime file), `core/audit.py` (the agency system would replace the JSONL),
`llm/intake.py` (the provider setting), `data/policy.py` (a live index behind the same
lookup). Phase 2's last task, Task-36, is the only one that pulls or calls an Ollama chat
model (Tarik, 2026-09-14): everything before it runs on Claude. The report PDF and slide
deck stay hand-written deliverables outside this list.

## Tasks

- [x] Task-00: Package layout, constants, theme tokens, wording lint
- [x] Task-01: Geography layer with pseudonymous community ids
- [x] Task-02: Core types and the ranking formula
- [x] Task-03: Synthetic labels, personas, closures and climate table
- [x] Task-04: Capacity simulation and wait metrics
- [x] Task-05: Feedback-loop simulation
- [x] Task-06: Explanation templates
- [x] Task-07: Audit log
- [x] Task-08: Extraction schema and source-phrase verification
- [x] Task-09: CLI wrappers for the two subscription models
- [x] Task-10: Generate the synthetic report texts
- [x] Task-11: Extract typed fields from every report, plus the adversarial set
- [x] Task-12: Evaluation: per-field metrics, baseline classifier, eval script
- [x] Task-13: App shell, artefact loader, session state, offline smoke test
- [x] Task-14: Triage board: ranked list, equity slider, two rankings, human queue
- [x] Task-15: Board map and metrics panel with decide-before-reveal
- [x] Task-16: Job card with source-phrase highlights and per-job override
- [x] Task-17: Sign-off page and audit log page
- [x] Task-18: Tenant view
- [x] Task-19: Feedback-loop simulation page
- [x] Task-20: README, reproduction steps and submission zip
- [x] Task-21: Report tables and figures export

Phase 2:

- [x] Task-22: Workspace interaction spike: pydeck map, selectable list, shared selection
- [x] Task-23: Phase 2 shell: five surfaces, layer rule, runtime store, human-set fields reach the ranking
- [x] Task-24: Audit log, Phase 2: two clocks, batch versions, new record kinds
- [x] Task-25: Core: sign-off batch freeze and the two-stage effect sentence
- [x] Task-26: Core: visit plan in signed order with distance suggestions
- [x] Task-27: Policy index: FS17 passages as a build artefact keyed by typed fields
- [x] Task-28: Intake: provider seam and the in-page new-report action
- [x] Task-29: Workspace page: today's list, backlog, map, weighting, selected-job pane, overrides
- [x] Task-30: Sign-off form, decision states, metrics reveal; retire the Phase 1 board, job card and sign-off pages
- [x] Task-31: Review queue page
- [x] Task-32: Visit plan page
- [x] Task-33: Tenant answer: question-headed blocks, signed rank versus visit order, per-state copy
- [x] Task-34: Evidence lab: extraction quality, feedback loop, audit log with two clocks; retire the Phase 1 feedback and audit pages
- [x] Task-35: Integration: five-surface smoke, offline proof, README, submission package, docstring citations
- [x] Task-36: Ollama extractor benchmark (last step): qwen3:8b against the build extractor, default decided by the table

Presentation wave (added 2026-09-14 from `reports/research-ui-*-2026-09-14.md`, Tarik's approval):

- [x] Task-37: Map markers in pixels, direct single-job pick, compact multi-job chooser
- [x] Task-38: Workspace table shows the whole row; a job is always selected; filters as pills
- [x] Task-39: Empty and refusal states that show what they refuse; review queue and tenant framing
- [x] Task-40: Government chrome through theme keys, the one stylesheet seam, page intros
- [x] Task-41: Workspace KPI row, effect sentence in the main column, outcome tiles after signature
- [x] Task-42: Selected-job pane as a summary list with badges
- [x] Task-44: Evidence lab headline tiles and expanders

Presentation wave 2 (added 2026-09-14 evening, Tarik's requests):

- [ ] Task-45: Today's list as readable job rows with one-click open
- [ ] Task-46: Visual identity: logo, page icons, dark sidebar, tinted tiles
- [ ] Task-47: Review queue with less typing: reason chips, remembered name, drafted clarification
- [ ] Task-48: Provider switch and example reports for intake, from the UI
- [x] Task-49: Map markers show their job count
- [ ] Task-50: User guide in English and an in-app "How to use" popover

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
| 08 | claude | no | high | 02 |
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
| 22 | codex | no | high | none |
| 23 | codex | no | medium | none |
| 24 | codex | no | high | none |
| 25 | codex | no | high | 24 |
| 26 | codex | no | high | 25 |
| 27 | codex | no | high | none (real build run: main loop, needs Ollama `bge-m3`) |
| 28 | codex | no | high | 23, 24 |
| 29 | codex | no | high | 22, 23, 25, 27, 28 |
| 30 | codex | no | high | 29 |
| 31 | codex | no | medium | 23, 24, 28 |
| 32 | codex | no | medium | 26, 30 |
| 33 | codex | no | high | 26, 30 |
| 34 | codex | no | medium | 24, 30 |
| 35 | codex | no | medium | 31, 32, 33, 34 |
| 36 | codex | no | high | 28, 35 (real benchmark run: main loop, pulls `qwen3:8b`) |
| 37 | codex | no | high | none |
| 38 | codex | no | high | 40 |
| 39 | codex | no | medium | 40 |
| 40 | codex | no | medium | none |
| 41 | codex | no | high | 38, 40 |
| 42 | codex | no | high | 37, 40 |
| 44 | codex | no | medium | 40 |
| 45 | claude | no | high | 38, 41, 42 |
| 46 | claude | no | high | 40 |
| 47 | claude | no | high | 39 |
| 48 | claude | no | medium | none |
| 49 | claude | no | medium | 37 |
| 50 | claude | no | medium | 40 |

**Parallel waves** (from the dependency graph, for `otopilot`): after 00 → {01, 02}; after
02 → {04, 06, 07, 08}; then {03, 05, 09}; 10 → 11 → {12, 13}; after 13 → {14, 19}; 14 →
{15, 16} → 17 → 18; finally {20, 21}. Tasks 09, 10 and 11 spend subscription windows and
run in the main loop, one at a time.

**Phase 2 parallel waves** (from the DEPENDS ON lines): wave A {22, 23, 24, 27}; wave B
{25, 28, 31 after 23+24+28}; wave C {26, 29}; then 30; wave D {32, 33, 34}; then 35; then
36 alone. **Presentation wave (2026-09-14):** {37, 40} first, then {38, 39} after 40 is integrated. Second wave {41, 42, 44} after 38 is integrated (43 was not needed: the tenant page already carries the counterfactual rank and the FS17 window). `agent codex` means a bee; which pool the bee runs in (Codex or a Claude
sub-agent) is the chef's call at spawn time from the live limits, never the main loop
typing the code. Tasks 27 and 36 have a real run the main loop performs on Tarik's
machine after the bee's gate is green.
