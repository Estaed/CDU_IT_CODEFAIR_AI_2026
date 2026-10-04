# Task-28: accessibility and delivery notes

Audit date: 4 October 2026. Reference: `design/DESIGN.md` and
`reports/screens/ui-references/mock-6-gov-filepanel.png`. Light mode only.

## Automated accessibility audit

Tool: **axe-core 4.10.3**, run in Chromium through **Playwright 1.63.0** on
Python 3.13.5. The test tool is separate from the app; no application dependency was added.
`tests/audit_accessibility.py` checks the downloaded tool's SHA-256 before using it:
`880970c081707360e64f34cea25ff91892f5bc95675b0776925b9709dd8a68bb`.
The pinned build comes from
[axe-core 4.10.3](https://cdn.jsdelivr.net/npm/axe-core@4.10.3/axe.min.js).

Run `python tests/audit_accessibility.py` with that build saved at
`.tmp/shots/axe-core-4.10.3.min.js`. Findings and Chromium accessibility snapshots are written
to `.tmp/shots/wave13/accessibility.json`. The runner uses only replay data and fixed test
responses, with the model CLI removed from PATH and the server's model key reader disabled.

Tags checked: `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, `wcag22aa`, `best-practice`.

| Surface | Widths | Violations | Serious / critical |
|---|---|---|---|
| Home | 1280, 1440 | 0 on each | 0 / 0 |
| A-0142 with intake note and first-run panel | 1280, 1440 | 0 on each | 0 / 0 |
| A-0142 question, panels closed | 1280, 1440 | 0 on each | 0 / 0 |
| Full-file dialog | 1280, 1440 | 0 on each | 0 / 0 |
| About these checks dialog | 1280, 1440 | 0 on each | 0 / 0 |
| Question-list review, including an unverified sentence | 1280, 1440 | 0 on each | 0 / 0 |

The first five surfaces each have one incomplete **color-contrast** check: axe cannot
classify the `○` character as text. Manual calculation from the stylesheet resolves it:
`#4b6475` on white is **6.22:1**, and on the selected background is **5.83:1**. Both exceed
4.5:1 for text and 3:1 for meaningful graphics. The words “Worth a look” remain beside it.
The question-list review has no incomplete checks.

## Keyboard and accessible names

Direct keyboard input in Chromium exercised **16 actions**: home to case; close and recall
the intake note; dismiss guidance; open and close the full file; select an outcome with
native radio-group arrow keys; save and move to the next question; open and close About;
and edit, check and approve a corrected suggestion at both widths. Tab reached each tested
action, and each tested focused control drew a **3 px solid visible outline**.

The focus colour on white is **6.15:1**, and on the viewer background **5.58:1**. The white
mark on the header is **14.11:1**. The flag text on its warning box is **4.87:1**.
The existing palette regression also checks all **26 text/background pairs** against 4.5:1.

Chromium accessibility snapshots expose named buttons, labelled search and editing fields,
the “Is this question met?” radio group, descriptive dialog names, and a receiving-officer
intake-note heading. Decorative icons are hidden from assistive technology; statuses retain
their words. Native Escape closes the dialogs. No outcome is selected when a case opens.

## Changes made

- Added an SVG marked-page service mark and favicon, with no government insignia.
- Added document icons; kept the existing flagged, checked and opened icons with their words.
- Used definition-list rows for case facts and inset boxes for explanatory copy.
- Added a closable, recallable intake note with keyboard focus returned to the search field.
- Made disabled approval look disabled and explain how to correct an unverified sentence.
- Preserved focus when suggestion checking, approval or rejection redraws the review.
- Put review content inside one named main landmark and the case identity inside a named region.
- Fixed singular page wording and consolidated repeated paragraph tags without losing quote,
  claim or navigation targets. The full-file link no longer breaks its arrow onto a second line.

## Limits and outstanding review

No known axe violations remain on the tested surfaces. This is evidence for those states,
not a claim of complete WCAG conformance. A native screen reader such as NVDA was not run;
accessible names were checked through Chromium's accessibility tree. W-01 has no run or
question list in Task-28, so its rendered pages require the Task-29 check.

**Eye check remains Tarık's:** open A-0142 and judge whether its intake note can be understood
in under ten seconds, hints at no outcome, and fits the sober government reference.
The delivered home, intake-note and question screenshots at both widths are in
`reports/screens/2026-10-05-wave13/`; tests produce them under `.tmp/shots/wave13/` first.

## Data and contract notes

W-01's `data/cases/W-01/intake-note.json` contains the `intake_note` field. The screen requests
`/api/intake-note?case=<id>`; the server reads that file independently of the frozen view.
Missing metadata hides the panel; unavailable metadata shows a closable notice and leaves
review usable. The browser remembers dismissal per case and offers **Intake note** to reopen it.

**Lane conflict:** the task asks for A-0142's note in its case folder but explicitly forbids
writing anywhere under `data/cases/A-0142/`. No permission to extend that Lane was received.
Its exact requested note therefore lives at `web/case-notes/A-0142/intake-note.json`, through
the same generic companion-folder fallback. A-0142's source folder and replay remain unchanged.
Moving that one metadata file into the native case folder requires the main loop's decision.

Home's API admits only `A-0142`, `W-01` and ready officer uploads (`U-*`). A showcase without
`view.json` is absent. E-01..E-03, H-01 and stub remain directly addressable and in the
evaluation case set; no evaluation or analysis code was changed. The old CDU list, S-01 and
the CDU fetch script were deleted after verifying identical originals in the main checkout
(129 files). No local U-* cases were present. Dated reports remain history.

Task-29 integration must also retain a compatible case source and replay identities:
the current ingest defaults to `case.md` for committed cases, while browser uploads use
`case.json` and U-* passage ids. Moving an upload's run directory alone is insufficient.
This is an integration constraint for Task-29, not a W-01 run made in this task.

The two rule PDFs were downloaded from the official NT site with a browser User-Agent and
matched the supplied originals. Pins are in `data/policies/nt-wwcc/policies.lock.json`:

| Rule PDF | SHA-256 |
|---|---|
| `care-and-protection-of-children-act-2007.pdf` | `05c617e071490a3ca606c4c6da1bfbd2870c3c9757a2acbb7823d8ad139b2950` |
| `care-and-protection-of-children-screening-regulations-2010.pdf` | `27e652e994236e8b785775ddb4c55bea5d926b9722bef319f7d4c23cf17e3e05` |

The Act pin is the supplied version as in force at 31 August 2026 (201 PDF pages); the
Regulations pin is as in force at 25 March 2024 (15 PDF pages). The application is 24 PDFs,
104 pages. Rule PDFs remain ignored; only their lock is selected for staging.

## Existing test assertions changed or removed

- `test_home.py`: two discovery expectations now intersect ready views with A-0142/W-01;
  the expectation that evaluation rows are visible becomes an assertion that the evaluation
  group is absent. The E-02 isolation flow asserts its home row is absent and opens it directly.
  The coverage loop drops CDU; its two Procedure (74)/(78) heading assertions are removed.
  The foreign-policy and missing-paragraph 404 assertions now use the retained housing list.
- `test_coverage.py`: removed the CDU parameter and its Procedure (74)/(78) membership
  assertion. Housing replay, verified excerpts and thresholds remain checked.
- `test_screen.py`: removed S-01's “at most two flags” assertion with that retired case.
  Next-flag expectations now expand every flagged target carried by each consolidated tag;
  the same visited-set, rank and visibility assertions remain. The comparison setup waits
  for the deliberately opened page's short clock to settle; no comparison assertion was removed.
- `test_search.py`: replaced S-01 search-prefix assertions with E-02 case isolation; the CDU
  policy-prefix assertion becomes an assertion that no A-0142 passage leaked. The foreign
  passage 404 and wrong-case record 422 checks now use retained case ids.
- `test_upload.py`: removed S-01 from the assertion that committed run views are not ignored.
- `test_eval_cases.py`: byte equality for case scores and summary becomes exact JSON equality
  with one checked exception: H-01's `changed_result_files` may lose precisely the two deleted
  CDU source paths. Every other field, number and denominator stays equal; other evaluation
  artifacts and all case stage files remain byte-for-byte checked.
- `test_checklist.py`: comment only; no assertion changed.
- `test_generate_list.py`: added focus-preservation assertions; no existing assertion changed
  or removed. Screenshot filters mentioning S-01 now use W-01 where applicable.

`test_polish.py` adds checks for ready-showcase discovery, hidden evaluation access, future
W-01 discovery using a temporary view, the supplied document/page counts and pins, safe rule
download failure, note dismissal/recall/unavailability, and consolidated quote targets.

The first local test attempt could not access Windows' shared pytest temp directory. Subsequent
runs use worktree-local TEMP/TMP and PYTEST_DEBUG_TEMPROOT. `PYTEST_ADDOPTS` remains exactly
`-p no:cacheprovider`. The first `uv run` attempt was blocked by its shared cache. The final
run used worktree-local `UV_CACHE_DIR` and `UV_NO_SYNC=true` with the ready virtual environment.

Final `uv run python scripts/gate.py`: **exit 0**, Ruff clean, **254 passed, 8 skipped**
in 379.93 seconds, followed by successful stub and A-0142 replay/schema checks: **GATE CLEAN**.
The earlier direct-venv gate also passed (254 passed, 8 skipped in 380.20 seconds).
Hash snapshots of all eleven source/data/report roots were identical immediately before and
after the final gate. Protected input/replay files and the committed evaluation summary remain
unchanged; the isolated evaluation regression checks every number with only the documented
H-01 retired-file exception. No model calls were made.

The final standalone axe/keyboard audit exited 0. The rule fetch exited 0 and matched both
pins. All 26 copied application/answer-key files match their supplied originals byte for byte;
W-01 still has neither a question list nor a run. The six delivered PNGs were copied once
from the test output and verified byte for byte.

Staging was attempted only for owned paths. `git add -A -- <owned paths>` exited 1:
`fatal: Unable to create 'D:/Charles Darwin University/6 - Year 2 - Semester 2/CODE IT FAIR 2026/AI Challenge 2026/.git/worktrees/task-28/index.lock': Permission denied`.
No commit was attempted because staging failed. The main loop can stage and commit the
working-tree changes; the bee did not request writes outside its worktree.
