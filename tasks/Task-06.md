# Task-06: Summary under audit on the demo file
**Status: DONE** — verified 2026-10-03
> **Execution:** agent `ultracode` · effort `xhigh`
> *Why:* Readmark's riskiest assumption is that it finds real errors in a summary we did not
> write; this builds that path on A-0142, so the evaluation wave can measure it.

**Lane**
- OWNS: `readmark/audit/**`, `readmark/pipeline.py`, `readmark/schemas/**`, `tests/test_audit.py`, `runs/stub/**`, `runs/A-0142/**`
- MUST NOT TOUCH: `web/**`, `readmark/serve.py`, `readmark/record/**`, `tests/test_screen.py` (Task-07); `readmark/eval/**`, `readmark/__main__.py`, `data/benchmark/**`, `runs/eval/**` (Task-08); `readmark/jev/**`, `readmark/gate/**`, `readmark/checks/**`, `readmark/writer/**` (Task-05's; call them, change them only if a check cannot be reached otherwise, and say so); `readmark/checklist/clauses.yaml`; `data/cases/**`, `data/heldout/**`, `design/**`, `docs/contracts.md`, `AGENTS.md`, `notes.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: Task-05

## Goal
- **The summary under audit.** Claude (`opus`) gets one line, "Summarise this file.", with the
  A-0142 case text as data, the way an officer uses a general assistant (Blueprint → Decisions: a
  one-line prompt, frozen with model id and prompt). It is generated once and stored with its model
  id, prompt and date. A replay reads it from the cache and never regenerates it.
- **The audit.** The summary is split into its claims. Each claim gets the case passages that bear
  on it with verbatim quotes, then exactly the checks the evidence map uses: quote present, numbers
  and dates in a cited quote (code), Jev's second key, and Task-05's contradiction pairs. Nothing is
  hidden: a claim no passage supports shows "quote not found".
- **Omissions.** Supported evidence-map claims on decisive clauses that the summary never states
  are listed as left out of the summary, by clause.
- **On the view.** `view.json` gets the `audit` block below, and every passage it names is in
  `sources`. The audit adds nothing to required reading: the reading gate stays the evidence map's,
  capped at 8.
- **Reusable claim path.** A function in `readmark/audit/` takes a case and a list of claim
  sentences and returns claims in the view's claim shape. The evaluation wave runs the mutation set
  through it, so it needs no summary.
- **No staging.** The summary is generated once. If the audit finds no error in it, that is the
  result and is reported as such (Blueprint: we show the errors it really makes and fake none).

## Why
The evaluation wave measures the riskiest assumption on this path: the frozen demo summary, the
mutation set and the held-out file all go through it. The screen's "Summary under audit" tab
(Task-07) renders this block.

## Acceptance
- [x] `uv run python scripts/gate.py` exits 0; the A-0142 replay smoke validates the `audit` block.
- [x] `run --case A-0142 --replay` twice gives byte-identical `view.json` with no keys and `claude`
  not on PATH; the frozen summary comes from the cache.
- [x] A test: a fixed summary that states the January arrears as current, against the stub's
  passages, yields a claim that is flagged (contradicted, checker disagrees or quote not found) and
  never `supported`.
- [x] A test: a summary that leaves out a supported decisive map claim lists it in `omitted`.
- [x] A test: every sentence of the summary appears in `sentences`, in order; none is dropped.
- [x] A test calls the reusable claim path directly with two claim sentences and gets two claims in
  the view's claim shape.
- [x] `runs/A-0142/audit.json` holds the summary, its model id, prompt and date, the count of audit
  claims per status and the count left out, each with n. The builder's report lists what the real
  summary got wrong in plain words, each with its passage, or says it found nothing.

## Out of scope
- The tab on screen (Task-07), the mutation-set and held-out evaluation (wave 3).
- Feeding audit flags into required reading, re-prompting the summary until it errs.
- Opening anything under `data/heldout/`: it stays sealed until the evaluation wave.

Fixed (Task-07 renders it from a fixture until this task lands): `view.json` gets a top-level
`audit`, which is `null` when no summary was audited (the stub) or:
```json
{"model": "<model id>", "prompt": "<the one line>", "created": "YYYY-MM-DD",
 "summary": "<full text>",
 "sentences": [{"sentence_id": "s01", "text": "...", "claim_ids": ["a01"]}],
 "claims": ["<same shape as view claims[], claim_id a01, a02, ...>"],
 "omitted": [{"claim_id": "<evidence-map claim id>", "clause_id": "<clause id>"}]}
```
