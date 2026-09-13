# otopilot run report — 2026-09-14 night (plan: `reports/otopilot-2026-09-14-plan.md`)

**Direction:** Claude main loop (Fable 5.1, orchestrator) → Codex bees (`codex exec`,
`gpt-5.6-terra`), fallback row Claude bees per the plan. **BASE_SHA** `e3dce34` (the plan
commit) for wave A; later waves cut from the integrated main HEAD. Gate:
`venv/Scripts/python scripts/gate.py`, GREEN on `8d9d287` at 03:17 (253 tests). Wake lock
held from 03:18 in a separate PowerShell process.

**Probe (03:18–03:21, luna/low):** a Codex bee under `--sandbox workspace-write` can write
files and run pytest in a detached worktree but cannot `git commit` (`.git/worktrees/<lane>/
index.lock: Permission denied` — the worktree's metadata lives in the main repo, outside the
sandbox root). Recipe consequence: bees leave their work in the tree, the orchestrator
commits it after checking the diff against OWNS. Also: the Codex event stream goes to
stderr, so `codex-bee.ps1` sets `$ErrorActionPreference = "Continue"` around the call.

## Checkpoints

_(appended after every wave)_

### Wave A (22, 23, 24, 27) — launched 03:26, Codex `terra`

| Task | Effort | Attempts | Outcome | Bee elapsed | Main commit |
|---|---|---:|---|---|---|
| Task-23 Phase 2 shell, runtime store | medium | 1 | **green** (worktree gate GREEN, main gate GREEN) | 8.5 min | `2c8e6e2` |
| Task-22 workspace map + list spike | high | 1 | **green, review-visual pending** (criterion 5, the click path, is a human check) | 10.2 min | `9fe1785` |
| Task-24 audit log Phase 2 | high | 1 | **green** | 10.5 min | `f94db31` |
| Task-27 policy index code | high | 1 | bee reported BLOCKED on two `test_cli_wrappers` timeout tests that failed only under the load of four concurrent gates; orchestrator gate rerun pending; real Ollama build pending | 15 min | — |

Quota delta, wave A: Codex 5 h 33 % → 65 % (+32 for four bees, i.e. ~8 per bee, against the
plan's 20 estimate); Claude 5 h 38 % → 61 % (orchestrator only). Wave B (25, 28) launched
03:42 at Codex 65 % (`GO`).
