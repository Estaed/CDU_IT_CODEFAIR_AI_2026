# Task-20: New case: upload several documents and run the checks live
**Status: DONE** — verified 2026-10-03, eye check pending: 1
> **Execution:** agent `codex` · effort `high`
> *Why:* Tarık wants new cases, where a case is a folder of several documents (2026-10-03: "yeni proje
> gibi onun içine dosyaları atarız"). The home screen's "New case" button (Task-19) needs it.

**Lane**
- OWNS: `web/**`, `readmark/serve.py`, `readmark/ingest/**`, `readmark/pipeline.py`, `tests/test_upload.py`, `tests/test_screen.py`, `tests/test_home.py`, `tests/test_ingest.py`, `.gitignore`, `reports/screens/2026-10-05-wave9/**`
- MUST NOT TOUCH: `readmark/checklist/**`, `readmark/checks/**`, `readmark/jev/**`, `readmark/writer/**`, `readmark/audit/**`, `readmark/eval/**`, `readmark/schemas/**`, `runs/A-0142/**`, `runs/E-*/**`, `runs/H-01/**`, `runs/S-01/**`, `runs/eval/**`, `data/cases/**`, `data/heldout/**`, `design/**`, `docs/contracts.md`, `AGENTS.md`, `notes.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: Task-18, Task-19

## Goal
- **"New case" on the home screen opens a short form:**
  - a case name;
  - a question list, chosen from the Task-18 lists;
  - one or more files, PDF (with a text layer) or text, dropped or picked together.
- **The documents become one case.**
  - Each file is one document, with its pages and a document id in every passage id, the way
    A-0142's documents are today.
  - Uploads live in a git-ignored folder. No uploaded file and no `.env` is ever committed.
- **Run the checks live.**
  - The server runs the pipeline on the new case: the Claude writer and Jev, with keys from `.env`.
  - The screen shows its progress stage by stage, in plain words: "Splitting into passages",
    "The AI is reading", "Checking quotes", "Second reader", "Ready".
  - When it finishes, the case joins In progress. Its run is cached like any other, so it replays
    offline afterwards.
- **Fail plainly.** A missing key, a model error or a page with no text gives one clear sentence
  and keeps the uploaded files. A scanned page with no text layer says "scanned page: Task-22 adds
  reading these"; Task-22 replaces that message.

## Why
A judge can see Readmark work on documents nobody prepared. This is also the path the easy example
and any later file use.

## Acceptance
- [x] `uv run python scripts/gate.py` exits 0, and `git status` shows no change after it runs.
- [x] Every existing replay is byte-identical: A-0142, E-*, H-01 and S-01, and `runs/eval/`.
- [x] A test uploads two small text documents with a fake writer and checker (no keys, no network).
  The case appears In progress with passages from both documents, each carrying its document id,
  and the progress steps are shown in order.
- [x] A test proves that uploaded files and runs of uploaded cases are git-ignored.
- [x] A failing stage shows one plain sentence, and the uploaded files are kept.
- [x] Once, by hand (orchestrator, live keys, after measuring the Claude quota): two short real PDFs
  uploaded as one case run to Ready. The case opens with highlights from both documents. Its time
  and the Claude quota cost go in the wave report.
  *(Done 2026-10-04 02:20: two PDFs rendered from S-01 pages 1 and 2, list cdu-extension, uploaded through `POST /api/cases`; Ready after 50 s, one Claude call of 42 s, 14 notes, 1 required passage, highlights from both documents. The Claude weekly window was not re-measured (Tarık: on Max, not a concern).)*
- [x] Screenshots of the form, the progress and the new case at 1280 and 1440 in
  `reports/screens/2026-10-05-wave9/`. Tests write to `.tmp/shots/`, and the delivered set is
  copied once.
- [ ] (eye) Tarık uploads two files himself and follows the progress without help.

## Out of scope
- Scanned pages (Task-22). Search (Task-23). Editing or deleting a case.
