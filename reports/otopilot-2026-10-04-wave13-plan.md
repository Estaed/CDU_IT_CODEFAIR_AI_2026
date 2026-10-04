# otopilot plan, 4 October 2026: wave 13 (Task-28)

Approved by Tarık in chat at 16:17 ("tamam basla"), after the route was named: one Codex bee, no
Claude calls.

- **Direction:** orchestrator Claude (`opus`, this session) → Codex bee. No fallback row: the Claude
  pool is at 96% weekly (wall 97%), so the orchestrator only gates, looks and integrates.
- **SOURCE:** tasks (Task-28). **UNTIL:** done.
- **BASE_SHA:** `a0748996d48933931d7e755e594473cdfb962547`.
- **Preflight:** `onkontrol.py --tasks 28 --orchestrator claude`: OVERALL OK, quota GO (Codex weekly
  57%, 5-hour 0%). Claude pool: NARROW (96% weekly, resets 21:30).
- **Baseline gate:** `uv run python scripts/gate.py` at BASE_SHA (result in the report).
- **Codex auth:** `codex login status` → logged in using ChatGPT.
- **PREVIOUSLY TRIED:** nothing in `notes.md` → *After v1* matches.
- **Wake lock:** `uyanik_tut.py`, PID in the report.

| Task | Wave | Agent | Model | Effort | OWNS | GATE | Timebox | Attempts |
|---|---|---|---|---|---|---|---|---|
| Task-28 | 13 | codex (network on, for `fetch_wwcc_rules.py` and the a11y audit) | `gpt-6.1-sol` | high | as in the task's Lane block | `uv run python scripts/gate.py` | 150 min | 1 (+1 retry) |

Lane: `../readmark-lanes/task-28`, detached at BASE_SHA; `.env`, the NT housing policy PDFs and the
CDU policy text copied in (git-ignored); `.venv` from `uv sync`.

Orchestrator-side, outside the bee: removing the git-ignored local test cases `runs/U-*` and
`data/uploads/U-*` from the main checkout at integration (the task asks for it; the bee cannot reach
them from its worktree).

Excluded: Task-29 (main-loop, by hand on the website after the Claude reset).
