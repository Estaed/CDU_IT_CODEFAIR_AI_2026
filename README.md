# Readmark

Readmark helps an NT delegated officer assess an urban priority-housing application without
over-trusting an AI summary. For each decisive policy clause it shows the verbatim quotes first,
then the AI's claims and how each one fared against the file. The officer must open the flagged
passages before signing. The officer sets every clause outcome; the app never recommends one.

CDU IT Code Fair 2026, AI Challenge brief 6, team AIC014. The case files are synthetic. The NT
policies are real and are not bundled.

## 1. Setup

You need Python 3.13 and [uv](https://docs.astral.sh/uv/) 0.12 or later.

```sh
uv sync                              # creates .venv from uv.lock
uv run playwright install chromium   # only needed for the screen test in the gate
```

## 2. Download the five policy PDFs by hand

The NT Government site blocks scripted downloads, so the PDFs are fetched in a browser and saved
in `data/policies/` under the names below. They are NTG copyright, so they are git-ignored and never
redistributed. Ingest checks each file against its SHA-256 in `data/policies/policies.lock.json`
and stops, naming the file, if one differs.

| Save as | Download from | Version | SHA-256 |
|---|---|---|---|
| `priority-housing-policy.pdf` | <https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/accessing/priority-housing-policy.pdf> | 2.04 | `ea6c52753092bb22a71689862fe8e9a06bc80f604f3ae6b74b5302da4eab12d5` |
| `eligibility-for-social-housing-policy.pdf` | <https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/accessing/eligibility-for-social-housing-policy.pdf> | 7.1 | `f628d219bf38bea1a8156364f8d2b665eae4d6c37e097e6e4869fb0dd7f64fbf` |
| `identification-and-documentation-policy.pdf` | <https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/accessing/identification-and-documentation-policy.pdf> | 4.02 | `ce59a9a3b24a6a7f2e8a505a3588c86b93ea321cd39048a12b1072797fa97404` |
| `domestic-family-violence-policy.pdf` | <https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/living/domestic-family-violence-policy.pdf> | 2.01 | `5209d377b63a291af8386245c539aa0ded413581adb2af7e60bb0332314d5bde` |
| `discretionary-decision-making-policy.pdf` | <https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/foundations/discretionary-decision-making-policy.pdf> | 2.02 | `275b445c9e0e2241064c28a90ff5a5f260f5c05ec17290fc10848d228014ffdd` |

If the site has published a newer version, its SHA-256 will differ and ingest will stop. Re-pin it
on purpose (update `policies.lock.json` and check that `readmark/checklist/clauses.yaml` still
matches word for word), never silently.

## 3. Replay first: no keys, no network

Every model response from our runs is in the replay cache (`runs/<case>/cache/`). Replay rebuilds
every stage file from it, byte for byte:

```sh
uv run python -m readmark run --case stub --replay   # rebuilds runs/stub/*.json
uv run python -m readmark serve                      # http://localhost:8765/
```

The review screen lets you follow a claim to its passage, see why sign-off is locked, open the
required passages one at a time, set each clause outcome, dispute a claim, sign, and export the
decision record as HTML or JSON. Records are saved under `runs/<case>/records/`.

## 4. Live runs with your own keys

A live run sends the synthetic case file and the policy passages to two model services. Never use
it with real case data.

- **Writer:** Claude through the Claude Code CLI (`claude -p --model opus --json-schema`). Install
  it and sign in; there is no API key to set.
- **Checker:** Jev (TypeSafe) at `https://api.typesafe.ai/v1/systemone`. Put your key in the
  environment or in a git-ignored `.env` at the repo root: `TYPESAFE_API_KEY=...`.

```sh
uv run python -m readmark run --case stub                    # Claude writer, Jev checker
uv run python -m readmark run --case stub --checker claude   # Claude as the checker as well
```

New responses are added to the cache, so the same run can be replayed afterwards. Jev is not
deterministic, so a fresh live run can give different verdicts from the cached ones.

## 5. Check it

```sh
uv run python scripts/gate.py
```

The gate runs `ruff check`, `pytest` (including a headless browser test of the review screen) and
a replay smoke test of the stub case with no API key, which validates `view.json` against
`readmark/schemas/view.schema.json`. Exit 0 means clean.

## How it works

`python -m readmark run` runs each stage once and writes `runs/<case>/<stage>.json`:

1. **Ingest** (`readmark/ingest/`): the pinned PDFs and the case file become numbered passages
   (`<case>:p<page>:<paragraph>`). Stage files keep policy passages as offsets and hashes only;
   the server reads policy text from the PDFs when a passage is opened.
2. **Checklist** (`readmark/checklist/clauses.yaml`): the eight decisive clauses, each anchored to
   its verbatim policy sentence.
3. **Writer** (`readmark/writer/`): Claude gets a goal, not steps: find everything that could
   change the officer's decision, for and against, with verbatim quotes, or say what is missing.
4. **Code checks** (`readmark/checks/`): each quote must be in its passage, and every number and
   date in a claim must appear in a cited quote. A failure shows as "quote not found".
5. **Checker** (`readmark/jev/`): a second key on every claim (supports, contradicts, not enough
   information), from a different model family than the writer.
6. **Gate** (`readmark/gate/`): passages behind failed checks become required reading, at most 8,
   most decisive first.
7. **View** (`runs/<case>/view.json`), served by `readmark/serve.py` to `web/`.

`python -m readmark eval` (the evaluation) arrives in wave 2.

Opening a passage is recorded; it does not prove it was read. The decision record says "opened".
