# otopilot run report — 2026-09-13 evening (plan: `reports/otopilot-2026-09-13-evening-plan.md`)

**Direction:** Claude main loop (Fable 5.1, orchestrator) → Claude bees (`claude -p`), Codex
untouched (operator decision). **BASE_SHA** `685f1ae` (the plan commit) for wave 1; every
later wave was cut from the integrated main HEAD. Gate: `venv/Scripts/python scripts/gate.py`,
GREEN at every base and after every integration. Quota (Claude): 5 h 3 % → 72 %, 7 d
71 % → 77 % over the run; `--quota-only` GO before each wave (fullest window 71 → 77 %).
Wake lock held 19:53–20:54 in a separate PowerShell process. Run: 19:53 → 20:55, 62 min,
ten bees, zero second attempts.

| Task | Model | Attempts | Outcome | Trajectory | Elapsed (bee) | Main commit |
|---|---|---:|---|---|---|---|
| Task-12 evaluation | opus | 1 | **green** | 0 fail; gate GREEN worktree + main | 6.9 min | `9d07cc3` |
| Task-13 app shell (main-loop task, typing delegated) | opus | 1 | **green** | 0 fail | 4.6 min | `ab5fa02` |
| Task-14 triage board | opus | 1 | **green, review-visual pending** | 0 fail | 5.6 min | `7e823d4` |
| Task-19 feedback-loop page | opus | 1 | **green, review-visual pending** | 0 fail | 6.9 min | `769b6ee` |
| Task-21 report tables export | sonnet | 1 | **green** | 0 fail | 7.2 min | `957ec34` |
| Task-15 map and metrics panel | opus | 1 | **green, review-visual pending** | 0 fail | 5.4 min | `01c4f86` |
| Task-16 job card | sonnet | 1 | **green, review-visual pending** | 0 fail | 10.1 min | `00cada7` |
| Task-20 README and packaging (main-loop task, typing delegated) | sonnet | 1 | **green** | 0 fail; README reviewed by the orchestrator; fresh-venv check done by the orchestrator (`a8d1bca`) | 3.8 min | `6c487d0` |
| Task-17 sign-off and audit pages | sonnet | 1 | **green, review-visual pending** | 0 fail | 9.2 min | `12d41c0` |
| Task-18 tenant view | sonnet | 1 | **green, review-visual pending** | 0 fail | 5.2 min | `3b55cdb` |

Main HEAD after the run: `3b55cdb`, gate GREEN (253 tests, up from 183). `docs/TASKS_INDEX.md`:
22 of 22 ticked. No `BACKLOG.md` red entries; the deferred items below are findings, not failures.

## Awaiting eye check (`review-visual`, advisory)

Every screen task shipped against `AppTest` assertions only. Look at each page in
`venv/Scripts/streamlit run fair_turn/app/main.py` against PRD §3: Triage board (14, 15),
Job card (16), Sign-off and Audit log (17), Tenant view (18), Feedback loop (19).

## Findings the operator decides on

- **`safety_class` macro-F1 0.564, target 0.85 not met** (`data/build/eval_tables.md`).
  Sonnet over-predicts `immediate` (precision 0.27, recall 0.93) and under-calls `urgent`
  (recall 0.38); the TF-IDF baseline is at 0.588. `fault_type` 0.919 and `health_risk`
  0.909 are fine. This is a class-definition problem in the extraction prompt, not a
  gate issue; `run_eval.py` exits 1 and the README says so. Options: (a) sharpen the
  prompt's three NT class definitions and rerun `extract.py` (about 74 Sonnet calls, one
  subscription window); (b) report the number as is. Recorded in `BACKLOG.md`.
- **No gold spans exist**, so the SemEval span scores are `null` with the reason in
  `eval.json`; hand-annotating the 20 graded items (PRD §6.4) is a human job.
- **Task-19 λ default**: the page reads the shared `state.lam` (default 1.0, PRD §3.1)
  rather than the task's 0.5, so a fresh page shows two identical runs until the slider
  moves. Either accept or give the page its own default.

## Orchestrator edits outside the lanes (all gated)

- `constants.md`: provenance row for `F1_TARGET` (Task-12 could not touch it).
- `tasks/Task-16.md`, `tasks/Task-17.md`: `state.py` added to OWNS (append-only accessors
  and the revision hook), because no page may read `st.session_state` and Task-13 was DONE;
  MUST NOT TOUCH lines aligned. Both bees stayed inside the addition (diffs checked).
- `.gitignore`: `data/audit/audit.jsonl`, the runtime log, after the Task-17 bee found that
  `tests/test_board_map_metrics.py` moves λ after a sign-off and so writes it during the gate.

## Recipe notes (candidates for the `otopilot` skill)

- The morning `bee.ps1` recipe (brief on stdin, `--allowedTools` prefix list, UTF-8 log)
  worked ten times out of ten. Every bee hit one or two `permission_denials` on
  compound shell lines (`... | tail`, `cd ...`, `echo $?`) and recovered by itself; harmless.
- Contract briefs pay off: the two `CONTRACT VIOLATIONS` reported (Task-13 types matching
  the real artefact, Task-15 rebuilding the sim inputs because Task-14 exposed no builder)
  were both the bee being right about the code and saying so, which is what the block is for.
- A Claude bee that imports a Streamlit page module at pytest collection corrupts global
  form state for the rest of the session (Task-16 finding); pages are exercised only
  through `AppTest.from_file`.
- Same-pool run: ten bees plus orchestration cost ~69 points of the 5 h window in an hour.
  Fine on a fresh window; not a 3 am recipe.

## Worktrees

All ten lanes removed after integration (junction broken with `rmdir` first, then
`git worktree remove`); `git worktree list` shows only the main checkout; the repo `venv`
is intact. The wake lock was released at 20:54.

## Result

10 of 10 approved lanes green and integrated; all 22 tasks DONE. Next: the hand-written
report and slides (`docs/report-requirements.md`), `review-visual` over the six screens,
and the `safety_class` decision above.
