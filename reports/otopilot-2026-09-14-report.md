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
