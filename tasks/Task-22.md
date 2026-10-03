# Task-22: Scanned pages: Claude reads the page image, and the image stays beside the text
> **Execution:** agent `codex` · effort `high`
> *Why:* real case files contain scans. Tarık asked whether Claude can read them (2026-10-03). It
> can read a page image and transcribe it, so no separate OCR program is needed.

**Lane**
- OWNS: `readmark/ingest/**`, `readmark/writer/**` (the transcription call only), `web/**`, `readmark/serve.py`, `tests/test_ocr.py`, `tests/test_screen.py`, `tests/fixtures/scanned/**`, `pyproject.toml`, `uv.lock`, `reports/screens/2026-10-06-wave10/**`
- MUST NOT TOUCH: `readmark/checklist/**`, `readmark/checks/**`, `readmark/jev/**`, `readmark/audit/**`, `readmark/eval/**`, `readmark/schemas/**`, `runs/A-0142/**`, `runs/E-*/**`, `runs/H-01/**`, `runs/S-01/**`, `runs/eval/**`, `data/**`, `design/**`, `docs/contracts.md`, `AGENTS.md`, `notes.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: Task-20

## Goal
- **A PDF page with no usable text layer** is rendered to an image. Claude transcribes it
  page by page, through the same CLI wrapper and model as the writer.
  - The transcription is cached like every other model call, so the case replays offline.
  - The page's passages come from the transcription, marked "transcribed from a scan".
- **Quotes on these pages** are verified against the transcription. The screen says so beside the
  page: "Read from a scanned image by Claude. Check the image."
- **The viewer shows the page image beside its transcription** for such pages, so the officer can
  compare them.
- **Upload (Task-20) accepts scanned PDFs**, and the progress shows "Reading scanned pages".
- **A new dependency for rendering** (for example `pypdfium2`) is allowed. Say which one and why.

## Why
It meets the brief's real-world condition: case files contain scans, and the human checks what the
machine read.

## Acceptance
- [ ] `uv run python scripts/gate.py` exits 0, and `git status` shows no change after it runs.
- [ ] Every existing replay is byte-identical: A-0142, E-*, H-01, S-01, and `runs/eval/`.
- [ ] A test with a small scanned-PDF fixture (text rendered to an image, no text layer) and a fake
  transcriber: the page becomes passages marked as transcribed, and a quote from it verifies.
- [ ] A test with a mixed PDF (a text page and a scanned page) keeps both kinds in page order.
- [ ] Once, by hand (orchestrator, live): a real two-page scan transcribes. The viewer shows the
  image beside the text. Time and quota cost go in the wave report.
- [ ] Screenshots of a scanned page in the viewer at 1280 and 1440 in
  `reports/screens/2026-10-06-wave10/`. Tests write to `.tmp/shots/`, and the delivered set is
  copied once.
- [ ] (eye) Tarık compares an image with its transcription and finds the label clear.

## Out of scope
- Handwriting quality guarantees, and layout reconstruction of tables.
