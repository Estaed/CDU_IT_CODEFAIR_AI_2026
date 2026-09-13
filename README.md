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

## Checks

`venv/Scripts/python scripts/gate.py` runs `ruff check`, `ruff format --check` and the
full pytest suite (unit, property and Streamlit `AppTest` smoke tests), stopping at the
first failure. It is the only gate; nothing is DONE without it green.

## Licences and sources

Reduced from `data/raw/PROVENANCE.md`:

| Source | Licence |
|---|---|
| BushTel (communities, community detail) | NT Government, licence to be confirmed |
| NT road report (obstructions) | to be confirmed |
| NT open data mobile coverage 2021 | Creative Commons Attribution |
| Natural Earth admin-1 outline | Public domain |
| BoM monthly mean-maximum normals | Cited, unverified |

## Packaging

```
venv/Scripts/python scripts/package_submission.py --team <N>
```

Refuses on a dirty working tree or a red gate; writes
`dist/AI-Challenge_Team-<N>_FairTurn.zip`.
