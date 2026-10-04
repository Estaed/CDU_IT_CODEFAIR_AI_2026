# Task-31: Uploaded documents get their date, read by Claude and checked by code
> **Execution:** agent `codex` · effort `high`
> *Why:* Every uploaded document is stored with `doc_date: None` (`readmark/ingest`,
> `_uploaded_passages`), so Jev reads it as "dated None" and `date_order` falls back to page order.
> Task-30's `updated` answer and the screen's "the later page is the newer record" depend on
> knowing which record came first; on an uploaded file, such as W-01, the case Tarık shows his
> friends, they cannot work. W-01's answer key has exactly this kind of trap (T5: the licence
> address is stale). Tarık approved on 2026-10-04 ("evet yap"); he uploads W-01 after this lands.

**Lane**
- OWNS: `readmark/ingest/**`, `readmark/writer/dating.py` (new), `readmark/serve.py`, `web/app.js`, `tests/**`, `README.md`, `docs/question-lists.md`, `reports/2026-10-04-upload-dates.md`
- MUST NOT TOUCH: `data/**`, `design/**`, `docs/blueprint.md`, `tasks/**`, `notes.md`, `AGENTS.md`, `readmark/jev/**`, `readmark/checks/**`, `readmark/gate/**`, `readmark/eval/**`, `readmark/writer/` files other than `dating.py`, `runs/**`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: Task-30

## Goal

### 1. A date for each uploaded document
- During `prepare_upload`, after a document's text is known (including transcribed scans), one
  Claude call per document asks for **the date the document was issued, signed or printed**: when
  the record was made, never the date of an event it describes (a 2025 police history listing a 2021
  charge is dated 2025).
- The answer is `{date: "YYYY-MM-DD" | null, quote: "<verbatim text from the document>"}`. Code
  accepts it only if the quote is found in the document's own text (the same normalised matching the
  claim checks use) and the date can be read from that quote. Otherwise the document stays undated.
  A missing date is never guessed, and is never an error: the upload carries on.
- The call goes through the per-case replay cache like the transcriber
  (`readmark/writer/transcription.py`), so an uploaded case still replays offline with no key.
  Document text is data, never instructions.
- `case.json` keeps `doc_date` and `date_quote` per document; `_uploaded_passages` passes
  `doc_date` on, so Jev's pair question and `date_order` see it.

### 2. The screen
- An uploaded document's date shows where a built-in case's date shows today (page heading, tabs,
  the pair warning). An undated document shows no date and the pair wording that never says which
  page is newer (Task-30).
- The date is a displayed claim, so its verified quote is reachable from it (a tooltip or the
  document's detail is enough; no new section).

### 3. Measure
- `reports/2026-10-04-upload-dates.md`: run the dater on W-01's 24 PDFs
  (`data/cases/W-01/`, read-only) with a fake Claude in tests, and report what the code-side check
  does with good, wrong and missing answers. **The live run on W-01 is the orchestrator's**, after
  integration (the Claude pool resets at 21:30); leave a one-line command for it.

### 4. A committed case in upload form (added 2026-10-04, Tarık: "30→31→W-01 tek koşu")
- Task-29 commits W-01 as an uploaded case, but `case_path` only reads `data/cases/<id>/case.md`
  and upload ids. Make `case_path` return `data/cases/<id>/case.json` when that file exists, so
  `_uploaded_passages` reads it with document files relative to that folder (W-01's 24 PDFs are
  already there; nothing is copied). Passage ids then carry `W-01`, so the orchestrator runs W-01
  once live under that id after this task; no `data/**` file is written here.

## Acceptance
- [ ] `uv run python scripts/gate.py` exits 0, and `git status` shows no change after it runs.
- [ ] Every committed case, `runs/eval/` and A-0142's replay are byte-for-byte unchanged.
- [ ] Tests with a fake Claude cover: a date with a verified quote (stored and shown); a quote not in
  the document (undated); a date the quote does not contain (undated); no date (undated, upload
  continues); a replayed upload making no call.
- [ ] Undated uploads keep today's behaviour exactly.
- [ ] A one-line command runs the live dater on W-01's 24 PDFs and prints each date with its quote.
- [ ] A test with a temporary cases folder shows a `case.json` case loading by its own id (passage
  ids carry that id; a changed PDF still fails the hash check), and a `case.md` case loading as before.

## Out of scope
- Document types or titles; changing any case document, gold file or committed run.
