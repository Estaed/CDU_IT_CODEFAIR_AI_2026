# otopilot report, 2026-10-03: wave 3 (Task-10, Task-11)

Plan: [otopilot-2026-10-03-wave3-plan.md](otopilot-2026-10-03-wave3-plan.md). BASE_SHA `a5ec523`.
Orchestrator `claude-opus-5-5` (this session). Both builders were Codex bees, `gpt-6.1-sol`/`high`,
network on. Launched 15:25 ACST.

## Outcomes

| Task | Engine | Outcome | Attempts | Elapsed | Gate (exit) | Main SHA |
|---|---|---|---|---|---|---|
| Task-10 | Codex bee | green | 1 | 15:25–15:54 | bee 0 (69 passed); orchestrator: lane 0 (69 passed), main 0 (69 passed) | `2f00e0d` |
| Task-11 | Codex bee, then a Claude screen lens and a Codex fix bee | green, eye check pending: 1 | 1 build + 1 fix round; main pick red once (seam with Task-10), re-picked after an integration fix | build 15:25–15:46; lens 15:49–16:03; fix 16:03–16:10; main 16:20 | lane 0 (63 passed); main attempt 1 (1: 3 failed, 69 passed), reverted in `e591406`; integration fix `6724aca`; main 0 (72 passed) | `61511e4` |

**Task-11's main gate, attempt 1:**
- 3 tests failed in `tests/test_eval_cases.py`: "Code changed after H-01 was frozen".
- The cause was not the screen. Task-10's held-out guard pins the hash of every file under
  `readmark/`, including `serve.py` and `record/`, which Task-11 changed. As written, the repo could
  never change again after H-01.
- Integration fix `6724aca`: the guard compares only files that can affect H-01's results. It leaves
  out `readmark/serve.py`, `readmark/record/**` and the guard itself (`readmark/eval/discipline.py`).
  The check that H-01's `view.json` is byte-identical to the completed live run is unchanged.
- Task-12 (false-alarm round 2) will change the checks. So the guard then has to report "changed
  after the freeze, not held-out" instead of refusing; that is part of Task-12's goal.
- Process slip: Task-11's DONE status went in a separate commit (`f6480bd`), not in its own commit.

**Orchestrator checks on main for Task-10:**
- The A-0142 replay is byte-identical to the committed run.
- `eval --part mutations | ablation | benchmark` and `--part cases --case H-01`, each with `--replay`
  and with no key and no `claude`, leave the tracked files unchanged.
- The first H-01 replay wrote one untracked pin file, `runs/H-01/cache/coverage-input.json` (Task-09's
  coverage pinning). It is stable on a second replay, so it was added to the Task-10 commit.
- A grep for an unquoted policy sentence in the new runs found nothing.

## The evaluation numbers (Task-10)

Every number is from `runs/eval/summary.json`.

**Mutation set** (E-01..E-03, through `readmark.audit.check_claims`):
- Caught 20 of 21 planted errors (n=21).
- False alarms: 1 of 24 correct claims (n=24, in E-03).
- By type, n=3 each:
  - date swap, entity swap, negation, number swap, omission, policy misread: 3 of 3;
  - stale value: 2 of 3 (the miss is in E-01).

**Ablation by layer, on the mutation set** (cumulative):
- Claude alone: 0 of 21. Without a check, every claim stands.
- Plus code checks: 5 of 21.
- Plus Jev's second key: 20 of 21.
- Plus contradiction pairs, plus scan: 20 of 21. Nothing added on this set.

**The files, end to end** (one live run each; required reading capped at 8):

| File | Required reading | Gold pages in required reading | Gold pages flagged anywhere | Gold pages cited by the writer |
|---|---|---|---|---|
| E-01 | 8 | 2 of 4 | 2 of 4 | 4 of 4 |
| E-02 | 8 | 3 of 4 | 3 of 4 | 4 of 4 |
| E-03 | 8 | 3 of 5 | 5 of 5 | 5 of 5 |
| H-01 | 8 | 4 of 8 | 8 of 8 | 8 of 8 |

- The writer cited every gold page in all four files. No gold page was invisible: each one appears as
  cited evidence on the screen.
- On H-01 every gold page is flagged by some layer (8 of 8). The cap of 8 lets 4 of them into
  required reading; the others are in suggested reading.
- Planted traps that the flags touch (from `facts.csv`): E-01 0 of 3, E-02 2 of 4, E-03 5 of 6,
  H-01 3 of 7.

**The held-out run:**
- H-01 ran once. Last code change 15:42:16; run 15:46:01–15:50:06 ACST. No code changed after it.
- Its frozen one-line summary was audited: 14 flags among 105 claims (quote not found 6, checker
  disagrees 4, contradicted 4).
- **Labelled by the orchestrator after the run** (`runs/eval/audit_labels.json`, at Tarık's request):
  - 1 real summary error: "correspondence via Larkhaven only" overstates the form's preferred
    contact;
  - 4 flags point at a real contradiction inside the file: the form says no prior social housing
    tenancy, while the Marigold records and the applicant's declaration show one;
  - 9 false alarms (n=14).
- **Causes of the 9 false alarms:**
  - 5 have a value in the document header or elsewhere in the passage, not in the short quote;
  - 1 is a date range ("21–27 February");
  - 2 are Jev "not enough information" or "contradicts" on true claims;
  - 1 is a suggestion sentence checked as a fact.
- Unflagged claims were not reviewed, so summary errors the audit missed are not counted.
- The demo summary (A-0142) stands at 2 real errors among 22 flags (n=95 claims), labelled by hand
  by the Task-06 builder.

**Riskiest assumption, the plain answer:**
- Required reading stayed at 8 or fewer on every file.
- Planted errors in single claims are caught (20 of 21, with 1 false alarm in 24).
- On the held-out file, half the gold pages are forced and all of them are flagged or cited.
- In an unseen summary, the audit found 1 real error and 1 real inconsistency in the file. 9 of its
  14 flags are false alarms (n=14).
- **Verdict:** the evidence map and the reading gate hold; the summary audit's precision is weak.
- **Tarık's decision:** improve it now (Task-12); test on a new held-out file another time. After
  Task-12, H-01 is no longer held-out, and every report says so.

**Benchmark release:** `data/benchmark/facts.csv` (63 facts), `gold.csv` (40 clause labels),
`mutations.csv` (45 claims), with `DATASHEET.md` updated.

**Live calls:** 11 Claude (`claude -p` opus, made from inside the Codex sandbox) and 736 Jev.

## Task-11, the answer-key screen

What the build does (bee screenshots, plus a Claude screen lens on commit `736daac`):
- The file is the middle of the screen. Each verified quote is highlighted on its page with a
  question label: 42 verified quotes, all marked and labelled.
- Flagged questions come first, each with a reason. On A-0142, 7 of 8 questions are flagged,
  because the 8 required passages touch 7 questions; only Former tenancy folds as clean.
- "Next flag" and "previous flag" reach all 8 required passages in order and wrap.
- The pair comparison shows pages 8 and 23 side by side.
- The summary tab is gone.
- Everything Task-07 did still works: the gate and lock, disputes, the record, exports, and time in
  view (it pauses behind dialogs).

The lens's 10-second answer: "Press the orange Open page 8, paragraph 3 button. It's the next step in
Debts."

| Score | Finding | Outcome |
|---|---|---|
| 80 | A saved dispute reason is squeezed into a 66 px text strip, so words break in the middle (`web/theme.css:186`) | **fixed** by the Codex fix bee: the text is now 204 of 254 px (was 66), the buttons sit on the row below; new test `test_saved_dispute_reason_uses_box_width` failed on the old CSS. The re-check was this test, not a second lens run, to spare the Claude pool |
| 78 | The same question carries different names in the list, the case bar and the sign-off list ("Supporting documents" against "Urgent need documented") | left; first item for the simplification list |
| 58 | "Next flag" stays on one paragraph for 2–3 presses when several labels share it (11 flags, 8 passages) | left |
| 52 | The possibly-missed list closes after one of its passages is opened | left |
| 48 | Optional scan hits use the same tick icon as "Supported" | left |
| 45 | After signing, "Next flag" looks active but is disabled, and picking a question no longer jumps | left |
| 45 | On load, the highlighted paragraph is visible, but the button still says "Open" it | left |
| 40 | A selected outcome chip is nearly unreadable on hover (from Task-07) | left |

## Integration notes
- **Codex bees could not write the git index** (as in waves 1 and 2c). The orchestrator committed
  each lane after checking the diff stayed inside `OWNS`.
- **Locked `.pytest_cache` folders.** Removing the Task-10 worktree failed halfway on a sandbox-locked
  `.pytest_cache`, which left copies of `.env` and H-01 in the folder. The orchestrator deleted
  everything except the locked cache. Main's PDFs, H-01 and `.env` were checked intact.
- **Class fix:** the Codex launchers and `bee-recipes.md` (vault `33809a8`) now set
  `PYTEST_ADDOPTS=-p no:cacheprovider` and `RUFF_NO_CACHE=true`. Two empty locked folders remain,
  `readmark-lanes/task-09/.pytest_cache` and `task-10/.pytest_cache`. They need an admin `takeown`.

## Quota
| When | Claude 5-hour | Claude weekly | Codex 5-hour | Codex weekly |
|---|---|---|---|---|
| 14:54 | 73% | 87% | 10% | 6% |
| 15:48 | 2% | 88% | 30% | 9% |
| 16:20 | 7% | 89% | 36% | 10% |

The wave cost the Claude weekly window 2 points (87% → 89%): 11 opus calls inside Task-10, one
screen lens, and the orchestrator. The Codex 5-hour window took 26 points.

## Awaiting eye check
- **Task-11, the answer-key screen.** Run `uv run python -m readmark serve --case A-0142`, or look
  at `reports/screens/2026-10-03-wave3/task-11-r0-*` (1280 and 1440 wide). Check: a first-time
  viewer names the next step within 10 seconds, and the screen reads as an answer key over the real
  file. The lens's 78 finding (one question, several names) is the first simplification item.

Run state: wave 3's two tasks are on main. Task-12 (false-alarm round 2) waits on Tarık's go and a
Blueprint change: the number and date check would also accept the cited passage and its document
header, not only the quote.
