# Fair Turn

Decision support for triaging housing maintenance requests across the Northern Territory:
free-text fault reports are read into typed fields, a transparent formula ranks the open
jobs, and a coordinator owns the equity trade-off between efficiency and remote-community
need through a single slider, signs the list, and can explain it to a tenant. Entry for
the CDU IT Code Fair 2026 AI Challenge, brief 1 (housing maintenance triage). Team `<N>`.

## Run it (no accounts, no network)

Windows PowerShell:

```
py -3.13 -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\streamlit run fair_turn/app/main.py
```

POSIX (Bash):

```
python3.13 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/streamlit run fair_turn/app/main.py
```

Python 3.13 is required.

## The six screens

1. **Triage board** — ranked open jobs for a day and region, an equity slider (λ = 1
   efficiency to λ = 0 need only), two rankings side by side, hidden metrics until
   sign-off, a needs-a-human queue, and a map of communities by region.
2. **Job card** — the report text with every extracted field highlighted at its source
   phrase, the score's factor breakdown, and an override with a written reason.
3. **Sign-off** — choose λ, write a reason, sign; the signed list and any later revision
   go to the audit log.
4. **Tenant view** — look up a job by registration number and get a plain-language answer:
   what was understood, why it sits where it does, and where it would sit at λ = 0.
5. **Feedback loop** — replay the 90-day synthetic dataset at λ = 1 against a chosen λ,
   showing reporting rate and wait-time gap between town and remote communities.
6. **Audit log** — every signed day's λ, reason, revisions and overrides, the override
   rate over time, exportable as a table.

## What is real and what is synthetic

Geography real (BushTel/ABS); events synthetic. Communities are shown at their real
coordinates with real attributes, but under pseudonymous, region-coded ids
(`data/raw/PROVENANCE.md`); the id-to-name key is not in this repository. Every fault
report's text, its extracted labels and the 90-day event window are synthetic, generated
and labelled by the build pipeline, not real tenant data.

## Evaluation numbers

Full tables: `data/build/eval.json` (machine-readable), `data/build/eval_tables.md`
(rendered), `data/build/report/` (the tables and figures the project report quotes).

Extractor macro-F1 against the *provisional* 0.85 target, on the 150-item holdout set:

- `fault_type`: **0.919** — target met.
- `safety_class`: **0.564** — target not met, reported as such.

## Rebuilding the artefacts

Everything above runs from the committed `data/build/` artefacts with no rebuild needed.
To regenerate them, run in order from the repo root:

```
venv/Scripts/python scripts/fetch_raw_sources.py   # frozen, already run; needs network once
venv/Scripts/python scripts/build_labels.py
venv/Scripts/python scripts/generate_text.py       # needs a logged-in `claude` CLI (Opus)
venv/Scripts/python scripts/extract.py             # needs a logged-in `claude` CLI (Sonnet)
venv/Scripts/python scripts/run_eval.py
venv/Scripts/python scripts/export_report_tables.py
```

`generate_text.py` and `extract.py` are the only steps that call a model, through a
subscription CLI already logged in on the machine that runs them; no API key is used or
accepted anywhere in this repository. The app and the test suite never call a model or
open a network connection.

## Live intake (optional)

Nothing above requires it: the app runs and every surface renders with no provider set. To
enable the workspace's "New report" extraction against a live model, set `FAIR_TURN_PROVIDER`
before starting Streamlit.

PowerShell:

```
$env:FAIR_TURN_PROVIDER = "claude"
venv\Scripts\streamlit run fair_turn/app/main.py
```

Git Bash:

```
export FAIR_TURN_PROVIDER=claude
venv/Scripts/streamlit run fair_turn/app/main.py
```

`claude` requires a logged-in `claude` CLI on the machine (Sonnet, the same wrapper the build
uses); `ollama` is selectable with `FAIR_TURN_PROVIDER=ollama` and runs `qwen3:8b` locally
(`ollama pull qwen3:8b` first). The default stays `claude` until Task-36's benchmark
(`scripts/benchmark_provider.py`) says otherwise. A submitted report,
its extraction, and any coordinator-set field are appended to `data/runtime/runtime.jsonl`
(gitignored, never committed) and merged into the ranking alongside the committed artefacts.

## Policy index

`data/build/policy_passages.json` is committed, so a judge never needs to rebuild it. To
regenerate it after changing the source fact sheet or the retrieval threshold, a running
Ollama with the `bge-m3` model pulled is required:

PowerShell:

```
venv\Scripts\python scripts\build_policy_index.py
```

Git Bash:

```
venv/Scripts/python scripts/build_policy_index.py
```

The indexed source, `data/raw/nt_fs17_repairs_and_maintenance_2025-10.pdf`, is © NT Government
and is quoted with attribution in the app; its licence for this use is PRD open question 6
(not yet confirmed).

Ollama chat extraction (`qwen3:8b`) is a separate, later benchmark (Task-36) against the same
150-item and adversarial tables Claude is scored on; it is not the default provider unless that
benchmark shows it is not below Claude on both required fields.

## Checks

`venv/Scripts/python scripts/gate.py` runs `ruff check`, `ruff format --check` and the
full pytest suite (unit, property and Streamlit `AppTest` smoke tests), stopping at the
first failure. It is the only gate; nothing is DONE without it green.

## Licences and sources

Reduced from `data/raw/PROVENANCE.md`:

| Source | Licence |
|---|---|
| BushTel (communities, community detail) | NT Open Data Creative Commons licence; attribution: Department of Housing, Local Government and Community Development, Northern Territory, BushTel community data, sourced 12 September 2026, https://bushtel.nt.gov.au/ |
| NT road report (obstructions) | to be confirmed |
| NT open data mobile coverage 2021 | Creative Commons Attribution |
| Natural Earth admin-1 outline | Public domain |
| BoM monthly mean-maximum normals | CC BY 4.0; attribution: Bureau of Meteorology, © Commonwealth of Australia. Licensed from the Commonwealth of Australia under a Creative Commons Attribution 4.0 International licence. Values still unverified |

## Packaging

```
venv/Scripts/python scripts/package_submission.py --team <N>
```

Refuses on a dirty working tree or a red gate; writes
`dist/AI-Challenge_Team-<N>_FairTurn.zip`.
