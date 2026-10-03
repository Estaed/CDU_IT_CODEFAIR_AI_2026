# otopilot plan, 2026-10-03: wave 3 (Task-10, Task-11)

Status: **started on Tarık's word, 2026-10-03** ("tamam basla limitine dikkat et hatta sol 6.1
performanstan memnun kaldiysan onu da kullanabilirsin"), after the wave was agreed in chat: the
evaluation, and the answer-key screen with the summary tab removed.

## Run shape
- **Direction:** orchestrator Claude (this session, `claude-opus-5-5`). Both tasks are
  `agent codex`: Codex bees `gpt-6.1-sol`/`high`, network on (Jev; Task-10 also `claude -p`,
  probed working inside the Codex sandbox at 15:0x: `is_error: false`, "pong").
- **Why Codex:** Claude weekly is at 87% and the quota hook stops spawns at 92%. Task-09 on
  `gpt-6.1-sol` was careful and honest (no tuning, stated its limits) in 22 minutes.
- **Review:** Codex bees have no ultracode panel. After Task-11 lands, one read-only Claude screen
  lens (`opus`/`high`, `yardimci-denetim`) looks at it if the Claude pool is under 90%. A finding
  at 80 or above goes back to a Codex fix bee.
- **SOURCE:** `tasks`, Task-10 and Task-11. **UNTIL:** `done`.

## Waves
| Wave | Tasks | Why |
|---|---|---|
| 3 | Task-10 and Task-11 in parallel | No dependency; `OWNS` disjoint |

## Task rows
| Task | Engine | Model / effort | GATE | Timebox | Attempts | Lane notes |
|---|---|---|---|---|---|---|
| Task-10 | Codex bee | `gpt-6.1-sol`/`high` | `uv run python scripts/gate.py` | 150 min | 1 + 1 | Full checkout including `data/heldout/` (it runs H-01); about 11 live `claude -p` opus calls (4 writers, the H-01 summary and audit, 3 mutation locators) |
| Task-11 | Codex bee | `gpt-6.1-sol`/`high` | same | 150 min | 1 + 1 | Sparse checkout without `data/heldout/`; no model calls |

## Quota (14:54)
Claude 5-hour 73%, weekly 87% (resets 2026-10-04 21:30 ACST). Codex 5-hour 10%, weekly 6%.
Estimate: Codex +15–25 points in the 5-hour window. Claude: about 11 opus calls inside Task-10,
plus one lens, about 1–2 weekly points.
