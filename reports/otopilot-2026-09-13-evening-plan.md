# otopilot wave plan — 2026-09-13 evening

**Direction:** Claude main loop (Fable 5.1) orchestrates, **Claude bees** (`claude -p`, model
per row) run the lanes. Codex untouched by operator decision (19:45: "claude swarm yap
sadece, limit bol claude'da"). Preflight: `onkontrol.py . --tasks 12,14,15,16,17,18,19,21
--orchestrator claude --delegate claude` → OVERALL OK, direction row
`orchestrator claude -> claude bees (same pool: watch pressure)`, `owns_disjoint` OK.

| Item | Value |
|---|---|
| `BASE_SHA` | the commit that carries this plan (main HEAD at launch, gate GREEN on `514a3f0` at 19:41, 183 tests); later waves are cut from the integrated main HEAD, as on the morning run |
| Baseline gate | `venv/Scripts/python scripts/gate.py` (ruff check, ruff format --check, pytest) |
| Stop markers | none in the eight selected tasks |
| Quota snapshot | 19:41: Claude 5 h 3 % (window reset 19:40), 7 d 71 % (resets 21:30) → `GO`; Codex 12 % / 10 %, untouched |
| Target | operator: as much as possible by 21:30; the run continues past it if lanes are in flight (the 7 d window resets then, so nothing is lost) |
| Timebox per bee | 20 min wall clock; 2 attempts max |
| Lane roots | `..\..\.lanes\fair-turn\task-NN` (outside the repo), detached worktree; `venv` directory junction to the repo's `venv\`; removed with `cmd /c rmdir` BEFORE `git worktree remove` (morning lesson: `--force` followed the junction and deleted the repo venv) |
| Wake lock | `wakelock.ps1` in a separate PowerShell process, released at closeout |
| Bee recipe | `.lanes/fair-turn/bee.ps1` from the morning run: brief on stdin, `--permission-mode acceptEdits`, `--allowedTools` for `venv/Scripts/python` and `git status/diff/log/add/commit`, house rules via `--append-system-prompt`, `BEYIN_INVOKED_BY=bee` |
| Model / tier | `opus` for the reasoning-bearing lanes (12 metrics, 14 board, 15 map+metrics, 19 feedback page), `sonnet` for the mechanical ones (16, 17, 18, 21). `fable` never a lane. |

## Waves (otopilot lanes)

| Task | Wave | Agent | Model | Effort | OWNS | GATE | Attempts |
|---|---:|---|---|---|---|---|---:|
| Task-12 Evaluation | 1 | claude bee | opus | high | `fair_turn/eval/metrics.py`, `fair_turn/eval/baseline.py`, `scripts/run_eval.py`, `data/build/eval.json`, `data/build/eval_tables.md`, `tests/test_metrics.py` | `venv/Scripts/python scripts/gate.py` | 1–2 |
| Task-14 Triage board | 2 | claude bee | opus | high | `fair_turn/app/pages/board.py`, `fair_turn/app/components/ranking_table.py`, `tests/test_page_board.py` | same | 1–2 |
| Task-19 Feedback-loop page | 2 | claude bee | opus | high | `fair_turn/app/pages/feedback.py`, `tests/test_page_feedback.py` | same | 1–2 |
| Task-21 Report tables export | 2 | claude bee | sonnet | medium | `scripts/export_report_tables.py`, `data/build/report/`, `tests/test_report_export.py` | same | 1–2 |
| Task-15 Map and metrics panel | 3 | claude bee | opus | high | `fair_turn/app/components/map.py`, `fair_turn/app/components/metrics.py`, `tests/test_board_map_metrics.py`, `fair_turn/app/pages/board.py` (append two calls) | same | 1–2 |
| Task-16 Job card | 3 | claude bee | sonnet | high | `fair_turn/app/pages/job_card.py`, `fair_turn/app/components/highlight.py`, `tests/test_page_job_card.py` | same | 1–2 |
| Task-17 Sign-off and audit log pages | 4 | claude bee | sonnet | medium | `fair_turn/app/pages/sign_off.py`, `fair_turn/app/pages/audit_log.py`, `scripts/seed_audit.py`, `data/audit/sample.jsonl`, `tests/test_pages_signoff_audit.py` | same | 1–2 |
| Task-18 Tenant view | 5 | claude bee | sonnet | medium | `fair_turn/app/pages/tenant.py`, `tests/test_page_tenant.py` | same | 1–2 |

Dependencies: 12 → 11 (DONE). 14 and 19 → 13 (main loop, below); 19 also → 05 (DONE);
21 → 12 and 05. 15 → 14 and 04; 16 → 14. 17 → 15 and 16. 18 → 17. Wave 2 starts only
after Task-13 is integrated green on main; wave N+1 only after every wave-N dependency
is integrated. A red task skips its dependency closure with the reason recorded.
Within a wave OWNS sets are disjoint (preflight). Task-15 appends to `board.py`, which
Task-14 owns: legitimate across waves (15 depends on 14), never inside one.

## Main-loop tasks run alongside the waves (not otopilot lanes)

| Task | When | How |
|---|---|---|
| Task-13 App shell, artefact loader, state, smoke test | with wave 1 | routed `agent claude (main loop)`. The main loop wrote the contract (page names, loader API, join rule, state keys, socket-blocked smoke test) and delegates the typing to an `opus` `claude -p` process on the same bee recipe, per the house rule that Fable chefs and never writes code; the main loop runs the gate and integrates. Judgment stays in the brief, not in the bee. |
| Task-20 README, reproduction steps, zip | after 12 and 19 are green (during wave 3–4) | same pattern, `sonnet`; the README prose is reviewed by the main loop before the integrated commit. |

Two contract decisions taken by the main loop for those briefs, recorded here so they are
not mistaken for bee improvisation:

- **Task-12, span scores:** `labels.json` carries no gold spans (labels first, text second;
  the generator returned text only). `span_scores` is implemented and unit-tested on the
  SemEval-2013 worked example; `run_eval.py` computes it against
  `data/build/gold_spans.json` when that file exists and otherwise writes `null` with the
  reason. Hand-annotating the 20 graded items (PRD §6.4) is a human job → `BACKLOG.md`.
  Likewise `location_mentioned` and `crew_or_access_note` have no gold label, so the
  eval reports P/R/F1 for `fault_type`, `safety_class` and `health_risk` only and says so.
- **Task-13, loader scope:** the criterion "load_all is the only place `data/build/` paths
  appear in `fair_turn/app` or `fair_turn/data`" cannot hold literally: `synth.py` and
  `geography.py` already carry the build paths as *writers*. The test asserts it for
  `fair_turn/app` and for every reader in `fair_turn/data` (i.e. `artefacts.py` only).

## Excluded (not eligible this run)

| Task | Reason |
|---|---|
| Task-13, Task-20 | routed `agent claude` = the orchestrating CLI; handled in the main loop as above |
| Task-00–11 | DONE |

## Integration protocol (Phase 3, unchanged)

Per bee, in completion order: gate in the worktree → exactly one commit inside OWNS →
cherry-pick onto `main` → gate again on `main` → only then status DONE + index tick in the
integrated commit. Red twice or timebox: worktree discarded, one dated line in
`BACKLOG.md` with the failing assertion and the reason, dependents skipped. Quota is
re-measured before every wave (`--quota-only --orchestrator claude --delegate claude`);
`STOP` spawns nothing new and never switches delegate.

## Approval

Operator message 2026-09-13 19:45: "basla otopilota claude swarm yap sadece limit bol
claude da bitirelim 9.30 a kadar" — taken as approval of this plan with the direction
and target it states. After approval the run cannot widen its selection or ownership.
