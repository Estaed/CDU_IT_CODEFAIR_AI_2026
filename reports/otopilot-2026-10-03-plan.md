# otopilot plan, 2026-10-03: wave 1 (Task-00..03)

Status: **approved by Tarık, 2026-10-03 10:40 ACST** (clears the Task-00 marker).

## Run shape
- **Direction:** orchestrator Claude (this session). Engines by each task's `Execution` line:
  Task-00 → ultracode Workflow (Claude agents); Task-01, Task-02 → Codex bees (`codex exec`,
  `codex-swarm` Part 3 recipe); Task-03 → contract-first lane built by the orchestrator in the main
  loop (design is eye work). Mixed engines, so preflight checked both pools.
- **Fallback row:** none. Claude is the tight pool, so it cannot absorb a Codex lane, and a Claude
  wall cannot move Task-00 to Codex (product code is Opus's, chef 2026-09-27).
- **Seats:** plan and orchestration in this session, `claude-opus-5-5`.
- **SOURCE:** `tasks`, Task-00..03. **UNTIL:** `done`.
- **BASE_SHA:** `5ac876ef783ddee8ae4fe665aeba8365b889bf89` (the plan commit; preflight rerun green on it, 10:41). Quota at start: Claude weekly 79%, 5-hour 1%; Codex weekly 0%, 5-hour 0%.

## Waves
| Wave | Tasks | Why |
|---|---|---|
| 1 | Task-00, Task-01, Task-03 in parallel | No dependencies between them; `OWNS` disjoint (preflight `owns_disjoint` OK) |
| 2 | Task-02 | Depends on Task-01's `scripts/validate_cases.py`; starts once Task-01 is green on main |

## Task rows
| Task | Wave | Engine | Model / effort | OWNS | GATE | Timebox | Attempts |
|---|---|---|---|---|---|---|---|
| Task-00 | 1 | ultracode Workflow: builder, then spec + screen lenses, fix loop ≤ 3 rounds | builder and fixer `opus`/`xhigh`; lenses `opus`/`high` (`yardimci-denetim`) | as in task file | `uv run python scripts/gate.py` | 180 min build | 1 + 1 |
| Task-01 | 1 | Codex bee | `gpt-6-sol`/`high` (gate lane: its validator gates Task-02; verbatim quotes and exact gold) | as in task file | `python scripts/validate_cases.py` | 150 min | 1 + 1 |
| Task-02 | 2 | Codex bee | `gpt-6-sol`/`high` (outcome must follow the real policy text, blind) | `data/heldout/H-01/**` | `python scripts/validate_cases.py data/heldout/H-01` | 90 min | 1 + 1 |
| Task-03 | 1 | main loop (contract-first lane) | this session | `design/direction-A.html`, `design/ab.html`, `design/shots/**` | exists check in task file | — | — |

Excluded tasks: none.

## Repairs made at plan time (committed with this plan once approved)
1. **Task-00 stop marker.** Preflight failed on the literal ⛔ in Task-00's last line ("If they are
   missing, stop with ⛔ rather than invent policy text"). It is a conditional instruction, not an
   open question, and the condition does not hold: all five PDFs are in `data/policies/`. The line
   becomes "stop and report BLOCKED rather than invent policy text". **Approving this plan clears
   the marker.**
2. **Task-03 contract.** Preflight requires a `## Contract (main loop, <date>)` section for a task
   routed to the orchestrator. Written into `tasks/Task-03.md`; no open decision in it.

## Lane setup (orchestrator, before each spawn)
- Worktrees outside the repo: `../readmark-lanes/task-NN`, `git worktree add --detach`.
- The five policy PDFs are git-ignored, so they are **copied** (not junctioned) into each lane's
  `data/policies/`. A junction would let Task-00's `policies.lock.json` land in main's tree.
- Task-00 also gets copies of `.env` (Jev key) and `.tmp/jev_smoke.py` (both git-ignored).
- **Task-02 is cut from `BASE_SHA`, not from main after wave 1**, so its worktree holds no
  `data/cases/**`, `readmark/**` or `runs/**` at all (the task requires the author sees no other
  case). Main's `scripts/validate_cases.py` is copied in untracked so its GATE runs. Its commit
  touches only `data/heldout/H-01/**`, so it cherry-picks cleanly onto main.
- Port lock: Task-00's builder and screen lens serve on `localhost:8765`, held through
  `cihaz_kilidi.py al port-8765 … birak`. Task-03 screenshots use `file://`, no port.

## Seams the briefs name (integration risks between lanes)
- Task-01's validator checks every case under `data/cases/`, so it will also see Task-00's
  `data/cases/stub/` on main. Brief to Task-01: page-count rules only for A-0142 and `E-*`,
  `mutations.jsonl` required only for `E-*`. Brief to Task-00: the stub follows the contract
  exactly (it will be validated).
- Task-00's `ruff check` will lint Task-01's `scripts/validate_cases.py` on main. Brief to Task-00:
  keep ruff's default rule set (any extra rules scoped to its own paths). Brief to Task-01:
  pyflakes-clean stdlib code.
- Integration order: whichever lane is green first goes first; after the second pick, both GATEs
  run on main.

## Preflight and baseline
- `onkontrol.py --tasks 00,01,02,03 --orchestrator claude` (codex pool) and `--delegate claude`:
  everything OK except the two items repaired above. Rerun on the clean tree after the plan commit.
- **Baseline gate:** none exists at `BASE_SHA`. Task-00 creates `scripts/gate.py` (Blueprint: "It
  runs for the first time at the end of Task-00"); Task-01 creates its validator. Recorded, not
  skipped.
- Delegate auth: `codex login status` → logged in (codex-cli 0.159.3); `claude -p --model sonnet`
  ping → `is_error: false`. Playwright Chromium launches; `uv` 0.12.13; `pypdf` 6.16.2 in the
  global Python (for the Codex bees to read the PDFs).
- Wake lock: `uyanik_tut.py`, PID 3220, no `--until` (UNTIL done); released at closeout by the
  stop file.

## Quota (measured 04:42 ACST with `limit.py`)
| Pool | 5-hour | Weekly | Weekly resets |
|---|---|---|---|
| Claude (max) | 40% (resets 05:30) | **79%** | 2026-10-04 21:30 ACST |
| Codex (plus) | 0% | 36% | 2026-10-08 12:56 ACST |

**Per-wave estimate (window points, weekly):** Task-00 about 10–16 Claude (one large feature,
builder `xhigh`, two lenses, fix rounds), Task-03 about 3–5 Claude, Task-01 and Task-02 about 10–20
Codex together.

**Risk, stated up front:** Claude weekly 79% + 13–21 = 92–100%. The quota hook stops every spawn
and every sub-agent tool call at 92%, so Task-00 may be cut during review or fixing. To keep the
cut late rather than early, the panel runs only the spec and screen lenses (the code lens is
dropped: the GATE covers ruff and pytest, and in the Terra NT count of about 30 findings across
three lenses, the 2 real ones both came from the screen lens). If the cut comes, the run stops new Claude work, gates what exists, and **Tarık decides**:
wait for the weekly reset (2026-10-04 21:30) or spend the one banked Claude reset (Opus 5.5 launch
grant, resets 5-hour and weekly). The Codex lanes are unaffected.

## Approval
Tarık approves this file; then the orchestrator commits it with the two task repairs, reruns
preflight, records the final `BASE_SHA`, and starts wave 1.

## Addition approved by Tarık, 2026-10-03 11:25 ACST: Task-04 (wave 3)
Tarık asked for the Task-01 fix after the first look ("önerini yap ... sana bıraktım"). Task-04
rewrites the four Task-01 case files as real paperwork and adds two validator checks (words per
page, meta commentary) for `A-0142` and `E-*`. Codex bee `gpt-6-sol`/`high`, timebox 90 min, OWNS
as Task-01's, GATE `python scripts/validate_cases.py`. Disjoint from Task-00, which is still
running. Worktree cut from main after Task-02 (`6f23392` plus this commit).
