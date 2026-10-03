# otopilot report, 2026-10-03: wave 2 (Task-05..09)

Plan: [otopilot-2026-10-03-wave2-plan.md](otopilot-2026-10-03-wave2-plan.md). BASE_SHA `f6fa15f`
(2a), `961a3d4` (2b). Orchestrator `claude-opus-5-5` (this session). Approved just before 12:24
ACST; wave 2a launched 12:29.

## Outcomes

| Task | Wave | Engine | Outcome | Attempts | Elapsed | Gate (exit) | Main SHA |
|---|---|---|---|---|---|---|---|
| Task-05 | 2a | ultracode Workflow `wf_e58e292b-566`, spec lens | green | 1 (no fix round) | 12:29–12:59 | `uv run python scripts/gate.py` lane (0), main (0: ruff ok, 32 passed, replay smoke stub and A-0142 at schema 2) | `c911a88` |
| Task-08 | 2a | same Workflow, spec lens | green | 1 (no fix round) | 12:29–13:00 | lane (0), main (0: ruff ok, 39 passed, both smokes ok) | `961a3d4` |
| Task-06 | 2b | ultracode Workflow `wf_e04d13ff-b3e`, spec lens | green | 1 (no fix round) | 13:03–14:06 | lane (0), main (0: ruff ok, 49 passed, both smokes ok) | `337aff2` |
| Task-07 | 2b | same Workflow, screen lens, 1 fix round; attempt 2 `wf_3c54762c-ada`, screen lens | green on attempt 2, eye check pending: 1 | 2 | 13:03–14:07; attempt 2 14:10–14:26 | attempt 1: lane (0: 43 passed); main after Task-06 (1: 2 failed, 51 passed); pick reverted in `67411ba`. Attempt 2: lane (0: 44 passed), main (0: 54 passed) | `4faaeb4` |
| Task-09 | 2c | Codex bee `gpt-6.1-sol`/`high`, network on (added by Tarık at 14:20) | green | 1 | 14:28–14:50 | bee: gate 0 (60 passed); orchestrator: lane (0: 60 passed), main (0: 60 passed) | `ee086e1` |

Failure counts: Task-07 `0 -> 2` (lane gate 0 fail, main gate 2 fail:
`test_guided_review_flow_on_a0142[1280]` and `[1440]`). The flow test expected A-0142's audit tab
to say "No summary was audited" (`tests/test_screen.py:324`); Task-06, landed just before, gave
A-0142 its real audit block. The pick was undone with `git revert` (the vault's git hook blocks
`reset --hard` while another session is open in the folder). Attempt 2 runs in the same worktree
with the full main gate output: it makes the tests follow the data and checks the real block in
an integration preview (main's HEAD without `data/heldout`, plus the lane's screen files).

**Orchestrator checks on main, beyond the gate** (`.tmp/check_task05.py`, and the eval replay):
- Task-05: `run --case A-0142 --replay` twice with `TYPESAFE_API_KEY` unset and `claude` off PATH:
  byte-identical, and equal to the committed `view.json`. Under Debts the pair
  `A-0142:p8:3`–`A-0142:p23:3` is contradicting (0.58). Required reading 8, suggested 47, no
  passage twice; every passage id the view names has a `sources` entry.
- Task-08: `eval --part checker --replay` twice with no key and no `claude`: `runs/eval/` unchanged.

- Task-06: the same replay check on main: byte-identical with no key and no `claude`. One
  `summary-*` file in the cache; audit 95 claims, 44 sentences, 9 omitted.
- Task-09: the same replay check: byte-identical. Audit after the fix: supported 73,
  quote not found 11, checker disagrees 11, contradicted 0 (n=95). The two real errors (a36, a47)
  are still `checker_disagrees`. The March "debt cleared" map claim (c15) is now `supported`.

## What 2c produced (Task-09, Codex `gpt-6.1-sol`)
- **Audit flags 28 → 22** (n=95 claims):
  - contradicted 4 → 0;
  - quote not found 13 → 11;
  - checker disagrees 11 → 11.
- Why only 2 of the 13 quote-not-found went away: the bee says the remaining failures are honest.
  The date or reference really is not in the frozen quote, or zero is written in words. It did not
  change the locator to manufacture citations.
- **The pair rule:** a claim that cites one side of a pair is now checked by Jev against the other
  side. The pair itself stays under Debts (0.58), and both passages stay required.
- **Possibly missed:** prio-documentation 28 → 25 and prio-category 19 → 18. The other clauses are
  unchanged (n=357 passages scanned). The duplicate rule is conservative (a binary duplicate
  probability of at least 0.9), so the lists stay long.
- **Required reading** is still 8. p23:2 left and p51:5 (the support-agency letter, a gold page)
  came in, so 3 of the 5 gold required pages are now required (p8, p23, p51; n=5).
- **Cost:** 24 new Jev calls and 0 Claude calls. All 358 original cache files keep their SHA-256.
  To keep the coverage request byte-identical, the bee pinned its original candidate ids in
  `runs/A-0142/cache/coverage-input.json`. The "left out" list is therefore computed against the
  pre-Task-09 candidates.
- **Screen tests:** 4 assertions in `tests/test_screen.py` changed (lines 280, 311–313), all values
  pinned to A-0142's data. The intro's flagged example is now "Checker disagrees". The March claim
  is now "Supported" with "the second checker agrees".
- **Integration:** the Codex sandbox could not write the worktree's git index (as in wave 1), so
  the orchestrator made the single commit after checking the diff stayed inside `OWNS`. The bee
  had also written two report files under `runs/A-0142/` that are not stage files; they were left
  out of the commit (kept in `readmark-lanes/logs/task-09-bee-report.md`).

## What 2a produced

**Task-05 (A-0142, live once):**
- 34 claims: 30 supported, 2 contradicted, 2 checker disagrees.
- Required reading (8):
  - p8:3 and p23:3, the ledger pair;
  - p23:2;
  - p34:4 and p16:1, where the checker disagrees;
  - p4:1, p19:3 and p56:1, possibly missed.
- Threshold 1.76 on Jev's 0–4 scale. Rule: the highest threshold at which every gold required page
  of A-0142 still has a passage at or above it. The page that sets it is p23 (1.76).
- Gold coverage: required reading covers 2 of the 5 gold required pages (p8, p23; n=5). All 5 are
  in required plus suggested.
- Cost: 1 writer call (`claude -p` opus, 62 s), about 394 Jev calls including about 71 probe calls.

**Task-08 (SummEdits, n=300):**
- Sample: 10 domains × 15 consistent and 15 inconsistent pairs, seed 20261003; CC BY 4.0 per the
  Hugging Face card (`Salesforce/summedits`, revision `ce0c479a`).
- Balanced accuracy:
  - Claude as checker (`claude-opus-5-5`): 0.85;
  - Jev (`jev-1.13.0`): 0.827. Jev's recall on inconsistent summaries is only 0.687 (n=150); its
    main error is a confident "supports".
- Jev two-run agreement: 296/300 (0.987).
- Suggested unsure band for Jev: below 0.8. Calls below it are right 0.655 of the time (n=55);
  calls at or above it, 0.865 (n=245).
- Cost: 30 `claude -p` opus calls (10 pairs each), 600 Jev calls.

**Task-07 attempt 2:** only `tests/test_screen.py` changed. A new helper checks the audit tab in
both states: no audit, and a real audit. No assertion about behaviour was relaxed (the screen lens
checked the diff). The builder ran the gate in an integration preview: main with Task-06's real
block, no `data/heldout`, its own files laid on top. It exited 0 with 54 passed. On the real block:
all 44 sentences present, "17 of 44 sentences flagged", no console errors, no overflow.

Left for the polish wave:
- The audit tab is very long (about 40,000 px at 1440) because all 95 claims are shown expanded.
- The summary's markdown shows as raw characters.
- A sentence with a single claim hides that claim, so its reason names figures that are not in the
  sentence (screen lens, 70).

## What 2b produced

**Task-06, the summary under audit (A-0142):**
- The frozen summary: `claude-opus-5-5`, prompt "Summarise this file.", 2026-10-03, 44 sentences.
  The call ran in an empty temp folder with no tools, CLAUDE.md or hooks. A live run refuses to
  make a second summary. On main there is one `summary-*` file in the cache.
- Audit: 95 claims. Supported 67, quote not found 13, checker disagrees 11, contradicted 4.
  Left out: 9 of the 23 map claims considered. Required reading is unchanged at 8.
- **Real errors found: 2 of 28 flags** (the builder checked every flag by hand):
  1. The heading "Eligibility evidence (verified)" overstates: current income evidence never came
     (p48:1, p58:1). Jev: contradicts, 0.96.
  2. "All contact goes through the support worker" overstates p46:1 and p1:1. Jev: contradicts,
     0.59.
- The summary got the main trap right: the January $2,400 is cleared and superseded.
- **Why the other 26 are false alarms:**
  - 13 quote-not-found: the date check (Task-05's) cannot match "15 Mar" or "January 2026"
    against "2026-03-15", nor "A-0142" against "A0142". The same weakness hits the evidence map.
  - 4 contradicted: true ledger-history claims, flagged by the pair rule.
  - 9 of the 11 checker-disagrees: Jev said "not enough information" on true or opinion claims.
- Reusable claim path for wave 3: `readmark.audit.check_claims(case_id, claims, ...)`.
- Cost: 4 opus calls ($1.03 list) and 95 Jev calls. **The builder's own mistake:** in its first
  version, a test run on A-0142 audited by default, so 4 extra full audit runs went live (about
  $4 list). Nothing from them was committed. It is fixed, with a test that fails on any Claude call
  in such a run.

## Needs Tarık's judgement (from the builders and lenses)

1. **The pair question was reworded after the demo pair failed (Task-05, lens score 55).**
   - The acceptance said: if Jev does not call p.8/p.23 contradictory, stop and report.
   - With the first neutral wording, Jev said "agree" (0.85). The builder then tried 4 more
     wordings on this pair plus 12 control pairs. It kept the generic one, "does either passage
     show that a fact stated in the other is wrong or out of date".
   - With it, all 12 controls stay "agree" and the demo pair is "contradict" at 0.58.
   - Nothing names the pair in code, so it is not special-casing. It is wording chosen on the demo
     pair, and 0.58 is borderline: a fresh live run could flip, while the replay is fixed.
   - The held-out file, never seen by any builder, is the honest test of this wording.
2. **Possibly-missed lists are long.** The low threshold gives up to 28 passages under
   `prio-documentation` and 19 under `prio-category`. The notes' "deduplicated by fact" was not in
   the task and was not built, so neighbouring paragraphs that restate a cited fact take required
   slots (p56:1, p19:3).
3. **A correct claim shows "contradicted".** The March "debt cleared" claim cites one side of the
   pair, so it is also marked contradicted. This is per the task text; Task-07's brief asks the
   screen to say which passage disagrees, in plain words.
4. **The Jev unsure band rule was changed after seeing the data.**
   - The first rule returned an empty band. The disclosure is in `checker.json` and the README.
   - The calibration bins Jev's `confidence`, not its class probability (lens score 52). The report
     should say so.
   - Jev's separate "supports" score separates the labels better: AUC 0.899, balanced accuracy 0.857
     at 0.3 (n=300). This is an option for after v1.
5. **SAMSum licence caveat.** The SummEdits samsum documents come from SAMSum, which a mirror card
   lists as CC BY-NC-ND 4.0. Our use is non-commercial and attributed.
6. **The riskiest assumption's first signal is weak precision (Task-06).** The audit found 2 real
   errors, but 26 of its 28 flags were false (n=95 claims). Most come from two fixable causes,
   the date format check and the pair rule. A fix before the evaluation wave would move the frozen
   numbers, so it has to be decided before 7 Oct. **Decided by Tarık at 14:20: fixed in Task-09**
   (28 → 22 flags; the remaining quote failures are honest; checker-disagrees is unchanged at 11).
7. **"Left out of the summary" overstates (Task-06 lens, 50).** The coverage call marks a fact as
   left out when the summary gives the core but not every detail (c21, c02).
8. **Three cosmetic sentence-split defects** in the frozen summary: literal `**` in s27, and two
   merged sentences. Cleaning them takes one new split and locate call (about $0.72 list); the
   summary itself stays frozen.

## Review panel

| Task | Lens | Score | Finding | Outcome |
|---|---|---|---|---|
| Task-05 | spec | 65 | `serve --case A-0142` (README demo command) shows a load error on the old screen: `web/app.js:143` has no `possibly_missed` reason | left; Task-07 replaces the screen this wave |
| Task-05 | spec | 55 | Pair wording tuned after the demo pair returned "agree" | left; item 1 above |
| Task-05 | spec | 35 | Correct March claim marked contradicted | left; item 3 above |
| Task-08 | spec | 52 | Jev's "probability" is the API's `confidence`, and nothing says so | left; item 4 above |
| Task-06 | spec | 60 | Most flags on the real summary are false alarms | left; item 6 above |
| Task-06 | spec | 50 | Some "left out" entries are facts the summary states | left; item 7 above |
| Task-06 | spec | 45 | Sentence s27 keeps literal `**` | left; item 8 above |
| Task-07 | screen | 88 | Audit tab on A-0142 with no audit block opened with a 335 px empty band, tabs jumped down (`web/theme.css:89`) | **fixed** in round 1 (`grid-template-rows: auto auto 1fr`; regression test failed on the old CSS); re-review clean |
| Task-07 | screen | 62 | On the audit tab, a contradicted summary sentence gets "not that this claim is false", wording meant for the correct map claim (`web/app.js:237`) | left; with the real block the 4 contradicted audit claims are true ledger claims, so the wording holds there |
| Task-07 | screen | 50 | First-run panel says "Code found every quote in its passage" as fixed text | left |
| Task-07 | screen | 45 | Debts lists the same two passages in "Open before you sign" and in "Passages that disagree" before any evidence | left |
| Task-07 | screen | 30 | JSON record mixes UTC and +09:30 (the HTML export uses one zone, as accepted) | left |
| Task-07 a2 | screen | 70 | On the audit tab, a sentence with one claim hides that claim, so its reason names figures not in the sentence (`web/app.js:610`) | left; polish wave |
| Task-07 a2 | screen | 45 | Source pane says "no claim uses it", then lists a summary claim resting on that passage | left |

Task-09 (a Codex bee) had no review panel: otopilot's lenses are part of the ultracode engine.
Its gate ran in the lane and on main, and the orchestrator checked the replay on main.

No finding reached 80 in 2a, so no fix round ran there. The Task-07 lens's 10-second answer
(first-time viewer): "Open page 16, paragraph 1, in the Residency clause", read from the
next-step button. It passes the Blueprint check; with the intro open, the clause content starts
below the fold at 1280×800. The Task-08 lens recomputed every number
independently from the cached verdicts and found them right.

## Quota
| When | Claude 5-hour | Claude weekly |
|---|---|---|
| 12:19 plan | 25% | 82% |
| 13:00 before 2b | — | 84% |
| 14:09 before Task-07 attempt 2 | — | 87% |
| 14:54 close | 73% | 87% |

Codex (Task-09): 5-hour 0% → 10%, weekly 5% → 6%. The whole run moved the Claude weekly window
82% → 87%, inside the plan's 4–8 point estimate.

## Awaiting eye check
- **Task-07, the review screen (layout B).** Run `uv run python -m readmark serve --case A-0142`
  and open the printed address, or look at `reports/screens/2026-10-03-wave2/task-07-r1-*` and
  `task-07-a2-r1-*` (1280 and 1440 wide). Check: a first-time viewer names the next step within 10
  seconds. The layout should match Blueprint → Decisions (layout B), with the look of design A.
  Once you approve it, its screenshots go to `design/screens/` (Blueprint → Verification).
- **Task-00's `readmark/checklist/clauses.yaml`** (from wave 1): the eight clauses read right.

## Integration notes
- A parallel session committed `deed747` (`notes.md`, a home screen moved to *After v1*) and
  `28cafc3` (an HTML view of the wave 1 report) on main during 2a. Neither touches a lane's `OWNS`;
  the cherry-picks applied cleanly on top.
- Lanes were cut with a sparse checkout that leaves out `data/heldout/`; both 2a builders confirmed
  they did not need it.
- 2a worktrees removed (no junctions; files were copied); `data/policies/` on main still holds its
  five PDFs and `policies.lock.json`.
- Cleanup at close: all five run worktrees are unregistered (`git worktree list` shows only main).
  One folder is left: `readmark-lanes/task-09/.pytest_cache`. The Codex sandbox created it with an
  ACL this session cannot read or delete (`Access is denied`). It is outside the repo and harmless.
  It goes with `takeown /f <dir> /r /d y` and then `rd /s /q` from an admin prompt. Logged with
  `gardener.py`.
- Two orchestrator lessons, written down in the vault: a `plan-wave` line (parallel tasks that
  share data say their tests follow it in both states), and the calibration log.
- Wake lock released at close by its stop file.

Run closed: tasks consumed
