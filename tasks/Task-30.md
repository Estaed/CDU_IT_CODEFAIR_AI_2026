# Task-30: Jev tells a record that was updated from two records that disagree
**Status: DONE** — 2026-10-04, main `8aaaa03` + `73aec1e`, gate clean; eye check pending: 1 (A-0142 Debts). Retry used for required reading (pages, update chains); the orchestrator collapsed one record over time into one sentence.
> **Execution:** agent `codex` · effort `high`
> *Why:* Tarık opened A-0142 → Debts and saw "Two pages disagree" for the January ledger
> ($2,400 owed) and the March ledger ($0, paid on 2 March). That is a record updated over time,
> not a disagreement (2026-10-04: "borcu odemis kisi ... celiski var demek yerine?"). The cause is
> Jev's pair question: since wave 2 it folds "wrong" and "out of date" into one `contradict`
> answer (`readmark/jev/__init__.py`, note above `PAIR_VERDICTS`), and the screen calls both
> "disagree". A same-day screen rule (`a37ed66`, `datedPair` in `web/app.js`) guesses from dates and
> document types; this task replaces the guess with Jev's own answer. Tarık: "sistemin iyi calismasi
> lazim hatasiz ... bizim vaadimiz hepsini okumana gerek yok demek." Codex: the Claude pool is at
> its weekly wall.

**Lane**
- OWNS: `readmark/jev/**`, `readmark/checks/**`, `readmark/gate/**`, `readmark/schemas/**`, `readmark/pipeline.py`, `readmark/record/**`, `readmark/eval/**`, `runs/A-0142/**` (except git-ignored `records/`), `runs/E-*/**`, `runs/H-01/**`, `runs/stub/**`, `runs/eval/**`, `web/app.js`, `web/theme.css`, `tests/**`, `README.md`, `reports/2026-10-04-pair-updates.md`, `reports/screens/2026-10-04-pair-updates/**`
- MUST NOT TOUCH: `data/**`, `design/**`, `docs/**`, `tasks/**`, `notes.md`, `AGENTS.md`, `readmark/writer/**`, `readmark/checklist/**`, `readmark/ingest/**`, `web/home.js`, `web/lists.js`, `web/upload.js`, `web/index.html`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: Task-28

## Goal

### 1. A fourth answer for Jev's pair question
- `PAIR_VERDICTS` becomes `agree | updated | contradict | unrelated`:
  - **updated:** both passages describe the same fact or record at different times, and the later
    one changes it (a balance paid, a status changed, an address moved). Both were true when written.
  - **contradict:** they cannot both be true about the same thing: two accounts of one event differ,
    or one shows a value in the other is wrong.
  - `agree` and `unrelated` keep their meaning.
- The wording is generic and names nothing from any one file. Choose it by measurement, the way
  wave 2 did (`reports/otopilot-2026-10-03-wave2-report.md`, item 1), on these live pairs:
  - **updated controls:** A-0142 p8 ↔ p23 (the Debts pair) and the same pair in `stub`;
  - **contradict controls:** every pair that is `contradict` today in E-01, E-02, E-03 and H-01
    (13 pairs; list them from the committed `view.json` files), read against each case's
    `gold.json` rationale to tell which are planted contradictions; and W-01's two planted ones from
    the answer key (`../Readmark test files/ochre-card/answer-key/README.md`, T1 `03-p4` ↔ `10-p1`
    and T2 `12-p1` ↔ `13-p1`; the text is in `../Readmark test files/ochre-card/application/`);
  - **agree controls:** the 12 control pairs wave 2 used, if you can find them in the code, tests or
    its report; otherwise 12 pairs from the committed runs that Jev calls `agree` today.
- If no wording gets every planted contradiction to `contradict` and the Debts pair to `updated`,
  keep the wording with the fewest planted contradictions lost, and report the trade-off. **Losing a
  planted contradiction is worse than calling an update a contradiction:** a missed conflict is the
  error the officer cannot see.

### 2. The pipeline treats `updated` like `contradict`, and says which it is
- An `updated` pair still puts both pages in required reading, and a claim that rests on one side is
  still checked against the other (`contradicted_by`): that is what catches "arrears $2,400" citing
  only January. Only the name changes, never what the officer must open.
- Each pair in a clause's `contradictions` list gains `"relation": "contradict" | "updated"`
  (keep the list's name, so the gate, the eval and the record need no rename). Update
  `readmark/schemas/view.schema.json` and its version, and the record if it names pairs.

### 3. The screen speaks from the answer, not a guess
- Replace the date-and-type guess in `web/app.js` (`caseDate`, `datedPair`, `updatedOverTime`)
  with the pair's `relation`:
  - `updated`: the label is "A later page updates this"; the warning names the pages oldest first
    with their dates ("Page 8 (15 Jan 2026) and page 23 (4 Mar 2026) differ; the later page is the
    newer record. Open both before you decide."); the comparison dialog heading is
    "Pages 8 and 23 differ over time". When the pages have no dates (uploaded files), say
    "Pages X and Y record a change over time; open both before you decide." and never claim which
    is newer.
  - `contradict`: today's "Two pages disagree" wording, unchanged.
- Neutral facts only: never "strengthens", "resolved", or any hint at an outcome.

### 4. Re-run and measure
- Re-run the pair stage and everything after it for A-0142, E-01..E-03, H-01 and `stub` with live
  Jev (the key is in `.env`); the writer stage must replay from its cache with no Claude call. Then
  regenerate `runs/eval/` so every case and the evaluation replay offline with no key.
- Write `reports/2026-10-04-pair-updates.md`, each number with its n:
  - the wordings tried and each control set's result (updated / contradict / agree hits);
  - every pair whose verdict changed, before → after, with its probabilities;
  - every evaluation number in `runs/eval/summary.json` before → after, and why each change happened;
  - the W-01 T1 and T2 verdicts.

## Acceptance
- [ ] `uv run python scripts/gate.py` exits 0, and `git status` shows no change after it runs.
- [ ] A-0142 Debts shows "A later page updates this" and still requires pages 8 and 23.
- [ ] No planted contradiction among the controls is lost, or the report names each one lost and why
  no wording kept it.
- [ ] Every case and `runs/eval/` replay byte for byte with no key and no Claude.
- [ ] A test with a fake Jev covers: an `updated` pair (required reading, claim re-check, label,
  undated wording) and a `contradict` pair (unchanged).
- [ ] Screenshots of A-0142 Debts (warning and comparison dialog) at 1280 and 1440 in
  `reports/screens/2026-10-04-pair-updates/`.
- [ ] (eye) Tarık opens A-0142 Debts and reads it as a record that changed, with nothing hinting
  at an outcome.

## Out of scope
- Changing any case document, gold file or the writer.
- New flags or a new screen section.
