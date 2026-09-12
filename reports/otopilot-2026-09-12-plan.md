# otopilot wave plan — 2026-09-12

**Direction:** Claude main loop orchestrates, **Claude bees** (`claude -p --model sonnet`)
run the lanes. Codex is held back by operator decision (Claude window renews Sunday
evening; spend it first). Preflight: `onkontrol.py . --tasks 04,05,06,07
--orchestrator claude --delegate claude` → OVERALL OK, direction row
`orchestrator claude -> claude bees (same pool: watch pressure)`.

| Item | Value |
|---|---|
| `BASE_SHA` | `main` HEAD at launch (`709af21` when this plan was last checked, gate GREEN, 66 tests); the orchestrator reruns preflight and records the pinned SHA in the report |
| Baseline gate | `venv/Scripts/python scripts/gate.py` (ruff check, ruff format --check, pytest) |
| Stop markers | none in the four selected tasks |
| Quota snapshot | Claude fullest window 56 % (`--quota-only` GO); Codex untouched by design |
| Bee auth probe | `echo ping \| claude -p --model haiku` → `is_error: false`, no denials |
| Timebox per bee | 30 min wall clock; 2 attempts max |
| Lane roots | `..\..\.lanes\fair-turn\task-NN` (outside the repo), detached worktree at `BASE_SHA` |
| Stack setup per lane | directory junction `<lane>\venv` → the repo's `venv\` (gitignored; `gate.py` resolves the junction so its interpreter check passes) |
| Wake lock | overnight run: the orchestrator holds `SetThreadExecutionState` in a separate long-lived process (`powershell` started in the background, released at closeout); confirm it before wave 1 |
| Model / tier | `sonnet` for every bee (claude-chef bee default; single Pro pool, so no `opus` lanes) |
| Hooks in bees | `BEYIN_INVOKED_BY=bee`; house rules via `--append-system-prompt` (lane_preamble, 5,155 bytes) |

## Waves

Single pool on a Pro plan, so wave 1 runs as two pairs, not four at once. Quota is
re-measured before every pair (`--quota-only --orchestrator claude --delegate claude`).

| Task | Wave | Agent | Model | Effort | OWNS | GATE | Attempts |
|---|---:|---|---|---|---|---|---:|
| Task-04 Capacity simulation and wait metrics | 1a | claude bee | sonnet | high | `fair_turn/core/capacity_sim.py`, `tests/test_capacity_sim.py` | `venv/Scripts/python scripts/gate.py` | 1–2 |
| Task-06 Explanation templates | 1a | claude bee | sonnet | high | `fair_turn/core/explain.py`, `tests/test_explain.py` | same | 1–2 |
| Task-05 Feedback-loop simulation | 1b | claude bee | sonnet | high | `fair_turn/core/feedback_sim.py`, `tests/test_feedback_sim.py` | same | 1–2 |
| Task-07 Audit log | 1b | claude bee | sonnet | medium | `fair_turn/core/audit.py`, `tests/test_audit.py`, `data/audit/.gitkeep` | same | 1–2 |

Dependencies: 04, 06, 07 depend on Task-02 only (DONE). 05 depends on 04, so wave 1b
starts only after 04's integrated green; a red 04 skips 05 with the reason recorded.
OWNS sets are pairwise disjoint (preflight `owns_disjoint` OK). Task-08 left this plan on
2026-09-12: done in the main loop the same afternoon because it gated 09–11.

## Excluded (not eligible this run)

| Task | Reason |
|---|---|
| Task-08 | DONE in the main loop before the run (rerouted, see its Execution block) |
| Task-09, 10, 11, 13, 20 | routed `agent claude` = the orchestrating CLI; main-loop tasks. 10 and 11 also spend the `claude -p` generation window and run one at a time by design |
| Task-12, 14–19, 21 | depend on 11 or 13, which are not DONE |

## Integration protocol (Phase 3, unchanged)

Per bee, in completion order: gate in the worktree → exactly one commit inside OWNS →
cherry-pick onto `main` → gate again on `main` → only then Status DONE + index tick in the
integrated commit. Red twice or timebox: worktree discarded, one dated line in
`BACKLOG.md` with the failing assertion, dependents skipped.

## Approval

The operator approves this file. After approval the run cannot widen its selection or
ownership, and never switches delegate mid-run.
