# otopilot plan, 2026-10-03: wave 2 (Task-05..08)

Status: **approved by Tarık, 2026-10-03, just before the plan commit `f6fa15f` (12:24 ACST).** Eye reference decided at the same time: the
approved Task-07 screen's screenshots in `design/screens/` (Blueprint → Verification and Decisions
updated in the plan commit).

## Run shape
- **Direction:** orchestrator Claude (this session). All four tasks are `agent ultracode`, so every
  feature runs in the ultracode engine: an Opus builder per feature in a Workflow, then its review
  lens, a fix loop of at most 3 rounds. No Codex bee.
- **Fallback row:** none. Product code is Opus's (chef, 2026-09-27); a Claude wall halts the run.
- **Seats:** plan and orchestration in this session, `claude-opus-5-5`.
- **SOURCE:** `tasks`, Task-05..08. **UNTIL:** `done`.
- **BASE_SHA:** `6864332` (the wave-2 task commit); becomes the plan commit once approved, and
  preflight reruns on it.

## Waves
| Wave | Tasks | Why |
|---|---|---|
| 2a | Task-05, Task-08 in parallel | No dependency between them; `OWNS` disjoint (preflight `owns_disjoint` OK) |
| 2b | Task-06, Task-07 in parallel | Both build on Task-05's schema-2 `view.json` and the A-0142 run; worktrees cut from main after Task-05 is integrated. `OWNS` disjoint |

Task-08 does not block 2b: if it is still running when Task-05 lands, 2b starts anyway.

## Task rows
| Task | Wave | Engine | Model / effort | Review lens | GATE | Timebox | Attempts |
|---|---|---|---|---|---|---|---|
| Task-05 | 2a | ultracode Workflow | builder and fixer `opus`/`xhigh` | spec (`opus`/`high`): logic two later features rely on | `uv run python scripts/gate.py` | 180 min | 1 + 1 |
| Task-08 | 2a | ultracode Workflow | builder `opus`/`high` (task's effort), fixer `opus`/`xhigh` | spec (`opus`/`high`): numbers that go into the report | same | 150 min | 1 + 1 |
| Task-06 | 2b | ultracode Workflow | builder and fixer `opus`/`xhigh` | spec (`opus`/`high`): the riskiest-assumption path | same | 150 min | 1 + 1 |
| Task-07 | 2b | ultracode Workflow | builder and fixer `opus`/`xhigh` | screen (`opus`/`high`), 1280 and 1440 wide | same | 180 min | 1 + 1 |

OWNS, MUST NOT TOUCH and DEPENDS ON exactly as in each task file. Excluded tasks: none.

## Lane setup (orchestrator, before each spawn)
- Worktrees outside the repo: `../readmark-lanes/task-NN`, `git worktree add --detach`.
- **`data/heldout/` is left out of every lane** (sparse checkout), so no builder or reviewer can
  read H-01 while writing prompts or thresholds. Blueprint: no Claude stage sees the held-out file
  before its run.
- Git-ignored inputs **copied** into each lane (never junctioned): the five policy PDFs in
  `data/policies/`, and `.env` (`TYPESAFE_API_KEY`).
- Port lock: the Task-07 builder and its screen lens serve on `localhost:8765` through
  `cihaz_kilidi.py al port-8765 … birak`; tests that start their own server use a free port.
- Live model calls: Task-05 runs A-0142 live once (writer `claude -p --model opus`, Jev);
  Task-06 adds one summary call and its audit calls on top of that cache; Task-08 runs Claude as
  checker over the sample once and Jev twice. After that, `--replay`.

## Seams the briefs name
- Task-05 fixes the schema-2 additions; Task-06 adds `audit` to the same schema after it, and
  Task-07 renders both from that contract (the audit tab from a fixture until Task-06 lands).
- After Task-06 and Task-07 are both on main, the orchestrator serves A-0142 and checks that the
  real audit block renders in the tab. Only if it does not, the integrator runs (`opus`/`xhigh`,
  OWNS = the wave's union, no new behaviour).
- Task-08 owns `readmark/__main__.py` and the `eval` verb; nobody else edits it this wave.
- Integration order: whichever lane is green first goes first; after each pick the GATE runs on main.

## Preflight and baseline
- `onkontrol.py --tasks 05,06,07,08 --orchestrator claude --delegate claude`: OVERALL OK
  (clean tree, Blueprint present, all four eligible, OWNS disjoint, quota GO).
- **Baseline gate at `6864332`:** `uv run python scripts/gate.py` exit 0 (ruff ok, 24 passed,
  replay smoke ok).
- Delegate auth: `claude -p --model sonnet` ping → `is_error: false`, "pong".
- Wake lock: `uyanik_tut.py`, PID 32032, no `--until` (UNTIL done); released at closeout.
- Preflight rerun on the plan commit `f6fa15f`: OVERALL OK. Final `BASE_SHA` for wave 2a:
  `f6fa15f325fc4f2c61466c2ad23bad17d3b794c0`.

## Quota (measured 12:19 ACST with `limit.py`)
| Pool | 5-hour | Weekly | Weekly resets |
|---|---|---|---|
| Claude (max) | 25% (resets 15:40) | **82%** | 2026-10-04 21:30 ACST |
| Codex (plus) | 0% | 5% | not used |

**Estimate (Claude weekly points):** wave 1's Task-00 Workflow moved the weekly window about 1
point and the whole run 2. Four features of similar size, plus Claude-as-checker over 300+
pairs: about 4–8 points, so 86–90% at the end. The 5-hour window may wall during wave 2b (Task-00
alone took it 1% → 12%); that is waited out at the 15:40 reset.

**Risk, stated up front:** the quota hook stops spawns and sub-agent tool calls at 92% weekly. If
the run reaches it, new Claude work stops, what exists is gated, and Tarık decides: wait for the
weekly reset (2026-10-04 21:30) or spend the banked reset. Order puts the two tasks the screen and
the evaluation need first (Task-05), so a cut lands on the later ones.

## Honest note before the run
Planning this wave, the orchestrator printed `data/heldout/H-01/SEALED.md` (the answer key) while
listing the data folder, by mistake. No pipeline stage, prompt or task file used it, and the four
task files name nothing from it. From here the orchestrator writes no prompt, threshold or test
that touches H-01, and every lane is cut without `data/heldout/`. The held-out run in wave 3 should
be read with this note beside it.

## Approval
Tarık approves this file; then the orchestrator commits it, reruns preflight, records the final
`BASE_SHA`, starts the wake lock and wave 2a.

## Addition requested by Tarık, 2026-10-03 14:20 ACST: Task-09 (wave 2c)
After the 2b report, Tarık asked for the false-alarm fixes on Codex `gpt-6.1-sol`, to spare the
Claude pool ("bunlari 6.1 sol a yaptir claude kotasini bitirmeyelim"). Task-09 fixes the date
check, the pair rule and possibly-missed duplicates. Codex bee `gpt-6.1-sol`/`high`, timebox 90
min, network on (new Jev calls), no Claude call. It is cut from main after Task-07 lands, because
it changes A-0142 values that the screen tests read. GATE `uv run python scripts/gate.py`.
