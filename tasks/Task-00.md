# Task-00: Thinnest end-to-end path, from a stub case to a signed decision record
**Status: DONE** — verified 2026-10-03, eye check pending: 2
> **Execution:** agent `ultracode` · effort `xhigh`
> *Why:* lays the package, the stage contract, the model seams and the gate. Every later feature
> plugs into them.

**Lane**
- OWNS: `pyproject.toml`, `uv.lock`, `readmark/**`, `web/**`, `tests/**`, `scripts/gate.py`, `data/policies/policies.lock.json`, `data/cases/stub/**`, `runs/stub/**`, `README.md`
- MUST NOT TOUCH: `data/cases/A-0142/**`, `data/cases/E-*/**`, `data/benchmark/**`, `scripts/validate_cases.py` (Task-01); `data/heldout/**` (Task-02); `design/**` (Task-03); `docs/contracts.md`, `AGENTS.md`, `notes.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: none

## Goal
**Stub case:**
- A small stub case exists in `data/cases/stub/`, about 6 pages in the `docs/contracts.md` format.
- It holds the four scenario passages from `design/mock-v0.html`: the p.8 ledger, the p.23 ledger,
  the p.30 tenancy record and the p.51 support letter. The ledger text must make the debt a
  **former-tenancy debt owed to the CEO (Housing)**.
- It has no income statement.
- It comes with its own `facts.csv` and `gold.json`.

**Pipeline:** `uv run python -m readmark run --case stub` runs every v1 layer once.
1. **Ingest:** the five policy PDFs in `data/policies/` become numbered passages, pinned in
   `policies.lock.json` (version and SHA-256). The case becomes passages using the contract's id
   scheme.
2. **Checklist:** `readmark/checklist/clauses.yaml` holds the eight contract clause ids, each with
   the verbatim policy sentence it rests on.
3. **Writer:** Claude through `claude -p --model opus --json-schema`. Port the wrapper from
   `git show archive/v2-weekly-plan:fair_turn/llm/claude_cli.py`: prompt on stdin, process-tree kill
   on timeout, one retry on invalid JSON, `BEYIN_INVOKED_BY` set.
   - The prompt gives a **goal, not steps**: the officer decides this file against these clauses, so
     find everything that could change the decision, for and against, contradictions and what is
     missing. Every fact comes with 1..n `{passage_id, verbatim quote}`, and "not found" is allowed.
   - Case and policy text go in as data, never as instructions.
4. **Code checks:** each quote is present in its passage after whitespace normalisation, and every
   number and date in the claim appears in one of its cited quotes. Failures show as "quote not
   found" and are never dropped.
5. **Checker, Jev:** `POST https://api.typesafe.ai/v1/systemone`, body
   `{"model":"jev-latest","state":{...},"questions":{...}}`, `TYPESAFE_API_KEY` from env or `.env`.
   - It gives a second-key verdict per claim (supports / contradicts / not enough information, with
     a probability).
   - `--checker claude` swaps in Claude, behind the same small interface.
   - The call shapes are in `reports/2026-10-03-jev-smoke-test.md` and `.tmp/jev_smoke.py`.
6. **Gate:** required reading = quote-not-found, checker disagrees and contradicts. At most 8 items,
   most decisive first.
7. **View:** `runs/stub/view.json`, with its schema in `readmark/schemas/`.

**Screen:** `uv run python -m readmark serve` serves `web/` on localhost with a working review screen.
- The behaviour follows `design/mock-v0.html`: evidence by clause with the verbatim quote first;
  three separate status lists; the source pane; required-reading counter.
- Passages open **one at a time** and log time in view.
- The officer sets each clause outcome (met / not met / cannot decide yet). The AI never pre-fills it.
- A claim can be disputed with a reason.
- The sign-off lock explains what is missing. The decision dialog asks for a decision and a reason.
- The decision record is saved by POST under `runs/stub/records/` and exports as HTML and JSON.
- All styling lives in `web/theme.css`, starting from Tarik Base tokens (copy
  `D:/TarikOS/.brain/skills/tasarim/references/tokens.css` unchanged into `web/`). The look is
  settled after the A/B (Task-03).

**Replay:** every model response is cached in `runs/stub/cache/`. `run --case stub --replay`
rebuilds `view.json` with no keys and no network.

**README:** `README.md` covers setup (uv), the manual PDF download with the five links and their
SHA-256, replay first, and live runs with your own keys.

## Why
It retires the plumbing risk in one go: nested `claude -p`, the Jev API from Python, PDF page
anchors, the replay cache, and a screen that never shows a claim without a checked quote. Wave 2
then adds the real demo case, contradiction pairs, the scan, the summary under audit and the
evaluation as separate features on these seams.

## Acceptance
- [x] `uv run python scripts/gate.py` exits 0. It runs `ruff check`, `pytest`, and a replay smoke
  that runs the stub with no API keys in env and validates `view.json` against its schema.
- [x] Replay is deterministic: `run --case stub --replay` twice gives byte-identical `view.json`,
  with `TYPESAFE_API_KEY` unset and `claude` not on PATH.
- [x] A test changes one byte of a copy of a policy PDF; ingest stops with a message naming the
  file and the expected SHA-256.
- [x] A test injects a claim with a fabricated quote; it reaches `view.json` with the status
  "quote not found" and is in required reading.
- [x] A test shows that a claim citing only p.8 ("arrears $2,400") passes the code check, so the
  gap that wave 2's contradiction pairs close is measured, not assumed.
- [x] Required reading has 8 items or fewer and is ordered. A test covers the cap.
- [x] A headless Playwright test opens the served page with no console errors. It opens the
  required passages one by one, confirms the sign-off is locked before and unlocked after, signs,
  and finds the record JSON with `opened_at` and `seconds_in_view` per passage.
- [x] `runs/stub/` and the cache contain no policy text beyond the quotes shown on screen. A test
  greps the cache for a long policy sentence that is not quoted.
- [ ] (eye) Against `design/mock-v0.html`'s behaviour (not its look): Tarık can follow one claim to
  its passage, see why the gate is locked, open passages, set clause outcomes, sign, and read the
  record. Screenshots at 1280 and 1440 wide go in the wave report.
- [ ] (eye) `readmark/checklist/clauses.yaml` reads right to Tarık: the eight decisive clauses,
  each with its verbatim policy sentence.

## Out of scope
- The real 60-page demo case (Task-01) and the held-out case (Task-02).
- Contradiction pairs, the relevance scan, the summary under audit and the evaluation: wave 2.
- The final look (Task-03 chooses A or B), local models and OCR.

Fixed:
- The formats and clause ids in `docs/contracts.md`.
- The stage file names `runs/<case>/<stage>.json`.
- The CLI verbs `run | serve | eval` and the flags `--case`, `--replay`, `--checker`.
- The five PDFs must be in `data/policies/`; Tarık downloads them before the run. If they are
  missing, stop and report BLOCKED rather than invent policy text (all five were present on
  2026-10-03).
