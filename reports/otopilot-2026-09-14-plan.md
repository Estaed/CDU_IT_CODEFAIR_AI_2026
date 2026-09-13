# otopilot wave plan — 2026-09-14 (Phase 2, night run)

**Direction:** Claude main loop (Fable 5.1, planner and orchestrator in one session; the
operator is asleep, so no seat change) orchestrates, **Codex bees** (`codex exec`,
`codex-swarm` recipe) run the lanes. **Fallback delegate row: Claude bees** (`claude -p`,
`claude-swarm` recipe, `.lanes/fair-turn/bee.ps1`) — operator instruction 2026-09-14 03:10:
"codex swarmla basla, limiti bitmeye yakin yeni taska gecerken claude swarm a gec". Preflight:
`onkontrol.py . --tasks 22..36 --orchestrator claude` → OVERALL OK, direction row
`orchestrator claude -> codex bees`, `owns_disjoint` OK, quota GO.

| Item | Value |
|---|---|
| `BASE_SHA` | the commit that carries this plan (main HEAD at launch; gate GREEN on `8d9d287` at 03:17, 253 tests); later waves are cut from the integrated main HEAD |
| Baseline gate | `venv/Scripts/python scripts/gate.py` (ruff check, ruff format --check, pytest) |
| Stop markers | none in the fifteen selected tasks |
| Quota snapshot | 03:15: Claude 5 h 38 % (resets 05:39), 7 d 4 %; Codex 5 h 33 % (resets 07:20), 7 d 30 % → both `GO` |
| Target | every Phase 2 task, 22 → 36, as far as the pools allow; Task-27 and Task-36 have a real run after the bee's gate (see below) |
| Timebox per bee | Codex 45 min wall clock, Claude 25 min; 2 attempts max |
| Lane roots | `..\..\.lanes\fair-turn\task-NN`, detached worktree; `venv` directory junction to the repo's `venv\`; junction broken with `cmd /c rmdir` BEFORE `git worktree remove` |
| Wake lock | `wakelock.ps1` in a separate PowerShell process (laptop; DC idle sleep 20 min), held 03:18, released at closeout |
| Codex bee recipe | `.lanes/fair-turn/codex-bee.ps1`: house rules + brief on stdin (`-`), `--sandbox workspace-write -C <lane>`, explicit `-m` and `-c model_reasoning_effort`, `-c mcp_servers={}`, `-o <last message>`, `BEYIN_INVOKED_BY=bee`. Probe bee (luna/low) run before wave A to confirm the worktree commit works under the sandbox |
| Claude bee recipe (fallback) | `.lanes/fair-turn/bee.ps1` from the 2026-09-13 runs, `opus` for reasoning lanes, `sonnet` for mechanical ones |
| Model / tier (Codex) | mid tier `gpt-5.6-terra` for every lane; effort `high` for the reasoning lanes (22, 24, 25, 26, 27, 28, 29, 30, 33, 36), `medium` for the mechanical ones (23, 31, 32, 34, 35). `gpt-6-astra` never; `gpt-5.6-sol` not named by the operator |
| Handover rule | at a wave boundary only; trigger: Codex pool `NARROW` (5 h ≥ 90 % or 7 d ≥ 92 %) or at a wall, AND both Claude windows clear; the report records the wave and both pools' numbers. Bee briefs are recipe-neutral (task file, Part 2 slice, Lane, BASE_SHA, timebox, report contract) |

## Waves (otopilot lanes)

| Task | Wave | Agent | Model (Codex / Claude fallback) | Effort | OWNS | GATE | Attempts |
|---|---:|---|---|---|---|---|---:|
| Task-22 Workspace interaction spike | A | bee | terra / opus | high | `fair_turn/app/components/workspace_map.py`, `job_list.py`, `tests/test_workspace_components.py` | `venv/Scripts/python scripts/gate.py` | 1–2 |
| Task-23 Phase 2 shell, runtime store | A | bee | terra / opus | medium | `main.py`, four stub pages, `state.py`, `data/runtime.py`, `artefacts.py` (`to_jobs` merge), `.gitignore`, `tests/test_layers.py`, `test_runtime.py`, `test_app_smoke.py` (default page) | same | 1–2 |
| Task-24 Audit log Phase 2 | A | bee | terra / opus | high | `core/audit.py`, `tests/test_audit.py`, `scripts/seed_audit.py`, `data/audit/sample.jsonl` | same | 1–2 |
| Task-27 Policy index | A | bee | terra / opus | high | `scripts/build_policy_index.py`, `llm/ollama.py` (embed), `data/policy.py`, `tests/test_policy.py`, `data/raw/PROVENANCE.md` (row), FS17 PDF, `data/build/policy_passages.json` | same | 1–2 |
| Task-25 Batch freeze, effect sentence | B | bee | terra / opus | high | `core/batch.py`, `core/effect.py`, `tests/test_batch.py`, `tests/test_effect.py` | same | 1–2 |
| Task-28 Intake seam and action | B | bee | terra / opus | high | `llm/intake.py`, `llm/prompts.py` (append), `app/intake.py`, `tests/test_intake.py`, `tests/fakes/provider.py` | same | 1–2 |
| Task-26 Visit plan core | C | bee | terra / opus | high | `core/visit_plan.py`, `tests/test_visit_plan.py`, `core/constants.py` (append), `constants.md` (append) | same | 1–2 |
| Task-29 Workspace page | C | bee | terra / opus | high | `pages/workspace.py`, `components/details_pane.py`, `weighting.py`, `ranking_table.py` (extend), `tests/test_page_workspace.py` | same | 1–2 |
| Task-31 Review queue page | C | bee | terra / sonnet | medium | `pages/review_queue.py`, `tests/test_page_review_queue.py` | same | 1–2 |
| Task-30 Sign-off form, decision states, retire Phase 1 pages | D | bee | terra / opus | high | `pages/workspace.py` (sign-off), `components/sign_off_form.py`, `metrics.py`, `tests/test_page_workspace_signoff.py`, deletions listed in the task | same | 1–2 |
| Task-32 Visit plan page | E | bee | terra / sonnet | medium | `pages/visit_plan.py`, `tests/test_page_visit_plan.py` | same | 1–2 |
| Task-33 Tenant answer | E | bee | terra / opus | high | `core/explain.py`, `pages/tenant.py`, `tests/test_explain.py`, `tests/test_page_tenant.py` | same | 1–2 |
| Task-34 Evidence lab | E | bee | terra / sonnet | medium | `pages/evidence_lab.py`, `tests/test_page_evidence_lab.py`, deletions listed in the task | same | 1–2 |
| Task-35 Integration, README, package | F | bee | terra / sonnet | medium | `tests/test_app_smoke.py`, `README.md`, `scripts/package_submission.py`, `tests/test_package.py`, `pages/workspace.py` (caption), docstring citations, wireframes §4 sentence | same | 1–2 |
| Task-36 Ollama benchmark code | G | bee | terra / opus | high | `llm/ollama.py` (chat), `llm/intake.py` (route), `scripts/benchmark_provider.py`, `tests/test_ollama.py`, `data/build/eval_ollama.json`, `MODELS.md` | same | 1–2 |

Dependencies (from the task files): 25 → 24; 28 → 23, 24; 26 → 25; 29 → 22, 23, 25, 27, 28;
31 → 23, 24, 28; 30 → 29; 32 → 26, 30; 33 → 26, 30; 34 → 24, 30; 35 → 31, 32, 33, 34;
36 → 28, 35. Wave N+1 starts only after every dependency is integrated green on main; a
red task skips its dependency closure with the reason recorded. OWNS sets inside a wave are
pairwise disjoint (preflight; checked again per wave). Cross-wave overlaps are legitimate
only along a dependency edge (29 → 30 on `workspace.py`; 30 → 34/35 on the evidence-lab
test file and `workspace.py`; 27 → 36 and 28 → 36 on `ollama.py` / `intake.py`).

**Quota estimate per wave (window points, Codex 5 h):** A ≈ 20, B ≈ 10, C ≈ 15, D ≈ 6,
E ≈ 15, F ≈ 5, G ≈ 5 — a guess from the 2026-09-13 Claude runs (about 7 points per bee);
no Codex bee has been measured on this project yet, and the checkpoint after each wave
records the real delta.

## Real runs after the bee's gate (main loop, on this machine)

| Task | What | When |
|---|---|---|
| Task-27 | `venv/Scripts/python scripts/build_policy_index.py` with Ollama up and `bge-m3` pulled; fetches the FS17 PDF (network, scripts only); `verify` must hold; artefact, PDF and PROVENANCE row committed | right after the Task-27 lane is integrated, before wave C (Task-29 reads the artefact) |
| Task-36 | `ollama pull qwen3:8b` (5.2 GB) then `scripts/benchmark_provider.py --provider ollama --model qwen3:8b`; decision line quoted in the report | **not tonight**: the pull and a 170-call local benchmark are a state change on the operator's machine with no one watching, and the decision (a possible Part 2 seam edit, rule 8) is the operator's. The lane ships the code; the run waits for the morning |

## Ownership widened by the orchestrator at plan time (written into the task files)

- **Task-23** + `tests/conftest.py` (new): once human-set fields persist to `data/runtime/`,
  every Phase 1 test that sets one through the UI would write into the working tree; an
  autouse fixture points `runtime.RUNTIME_DIR` at `tmp_path`. `tests/test_app_smoke.py`'s
  page-registration test must also change (it asserts the six Phase 1 pages are exactly the
  on-disk set), so the "default-page assertion only" limit is lifted for that file.
- **Task-24** + `fair_turn/app/pages/audit_log.py`, two key names only: the export column
  rename (`day` -> `decision_day`) would break the untouched Phase 1 page and its test; the
  page is deleted by Task-34 anyway.

## Excluded (not eligible this run)

| Task | Reason |
|---|---|
| Task-00–21 | DONE (Phase 1) |
| Task-22 criterion 5 | human click check; the lane is reported **green, review-visual pending** |

## Integration protocol (Phase 3)

Per bee, in completion order: gate in the worktree → exactly one commit inside OWNS (the
orchestrator checks the diff) → cherry-pick onto `main` → gate again on `main` → only then
status DONE + index tick in the integrated commit. Red twice or timebox: worktree discarded,
one dated line in `BACKLOG.md` with the failing assertion and the reason, dependents skipped.
Quota is re-measured before every wave (`--quota-only`, delegate pool) and the handover rule
above applies at that boundary. A checkpoint is appended to the report after every wave.

## Approval

Operator message 2026-09-14 03:10: "tasklari otopilotla yap once codex swarmla basla limiti
bitmeye yakin yeni taska gecerken claude swarm a gec ilerleyebildigin kadar ilerle uyumaya
gidiyorum sabah kalkinca bakarim" — taken as approval of this plan, its direction, its
fallback row and its Task-36 real-run deferral. After approval the run cannot widen its
selection or ownership.
