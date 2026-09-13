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

### Wave C (26 on Codex; 29, 31 on Claude after the handover) — 03:53 / 04:14

| Task | Delegate | Attempts | Outcome | Bee elapsed | Main commit |
|---|---|---:|---|---|---|
| Task-26 visit plan core | Codex `terra`/high | 1 | **green** (312 tests in the lane) | 19.8 min | `5191b99` |
| Task-31 review queue page | Claude `sonnet` | 1 | **green, review-visual pending**; one permission denial, self-recovered | 8.8 min | `890c180` |
| Task-29 workspace page | Claude `opus` | 1 | lane gate GREEN (326 tests); **main gate RED on integration** with Task-31: `open_jobs` now applies human-set fields, so a job marked rankable is dispatched by the capacity simulation and leaves the open set, and the review-queue page's `_job_for_rank` then assumes it is an intake report (`StopIteration`). Neither lane could see the other. Fix bee (`sonnet`, lane `task-29fix`) launched 04:32 on the exact cause; the code sits on main at `e47ae2e` with the gate red until the fix lands. Five contract deviations the bee reported honestly are in `BACKLOG.md`. | 15 min | pending |

**Handover executed 04:14:** Codex 5 h reached 95 % (the wall) as Task-26 returned; both
Claude windows were clear (5 h 67 %, 7 d 7 %), so 29 and 31 ran as Claude bees per the
plan's fallback row. Quota after wave C: Codex 5 h 95 % (resets 07:20), Claude 5 h 78 %
(resets 05:39). Orchestrator error to note: a `BACKLOG.md` commit was made while a
cherry-pick was staged, which folded Task-29's code into it; split afterwards into
`9e9eadf` (BACKLOG) and `e47ae2e` (code). Lesson: never commit on main while `integrate.sh`
is running.

### Wave D (30) — Claude `opus`, 04:37

| Task | Attempts | Outcome | Bee elapsed | Main commit |
|---|---:|---|---|---|
| Task-29 integration fix (`task-29fix`, `sonnet`) | 1 | **green**; cause verified by the bee: after "Mark rankable" the typed job is dispatched by the capacity model and leaves `open_jobs`; `_job_for_rank` now falls through open jobs → intake record → build label → the item itself | 2.5 min | `fdb5575` (Task-29 DONE) |
| Task-30 sign-off form, decision states, metrics reveal, Phase 1 pages retired | 1 | **green, review-visual pending** (313 tests + 2 skipped for Task-34); one contract deviation reported: `sign_off_form.render` takes the frozen rows as a sixth argument | 8.2 min | `ad732fb` |

Quota after wave D: Claude 5 h 84 % (resets 05:39), Codex 5 h 95 % (resets 07:20). Wave E
runs narrow: Task-34 (`sonnet`) alone at 04:48; 32 and 33 after the Claude reset.
