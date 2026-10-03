# Task-13: Light by default, wait-time context on the case header, a cleaner record
> **Execution:** agent `codex` · effort `high`
> *Why:* Tarık asked for a light default and the NT wait-time dataset on the case header (the one
> real open dataset in v1, for the datasets criterion). He found the exported record still carried
> needless fields (2026-10-03). The bigger interface rework comes last, after a look at comparable
> tools. Codex `gpt-6.1-sol` at his request.

**Lane**
- OWNS: `web/**`, `readmark/serve.py`, `readmark/record/**`, `tests/test_screen.py`, `data/context/**`
- MUST NOT TOUCH: `readmark/checks/**`, `readmark/audit/**`, `readmark/eval/**`, `readmark/pipeline.py`, `runs/**` (Task-12); `readmark/jev/**`, `readmark/writer/**`, `readmark/schemas/**`, `readmark/ingest/**`; `data/cases/**`, `data/heldout/**`, `data/policies/**`, `data/benchmark/**`, `design/**`, `docs/contracts.md`, `AGENTS.md`, `notes.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: none

## Goal
- **Light by default.** The screen opens in light mode. The toggle stays, and a saved choice is
  still honoured.
- **Wait-time context.** Download the NT open dataset "Urban Public Housing Wait Times, Wait List and
  Allocations" (December 2020 release,
  <https://data.nt.gov.au/dataset/urban-public-housing-wait-times-wait-list-and-allocations-december-2020>).
  - Confirm its CC BY licence at the source, and store the CSV in `data/context/` with a short
    README: source URL, licence, period and date read.
  - The case header shows one line of context for urban priority housing in Darwin, labelled with
    its source and its age. Example: "Priority housing, Darwin: typical wait N months · NT open data,
    Dec 2020".
  - It is context only, never part of a check, a flag or a decision.
  - If the dataset has no Darwin priority figure, pick the closest honest one and say so in the
    README.
- **A cleaner record.** The exported JSON drops what it repeats:
  - `decision_label`, which `decision` already holds;
  - the top-level `required_reading` list, which each passage's `required` flag already carries.
  - The two hashes move under one `integrity` block, explained in one line each.
  - It keeps what Blueprint asks for: passages opened, time in view, disputes, the reason and the
    models.
  - The HTML export reads the same as before, apart from the same cleanup.

## Why
Small, visible items Tarık asked for, which the final interface pass would otherwise have to carry.

## Acceptance
- [ ] `uv run python scripts/gate.py` exits 0.
- [ ] Headless: a fresh browser opens in light mode; after toggling to dark and reloading, it stays
  dark.
- [ ] Headless: the case header shows the wait-time line with its source and period.
  `data/context/` holds the CSV and its README, with the licence confirmed at the source.
- [ ] The exported record JSON has no `decision_label` and no top-level `required_reading`. It has
  an `integrity` block. Every opened passage still has `opened_at`, `seconds_in_view` and
  `required`.
- [ ] The A-0142 screen tests read flagged items, statuses and counts from `runs/A-0142/view.json`
  rather than pinning them. Task-12 changes those values at the same time, and both states must pass.

## Out of scope
- The interface rework (layout, wording, density): the last job of v1.
- Changing what the checks flag (Task-12).
- Opening anything under `data/heldout/`.
