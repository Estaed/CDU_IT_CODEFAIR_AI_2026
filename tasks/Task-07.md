# Task-07: Guided review screen, layout B
**Status: DONE** — verified 2026-10-03, eye check pending: 1
> **Execution:** agent `ultracode` · effort `xhigh`
> *Why:* Tarık followed the Task-00 flow but could not read it: nothing said what was done and
> what came next. Blueprint → Decisions picked layout B on 2026-10-03.

**Lane**
- OWNS: `web/**`, `readmark/serve.py`, `readmark/record/**`, `tests/test_screen.py`
- MUST NOT TOUCH: `readmark/pipeline.py`, `readmark/schemas/**`, `readmark/audit/**`, `runs/**` (Task-05, Task-06); `readmark/jev/**`, `readmark/gate/**`, `readmark/checks/**`, `readmark/writer/**`, `readmark/ingest/**` (Task-05); `readmark/eval/**`, `readmark/__main__.py` (Task-08); `design/**` (references, read only); `data/**`, `docs/contracts.md`, `AGENTS.md`, `notes.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: Task-05

## Goal
Load the `tasarim` skill first (Tarik Base). The look stays design A (`web/theme.css`,
`design/direction-A.html`); this wave changes the layout and the words, not the look. The screen
works on `serve --case A-0142`, the real demo file from Task-05.

- **Clause list on the left.** One row per decisive clause in plain words ("Debts, Eligibility
  §3.4"), each showing whether its outcome is set and whether its flagged passages are opened. The
  whole row is clickable. A "Sign off" row at the bottom says whether it can start yet.
- **The selected clause on the right:** its policy sentence; the evidence rows (verbatim quote
  first, then the AI's sentence, then its check status with the reason in one plain sentence); its
  contradicting pairs and possibly missed passages; the source passage beside them, or over them
  where 1280 px is too tight; the outcome control (met / not met / cannot decide yet); "Next
  clause".
- **Case bar** that stays on screen: the file, "Outcomes 3 of 8 · Flagged passages 2 of 6 opened",
  and the one next action as a button.
- **Orientation:** a one-line job statement, and a dismissible first-run panel ("How this works":
  what the AI did, what the checks did, what the officer decides, with one supported and one flagged
  claim from this file), recallable with "?".
- **Plain language:** "page 8, paragraph 2"; no claim ids; no model ids on the main screen (they
  move under "About these checks"); no per-claim probability.
- **Sign-off:** the button is always enabled. Clicked early, it lists what is still missing, each
  item a link to its clause. When ready, a check-your-answers summary (the 8 outcomes, disputes, the
  reason, each with Change), then the record.
- **"Summary under audit" tab:** renders the `audit` block (Task-06's Fixed shape) with each
  sentence marked by how it fared, its passages opening in the source pane, and the facts it left
  out. It renders from a test fixture until Task-06 lands; with `audit: null` it says no summary was
  audited.
- **Record (wave 1 review leftovers 40 and 25):** the HTML export uses one time zone, disputes show
  the claim text, and its styles come from `web/theme.css` rather than a separate CSS copy.
- **Everything Task-00's screen does keeps working:** passages open one at a time with time in
  view; outcomes are never pre-filled; dispute with a reason; the server enforces the lock; the
  record is locked after sign-off; export as HTML and JSON.

References: Blueprint → Decisions (review screen layout); `reports/2026-10-03-ux-guided-review.md`
§5, Option B and its common parts; `design/direction-A.html` and `design/shots/A-*` for the look;
`design/mock-v0.html` for behaviour.

## Why
The screen is what the judges and Tarık see. The readability problem from the Task-00 eye check is
the next thing between v1 and the demo.

## Acceptance
- [x] `uv run python scripts/gate.py` exits 0.
- [x] Headless Playwright on A-0142, at 1280 and 1440 wide: no console errors and no horizontal
  overflow; the whole flow passes in the new layout (open each required passage, set 8 outcomes,
  locked before and unlocked after, sign, the record holds `opened_at` and `seconds_in_view` per
  passage, export HTML and JSON).
- [x] Headless: the main screen's visible text (outside "About these checks") contains no claim id
  (`\bc\d{2}\b`), no model id (`claude-`, `jev-`) and no "¶".
- [x] Headless: after an outcome is set and a passage opened, both case-bar counters change, and the
  next-action button points to the next unresolved item.
- [x] Headless: an early "Sign decision" lists what is missing; clicking an item selects its clause.
- [x] Headless: the audit tab, fed the fixture, shows every sentence with a status word (never
  colour alone), and a sentence's passage opens in the source pane.
- [x] The exported HTML record uses one time zone, shows each dispute with its claim text, and
  carries no CSS of its own beyond `web/theme.css`.
- [ ] (eye) Tarık opens `uv run python -m readmark serve --case A-0142` or the wave's screenshots at
  1280 and 1440: a first-time viewer names the next step within 10 seconds (Blueprint check). The
  layout matches the Blueprint decision and the survey's Option B, and the look stays design A.

## Out of scope
- The look polish pass on design A (a later wave), new pipeline data, the backlog queue, a formatted
  PDF record.
- Opening anything under `data/heldout/`.
