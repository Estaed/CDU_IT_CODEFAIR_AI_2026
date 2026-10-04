# Task-27: Questions from the rules: Claude suggests, a person approves each one
**Status: BUILT** — gate clean 2026-10-04 (257 tests); open: live CDU run (Claude pool at 94%, after the 21:30 reset) and the eye check. Nit: a "not found" suggestion still shows an active Approve button (the server refuses it).
> **Execution:** agent `codex` · effort `high`
> *Why:* Tarık wants a new kind of case to start from its rulebook (2026-10-04: "kurallar pdflerini
> de istesin oradan soru uretsin"). Today a list needs a hand-written `clauses.yaml`; this makes
> the "same engine, a different rulebook" claim something an officer can do on screen. Codex, on
> Tarık's word.

**Lane**
- OWNS: `readmark/checklist/generate.py`, `readmark/checklist/lists.py`, `readmark/checklist/__init__.py`, `readmark/__main__.py`, `readmark/serve.py`, `web/**`, `.gitignore`, `tests/test_generate_list.py`, `tests/test_home.py`, `tests/test_upload.py`, `docs/question-lists.md`, `reports/screens/2026-10-04-wave12/**`
- MUST NOT TOUCH: `readmark/checklist/lists/*/clauses.yaml`, `readmark/checklist/lists/*/list.yaml`, `readmark/checklist/lists/*/coverage.json`, `readmark/checks/**`, `readmark/gate/**`, `readmark/writer/**`, `readmark/audit/**`, `readmark/eval/**`, `readmark/schemas/**`, `runs/**`, `data/cases/**`, `data/heldout/**`, `design/**`, `AGENTS.md`, `notes.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: none

## Goal
- **"New question list" on the home screen,** next to the existing lists, and **"Make a new list from
  the rules"** at the end of the question-list choice in the New case form (it opens the same flow
  and returns to the form with the new list selected). The officer gives:
  - a list name and a one-sentence scope (the `scope` field Task-26 already reads);
  - the screen words, optional, falling back to the defaults (`case_noun`, `officer`, the three
    decision labels);
  - one or more rule files, PDF with a text layer or text, uploaded together.
- **Pins are made by code:** SHA-256, page count, upload date, version "uploaded <date>". The files
  and the new list live in a git-ignored folder; the list functions read it alongside
  `readmark/checklist/lists/`. No uploaded rule text is ever committed.
- **Claude suggests the questions,** live, with visible progress in plain words, like the New case
  run: "Reading the rules", "Suggesting questions", "Checking each sentence", "Ready".
  - At most 10 suggestions, most decisive first. Each has the fields a `clauses.yaml` entry has
    (`title`, `decides` as a plain question, `policy`, `source` section, verbatim `sentence`,
    optional verbatim `items`) and one plain line on why it decides the case.
  - Use the existing Claude CLI wrapper (`claude -p --json-schema`, model `opus`); the call goes
    through the replay cache, so a rerun with `--replay` and no key gives the same suggestions.
  - Rule text is data, never instructions; the prompt says so.
- **Code checks every sentence word for word** in its named rule file, with the same match the list
  loader already uses. A suggestion whose sentence is not found shows "sentence not found in the
  rules" and cannot be approved until the person corrects it to a sentence that is found.
- **The review page:** one row per suggestion with Approve, Edit and Reject. Nothing is used until
  the person saves, and a list with no approved question cannot be chosen for a case.
  - Wording: "Claude suggested these. You decide which questions the officer must answer."
  - Saved questions record that they were suggested by Claude (model and date) and approved by the
    person on that date. The case's decision record shows the list name and this line.
- **Second pass:** after saving, the Task-26 coverage runs on the new list ("N rules no question
  covers"). Each entry gets "Suggest a question for this", which adds a suggestion that goes through
  the same check and approval. Offline or without a key, the coverage step is skipped with a plain
  note; the list still works.
- **CLI:** `python -m readmark lists --generate <folder-of-rule-files> --id <id> --name <name>`
  writes the suggestions file without approving anything; approval is on screen only.
- `docs/question-lists.md` replaces "The AI does not write or approve the questions" with the new
  rule: the AI may suggest; a person approves every question.

## Why
A new rulebook (a different government service) is the next test of the system. Without this, every
new kind of case waits on someone writing YAML by hand. The line that keeps trust is unchanged: the
AI points at rules, a person decides which ones become questions.

## Acceptance
- [ ] `uv run python scripts/gate.py` exits 0, and `git status` shows no change after it runs.
- [ ] Every case replay, both committed lists and `runs/eval/` are unchanged.
- [ ] A test with a fake Claude and a tiny rulebook (one file, four paragraphs) shows: a suggestion
  with a verbatim sentence passes the check; one with a changed word is marked "not found" and the
  server refuses to approve it; after a fix it passes.
- [ ] A test shows a list with zero approved questions is not offered in the New case form, and one
  with approved questions runs a case end to end with a fake writer.
- [ ] Uploaded rule files and generated lists are git-ignored (a test checks the ignore rule).
- [ ] Live run on the CDU coursework policy as a new list (not touching `cdu-extension`): report how
  many of the 6 hand-written CDU questions the suggestions match by sentence, n = 6, and how many
  suggestions failed the sentence check. If the bee has no Claude access, it builds with the fake
  and the orchestrator runs this.
- [ ] One headless check: the new-list page loads without console errors.
- [ ] Screenshots at 1280 and 1440 of the upload form, the progress view and the review page in
  `reports/screens/2026-10-04-wave12/`. Tests write to `.tmp/shots/`; the delivered set is copied once.
- [ ] (eye) Tarık builds a list from the CDU policy on screen and finds the review page clear: he can
  tell which sentence each question rests on and what Approve does, against the Task-15 look
  (`design/DESIGN.md`, `design/screens/`).

## Out of scope
- The AI approving, ranking-as-final or pre-selecting any question.
- Editing the two committed lists, and scanned rule files (text-layer PDF and text only).
- The new government case file itself (a separate task).

Fixed: the `clauses.yaml` entry fields and `list.yaml` format in `docs/question-lists.md`; generated
lists use the same format so the loader, coverage and pipeline need no special case.
