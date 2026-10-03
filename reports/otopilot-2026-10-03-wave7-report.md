# otopilot report, 2026-10-03: wave 7 (Task-17, Task-18)

Plan: `reports/otopilot-2026-10-03-wave7-plan.md`. BASE_SHA `a5484bc`. Two Codex bees,
`gpt-6.1-sol`/`high`, ran in parallel from 20:46. The orchestrator (Claude `opus`) gated, reviewed and
integrated.

## Outcomes

| Task | Outcome | Attempts | Bee time | Gate (exit) | Main SHA |
|---|---|---|---|---|---|
| Task-18 | green | 1 (bee BLOCKED on a test outside its lane; resolved at integration) | 20:46–21:03 | bee 1 (113 passed, 1 failed); orchestrator lane 0 (114 passed); main 0 (127 passed) | `972f554` |
| Task-17 | green, eye check pending: 2 | 1 | 20:46–21:22 | bee 0 (109 passed); lane 0 (109 passed, 13.5 min); main 0 (127 passed, 13.7 min) | `af7237f` |

**Task-18 integration.**
- `tests/test_eval_cases.py` replays the evaluation and compares the result with the committed
  `runs/eval/`.
- That evaluation lists the result-affecting files changed since H-01's frozen run, as
  `changed_result_files`. Task-18 added checklist files, so the list grew.
- The orchestrator regenerated `runs/eval/cases.json` and `summary.json` in the lane and checked the
  diff. Only file-path lines changed; **no number changed**.
- Every case replay (A-0142, E-01..03, H-01) stayed byte-identical.

**Task-17 review (screen lens).**
- "What the AI noted (N)" has plain cards.
- The sign button goes from outlined "N questions left", to green, to Signed.
- Each outcome has its own icon.
- No finding scored 80 or more.
- One minor point: a note quoting a policy says "Found in the file ✓". Policy quotes are not in the
  file. Scored 70, not sent back.

**Gate time (orchestrator fix, main loop, this wave).**
- Task-17 made the tests wait the real 3 s for every passage opening, and the gate went from about
  3 min to 13.7 min.
- `create_app` now takes `opened_seconds` and passes it to record validation. The CLI never sets it,
  so the shipped value stays `rec.OPENED_SECONDS` = 3, and there is no environment override.
- Screen tests run on a 0.3 s clock. Two tests keep the real 3 s:
  - the one that proves the rule;
  - the E-02 polish test, which counts pages opened while moving between questions.
- Two type assertions now accept an integer `seconds_in_view`.
- Result: gate 0, **127 passed in 5 min 37 s**.

## Awaiting eye check
- Task-17:
  - open "What the AI noted" on Debts and understand every card;
  - watch the sign button change.
- Earlier: Task-15 (2), Task-16 (1), and `clauses.yaml`.

## Next
- **Wave 8 (4 Oct):** Task-19 (home screen) ‖ Task-21 (easy example, main loop).
- The Claude weekly window resets on 4 Oct at 21:30. Task-19 runs on Codex if it starts before then.

Run closed: tasks consumed (wave 7)
