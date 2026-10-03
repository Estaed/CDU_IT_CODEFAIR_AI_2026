# Task-08: Checker evaluation: Jev against Claude on SummEdits
> **Execution:** agent `ultracode` · effort `high`
> *Why:* "flags where it's unsure" must rest on a measured threshold, and Jev as the v1 checker
> needs an external number (Blueprint → Decisions: several hundred SummEdits pairs, with
> calibration). The numbers freeze for the teammate's report on 7 Oct.

**Lane**
- OWNS: `readmark/eval/**`, `readmark/__main__.py`, `data/benchmark/summedits/**`, `runs/eval/**`, `tests/test_eval_checker.py`
- MUST NOT TOUCH: `readmark/jev/**` (Task-05; use its checker seam as it is), `readmark/pipeline.py`, `readmark/gate/**`, `readmark/schemas/**`, `runs/stub/**`, `runs/A-0142/**` (Task-05); `web/**` (Task-07); `data/benchmark/DATASHEET.md`, `data/cases/**`, `data/heldout/**`, `design/**`, `docs/contracts.md`, `AGENTS.md`, `notes.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: none

## Goal
- **The sample.** At least 300 SummEdits pairs (document, summary, label), stratified across its
  domains with a fixed seed, both labels present, stored in `data/benchmark/summedits/` with the
  source URL, licence, citation and how it was sampled. Check the licence at the source first; if it
  is not CC BY 4.0, stop and report.
- **Both checkers, same seam.** Jev and Claude-as-checker (`make_checker("jev" | "claude")`,
  `check(items)`) each judge every pair, the summary as the claim and the document as the passage.
  A "supports" verdict counts as consistent; anything else counts as inconsistent.
- **The numbers**, each with its n:
  - balanced accuracy per checker, overall and per domain, with the confusion counts;
  - a calibration table per checker (probability bins: n, accuracy);
  - a suggested "unsure" probability band for Jev, read from its table (recorded only, not wired
    into the gate);
  - Jev run twice on the same sample: the agreement rate between the two runs.
- **Replay.** The model responses are cached and committed; a replay rebuilds the numbers with no
  keys.
- **Command and files.** `uv run python -m readmark eval` with a flag for this part (the builder
  names it) writes `runs/eval/checker.json`. `runs/eval/summary.json` is assembled from every
  `runs/eval/<part>.json` present, so the evaluation wave adds its parts without editing this one.
  The verbs `run | serve | eval` and the flags `--case`, `--replay`, `--checker` stay as they are.

## Why
The pitch claims Jev as an independent second key. Without an external number and a calibration
table, "the checker disagrees" and "unsure" are just the model's word. This part needs nothing
from the rest of the wave, so it runs while the pipeline grows.

## Acceptance
- [ ] `uv run python scripts/gate.py` exits 0.
- [ ] The checker part's replay twice gives byte-identical `runs/eval/checker.json`, with
  `TYPESAFE_API_KEY` unset and `claude` not on PATH.
- [ ] A test: balanced accuracy and the calibration bins on a hand-made 10-item set match values
  computed by hand.
- [ ] A test walks `runs/eval/summary.json`: every number sits beside its n.
- [ ] The sample holds at least 300 pairs, both labels, every domain sampled; its licence and
  citation are written next to it.
- [ ] The builder's report gives both checkers' balanced accuracy with n, the Jev unsure band, and
  the two-run agreement, in plain words.

## Out of scope
- The case-level evaluation (mutation set by error type, the held-out file, the ablation): wave 3,
  as new parts beside this one.
- Wiring the unsure band into the gate, MiniCheck, the released benchmark CSV.
- Opening anything under `data/heldout/`.

Fixed: each evaluation part writes `runs/eval/<part>.json`; `summary.json` is assembled from all of
them; every reported number carries its n.
