# Task-31: verified uploaded-document dates

No live Claude call was made. W-01's 24 committed PDFs were read in place. All model answers
below came from a fake at `readmark.writer.claude_cli.generate`, the transcription tests' seam.
These results measure code verification, not Claude's ability to choose the correct document date.

## Which date counts

The prompt asks when the document was issued, signed or printed: when the record was made,
never a birth, expiry, historical event or period it describes. A 2025 police history describing
a 2021 charge is dated 2025. An explicit reissue or revised-record date can count; a mere copy
or forwarding date does not update the source record. Multiple source dates without a clear
whole-document date, missing components and ambiguous dates must produce null.

Code independently requires a nonempty quote found in that document's own extracted or
transcribed text through `readmark.checks.quote_present` (whitespace collapsed, case kept).
The returned date must be a valid, complete ISO calendar date. `values_missing` checks ISO and
day/month-name/year spellings as whole dates; the dater also accepts full month-first dates and
unambiguous numeric dates. For example, 25/09/2026 is readable; 03/04/2026 is rejected rather than
guessing a day/month order. Digits in unrelated numbers and missing day/year components cannot
supply a date. A missing, malformed or rejected answer stores both `doc_date` and `date_quote`
as null, and preparation continues. Presence checks cannot tell whether a real quoted date is
an event date; selecting the right role remains Claude's job and needs the live check.

## W-01 measurement

`test_w01_code_check_matrix_and_cli_replay` runs the PDF-folder command for each answer type,
with a separate response cache. It then forbids the model and replays every response.

| Fake answer | Documents (n) | Dates accepted | Documents left undated |
|---|---:|---:|---:|
| Full date with a real contextual quote | 24 | 24 | 0 |
| Correct date with an invented quote | 24 | 0 | 24 |
| 2099-12-31 with a real quote containing another date | 24 | 0 | 24 |
| Null date, empty quote | 24 | 0 | 24 |

There were 96 fake model calls (n=24 PDFs × 4 answer types). All 96 responses replayed with
zero further model calls and identical output. Every missing or rejected response completed
the command successfully. The positive fixtures are deliberately supplied examples, not
claimed live answers or a gold key for dates of bundles and reissued records.

| PDF | Positive fixture date | Verified fixture quote |
|---|---|---|
| 01-safe-nt-covering-email.pdf | 2026-09-22 | Sent: 22 September 2026, 09:16 ACST |
| 02-application-form.pdf | 2026-09-21 | Lodgement date: 21 September 2026 |
| 03-candidate-personal-statement.pdf | 2026-09-28 | Statement signed 28 September 2026, supplied with my application. |
| 04-identity-certified-copy-bundle.pdf | 2026-09-18 | certification  signature  is  also  fictional.  Prepared  by  Amity  Vale,  document-copy  clerk,  on  18  September  2026  for |
| 05-national-police-history.pdf | 2026-09-25 | Run date: 25 September 2026. Record identifier: INVALID-NPH-CJH-XX. |
| 06-nz-police-certificate.pdf | 2026-09-23 | Issued: 23 September 2026. Reference: INVALID-NZPOL-CJB. |
| 07-local-court-sentencing-remarks.pdf | 2017-04-03 | Date: 3 April 2017. Judicial officer: Magistrate Elin Marr, fictional. |
| 08-bond-completion-letter.pdf | 2018-04-03 | 3 April 2018 |
| 09-former-employer-personnel-extract.pdf | 2019-06-19 | Date: 19 June 2019. |
| 10-police-dv-incident-narrative.pdf | 2021-03-16 | Date: 16 March 2021. |
| 11-domestic-violence-order.pdf | 2021-03-22 | Court confirmation: Darwin Local Court, 22 March 2021. |
| 12-program-completion-certificate.pdf | 2022-04-04 | Certificate print date: 4 April 2022. |
| 13-facilitator-exit-report.pdf | 2022-04-08 | Report issued: 8 April 2022. |
| 14-reference-samuel-hartigan.pdf | 2026-09-26 | 26 September 2026 |
| 15-reference-moira-kells.pdf | 2026-09-25 | 25 September 2026 |
| 16-reference-devika-soren.pdf | 2026-09-27 | 27 September 2026 |
| 17-reference-owen-pritch.pdf | 2026-09-28 | 28 September 2026 |
| 18-reference-tessa-wren.pdf | 2026-09-29 | 29 September 2026 |
| 19-association-exemption-and-supervision.pdf | 2026-09-30 | 30 September 2026 |
| 20-club-incident-register-2024-2025.pdf | 2026-09-29 | Season 2024; source register leaf 1 of 9; controlled extract printed 29 September 2026. |
| 21-bank-statements-june-august-2022.pdf | 2026-09-22 | Historical monthly statement, June 2022; reissued 22 September 2026. |
| 22-katherine-tenancy-ledger.pdf | 2026-09-24 | Historical tenancy account, reissued 24 September 2026. |
| 23-current-employer-letter-and-admin.pdf | 2026-09-26 | 26 September 2026 |
| 24-traffic-history.pdf | 2026-09-25 | Issue date: 25 September 2026. |

## Upload and screen evidence

Tests cover verified, absent, wrong, partial, malformed and invalid-calendar answers; exact
whitespace-normalised matching; a mixed text/scan document dated once after transcription;
and a moved upload re-extracted offline with no call and byte-identical `case.json`.
The response-only cache keys on document text content, model, prompt and schema, not an absolute
path. Missing replay entries fail explicitly rather than attempting a live call.

Playwright uploads earlier and later records in reversed file order. At 1280 and 1440 pixels,
the dated comparison orders them by verified date, the tabs and page headers show the dates,
and tooltips expose their quotes. The full-file viewer retains both quotes. The undated variant
uses the existing “Date not recorded” labels and neutral update wording, with no page called
newer or newest. No outcome is selected. Screenshots were inspected at
`.tmp/shots/task31/upload-date-dated-1280.png` and
`.tmp/shots/task31/upload-date-undated-1440.png`; both widths were exercised by tests.
No design rule was changed.

## Validation

- Initial focused run could not create its pytest base directory because `.tmp` did not exist;
  creating that parent resolved the setup errors.
- The first running focused suite found a progress-label mismatch and an overbroad fake checker
  that marked two paragraphs on one page as an update. Date reading now keeps the existing
  progress stages; the screen fixture uses one passage per document. The corrected focused suite:
  **63 passed**, exit 0.
- The expanded W-01 matrix and alternate date spellings: **9 passed, 24 deselected**, exit 0.
- `uv run python scripts/gate.py` could not open the runner's external uv cache (access denied),
  exit 1. The contract allows the prepared virtual environment as the fallback.
- Prepared-venv full gate after the implementation-list correction: **306 passed, 8 skipped**,
  exit 0; both replay smokes passed and the result was `GATE CLEAN`.
- Final `uv run python scripts/gate.py`, with `UV_CACHE_DIR` under `.tmp/uv-cache` and offline
  dependency resolution: **308 passed, 8 skipped** (n=316 collected), exit 0; ruff and both replay
  smokes passed, ending with `GATE CLEAN`.
- The numeric-date punctuation cases: **10 passed, 25 deselected**, exit 0. A trailing sentence
  period is allowed; a numeric suffix cannot masquerade as a date.
- Final SHA-256 verification: all **2,867 files** under `data/cases/` and `runs/` still match the
  pre-task snapshot, including A-0142's cache and `runs/eval/`. All **629 pre-existing source/input
  files** match their snapshot before the final gate. Chromium created only the root's already
  git-ignored `debug.log`, a diagnostic explicitly anticipated by `.gitignore`; no source changed.
- `git add --` for the 12 owned paths failed with `index.lock: Permission denied` in the parent
  repository's worktree metadata. No commit was attempted; the integrator must stage and commit
  the owned changes. No git status/diff/checkout/push command was run by this bee.

The first full gate found one replay-test mismatch: adding the dater adds its exact source path
to H-01's implementation-change list. That run had 297 passed, 8 skipped and 1 failed; both replay
smokes passed. The test now permits only the new upload-dater path in that metadata list. No
evaluation metric or committed output was changed. A SHA-256 comparison of all 2,867 files under
`data/cases/` and `runs/` found no changed, missing or added files.

Model-using validation runs explicitly removed Claude from their effective PATH before
running, and asserted its absence. The shell PATH filter alone did not survive this runner's
native Python launch. `PYTEST_ADDOPTS` stayed `-p no:cacheprovider`. Temporary test data stayed
inside this worktree.

The exact final gate launcher (effective PATH and temporary files are confined before spawning
the prescribed gate command):

```powershell
.venv/Scripts/python.exe -c "import os,shutil,runpy,pathlib,subprocess,sys; os.environ['PATH']=';'.join(p for p in os.environ['PATH'].split(';') if '.local' not in p.lower()); assert shutil.which('claude') is None; temp=pathlib.Path('.tmp/runtime').resolve(); temp.mkdir(parents=True,exist_ok=True); os.environ.update(TEMP=str(temp),TMP=str(temp),TMPDIR=str(temp),UV_CACHE_DIR=str(pathlib.Path('.tmp/uv-cache').resolve()),UV_OFFLINE='1'); sys.exit(subprocess.call(['uv','run','python','scripts/gate.py']))"
```

## Existing test assertions changed or deleted

- `tests/test_ocr.py::test_uploaded_scan_pipeline_and_transcription_replay_byte_identically`:
  the expected Claude-seam call count changed from two (transcription and writer) to three
  (transcription, dating and writer); the first call still has an image and the two later calls
  have none. It now also requires a dating cache entry and injects a replay-only dater when
  re-extracting the upload.
- `tests/test_eval_cases.py::assert_replay_unchanged`: the exact H-01 implementation-list
  comparison now expects the additional `readmark/writer/dating.py` path, alongside the existing
  removal of the two retired CDU source paths. New source files naturally appear in the
  implementation pin; all other replay fields, numbers, denominators and stage bytes still
  must match the frozen baseline.
- No other existing assertion was changed or deleted. The upload replay test adds an assertion
  requiring two dating cache responses. Existing upload, scan and generated-list test fixtures
  explicitly inject an undated fake, or route date-schema requests through the fake Claude.

## Orchestrator's live check

Run this one line from the integrated repository root with the live Claude CLI available:

```powershell
uv run python -m readmark.writer.dating data/cases/W-01 --cache-dir .tmp/w01-dates-live
```

It prints one JSON line per PDF with its filename, verified date and quote (null when rejected),
and writes only its response cache. Add `--replay` to repeat offline. This command never edits
the PDFs, a committed case, or a committed run. The live date-selection result remains unmeasured.

## Live run on W-01 (orchestrator, 4 October 2026, after integration review)

Claude `opus` through the dating seam, 24 PDFs, one call each (16-29 s per call).

**First prompt (the bee's):** it told Claude to prefer an explicit reissue date. 5 of the 20
documents whose output was recorded (n=20) came back with the date of a later copy or reissue rather than when their facts were
recorded: the domestic violence order (copy issued 2026; order made 16 March 2021), the June 2022
bank statements and the Katherine tenancy ledger (both reissued 2026), the 2024-2025 club register
(printed 2026) and the former employer extract (prepared 2026). On the screen this would call a
2022 statement "the newest record". The task file asked for the date a record was "issued, signed
or printed"; "printed" invited this, so the fault is in the task wording, not the bee's reading of it.

**Corrected prompt:** the date a record was made, as its facts stood that day; a copy, reissue,
reprint, extract, release or forwarding date never counts; when the original gives only a month or
period, null. The generic example is not taken from W-01.

| Result | First prompt (n=20 seen: 05-24; 01-04 not recorded) | Corrected prompt (n=24) |
|---|---|---|
| Dated, verified quote | 19 | 16 |
| Undated (null or rejected) | 1 | 8 |
| Dated by a copy or reissue date | 5 | 0 |

Undated under the corrected prompt: 01 covering email, 04 identity bundle, 09 personnel extract,
11 domestic violence order, 19 association file, 20 club register, 21 bank statements, 22 tenancy
ledger. 11 and 19 state a usable original date (order made 16 March 2021; letter of
30 September 2026), so these two are missed dates: the safe direction, since an undated page is
never called newer. All 16 dated answers were read against their quotes by the orchestrator.
