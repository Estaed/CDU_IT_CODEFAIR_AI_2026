# Tasks index

Wave 1 (2026-10-03). Task-00, Task-01 and Task-03 can run in parallel. Task-02 waits for Task-01's
validator.

- [x] Task-00: Thinnest end-to-end path, from a stub case to a signed decision record (codex)
- [x] Task-01: Grounded synthetic case files: demo A-0142 plus three short evaluation files (codex)
- [x] Task-02: Held-out case H-01, written blind (codex)
- [x] Task-03: Design A/B, Tarik Base against a blind direction (main-loop)
- [x] Task-04: Rewrite the Task-01 case files as real paperwork, and make the validator catch it (codex)

Wave 2 (2026-10-03). Width 2: Task-05 and Task-08 start together; Task-06 and Task-07 wait for
Task-05 (both build on its schema-2 `view.json` and the A-0142 run), then run together.

- [x] Task-05: Cross-passage checks on the real demo file: contradiction pairs, relevance scan, possibly missed (codex)
- [x] Task-06: Summary under audit on the demo file (codex)
- [x] Task-07: Guided review screen, layout B (codex)
- [x] Task-08: Checker evaluation: Jev against Claude on SummEdits (codex)
- [x] Task-09: Cut the checks' false alarms: dates, the pair rule, possibly-missed duplicates (codex, gpt-6.1-sol; after Task-07)

Wave 3 (2026-10-03). Width 2: Task-10 and Task-11 run together (disjoint OWNS, no dependency). Both on Codex `gpt-6.1-sol` at Tarik's request.

- [x] Task-10: The evaluation: mutation set, held-out file, ablation, benchmark release (codex)
- [x] Task-11: Review screen as an answer key: the file itself, highlighted by question (codex)

Wave 4 (2026-10-03). Width 2: Task-12 and Task-13 run together (disjoint OWNS). Codex `gpt-6.1-sol`.

- [x] Task-12: False alarms, round 2: values in the passage, date ranges, suggestions; H-01 after changes (codex)
- [x] Task-13: Light by default, wait-time context on the case header, a cleaner record (codex)

Wave 5 (2026-10-03). Width 1.

- [x] Task-14: Jev's "supports" score as a second signal for "checker disagrees" (codex)

Wave 6 (2026-10-03). Width 1: one feature, the final look.

- [x] Task-15: The final look: a government question page with the file inside it (codex)

- [x] Task-16: Polish the final look: four small screen fixes (codex)

Waves 7–10 (2026-10-03 → 6 Oct): everything before submission. Wave 7 width 2; wave 8 width 2; waves 9, 10 width 1.

- [x] Task-17: Plain AI notes, and the usability fixes (codex)
- [x] Task-18: Question lists: each list brings its own policies and questions (codex)
- [x] Task-19: Case home screen: cases in progress and completed (codex)
- [x] Task-20: New case: upload several documents and run the checks live (codex)
- [x] Task-21: The easy example: a student's assessment extension under the real CDU rule (main-loop)
- [x] Task-22: Scanned pages: Claude reads the page image, and the image stays beside the text (codex)
- [x] Task-23: Search within a case: words always, meaning through Jev when online (codex)
- [x] Task-24: The case screen speaks its question list's language (codex)
- [x] Task-25: A calmer tier for "possibly missed": flags for problems, "worth a look" for unused pages (codex)
- [x] Task-26: Question-list coverage: Jev shows decisive policy rules no question covers (codex)

Wave 12 (2026-10-04). Width 1.

- [ ] Task-27: Questions from the rules: Claude suggests, a person approves each one (codex)

Wave 13 (2026-10-04). Width 1. No Claude calls (split on 4 Oct).

- [x] Task-28: Two showcase cases (housing, Ochre Card), an intake note, and a polish pass (codex), eye check pending: 1

Wave 14 (2026-10-04). By hand on the website, after the Claude reset; not for otopilot.

- [ ] Task-29: The Ochre Card case live on the website: questions from the rules, then the file (main-loop)

Wave 15 (2026-10-04). Width 1.

- [x] Task-30: Jev tells a record that was updated from two records that disagree (codex), eye check pending: 1

Wave 16 (2026-10-04). Width 1. After Task-30.

- [x] Task-31: Uploaded documents get their date, read by Claude and checked by code (codex)
