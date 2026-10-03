# Task-05: Cross-passage checks on the real demo file: contradiction pairs, relevance scan, possibly missed
> **Execution:** agent `ultracode` · effort `xhigh`
> *Why:* a claim checked only against its own passage still passes the stale January ledger, and
> nothing yet finds what the writer left out. These two Jev jobs are v1's "cited is not supported"
> and "omission map", and the demo file A-0142 has never been run.

**Lane**
- OWNS: `readmark/jev/**`, `readmark/gate/**`, `readmark/checks/**`, `readmark/writer/**`, `readmark/ingest/**`, `readmark/checklist/__init__.py`, `readmark/pipeline.py`, `readmark/cache.py`, `readmark/__init__.py`, `readmark/schemas/**`, `tests/conftest.py`, `tests/test_pipeline.py`, `tests/test_checks_and_gate.py`, `tests/test_models.py`, `tests/test_ingest.py`, `tests/test_cross.py`, `scripts/gate.py`, `runs/stub/**`, `runs/A-0142/**`, `README.md`
- MUST NOT TOUCH: `web/**`, `readmark/serve.py`, `readmark/record/**`, `tests/test_screen.py` (Task-07); `readmark/eval/**`, `readmark/__main__.py`, `data/benchmark/**`, `runs/eval/**` (Task-08); `readmark/checklist/clauses.yaml` (awaiting Tarık's eye check); `data/cases/**`, `data/heldout/**`, `design/**`, `docs/contracts.md`, `AGENTS.md`, `notes.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: none

## Goal
Two new Jev jobs join the pipeline, and the demo file runs through all of it.

- **Contradiction pairs.** For each decisive clause, the case passages that matter most to it (cited
  by a claim, or high in the scan; up to about five) are compared pair by pair: agree, contradict or
  unrelated. A contradicting pair shows under its clause. Every claim that cites one side of it
  gets the status "contradicted by another passage", naming the other passage, and both passages
  enter required reading.
- **Relevance scan.** Every case passage is scored against each approved decisive clause, about 20
  passages per Jev call. A passage at or above the threshold that no claim cites becomes "possibly
  missed" under that clause; the strongest enter required reading after the flagged claims. The
  threshold is set on A-0142 with its `gold.json`, before any evaluation, and recorded with how it
  was chosen. No other file's gold is used for it.
- **Required reading** stays at 8 or fewer, one entry per passage carrying all its reasons (a
  passage is never two tasks), most decisive first; the rest are suggested.
- **The demo file runs.** `uv run python -m readmark run --case A-0142` runs live once (Claude
  writer, Jev), and its cache is committed. `run --case A-0142 --replay` rebuilds it with no keys,
  and the gate's replay smoke covers A-0142 as well as the stub. The README's demo command becomes
  `serve --case A-0142`.
- **Wave 1 review leftover (score 60):** a writer fact marked found with no citation never looks
  supported. The writer contract asks for at least one citation when a fact is found; one that
  still arrives without any shows "quote not found".

## Why
"Arrears $2,400 [p.8]" passes against its own passage today (Task-00's test measures that gap), and
the omission map is half of what makes Readmark different from a citation tool. The screen
(Task-07) and the summary under audit (Task-06) both build on this view and this run.

## Acceptance
- [ ] `uv run python scripts/gate.py` exits 0; its replay smoke runs stub and A-0142 with no API
  keys and validates both `view.json` files against schema version 2.
- [ ] `run --case A-0142 --replay` twice gives byte-identical `view.json`, with
  `TYPESAFE_API_KEY` unset and `claude` not on PATH.
- [ ] A test: with a fixed checker that calls the p.8 and p.23 ledger passages contradictory, a
  claim citing only p.8 ("arrears $2,400") is `contradicted`, `contradicted_by` names the p.23
  passage, and both passages are in required reading. Task-00's gap test now shows the gap closed.
- [ ] A test: a passage scored above the threshold and cited by no claim is in its clause's
  `possibly_missed` and in required reading with the reason `possibly_missed`; one below it is not.
- [ ] A test: when flags exceed the cap, required reading still has 8 or fewer entries and no
  passage appears twice across required and suggested.
- [ ] On A-0142 (replayed): under the Debts clause (`elig-debts`) the January (p.8) and March
  (p.23) ledger passages form a contradicting pair. If Jev does not call them contradictory, stop
  and report its verdict; never special-case the pair. Required reading has 8 or fewer passages.
- [ ] `runs/A-0142/scan.json` records the threshold, how it was chosen and the number of passages
  scanned. The builder's report gives how many of A-0142's five gold required pages (p8, p23, p30,
  p51, p58) the required reading covers, with n.
- [ ] `runs/A-0142/` and its cache hold no policy text beyond the quotes the screen shows: the
  existing grep test covers A-0142.

## Out of scope
- The screen (Task-07), the summary under audit (Task-06), the evaluation numbers (Task-08, wave 3).
- Changing `clauses.yaml` (waiting on Tarık's eye check), local models.
- Opening anything under `data/heldout/`: it stays sealed until the evaluation wave.

Fixed (Task-06 and Task-07 build on it): `view.json` becomes `schema_version` 2 with these additions;
the rest of version 1 stays.
- `claims[].contradicted_by`: a list of passage ids, empty when none. `status` is `contradicted`
  when it is non-empty, and that status ranks first.
- `clauses[].contradictions`: `[{"a": passage_id, "b": passage_id, "probability": number|null}]`.
- `clauses[].possibly_missed`: `[{"passage_id", "score"}]`, most relevant first; `coverage` is
  `possibly_missed` when it is non-empty.
- `required_reading[]` and `suggested_reading[]` items: `claim_ids` may be empty; a new non-empty
  `clause_ids`; `reasons` drawn from `contradicted | quote_not_found | checker_disagrees |
  possibly_missed`.
- Every passage id named anywhere in `view.json` has an entry in `sources`.
- The checker seam `check(items) -> verdicts` keeps its signature (Task-08 calls it).
