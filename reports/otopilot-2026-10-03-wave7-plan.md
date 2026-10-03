# otopilot plan, 2026-10-03: waves 7–10 (everything before submission)

Tarık's decision (2026-10-03): every agreed item ships in the 8 Oct ZIP, with no development after
submission (Blueprint → *Added before submission*). He told the orchestrator to go ahead ("hepsi
yapılacak").

## Schedule

| Wave | When | Tasks | Width | Why this order |
|---|---|---|---|---|
| 7 | 3 Oct, evening | Task-17 plain AI notes and usability fixes ‖ Task-18 question lists | 2 (disjoint `OWNS`) | Both are foundations, and each has a clear lane |
| 8 | 4 Oct | Task-19 home screen ‖ Task-21 easy example (main loop) | 2 | 19 needs 17's screen and 18's API. 21 needs 18's lists |
| 9 | 5 Oct | Task-20 new case upload | 1 | Needs 18 and 19. It shares `web/` and `serve.py` |
| 10 | 6 Oct | Task-22 scanned pages, then Task-23 search | 1, then 1 | Both touch `web/`. 22 needs 20 |
| — | 7 Oct | Numbers frozen (main loop), Tarık's eye checks | — | Blueprint: numbers by 7 Oct |
| — | 8 Oct | ZIP (main loop) | — | Blueprint |

**Risk.** Waves 9–10 carry live model calls and new dependencies. If wave 10 runs late, Task-23
(search) is the smallest to finish on 7 Oct. Nothing slips past 8 Oct without Tarık's word.

## Wave 7 (now)
- **Direction:** a Claude main loop, with Codex bees. The Claude weekly window was at 90% at 18:07;
  it resets on 4 Oct at 21:30.
- **Seats:** the orchestrator is this session (Claude `opus`).
- **Baseline gate on main `28d28be`:** 96 passed, from the Task-16 integration at `64552d6`.
  Later commits touched only reports.

| Task | Agent | Model | Effort | OWNS | GATE | Timebox |
|---|---|---|---|---|---|---|
| Task-17 | codex | `gpt-6.1-sol` | high | `web/**`, `readmark/record/**`, `readmark/serve.py`, `tests/test_screen.py`, `reports/screens/2026-10-03-wave7/**` | `uv run python scripts/gate.py` | 120 min |
| Task-18 | codex | `gpt-6.1-sol` | high | `readmark/checklist/**`, `readmark/ingest/**`, `readmark/pipeline.py`, `readmark/__init__.py`, `readmark/__main__.py`, `tests/test_checklist.py`, `tests/test_ingest.py`, `tests/test_pipeline.py`, `docs/question-lists.md` | `uv run python scripts/gate.py` | 120 min |

- **Screen review:** the orchestrator, for Task-17, against the Task-16 screens and the usability
  notes.
- **Spec review:** the orchestrator, for Task-18. It checks byte-identical replays and that
  `runs/eval/` is unchanged.
- **Fix rounds:** at most 3, for findings scoring 80 or more.
- **Before writing any rule into a fix brief, count it in the data** (`knowledge/concepts/kural-yazmadan-once-veriyi-say.md`).
