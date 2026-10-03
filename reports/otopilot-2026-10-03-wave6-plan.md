# otopilot plan, 2026-10-03: wave 6 (Task-15, the final look)

Approved by Tarık in chat (2026-10-03: "evet başla"; engine choice: Codex bee).

- **Direction:** a Claude main loop orchestrates; the builder is a Codex bee. The fallback is none:
  the same task waits for the Claude weekly reset.
- **Seats:** the orchestrator is this session (Claude `opus`).
- **SOURCE:** `tasks` (Task-15 only). **UNTIL:** `done`.
- **BASE_SHA:** the commit holding this plan; its full SHA is recorded below after the second
  preflight.
- **Baseline gate at `d85ed2f`:** `uv run python scripts/gate.py` exit 0, 85 passed, `GATE CLEAN`.
- **Stop markers:** none (preflight `task_15`: no stop marker).
- **Quota at 18:07 ACST:**
  - Claude: 5-hour 15%, weekly **90%** (wall 97%, resets 2026-10-04 21:30 ACST).
  - Codex: 5-hour 61%, weekly 14%.
  - A single ultracode feature costs about 9 Claude weekly points (2026-09-29: four features, about
    35). That would hit the wall, so the builder is a Codex bee. The orchestrator's Claude cost is the
    gate, the screen check and integration, a few points.
- **Timebox:** 120 minutes wall clock for the bee; one retry on red, per otopilot.

| Task | Wave | Agent | Model | Effort | OWNS | GATE | Attempts (est.) |
|---|---|---|---|---|---|---|---|
| Task-15 | 6 | codex | `gpt-6.1-sol` | high | `web/**`, `readmark/serve.py`, `readmark/record/**`, `tests/test_screen.py`, `reports/screens/2026-10-03-wave6/**` | `uv run python scripts/gate.py` | 1 |

**Review:** the orchestrator runs the screen lens itself. It captures the screens with Playwright
at 1280 and 1440 and compares them with `reports/screens/ui-references/mock-6-gov-filepanel.png`
before integrating. It then sends one fix round to the bee if a finding scores 80 or more.

**Excluded:** none. No other task is pending.
