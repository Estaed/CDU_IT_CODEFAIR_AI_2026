# Task-32: pages one claim cites together reach Jev

Recorded 2026-10-05 by the main loop. Every number carries its n.

## Result

On W-01 the child-presence contradiction T1 is now a pair: under q05 (Allegations and patterns of
behaviour), Jev answers `contradict` at 0.99 for the police narrative (10-p1, screen page 38) and
the candidate's statement (03-p4, screen page 12). The screen shows "Two pages disagree" with a
comparison link. Both pages stay in required reading (ranks 1 and 2). No case lost a pair, a
flag, a required page or an evaluation number.

## What changed, and what was tried first

- **Kept: co-cited pages.** For each question, the pages that one claim cites together are
  compared even when they are outside the top 5 candidates. One passage per page is used (the
  first cited one), and pairs whose two pages are already compared are skipped.
- **Tried and dropped: one candidate slot per page.** On W-01 it freed slots, but H-01 lost its
  planted contradiction p2:3–p12:1. A page's best-scoring paragraph is not always the paragraph
  that conflicts, so slots stay per paragraph. E-03 also lost the p4–p7 pair, which Task-30
  reported as a false alarm. The responses from that attempt were removed from the caches before
  the final runs (175 files set aside; only responses the final code asks for were recorded).
- **Measured before choosing:** at top 5, one slot per page alone catches T1 in no question.
  Top 8 per page catches it, but pairs rise 2–3× (W-01 100 → 273, A-0142 80 → 157).

## Every case (old pairs from Task-30's runs, new pairs asked live by Jev)

| Case | Old pairs unchanged | New pairs | New `contradict`/`updated` |
|---|---|---|---|
| A-0142 | 80 of 80 | 2 | 0 |
| E-01 | 60 of 60 | 1 | 0 |
| E-02 | 41 of 41 | 0 | 0 |
| E-03 | 55 of 55 | 0 | 0 |
| H-01 | 62 of 62 | 2 | 1 (real) |
| stub | 30 of 30 | 0 | 0 |
| W-01 | 100 of 100 | 15 | 1 (real, T1) |

Required reading is unchanged in every case (at most 8, n=8 cap). On W-01 the first two pages
swapped order.

## Every new pair, with Jev's answer and a judgement

| Case | Question | Pages | Jev | p | Judgement |
|---|---|---|---|---|---|
| A-0142 | elig-former-tenancy | p30 / p1 | agree | 0.73 | — |
| A-0142 | prio-category | p34 / p36 | agree | 0.82 | — |
| E-01 | elig-former-tenancy | p7 / p1 | agree | 0.90 | — |
| H-01 | elig-income | p5 / p6 | **updated** | 0.68 | **Real.** Planted stale value (answer key F03/F04): a February 2026 payslip against the July 2026 end of that employment. |
| H-01 | prio-category | p9 / p17 | agree | 0.93 | — |
| W-01 | q04 | 05-p1 / 03-p7 | agree | 0.92 | — |
| W-01 | q04 | 07-p1 / 07-p2 | agree | 1.00 | — |
| W-01 | q05 | 03-p3 / 03-p7 | agree | 0.97 | — |
| W-01 | q05 | 10-p1 / 03-p4 | **contradict** | 0.99 | **Real.** T1, child presence. |
| W-01 | q05 | 10-p1 / 10-p5 | agree | 1.00 | — |
| W-01 | q05 | 20-p1 / 18-p1 | agree | 0.90 | — |
| W-01 | q05 | 20-p1 / 20-p8 | agree | 0.99 | — |
| W-01 | q05 | 20-p8 / 18-p1 | agree | 0.99 | — |
| W-01 | q07 | 02-p3 / 18-p1 | agree | 0.99 | — |
| W-01 | q07 | 12-p1 / 13-p1 | agree | 0.75 | **Missed.** T2, program dates (certificate 14 Feb 2022 against final session 28 Mar 2022). Task-30's direct control called it `contradict`; asked under q07 it reads as agreeing. |
| W-01 | q07 | 12-p1 / 13-p5 | agree | 0.93 | — |
| W-01 | q07 | 13-p1 / 13-p5 | agree | 0.97 | — |
| W-01 | q07 | 13-p1 / 13-p2 | agree | 1.00 | — |
| W-01 | q07 | 23-p1 / 16-p1 | agree | 1.00 | — |
| W-01 | q09 | 04-p1 / 04-p5 | agree | 0.61 | — |

New false alarms: 0 of 20 new pairs (n=20). New real catches: 2. Missed planted pair now asked: 1
(T2).

## Evaluation (regenerated: cases by replay, mutations with cached Claude and live Jev only)

- Mutations: caught 20 of 21 (n=21 errors), false alarms 1 of 24 (n=24 correct controls). Both
  unchanged.
- Case results (gold page coverage, required reading): unchanged for every case.
- Ablation, H-01: at the contradiction-pairs layer, gold page coverage rises from 5/8 to 6/8 (p6,
  the payslip trap). The next layer (scan) fills the cap of 8 and p6 drops out again, so the final
  coverage is unchanged.
- Task-30's relation controls (updated 2/2, contradict 4/4, agree 12/12) are unaffected: the pair
  question and its wording did not change.

## Checks

- `uv run python scripts/gate.py`: exit 0, 315 passed, 8 skipped; `git status` unchanged by it.
- Every case and evaluation part replays byte for byte with no key and no Claude (gate tests).
- New test: pages one claim cites together are paired outside the top five, and a pair already
  asked is not asked twice.
- Screenshots: `reports/screens/2026-10-05-pair-candidates/w01-q05-1280.png` and `-1440.png`.
