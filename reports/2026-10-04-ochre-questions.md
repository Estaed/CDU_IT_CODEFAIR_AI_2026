# Task-29: the Ochre Card case, W-01, from rules to a replayable run

Recorded 2026-10-05 (Darwin) by the main loop. Tarık did part 1 on the website; the main loop
made it part of the submission. Every number carries its n.

## What was done

- **Questions from the rules (Tarık, website).** He uploaded the Care and Protection of Children
  Act 2007 (201 pages) and the Screening Regulations 2010 (15 pages) with the scope sentence from
  the task. Claude suggested 10 questions. Tarık approved all 10. Two bugs in this flow were fixed
  on the way: a genuine blank page rejected the rules (410eaad), and a 104-page upload overflowed
  Jev's dedup call (82fa0c1).
- **The list is committed** as `readmark/checklist/lists/nt-wwcc/`. Its rule PDFs point at the
  git-ignored `data/policies/nt-wwcc/`, with pins from its lock file. The uploaded files matched
  those pins by SHA-256. Policy keys were renamed `act` and `regulations`, and titles were added;
  questions and sentences are unchanged. Coverage was run live and replays byte for byte: 0
  uncovered rules (n=2,247 paragraphs scanned).
- **W-01 ran once live under its own id** after Task-30 and Task-31 (Tarık's order).
  `data/cases/W-01/case.json` points at the 24 PDFs already in that folder, and
  `question-list.json` selects `nt-wwcc`. Document dates, transcription, the writer, Jev and the
  gate took 572 s. `readmark run --case W-01 --replay`, with no key and no `claude` on PATH,
  reproduced all 10 stage files byte for byte.
- The website copies (`U-*` uploads and runs, the three draft lists) were moved out of the app to
  `.tmp/removed-uploads/`. Home lists exactly A-0142 and W-01.

## Measurements (final run, `runs/W-01/view.json`)

| Measure | Result |
|---|---|
| Answer-key clause_ids covered by an approved question | 10 of 10 (n=10; mapping by the main loop, not code) |
| Suggestions failing the sentence check | 0 of 10 (n=10); none rejected |
| Required reading | 8 passages (cap 8) |
| Suggested reading | 78 passages (289 in the pre-30/31 upload) |
| Claims | 61: 59 supported, 2 checker disagrees, 0 quote not found (n=61) |
| Contradiction pairs | 1 (q06: 02-p4 with 10-p3) |
| Documents dated by Task-31 | 15 of 24 (n=24) |
| Answer-key decisive pages cited by a claim | 33 of 39 (n=39); 6 of them required |

**Clause mapping.** id-100-points → q09; disqualifying-offence → q02; whole-history → q01;
nature-gravity, relevance-to-work, victim-age and time-elapsed → q04 (q10 also for relevance);
alleged-and-pattern → q05; orders-and-agency → q06; form-complete → q08. q04 carries four
answer-key clauses in one question.

**Flags per question** (a passage can serve several questions, so the required counts sum to
more than 8):

| Question | Claims | Not supported | Pairs | Required | Suggested |
|---|---|---|---|---|---|
| q01 Prescribed conviction or criminal history | 4 | 0 | 0 | 5 | 23 |
| q02 Disqualifying offence | 2 | 0 | 0 | 4 | 6 |
| q03 Expunged charges | 1 | 0 | 0 | 2 | 4 |
| q04 Nature, gravity, relevance and age | 9 | 0 | 0 | 5 | 18 |
| q05 Allegations and patterns of behaviour | 10 | 1 | 0 | 5 | 28 |
| q06 Agency engagement and protective orders | 5 | 0 | 1 | 5 | 20 |
| q07 Unacceptable risk finding | 11 | 0 | 0 | 5 | 29 |
| q08 Application form, identity, authorisations | 4 | 0 | 0 | 4 | 11 |
| q09 100-point identity documents | 8 | 1 | 0 | 1 | 8 |
| q10 Child-related work | 3 | 0 | 0 | 3 | 40 |
| other (not on the checklist) | 4 | 0 | 0 | 0 | 7 |

## The two traps the pitch relies on

- **T1, child presence (03-p4 against 10-p1): flagged, both pages required (ranks 1 and 2).**
  Claude wrote it as claim c21: the candidate says the daughter was at her grandmother's, which
  contradicts the police narrative. Both quotes are verified. Jev's claim check scored it
  `contradicts` (supports 0.37), so it shows as "Checker disagrees". **Jev's pair scan did not
  pair 03-p4 with 10-p1**, so the screen does not say "Two pages disagree" here. Saying "Jev flags
  the contradiction" is true of the officer's reading list, but not of the pair warning.
- **T3, Katherine address omission (02-p2 against 21-p1 and 22-p1): flagged as a claim, not
  required.** Claim c67 (under "Not on the checklist") states that the form lists no other address
  while the tenancy ledger and bank statements show Katherine from June 2022. Its four quotes are
  verified and supported. None of the three pages is in required reading. q08 (form complete) did
  not carry it.

## Gaps reported (no code change in this task)

1. **"Quote not found" also labels a claim value missing from a found quote.** This did not occur
   in this run (0 of 61), but the pre-30/31 upload had 3 of 8 required passages labelled this way
   (c20 "March 2021", c47 "over 18") although their quotes were in the file.
2. **T3 sits under "Not on the checklist", not under q08.** The officer meets it only by opening
   that group.
3. **Suggested reading is large for broad questions:** q10 alone suggests 40 passages (78 in
   total, n=104 pages).
