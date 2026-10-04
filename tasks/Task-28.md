# Task-28: Two showcase cases, a short case note, and a polish pass on the look
> **Execution:** agent `codex` · effort `high`
> *Why:* Tarık wants the app to hold two examples for the pitch and for showing friends: the NT
> housing case and a new Ochre Card case (2026-10-04: "2 tane olsun biri ochre card digeri konut").
> The rest of the examples go, and the screens get small, sober fixes a government officer would
> understand ("cok ucmadan"). Codex: the Claude pool is near its weekly wall. ⛔ Do not start
> before Tarık says so; part 2 makes live Claude calls (after the 21:30 reset on 4 Oct).

**Lane**
- OWNS: `web/**`, `readmark/serve.py`, `readmark/__main__.py`, `readmark/checklist/lists.py`, `readmark/checklist/generate.py`, `readmark/checklist/lists/nt-wwcc/**`, `readmark/checklist/lists/cdu-extension/**` (delete), `data/cases/W-01/**`, `data/cases/S-01/**` (delete), `data/policies/nt-wwcc/**` (git-ignored), `runs/W-01/**`, `runs/S-01/**` (delete), `scripts/fetch_cdu_policy.py` (delete), `scripts/fetch_wwcc_rules.py`, `.gitignore`, `README.md`, `docs/question-lists.md`, `tests/**`, `reports/2026-10-04-ochre-questions.md`, `reports/2026-10-04-accessibility.md`, `reports/screens/2026-10-05-wave13/**`
- MUST NOT TOUCH: `data/cases/A-0142/**`, `data/cases/E-*/**`, `data/heldout/**`, `runs/A-0142/**` (except git-ignored `records/`), `runs/E-*/**`, `runs/H-01/**`, `runs/stub/**`, `readmark/checks/**`, `readmark/gate/**`, `readmark/writer/**`, `readmark/audit/**`, `readmark/eval/**`, `readmark/schemas/**`, `readmark/checklist/lists/nt-priority-housing/**`, `design/**`, `AGENTS.md`, `notes.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: Task-27

## Goal

### 1. Two cases on the home screen
- **Shown:** A-0142 (NT priority housing) and W-01 (NT Working with Children Clearance, new).
- **Kept but hidden:** E-01..E-03, H-01 and `stub`. The evaluation numbers and the gate depend
  on them. The home screen does not list them; they still run with `python -m readmark run|eval`.
- **Deleted:** the CDU list (`cdu-extension`), the easy example S-01 (`data/cases/S-01`,
  `runs/S-01`), `scripts/fetch_cdu_policy.py`, and every test, README line or doc line that
  exists only for them. The two local live-test cases (`runs/U-*`, `data/uploads/U-*`, git-ignored)
  are removed too. Dated reports stay as history.

### 2. The Ochre Card case, W-01
- **Source files** (outside the repo, read-only):
  `../Readmark test files/ochre-card/` with `application-pdf/` (24 PDFs, 104 pages),
  `application/` (the same as text), `policies/` (the Care and Protection of Children Act 2007
  and the Care and Protection of Children (Screening) Regulations 2010) and `answer-key/`
  (facts.csv, gold.json, README.md; the README explains the case).
- **Copy into the repo:** the 24 application PDFs into `data/cases/W-01/`, and facts.csv and
  gold.json beside them. The rule PDFs go to `data/policies/nt-wwcc/`, git-ignored and pinned by
  SHA-256 like the housing policies. `scripts/fetch_wwcc_rules.py` downloads them from
  legislation.nt.gov.au (it needs a browser User-Agent header; a plain request gets a 403).
- **Its question list, `nt-wwcc`, is made with Task-27's flow:** Claude suggests from the two rule
  files, and the orchestrator approves, in the same way an officer would. Approve only
  suggestions whose sentence is found in the rules. The scope sentence: the NT Screening
  Authority deciding whether a candidate for a Working with Children Clearance poses an
  unacceptable risk of harm or exploitation to children.
- **Measure it** in `reports/2026-10-04-ochre-questions.md`: how many of the answer key's 10
  clause_ids the approved questions cover, n = 10; how many suggestions failed the sentence
  check; and which suggestions were rejected and why.
- **Run W-01 live once** (Claude writer, Jev). Every call goes to the replay cache, so the case
  opens offline with no key, the way A-0142 does. Report its numbers in the same report: required
  reading (8 or fewer), flags per question, and whether the T1 contradiction (`03-p4` against
  `10-p1`) and the T3 address omission are flagged.

### 3. "About this file" on each case
- A short box at the top of the case page, closable, in the style of the existing first-run panel
  and not a pop-up.
- It is labelled as the note of the person who received the application ("Intake note"), not the AI.
- It states neutral facts only: who applied, what for, and what the file holds. It never hints at
  an outcome, a problem or a recommended action.
- The text comes from a field in the case folder, so the box needs no code per case:
  - **W-01:** "Callum Hartigan, 31, applies for a Working with Children Clearance to work as a paid
    assistant coach of under-12 football teams in Palmerston. SAFE NT asked him for more
    information because of his criminal history. The file holds his identity documents, police
    and court records, references and two years of club records (24 documents, 104 pages)."
  - **A-0142:** "Ms K. left her home with her two children because of family violence and applies
    for priority public housing in Darwin. She is staying in a refuge. The file holds the
    application, identity and income documents, records of a former tenancy and letters from
    support services."

### 4. Polish the look
- **A Readmark mark and favicon:** a simple marked-page symbol beside the name in the header, an
  SVG in `web/`. Never the NT coat of arms.
- **Status icons:** small icons for flagged, checked, document and opened, always with their
  word beside them, because colour or an icon is never the only signal.
- **Less plain text:** explanatory paragraphs become callout or inset boxes; case facts become a
  summary list (label and value rows), in the AgDS / GOV.UK manner the screen already follows.
- **Known nits:**
  - "1 pages";
  - stacked highlight tags in one paragraph;
  - an active-looking Approve button on a suggestion whose sentence was not found.
- **Accessibility check:** keyboard only (every action reachable, visible focus), labels a
  screen reader announces, and colour contrast to WCAG 2.2 AA. Use Playwright with axe-core or an
  equivalent. Fix what fails; list what remains in `reports/2026-10-04-accessibility.md`.

## Why
The pitch shows two very different NT decisions on the same engine, and Task-27 gets its first
real rulebook. The case note answers "what is this file" in ten seconds without leaning on the
answer. The polish removes the small things a judge notices first.

## Acceptance
- [ ] `uv run python scripts/gate.py` exits 0, and `git status` shows no change after it runs.
- [ ] Every evaluation number in `runs/eval/summary.json` is unchanged. Only H-01's
  `changed_result_files` list may change, from the deleted CDU files. A-0142's replay is unchanged.
- [ ] The home screen lists exactly A-0142 and W-01; `python -m readmark eval` still runs E-01..03
  and H-01.
- [ ] W-01 opens offline with no key from the replay cache, and validates like A-0142.
- [ ] `reports/2026-10-04-ochre-questions.md` gives the coverage of the 10 clause_ids with n, the
  failed sentence checks, and W-01's flags for T1 and T3.
- [ ] No uploaded or rule PDF is committed (`git ls-files data/policies` holds only lock files).
- [ ] The accessibility report lists the checks run, what was fixed and what remains; the
  automated check shows no serious or critical issue on the home, case and question pages.
- [ ] Screenshots of the home screen, both case pages with their intake note, and the question page
  at 1280 and 1440 in `reports/screens/2026-10-05-wave13/`. Tests write to `.tmp/shots/`, and the
  delivered set is copied once.
- [ ] (eye) Tarık opens both cases: the intake note says what the file is in under ten seconds and
  hints at no outcome. The mark, the icons and the boxes look sober and governmental against
  `reports/screens/ui-references/mock-6-gov-filepanel.png` and `design/DESIGN.md`, with nothing
  flashy.

## Out of scope
- Changing A-0142's documents or any evaluation file.
- New features beyond the list above; integration with a government system (a pitch line only).
- A pop-up or modal.
