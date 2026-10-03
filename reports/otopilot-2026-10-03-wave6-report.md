# otopilot report, 2026-10-03: wave 6 (Task-15, the final look)

Plan: `reports/otopilot-2026-10-03-wave6-plan.md`. BASE_SHA `c5415c4`. The builder was a Codex bee,
`gpt-6.1-sol`/`high`. The Claude weekly window stood at 90%, and Tarık chose Codex over waiting for
the reset. The orchestrator (Claude `opus`, this session) ran the gates, the screen review and the
integration.

## Outcomes

| Task | Outcome | Attempts | Elapsed | Gate (exit) | Main SHA |
|---|---|---|---|---|---|
| Task-15 | green, eye check pending: 2 | 1 build + 3 fix rounds | 18:20–19:45 (bee), integrated 19:55 | bee 0 (90, then 92 passed); orchestrator: lane 0 (90 → 90 → 92 passed), main 0 (92 passed) | this commit |

- **Baseline at `d85ed2f`:** 85 passed. **After:** 92 passed.
- **Tree after the gate:** clean on main (0 changed files). The gate no longer writes tracked files
  (finding 2).

## Review panel: the screen lens, run by the orchestrator

The orchestrator compared the screens with `mock-6-gov-filepanel.png` at 1280 and 1440.

| # | Finding | Score | Round | Result |
|---|---|---|---|---|
| 1 | Viewer tab labels were clipped ("Policy · Page 6 · dat"; at 1280 only "Page") | 85 | 1 | fixed. A headless check now asserts that no tab label overflows, on every question at both widths |
| 2 | `tests/test_screen.py` wrote screenshots into the tracked `reports/screens/2026-10-03-wave6/`, so every gate run on main would dirty the tree | 85 | 1 | fixed. Tests write to `.tmp/shots/wave6/`, and the delivered set was copied once. The cause was the task's wording, logged with `gardener.py` and fixed in `plan-wave` (vault `db05887`) |
| 3 | Too many viewer tabs (16 on Urgent-need category) | 80 | 2, 3 | fixed in round 3. Round 2's rule (required + cited + 2) still left 10, because claims cite many pages; the orchestrator had not counted the data first. Final rule: the required pages plus at most 2 more, the rest under "More pages (N)". The orchestrator checked that the list holds all 11 pages (4 cited, 7 possibly missed) |

Below 80, not sent to a fix round:
- The sign-off list says "Finish these 8 clauses" where the rest of the screen says "questions" (70).
- At 1440 the wait-time line wraps when the "Next" button is long (60).
- "More pages" opens inside a scrolling box, so its second group starts below the fold (60).

**Tab counts after round 3** (tabs / More pages), from the bee's report:

| Question | Tabs | More pages |
|---|---|---|
| Residency | 3 | 0 |
| Property | 3 | 1 |
| Income | 4 | 3 |
| Debts | 3 | 0 |
| Former tenancies | 2 | 6 |
| Urgent-need category | 4 | 11 |
| Urgent need documented | 4 | 12 |
| Discretion | 3 | 1 |
| Other facts | 2 | 2 |

## Integration notes
- **Commits:** in round 1 the bee could write the lane's git index and made one commit. In rounds 2
  and 3 it could not, so the orchestrator amended that commit to a single commit over BASE_SHA
  (`9368980` in the lane). Every path is inside `OWNS`. The bee's round 3 notes file was left out
  of the commit.
- **Model calls:** the bee reports that its first checks in round 3 ran with `claude` on PATH. Its
  final gate ran with `claude` off PATH. It made no model calls, and the replay cache is unchanged
  (no `runs/` path in the diff).
- **Changed test assertions** (from the bee):
  - the dark toggle and saved-theme checks became light-only and "saved dark opens light";
  - the initial all-pages count moved to the explicit full-file view;
  - the outcome selector became native radios;
  - the hidden reader at sign-off became an absent reader.
- **Acceptance wording:** the line "one tab per cited or required page" was narrowed in review. The
  task file records this next to the ticked box.
- **Intended differences from the mock:** in `design/deviations.md`.

## Awaiting eye check
1. Tarık puts `reports/screens/2026-10-03-wave6/opening-question-1440.png` beside
   `reports/screens/ui-references/mock-6-gov-filepanel.png`. To see it live, run
   `uv run python -m readmark serve --case A-0142`.
2. A first-time viewer names the next step within 10 s.

Still open from earlier waves: the eye check on `readmark/checklist/clauses.yaml`.

## Quota
- Claude weekly: 90% at 18:07, measured before the run. It was not re-measured at closeout.
- The builder ran on Codex; Codex weekly was 14% at the start.

Run closed: tasks consumed
