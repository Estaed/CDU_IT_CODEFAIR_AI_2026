# otopilot plan, 2026-10-03: wave 4 (Task-12, Task-13)

Status: **started on Tarık's word, 2026-10-03** ("bekleme suresi girsin ve task 12 degisiklik
onayliyorum", and a light default with the interface rework last). Blueprint updated in the same
commit: the number and date check rule; H-01 after changes; the wait-time context dataset; light
default.

## Run shape
- **Direction:** orchestrator Claude (this session). Both tasks are Codex bees, `gpt-6.1-sol`/`high`,
  network on. The launcher sets `PYTEST_ADDOPTS=-p no:cacheprovider` and `RUFF_NO_CACHE=true`.
- **Review:** the orchestrator runs each GATE in the lane and on main, plus a replay check on main.
  No Claude lens this wave: Task-13 is small, and the screen rework that needs a lens comes last.
- **SOURCE:** `tasks`, Task-12 and Task-13. **UNTIL:** `done`.

| Task | Engine | GATE | Timebox | Lane notes |
|---|---|---|---|---|
| Task-12 | Codex bee `gpt-6.1-sol`/`high` | `uv run python scripts/gate.py` | 120 min | Full checkout, including `data/heldout/` (H-01 is re-scored after changes); no Claude calls |
| Task-13 | Codex bee `gpt-6.1-sol`/`high` | same | 90 min | Sparse checkout without `data/heldout/`; downloads the NT wait-time CSV |

Parallel: `OWNS` disjoint. Integration order: Task-12 first, then Task-13, whose screen tests must
follow the data.

## Quota (16:20)
Claude 5-hour 7%, weekly 89%. Codex 5-hour 36%, weekly 10%. Estimate: Codex +15–25 points; Claude
only the orchestrator.
