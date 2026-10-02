# Task-01: Grounded synthetic case files: demo A-0142 plus three short evaluation files
> **Execution:** agent `codex` · effort `high`
> *Why:* the file the pipeline reads must be written by a different model family from the one that
> reads it (Tarık, 2026-10-03), and the data is the weakest judging criterion.

**Lane**
- OWNS: `data/cases/A-0142/**`, `data/cases/E-01/**`, `data/cases/E-02/**`, `data/cases/E-03/**`, `data/benchmark/DATASHEET.md`, `scripts/validate_cases.py`
- MUST NOT TOUCH: `readmark/**`, `web/**`, `tests/**`, `pyproject.toml`, `data/cases/stub/**` (Task-00); `data/heldout/**` (Task-02); `design/**` (Task-03); `docs/contracts.md`, `AGENTS.md`, `notes.md`
- GATE: `python scripts/validate_cases.py` (from repo root; stdlib only)
- DEPENDS ON: none

## Goal
**Format:** four case files in the `docs/contracts.md` format, each written **facts table first**,
then the documents, then `gold.json`.
- Read the five policies first: `data/policies/*.pdf`, or the r.jina.ai fallback in the contract.
- Every document type in a file must be one the Identification and documentation policy asks a
  priority applicant for, or one the contract lists. Name the policy sentence that justifies each
  type in `DATASHEET.md`.

**A-0142, the demo:** 55–65 pages, an urban priority applicant in Darwin with two children. The
scenario is fixed (`notes.md` → The scenario, decisions K1–K2):
- p.8: a January ledger of a **former public tenancy** with a $2,400 debt owed to the CEO (Housing),
  and a payment plan.
- p.23: a March ledger: arrears cleared in full by a lump sum from a support agency.
- p.30: the previous tenancy ended by mutual agreement on 12 June 2023, a debt outstanding at exit,
  no breach.
- p.51: a support-agency letter saying the applicant and children are fleeing family violence;
  police attended on 2 February 2026.
- p.44: a GP note on anxiety.
- Residency and property evidence present.
- **No income statement anywhere.**
- Gold:
  - `elig-debts` met, `elig-former-tenancy` met, `elig-residency` met, `elig-property` met;
  - `elig-income` cannot_decide;
  - `prio-category` met (DFV), `prio-documentation` met;
  - `prio-discretion` not_applicable;
  - correct decision `request_information`.
- The rest is realistic filler, varied and plausible: forms, correspondence, statutory declarations,
  Centrelink-style letters with invented numbers, appointment notes. The decisive passages sit mid-file.

**E-01, E-02, E-03:** 10–15 pages each. Each turns on a different decisive fact:
- **E-01:** the 2-year former-tenancy exclusion (Eligibility §3.5);
- **E-02:** urgent need claimed without supporting documentation (Priority §3.1);
- **E-03:** a case where Priority §3.1's "some discretion for extreme situations" is the honest
  answer.

Each `gold.json` rationale cites a verbatim policy sentence and file pages. Each has a
`mutations.jsonl`: one correct summary of 6–10 claims plus at least one mutation of each applicable
type, labelled.

**`scripts/validate_cases.py`** (stdlib only) checks every case under `data/cases/` and
`data/heldout/`, and takes optional path arguments:
- page markers are consecutive;
- every `facts.csv` quote is a verbatim substring of its page after collapsing whitespace;
- every clause_id is a contract id;
- `gold.json` keys and values follow the contract;
- `mutations.jsonl` lines parse and labels are valid;
- A-0142 has 55–65 pages and the E-files 10–15;
- no line contains a string that looks like a real phone number, TFN or Medicare number (regex).

**`DATASHEET.md`** (Gebru-style, one page): how the files were generated and by which model,
facts-table-first, the trap taxonomy with counts, licence (CC BY 4.0 for our files; the policies
are NTG copyright and not included), intended use, and limits ("synthetic; not evidence of
real-world accuracy").

## Why
The demo, the mutation evaluation and the ablation all read these files. Writing the facts first
gives exact gold labels. A different model family writing them blunts "you planted traps your own
model finds".

## Acceptance
- [ ] `python scripts/validate_cases.py` exits 0 and prints a per-case summary: pages, facts, traps
  by type, mutations by type.
- [ ] A-0142 gold matches the scenario above exactly (decision `request_information`, `elig-income`
  cannot_decide).
- [ ] Every person and organisation is invented, and the validator's PII regex finds nothing.
- [ ] (eye) Tarık skims pages 8, 23, 30, 51 and three random filler pages of A-0142. They read like
  real NT housing paperwork, not like a test. Reference: the scenario in `notes.md`.

## Out of scope
- Any pipeline code, any run output, the held-out file (Task-02) and the stub case (Task-00).
- The release CSV (built in wave 2 from these files).

Fixed: the formats and clause ids in `docs/contracts.md`; the case ids A-0142, E-01, E-02, E-03.
