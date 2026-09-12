# otopilot run report — 2026-09-13 (plan: `reports/otopilot-2026-09-12-plan.md`)

**Direction:** Claude main loop (Fable 5.1, orchestrator) → Claude bees (`claude -p`), Codex
untouched. **BASE_SHA** `8e42792` for wave 1a; wave 1b lanes were cut from the integrated
main HEAD (`c2e3885` for 05, `e2ee0bd` for 07) because 05 depends on 04. Gate:
`venv/Scripts/python scripts/gate.py`, GREEN at every base. Quota: Claude 5 h 14 % → ~20 %,
7 d 47 % → 49 % over the run; `--quota-only` GO before each wave. Wake lock held in a
separate PowerShell process for the whole run.

| Task | Model | Attempts | Outcome | Trajectory | Elapsed (bee) | Main commit |
|---|---|---:|---|---|---|---|
| Task-04 capacity sim | opus | 2 | **green** | attempt 1: files written, no command could run (recipe fault, see below), 0 fail on orchestrator gate → attempt 2: committed, gate GREEN worktree + main | 4.7 min + 0.8 min | `c2e3885` |
| Task-06 explain | sonnet | 2 | **green** | attempt 1: same recipe fault, 1 fail (ruff F841) → attempt 2: 0 fail, gate GREEN worktree + main | ~6 min + 3 min | `e2ee0bd` |
| Task-07 audit log | sonnet | 1 | **green** | 0 fail, gate GREEN worktree + main | 3 min | `9b1a45d` |
| Task-05 feedback sim | opus | 2 | **green** | attempt 1: BLOCKED, 1 of 7 fail (remote reports last 4 weeks 253 not below first 4 weeks 236) + ruff E501 → operator tightened the capacity constants (`c274d5c`), orchestrator pre-check 1 fail (gap week 12 9.0 not above week 1 12.5: end-of-window censoring) → attempt 2 with a 28-day completion tail: 0 fail, gate GREEN worktree + main | 5 min + 1.5 min | `2c56a34` |

## Task-05: what the bee found (verified by the orchestrator)

With the provisional capacity constants (2 crews per remote region, 3 town, 4 jobs per crew-day,
PRD §6.3) the toy model has far more capacity than demand: median remote wait is 2 days and
town 0 days at **both** λ = 1 and λ = 0, so almost nothing is unserved, reporting decay has
nothing to act on, and seasonal demand growth (December) outweighs it. The bee refused to
tune the decay floor or lookback to the test, correctly. Orchestrator sweep over the 90-day
labels (remote median / town median at λ = 1 → λ = 0, open at end):

| crews remote / town, jobs per crew-day | λ = 1 | λ = 0 | open at end |
|---|---|---|---|
| 2 / 3, 4 (current) | 2 / 0 | 2 / 0 | 126 / 81 |
| 1 / 3, 4 | 9 / 0 | 8 / 0 | 345 / 315 |
| 1 / 2, 2 | 16 / 0 | 14 / 2 | 537 / 601 |
| 1 / 1, 2 | 16 / 4 | 14 / 7 | 652 / 716 |
| 1 / 2, 1 | 27.5 / 6 | 24 / 14 | 875 / 946 |

The same slack also flattens the board's equity slider (the gap does not move with λ at
the current constants), so this is a Part 2 / constants decision, not a Task-05 fix.
**Decision (operator, 2026-09-13): option (a).** Constants tightened to 1 / 2 / 2 in `c274d5c` with provenance rows in `constants.md` and the PRD §6.3 prose updated. Options as presented: (a) tighten the provisional capacity constants in `constants.py` + `constants.md`
(PRD §6.3 already labels them provisional; Task-04's fixture tests are unaffected, its
30-day artefact test checks only speed and consistency); (b) change the Task-05 assertion
to a relative measure (share of the plain run's reports: 0.929 → 0.907 at λ = 1, weak);
(c) accept the finding and drop the feedback-loop claim from the PRD.

Second finding after the constants change: the per-week gap collapsed in the last weeks because
waits were censored at the window end (a week-12 report cannot wait more than about 7 days).
Measured with a completion tail: gap by report-week at λ = 1 goes 13.5 → 35 (28-day tail), so
the bee added `COMPLETION_TAIL_DAYS = 28` to the final capacity run; reporting decay still
stops at the 90-day window.

## Recipe faults found this run (candidates for the `otopilot` / `claude-swarm` skill)

- `--permission-mode acceptEdits` auto-accepts edits only; **every Bash / PowerShell call is
  denied**, so a bee can write files but cannot run the gate or `git commit`. It reports
  BLOCKED with exit 0 and `is_error: false`. Fix used here: `--allowedTools
  "Bash(venv/Scripts/python:*)" "Bash(git status:*)" "Bash(git diff:*)" "Bash(git log:*)"
  "Bash(git add:*)" "Bash(git commit:*)"` and a brief line saying so. A heredoc command
  (`python - <<'EOF'`) was still denied under the prefix rule.
- PowerShell 5.1 `*>> $LogPath` writes the bee's JSON as UTF-16 after a UTF-8 header line;
  the log reads as "binary". Fix: `2>&1 | Out-File -Encoding utf8 -Append`.
- `Start-Process -File` with a path containing spaces needs the path quoted inside the
  argument list, or the process exits at once with no error visible.

- **`git worktree remove --force` followed the `venv` directory junction inside the lane and
  deleted the contents of the repo's own `venv/`.** Rebuilt from `uv.lock` in about a minute
  (`uv venv venv --python 3.13`, `UV_PROJECT_ENVIRONMENT=venv uv sync`), gate GREEN after.
  One commit (`c274d5c`) was made while the interpreter was missing because `gate.py | tail`
  hid the failure; the gate was rerun on it afterwards and is GREEN. Rule for the recipe:
  `cmd /c rmdir <lane>env` (does not follow the junction) BEFORE `git worktree remove`,
  and never pipe the gate through `tail` in a commit chain.

## Worktrees

All four lanes removed after integration; `git worktree list` shows only the main checkout.
The wake lock was released at closeout.

## Result

4 of 4 approved tasks green and integrated: 04 `c2e3885`, 06 `e2ee0bd`, 07 `9b1a45d`,
05 `2c56a34`. Main HEAD after the run: `2c56a34`, gate GREEN (164 tests). Next in
`docs/TASKS_INDEX.md`: Task-11 (main loop, spends the Codex window) then 12 and 13.
