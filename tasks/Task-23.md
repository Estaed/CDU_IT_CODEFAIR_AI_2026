# Task-23: Search within a case: its documents and its policies
> **Execution:** agent `ultracode` · effort `high`
> *Why:* Tarık asked for search across documents (2026-10-03). An officer who remembers "the March
> statement" should find it without paging through 60 pages.

**Lane**
- OWNS: `web/**`, `readmark/serve.py`, `tests/test_search.py`, `tests/test_screen.py`, `reports/screens/2026-10-06-wave10b/**`
- MUST NOT TOUCH: `readmark/checklist/**`, `readmark/ingest/**`, `readmark/pipeline.py`, `readmark/checks/**`, `readmark/jev/**`, `readmark/writer/**`, `readmark/audit/**`, `readmark/eval/**`, `readmark/schemas/**`, `runs/**`, `data/**`, `design/**`, `docs/contracts.md`, `AGENTS.md`, `notes.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: Task-19

## Goal
- **A search box in the case screen** searches the case's own documents and its question list's
  policies. No other case is searched.
- **Plain text search, no AI.** It matches words and simple phrases, and ignores case. Results
  appear as you type, after a short pause.
- **Results are grouped by document.** Each shows the page, the date and a short snippet with the
  match marked.
- **Clicking a result** opens that page in the viewer, scrolled to the match and marked.
  - For a policy result, the policy dialog opens, as today.
  - Opening a page from search counts toward "opened" by the same 3-second rule as every other way
    of opening it.
- **Policy text is read from the pinned PDFs on demand,** as today. No policy text is stored under
  `runs/`.

## Why
Real files are long. Search is the first thing a caseworker reaches for.

## Acceptance
- [ ] `uv run python scripts/gate.py` exits 0, and `git status` shows no change after it runs.
- [ ] Headless on A-0142:
  - "arrears" finds pages 8 and 23 among its results;
  - clicking page 23 opens it with the match marked;
  - after 3 s in view, it counts as opened.
- [ ] Headless: a search on S-01 (or on E-02, if S-01 is not on main yet) returns only that case's
  pages.
- [ ] Headless: a policy word ("withheld") returns the Eligibility policy passage and opens it in the
  policy dialog.
- [ ] No policy text is written under `runs/` (`git status` clean after the tests).
- [ ] Screenshots at 1280 and 1440 in `reports/screens/2026-10-06-wave10b/`. Tests write to
  `.tmp/shots/`, and the delivered set is copied once.
- [ ] (eye) Tarık finds "the March statement" in A-0142 in under 10 s.

## Out of scope
- Meaning-based (embedding) search, and search across cases.
