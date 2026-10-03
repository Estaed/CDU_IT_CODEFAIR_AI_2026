# Task-23: Search within a case: words always, meaning through Jev when online
**Status: DONE** — verified 2026-10-03, eye check pending: 1
> **Execution:** agent `codex` · effort `high`
> *Why:* Tarık asked for search across documents (2026-10-03). An officer who remembers "the March
> statement" should find it without paging through 60 pages. On 2026-10-04 he also chose search by
> meaning through Jev. It runs when a key and the network are there, and falls back to word search,
> so the offline demo never breaks (Blueprint → Constraints). Codex `gpt-6.1-sol`.

**Lane**
- OWNS: `web/**`, `readmark/serve.py`, `readmark/search.py`, `readmark/jev/**`, `tests/test_search.py`, `tests/test_screen.py`, `reports/screens/2026-10-05-wave10b/**`
- MUST NOT TOUCH: `readmark/checklist/**`, `readmark/ingest/**`, `readmark/pipeline.py`, `readmark/checks/**`, `readmark/writer/**`, `readmark/audit/**`, `readmark/eval/**`, `readmark/schemas/**`, `runs/**`, `data/**`, `design/**`, `docs/contracts.md`, `AGENTS.md`, `notes.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: Task-19

## Goal
- **A search box in the case screen** searches the case's own documents and its question list's
  policies. No other case is searched.
- **Word search, always.** It matches words and simple phrases and ignores case. Results appear as
  you type, after a short pause. It needs no key and no network.
- **Meaning search, when online.**
  - With `TYPESAFE_API_KEY` set and Jev reachable, pressing Enter (or "Search by meaning") asks Jev
    to score the case's passages against the query, the way the relevance scan scores them against a
    question. It then shows the best matches, so "March statement" finds the ledger page even
    without those words.
  - Meaning results are labelled "found by meaning (Jev)". They are merged with the word matches,
    with no duplicates.
  - Without a key, or on a network error or timeout (5 s), the box quietly uses word search only,
    and shows "word search (offline)".
  - Meaning-search calls are not written into `runs/`; they never change a case's stored results.
- **Results are grouped by document.** Each shows the page, the date and a short snippet, with the
  match marked for word results.
- **Clicking a result** opens that page in the viewer, scrolled to it and marked.
  - For a policy result, the policy dialog opens, as today.
  - Opening a page from search counts toward "opened" by the same 3-second rule as every other way
    of opening it.
- **Policy text is read from the pinned files on demand,** as today. No policy text is stored under
  `runs/`.

## Why
Real files are long, and search is the first thing a caseworker reaches for. Meaning search shows
what Jev adds beyond keywords, without putting the offline demo at risk.

## Acceptance
- [x] `uv run python scripts/gate.py` exits 0, and `git status` shows no change after it runs. The
  gate has no key, so it proves the offline fallback.
- [x] Headless on A-0142, word search:
  - "arrears" finds pages 8 and 23 among its results;
  - clicking page 23 opens it with the match marked;
  - after 3 s in view, it counts as opened.
- [x] Headless: a search on S-01 returns only S-01's pages.
- [x] Headless: a policy word ("withheld") returns the Eligibility policy passage and opens it in the
  policy dialog.
- [x] A test with a fake Jev shows meaning results merged, labelled and de-duplicated. A test with no
  key shows "word search (offline)" and no error.
- [x] Once, by hand (orchestrator, live key): on A-0142, "March statement" by meaning puts page 23
  among the top 3. Record the call count and time in the wave report.
  *(Done 2026-10-04 04:05 on A-0142, query "March statement": word search found only p.24 (the literal phrase, 0.9 s); meaning search put p.23, the March statement, at rank 1 with Jev score 3.85, in 2.3 s.)*
- [x] No policy text is written under `runs/` (`git status` clean after the tests).
- [x] Screenshots of word and meaning results at 1280 and 1440 in
  `reports/screens/2026-10-05-wave10b/`. Tests write to `.tmp/shots/`, and the delivered set is
  copied once.
- [ ] (eye) Tarık finds "the March statement" in A-0142 in under 10 s.

## Out of scope
- Search across cases.
