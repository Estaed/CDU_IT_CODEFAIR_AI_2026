# Task-10: The evaluation: mutation set, held-out file, ablation, benchmark release
> **Execution:** agent `codex` · effort `high`
> *Why:* the evaluation numbers freeze on 7 Oct for the teammate's report, and the riskiest
> assumption (Readmark finds real errors while required reading stays at 8 or fewer) has not met
> the held-out file yet. Tarık asked for Codex `gpt-6.1-sol` to spare the Claude pool (2026-10-03).

**Lane**
- OWNS: `readmark/eval/**`, `readmark/__main__.py`, `readmark/ingest/**`, `readmark/pipeline.py`, `runs/eval/**`, `runs/E-01/**`, `runs/E-02/**`, `runs/E-03/**`, `runs/H-01/**`, `data/benchmark/**`, `tests/test_eval_cases.py`
- MUST NOT TOUCH: `web/**`, `readmark/serve.py`, `readmark/record/**`, `tests/test_screen.py` (Task-11); `readmark/checks/**`, `readmark/jev/**`, `readmark/gate/**`, `readmark/writer/**`, `readmark/audit/**`, `readmark/schemas/**`, `runs/stub/**`, `runs/A-0142/**`; `data/cases/**`, `data/heldout/**` (read only), `design/**`, `docs/contracts.md`, `AGENTS.md`, `notes.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: none

## Goal
New evaluation parts beside Task-08's checker part. Each writes `runs/eval/<part>.json`, and
`summary.json` is rebuilt from all parts. Every number carries its n.

- **Mutation set, by error type.** Every claim in `data/cases/E-01..E-03/mutations.jsonl` goes
  through the audit's claim path (`readmark.audit.check_claims`).
  - A claim counts as caught when it does not come out `supported`.
  - Report the catch rate per `mutation_type` against the labels, and the false-alarm rate on the
    `supported` claims, each with n.
- **The three evaluation files and the held-out file, end to end.** Run the pipeline once, live, on
  E-01, E-02, E-03 and H-01 (`data/heldout/H-01/`).
  - For each, report: the required-reading size; how many of the gold `required_reading` pages it
    covers, with n; and which planted traps (from `facts.csv`) the flags touch.
  - For H-01, also generate its frozen one-line summary and audit it, the same way A-0142's was.
    Count the flags by status.
- **Held-out discipline.** Prompts, thresholds and code are frozen before H-01 runs, and H-01 runs
  exactly once. Nothing is tuned after seeing its result. A crash fix is allowed and reported.
  H-01's `SEALED.md` and `gold.json` are read only by the scorer, after the run.
- **Ablation by layer.** From the stage files already written (no extra model calls), what each
  layer adds on the mutation set and on the gold required pages:
  1. Claude alone;
  2. plus the code checks;
  3. plus Jev's second key;
  4. plus contradiction pairs;
  5. plus the scan.
- **The riskiest-assumption result.** One short plain-words paragraph in `runs/eval/summary.json`:
  - what the held-out run found;
  - whether required reading stayed at 8 or fewer;
  - the demo summary's 2 real errors among 22 flags.
- **The released mini-benchmark.** Facts, gold labels and the mutation set as CSV in
  `data/benchmark/`. Update `DATASHEET.md`: how the data was generated, the trap taxonomy, licence,
  intended use and limits.

## Why
These are the numbers the report and the pitch stand on. The held-out file is the only test that
no prompt or threshold was tuned against.

## Acceptance
- [ ] `uv run python scripts/gate.py` exits 0.
- [ ] Each new part's replay runs twice with `TYPESAFE_API_KEY` unset and `claude` off PATH, and
  gives byte-identical output. The A-0142 and stub runs stay byte-identical to main.
- [ ] A test: catch rate and false-alarm rate on a hand-made 6-claim set match values computed by
  hand.
- [ ] A test walks `runs/eval/summary.json`: every number sits beside its n.
- [ ] `runs/H-01/view.json` exists, and the report states its required-reading size and gold page
  coverage with n. The builder's notes say when H-01 ran relative to the last code change.
- [ ] `data/benchmark/` holds the CSVs and an updated `DATASHEET.md`.
- [ ] The builder's report gives every headline number in plain words with n, and lists the live
  calls made (Claude, Jev).

## Out of scope
- Changing the checks, the prompts or the screen; the position test; MiniCheck.

Fixed: the parts seam from Task-08 (`runs/eval/<part>.json`, `summary.json` assembled from all of
them); the CLI verbs and the flags `--case`, `--replay`, `--checker`.
