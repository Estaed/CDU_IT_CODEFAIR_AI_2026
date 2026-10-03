# otopilot report, 2026-10-03: wave 2 (Task-05..08)

Plan: [otopilot-2026-10-03-wave2-plan.md](otopilot-2026-10-03-wave2-plan.md). BASE_SHA `f6fa15f`
(2a), `961a3d4` (2b). Orchestrator `claude-opus-5-5` (this session). Approved just before 12:24
ACST; wave 2a launched 12:29.

## Outcomes

| Task | Wave | Engine | Outcome | Attempts | Elapsed | Gate (exit) | Main SHA |
|---|---|---|---|---|---|---|---|
| Task-05 | 2a | ultracode Workflow `wf_e58e292b-566`, spec lens | green | 1 (no fix round) | 12:29–12:59 | `uv run python scripts/gate.py` lane (0), main (0: ruff ok, 32 passed, replay smoke stub and A-0142 at schema 2) | `c911a88` |
| Task-08 | 2a | same Workflow, spec lens | green | 1 (no fix round) | 12:29–13:00 | lane (0), main (0: ruff ok, 39 passed, both smokes ok) | `961a3d4` |
| Task-06 | 2b | ultracode Workflow `wf_e04d13ff-b3e`, spec lens | running | | from 13:03 | | |
| Task-07 | 2b | same Workflow, screen lens | running | | from 13:03 | | |

Failure counts: no red attempt in 2a.

**Orchestrator checks on main, beyond the gate** (`.tmp/check_task05.py`, and the eval replay):
- Task-05: `run --case A-0142 --replay` twice with `TYPESAFE_API_KEY` unset and `claude` off PATH:
  byte-identical, and equal to the committed `view.json`. Under Debts the pair
  `A-0142:p8:3`–`A-0142:p23:3` is contradicting (0.58). Required reading 8, suggested 47, no
  passage twice; every passage id the view names has a `sources` entry.
- Task-08: `eval --part checker --replay` twice with no key and no `claude`: `runs/eval/` unchanged.

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

## Needs Tarık's judgement (from the 2a builders and lenses)

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

## Review panel

| Task | Lens | Score | Finding | Outcome |
|---|---|---|---|---|
| Task-05 | spec | 65 | `serve --case A-0142` (README demo command) shows a load error on the old screen: `web/app.js:143` has no `possibly_missed` reason | left; Task-07 replaces the screen this wave |
| Task-05 | spec | 55 | Pair wording tuned after the demo pair returned "agree" | left; item 1 above |
| Task-05 | spec | 35 | Correct March claim marked contradicted | left; item 3 above |
| Task-08 | spec | 52 | Jev's "probability" is the API's `confidence`, and nothing says so | left; item 4 above |

No finding reached 80, so no fix round ran in 2a. The Task-08 lens recomputed every number
independently from the cached verdicts and found them right.

## Quota
| When | Claude 5-hour | Claude weekly |
|---|---|---|
| 12:19 plan | 25% | 82% |
| 13:00 before 2b | — | 84% |

## Integration notes
- A parallel session committed `deed747` (`notes.md`, a home screen moved to *After v1*) and
  `28cafc3` (an HTML view of the wave 1 report) on main during 2a. Neither touches a lane's `OWNS`;
  the cherry-picks applied cleanly on top.
- Lanes were cut with a sparse checkout that leaves out `data/heldout/`; both 2a builders confirmed
  they did not need it.
- 2a worktrees removed (no junctions; files were copied); `data/policies/` on main still holds its
  five PDFs and `policies.lock.json`.
