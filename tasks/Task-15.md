# Task-15: The final look: a government question page with the file inside it
> **Execution:** agent `ultracode` · effort `high`
> *Why:* Tarık picked the final look on 2026-10-03: hybrid 6 in `reports/2026-10-03-ui-references.md`.
> It is the Australian Government caseworker look of direction 1 (plain, few things on screen, the
> work goes click by click), with the original page and its labelled highlight inside the question
> page, so the answer-key idea stays. Blueprint → Decisions (final look) and `design/DESIGN.md`
> record it.

**Lane**
- OWNS: `web/**`, `readmark/serve.py`, `readmark/record/**`, `tests/test_screen.py`, `reports/screens/2026-10-03-wave6/**`
- MUST NOT TOUCH: `readmark/checks/**`, `readmark/audit/**`, `readmark/eval/**`, `readmark/jev/**`, `readmark/writer/**`, `readmark/schemas/**`, `readmark/ingest/**`, `readmark/gate/**`, `readmark/pipeline.py`, `runs/**`, `data/**`, `design/**`, `docs/contracts.md`, `AGENTS.md`, `notes.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: none

## Goal
The review screen becomes `reports/screens/ui-references/mock-6-gov-filepanel.png`, built for real
on every question of A-0142 and of any case `view.json` describes.

- **Header band and identity bar.**
  - The header band shows the service name.
  - The identity bar shows "Applicant file <id>", the case facts and the wait-time line, which
    keeps its source and age.
  - On the right: one primary "Next: …" button, which names the single next step as today, and the
    secondary "Sign decision".
- **Question list on the left (task list).**
  - "Decide these questions" with both counters (decided, required opened).
  - One row per question: its name, and its status in words with an icon ("Two pages disagree · 1
    of 2 opened", "Evidence not found", "Decided: Met").
  - Flagged questions come first. Clean ones fold into one line that opens (Blueprint).
  - "Other facts · no outcome needed" stays, as a quiet row.
  - "Sign decision" is the last row, saying what still blocks it.
- **One question per page on the right.**
  - The title, "Question n of 8 · <policy> §x", and the policy sentence as an inset.
  - A warning box saying in one sentence why the question is flagged.
  - The file viewer: one tab per page that the question cites or must open, showing that page's
    real text with the verified quote highlighted in place and tagged with the question name.
    - Tabs show the page, the date and an opened tick.
    - A page that disagrees with another gets its pair as the next tab. The side-by-side
      comparison stays reachable from the warning box.
    - "Possibly missed" passages are tabs marked as such.
    - "Open in full file (N pages)" opens the whole file as the reading surface, with every
      labelled highlight and "previous / next highlight": the Task-11 behaviour, restyled.
  - Beside the viewer: "Is this question met?" with Met / Not met / Cannot decide yet as large
    radios, none pre-selected; "Open before you sign" with each required page and its state; and
    "Save and next question", which goes to the next undecided question.
  - The AI's claims and the dispute control stay one click away on the question page, as today.
- **States the screen must still show** (this list is complete; the local explainer
  `.tmp/explain/ekran-durumlari.html` is untracked and absent in a worktree): two pages disagree,
  evidence not found ("missing evidence does not mean not met"), checker disagrees, possibly
  missed, a clean question, not ready to sign (a linked list of what is missing), and the locked
  decision record. Each gets its wording and box in the new look.
- **Light only.** Remove the dark mode: the toggle, the dark rules and the saved-theme read
  (Tarık, 2026-10-03). Remove `web/tokens.css`, which is Tarik Base. `web/theme.css` stays the
  single styling file and carries the palette in `design/DESIGN.md`.
- **The first-run panel, "How this works" and "About these checks"** stay, restyled.
- **The exported HTML record** uses the new look. The JSON record is unchanged.

## Why
It is the last job of v1 before the ZIP (8 Oct) and the pitch (15 Oct). Tarık could follow mock 1's
plain page, and he wants to see the original document. This gives him both, without changing what
the checks find or what the record holds.

## Acceptance
- [ ] `uv run python scripts/gate.py` exits 0.
- [ ] Headless at 1280 and 1440 on A-0142: no console errors. The header band, identity bar,
  question list and question page are present. No horizontal scroll.
- [ ] Headless: for every question in `runs/A-0142/view.json`, the viewer has one tab per cited or
  required page. Opening a tab records that passage as opened, with `opened_at` and
  `seconds_in_view` in the record, as before. The "required opened" counter and the row status
  update. The tests read questions, flags and pages from `view.json` and never pin them.
- [ ] Headless: every highlight shown is a code-verified quote. A claim whose quote was not found
  shows "quote not found" and is never highlighted (the existing test keeps passing).
- [ ] Headless: no outcome radio is checked when the screen opens. "Save and next question" moves
  to the next undecided question. Sign-off is refused, with its linked list, until every outcome is
  set and every required passage is opened.
- [ ] Headless: "Open in full file" shows the whole case file with labelled highlights and working
  previous / next highlight. A question with no evidence says "Evidence not found" and never
  "not met".
- [ ] Headless: there is no theme toggle. A saved `readmark-theme=dark` in localStorage still opens
  light. `web/tokens.css` is gone and nothing references it.
- [ ] Every status carries words, not only colour. Text colour pairs in `web/theme.css` measure at
  least 4.5:1 (computed in a test from the declared values).
- [ ] Screenshots of the opening screen and of each state above, at 1280 and 1440, in
  `reports/screens/2026-10-03-wave6/`.
- [ ] (eye) Tarık puts the 1440 opening screenshot beside
  `reports/screens/ui-references/mock-6-gov-filepanel.png`. Good means the same calm government
  page: the same places, palette, type and density, and the real page text visible with its
  tagged highlight. Intended differences go in `design/deviations.md`, which the orchestrator writes
  from the builder's list.
- [ ] (eye) A first-time viewer names the next step within 10 s (Blueprint layout check).

## Out of scope
- What the checks flag, the numbers, the view and record JSON contracts (`docs/contracts.md`).
- A new layout for the policy dialog beyond the restyle.
- Real AgDS components or React, the GOV.UK crown or font, and any build step.

Fixed: `view.json` and the record JSON keep their schema; the `/api/*` routes keep their shapes.
