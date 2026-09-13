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

**Task-27 real build (03:44–03:48, main loop):** the NT site returns 403 to plain `urllib`
(same as BoM on 2026-09-12), so the PDF was fetched once with `curl` and a browser user
agent and committed; `build_policy_index.py` then ran against Ollama `bge-m3`: 66 keys, 32
non-empty, 53 passages, cosine scores 0.55–0.59 against the provisional 0.55 threshold
(bge-m3 scores cluster tightly; the threshold deserves a look before the report quotes
retrieval quality). `verify` holds against the PDF text (`tests/test_policy.py`, 5 passed,
none skipped). Commit `3f98952`. Task-27 lane itself: orchestrator gate GREEN, `bdc4727`.

### Wave B (25, 28) — launched 03:42, Codex `terra`/high

| Task | Attempts | Outcome | Bee elapsed | Main commit |
|---|---:|---|---|---|
| Task-25 batch freeze, effect sentence | 1 | **green** | 8.3 min | `8924e5a` |
| Task-28 intake seam and action | 1 | **green** after one orchestrator fix outside the lane: `tests/test_layers.py::test_import_direction` still forbade `app -> llm`; the Task-23 contract had put the exception only in the new by-file test. Part 2 names `app/intake.py` as the one allowed importer, so the direction check now exempts that file (`6a9950a`). The bee reported BLOCKED correctly rather than editing a file it did not own. | 11.8 min | `7d04c4a` |

Quota delta, wave B: Codex 5 h 65 % → 82 % (two bees plus Task-26 launched at 03:53, which
is still running); Claude 5 h 61 % → 66 %. Codex bee gates see `test_cli_wrappers` timeout
flakes whenever three or more gates run at once on this laptop; the orchestrator's gate is
the verdict and was green every time.

**Handover decision (03:59):** Task-26 runs to completion on Codex (a wave never mixes
delegates). Tasks 29 and 31 then start as **Claude bees** (`bee.ps1`, `opus` for 29,
`sonnet` for 31): Codex will sit at about 90 % once 26 returns, which is `NARROW`, and both
Claude windows are clear (5 h 66 %, 7 d 7 %). Per the plan's fallback row.
