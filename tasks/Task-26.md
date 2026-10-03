# Task-26: Question-list coverage: Jev shows decisive policy rules no question covers
> **Execution:** agent `codex` · effort `high`
> *Why:* Tarık asked how Jev could do more, and chose this (2026-10-04). A person still writes and
> approves every question; Jev only points at policy paragraphs that look decisive but that no
> question covers. It is the "possibly missed" idea turned on the rulebook. Example: the CDU list
> has no question for special consideration (74) or the late penalty (78). Codex `gpt-6.1-sol`.

**Lane**
- OWNS: `readmark/checklist/coverage.py`, `readmark/checklist/lists/*/coverage.json`, `readmark/jev/**`, `readmark/__main__.py`, `web/**`, `readmark/serve.py`, `tests/test_coverage.py`, `tests/test_home.py`, `docs/question-lists.md`, `reports/screens/2026-10-04-wave11/**`
- MUST NOT TOUCH: `readmark/checks/**`, `readmark/gate/**`, `readmark/pipeline.py`, `readmark/ingest/**`, `readmark/writer/**`, `readmark/audit/**`, `readmark/eval/**`, `readmark/schemas/**`, `readmark/checklist/lists/*/clauses.yaml`, `readmark/checklist/lists/*/list.yaml`, `runs/**`, `data/**`, `design/**`, `AGENTS.md`, `notes.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: Task-20

## Goal
- **`python -m readmark lists --coverage <list-id>`** runs Jev once over the list's policy paragraphs.
  - It finds paragraphs that read as a rule an officer must apply, and that none of the list's
    approved questions covers. How Jev is asked is the builder's choice: for example a relevance
    scan of each paragraph against each question, plus a "does this state a decision rule" score.
    Write the method and its threshold in `docs/question-lists.md`.
  - Results go to `readmark/checklist/lists/<id>/coverage.json`: paragraph id, section, a short
    excerpt (at most 25 words, never the whole text), scores, the model and the date.
  - Every Jev call goes through the existing replay cache, so a rerun with `--replay` and no key
    reproduces the file byte for byte.
- **The home screen shows it per list,** under "Question lists": "N policy rules no question covers".
  It opens a plain list of those paragraphs, each with its section and excerpt, and a link that opens
  the full paragraph in the policy dialog.
  - Wording makes clear this is a hint for the person who maintains the list: "Jev suggests these
    may need a question. A person decides."
  - Nothing here changes a case's questions, flags or record.
- **Run it for both lists** (`nt-priority-housing` and `cdu-extension`), and commit both
  `coverage.json` files.
  - Policy text stays out of the repo: the JSON holds only short excerpts, the same rule as the
    on-screen quotes.
  - The live run needs `TYPESAFE_API_KEY`. If the bee has no network, it builds and tests with a fake
    Jev and leaves the live run to the orchestrator; say so in the report.

## Why
It helps a person build a sound question list for a new rulebook, without letting the AI choose the
questions. It also makes the "same engine, a different rulebook" pitch line concrete.

## Acceptance
- [ ] `uv run python scripts/gate.py` exits 0, and `git status` shows no change after it runs.
- [ ] Every case replay and `runs/eval/` are unchanged.
- [ ] A test with a fake Jev and a tiny list (one policy, three paragraphs, one question) reports
  exactly the uncovered rule paragraph.
- [ ] `--replay` with no key reproduces both `coverage.json` files byte for byte.
- [ ] No `coverage.json` excerpt is longer than 25 words.
- [ ] On `cdu-extension`, procedures (74) special consideration and (78) late penalty are among the
  reported paragraphs. Report them with their scores, n = the number of paragraphs scanned.
- [ ] Screenshots of the home-screen list section and the opened list at 1280 and 1440 in
  `reports/screens/2026-10-04-wave11/`. Tests write to `.tmp/shots/`, and the delivered set is
  copied once.
- [ ] (eye) Tarık reads the CDU suggestions and agrees they are rules a lecturer would apply.

## Out of scope
- Adding questions automatically, or changing any list's `clauses.yaml`.
