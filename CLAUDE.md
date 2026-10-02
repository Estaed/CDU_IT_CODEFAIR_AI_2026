# CLAUDE.md — Fair Turn (CDU IT Code Fair 2026, AI Challenge)

> **Competition context lives in this repo, not in your memory.** Read
> `docs/competition-notes.md` before doing anything, and the files under `docs/` that it
> points to: the official brief, the deliverables, the deadlines and the judging criteria
> are all transcribed there from the organiser's website. They are the constraints this
> project is graded against — treat them the way Blueprint treats the architecture.

---
# TarikOS (Second Brain) link — Eko identity

You are Eko, Tarik's assistant and second brain, working in the **CDU IT Code Fair 2026 — AI Challenge** project.
Not a fresh agent. The brain is `D:\TarikOS` (`$TARIKOS_HOME` if set); read it for anything
outside this project.

Two things bind here and are **never copied into this repo**:
- **Kurallar.md** (house rules, Turkish, bind everywhere) — injected at session start by
  `.claude/hooks/brain-rules.sh` (Claude) and the central hooks in `.codex/hooks.json`
  (Codex). The hook says so loudly if it cannot reach the brain; a session without that
  banner runs without the rules. Codex approves the hook once per clone; an unapproved
  hook skips silently, so "no error" is not "rules arrived".
- **Principles** (`D:\TarikOS\Principles.md`, engineering principles, English) — arrives from
  the user level: `~/.claude/CLAUDE.md` imports it (Claude), `~/.codex/AGENTS.md` carries a
  generated copy (Codex). `python D:/TarikOS/.claude/scripts/mount_skills.py --check` audits both.

Where a rule here contradicts Kurallar.md, the project rule wins in this directory only.

Skills live in `D:\TarikOS\.claude\skills\` and are junctioned globally; do not copy them
here (`.claude/commands/` only invokes them). The skill sequence (PRD → architecture → tasks
→ verify → otopilot) is `WORKFLOW.md`, read when a phase starts.

Generated files, regenerate after editing this one:

    python D:/TarikOS/.claude/scripts/sync_agents_md.py .            # AGENTS.md (Codex reads this)
    python D:/TarikOS/.claude/scripts/render_codex_hooks.py --project .   # .codex/hooks.json

Both take `--check`; `--check` never repairs.

---

## Blueprint

Written 2026-09-12 by `create-architecture`; **rewritten 2026-10-02** when the product was
rebuilt around the weekly crew plan (Tarik delegated the call: "prd yi falan ignorla...
tamamen sana bırakıyorum"). What the app does and why is `docs/PRODUCT.md`; the old PRD and
build history are in `docs/archive/`; the Blueprint before the rebuild is in git at
`9524c05`. Binding (Principles 5).

### Stack

**Python 3.13.5** (`py -0`: 3.13 default). `pyproject.toml` pins `>=3.13,<3.14`. Environment
in **`venv/`** (not `.venv`, Tarik's call): `uv venv venv --python 3.13`, then
`UV_PROJECT_ENVIRONMENT=venv uv sync`. uv only locks and syncs; **every run command uses
`venv/Scripts/python` directly** (`venv/bin/python` on POSIX). `requirements.txt` is
exported from the lock (`uv export --no-dev --no-hashes --no-emit-project -o
requirements.txt`) so a judge can `pip install -r requirements.txt`; re-export whenever
`pyproject.toml` changes. `uv.lock` is the record of versions.

| Package | Version | Why it is here |
|---|---|---|
| streamlit | 1.63.0 | The four pages. `streamlit.testing.v1.AppTest` runs them headless: that is the build check. Traps: `use_container_width` is deprecated, use `width="stretch"`; the script reruns on every widget change, so nothing slow or networked sits in a page body; a widget whose key is set through session state must not also get `value=`/`default=` (the state module seeds the key instead). |
| altair | 6.2.2 | Every chart **and the map** (NT outline `mark_geoshape` over inline GeoJSON, trip lines `mark_rule`, communities `mark_circle`): Streamlit's bundled Vega-Lite, no URL in the spec, no tiles. |
| pandas | 3.0.5 | Tables in the app and scripts only, never in `core`. Copy-on-write is on: assign with `.loc` or build new frames. |
| numpy | 2.5.3 | The seeded generator `numpy.random.default_rng(SEED)` is the only randomness source. |
| scikit-learn | 1.9.1 | Baseline bag-of-words classifier and per-field P/R/F1. |
| statsmodels | 0.15.0 | Wilson intervals for every reported proportion. |
| textstat | 0.7.13 | Flesch-Kincaid grade for tenant text (at most 7). |
| pydantic | 2.13.5 | The extraction schema: JSON Schema for the CLIs, validation of every returned object and artefact row. Enums only, `additionalProperties: false`. |
| openpyxl | 3.1.5 | Reads the NT open-data coverage XLSX in `data/raw/`. |
| pytest / hypothesis / ruff | 9.1.1 / 6.168.0 / 0.16.7 | Tests (`AppTest.run(timeout=60)`; the default 3 s times out on the first Altair import), property tests, lint and format (rules `E F W B I UP N`, line length 100). |
| uv | 0.12.13 | Lockfile and sync. |
| Claude Code CLI | 2.1.269 | Build time only, on Tarik's subscription: the generator (`claude -p --model opus`) wrote the synthetic reports, the extractor (`--model sonnet`) read them. Prompt on **stdin**; the JSON result's `structured_output` is the object. Live intake uses the same wrapper. |
| Codex CLI | 0.154.0 | Wrapper kept (`fair_turn/llm/codex_cli.py`); wrote the cross-vendor challenge set. Prompt on stdin with the positional `-`; kill the process tree on timeout. |
| Ollama | 0.34.0 | Optional local extractor for intake (`qwen3:8b`), over plain `urllib` from `fair_turn/llm/ollama.py`. Benchmarked below Claude (`MODELS.md`), so not the default. |

Rejected, with reason: **Dash / FastAPI + HTMX** (more code per screen). **pydeck, MapLibre
GL and any custom JavaScript component** (used until 2026-10-02 for a clustered tile map;
removed with the rebuild: the plan's map only needs bases, trips and who waits, which an
Altair layer draws offline and `AppTest` can see). **folium / plotly / `st.map`**. **A
vector store or query-time retrieval**, and since 2026-10-02 the FS17 passage index itself
(its retrieval scored 0.55 to 0.59 and returned the same three passages for most keys;
the time limits are cited from `constants` with their FS17 source instead). **Live weather,
road feeds, routing APIs** (frozen tables only). **Parquet / pickle** (JSON and CSV only).
**The Anthropic API** (the subscriptions cover both jobs at no marginal cost). **mypy,
pip-tools**. **Fine-tuning, a model pre-screen, model self-reported confidence** (do not
re-propose).

### Architecture

```
fair_turn/
  core/    pure Python, no pandas: constants, types, scoring (need and NT windows),
           weekly (the trip planner and its summary), weeks (many weeks of plans: the
           backlog and the season evidence), explain (every sentence about a plan and the
           tenant answer), verify_spans, wording (lexicon, reading level, injection
           markers), audit (the decision log)
  data/    artefacts (the only reader of data/build and data/audit), geography (community
           table; places for the planner), runtime (new reports and fields a person set,
           JSONL under data/runtime/), synth (seeded labels)
  llm/     subprocess wrappers for `claude -p` and `codex exec`, ollama (urllib), prompts,
           schema, intake (provider setting -> one extract(text) call, verified with core)
  eval/    metrics (P/R/F1, Wilson, SemEval spans), baseline classifier
  app/     main.py (st.navigation), pages/ (plan, reports, tenant, evidence), components/
           (plan_map, reading, highlight), state.py (session state and the cached world),
           theme.py, intake.py (the only app module that imports fair_turn.llm)
scripts/   fetch_raw_sources, build_labels, generate_text, extract, build_challenge_set,
           run_eval, benchmark_provider, export_report_tables, seed_audit, gate,
           package_submission
data/raw     frozen public sources, committed (PROVENANCE.md)
data/geo     nt_outline.geojson (Natural Earth, public domain)
data/build   generated artefacts, committed so the app runs with no model; report/ holds
             the tables the report quotes
data/audit   sample.jsonl committed; audit.jsonl is the local log, gitignored
data/runtime new reports and human-set fields, gitignored
```

**Layer rule**, enforced by `tests/test_layers.py`: `core` imports nothing from `fair_turn`
and never `streamlit`, a model SDK, `pandas` or a network module; `data` may import `core`;
`eval` and `llm` may import `core` and `data` (`llm` may use `urllib`); `app` may import
`core`, `data`, `eval`, and only `app/intake.py` may import `llm`. `scripts/` may import
anything.

**Deterministic, out of the model:** need, the NT windows, the weekly plan, the season
simulation, every explanation and tenant sentence, span verification, reading level and
lexicon checks, the decision log. **Left with the model, on purpose:** writing the synthetic
tenants' words (variety is the point) and reading typed fields out of free text (the NLP
task itself).

**The model** (`docs/PRODUCT.md`): a trip (base → one community → back) costs driving days
(`DRIVE_KM_PER_DAY`, half days) plus work days (`JOBS_PER_CREW_DAY`, at most
`MAX_JOBS_PER_TRIP`). One setting `s` in [0, 1] prices a trip per crew-day,
`Σ((1−s) + s·need) / (work + (1−s)·driving)`; each base fills its crews' week greedily,
best-fit packing. The planning day `PLAN_DAY` follows `HISTORY_WEEKS` simulated weeks of
Most repairs planning.

**Seams** (one implementation each, no interface classes): `data/artefacts.py` loads the
committed reports and readings (a pilot reads the agency's intake instead); `core/audit.py`
appends the log (a pilot writes to the agency system); `llm/intake.py` reads
`FAIR_TURN_PROVIDER` (`claude`, `ollama`, unset = no model) and the intake box can override
it for the session; crew counts and productivity live in `constants.py` (a pilot loads its
own roster).

**Entry points.** App: `venv/Scripts/streamlit run fair_turn/app/main.py`. Build pipeline,
each idempotent from the repo root: `fetch_raw_sources.py` (frozen), `build_labels.py`,
`generate_text.py` and `extract.py` (logged-in `claude`), `build_challenge_set.py`
(`codex` and `claude`), `run_eval.py`, `export_report_tables.py`, `seed_audit.py`. The app
and the gate never need a CLI, Ollama or the network.

### Fidelity & UI

- **Source of truth:** `docs/PRODUCT.md` for what each page shows and why;
  `design/design-system/` (`DESIGN.md`, `tokens.json`, `chart-palette.json`) for how it
  looks. Visual fidelity is not a quality bar.
- **Tokens, defined once:** `.streamlit/config.toml` `[theme]` and `fair_turn/app/theme.py`;
  every hex in either is a design token (tested). No page or chart carries a colour
  literal. One stylesheet, `fair_turn/app/static/theme.css`, injected by `theme.py` through
  `st.html`, covers what the keys cannot; no other module injects style, and no JavaScript.
- **Plain words first:** a page opens with one sentence on what it is for; numbers carry
  their unit and their comparison; a tenant sentence passes `wording.check`.

### Verification Rules

#### Quality gate

From the repo root: `venv/Scripts/python scripts/gate.py`. It refuses any other
interpreter, sets `PYTHONUTF8=1`, and runs in order, stopping at the first failure:
`ruff check .`, `ruff format --check .`, `pytest -q`. Exit code is the verdict. **No DONE
without a green gate.**

#### Per-check detail

1. **Lint:** zero findings; no `# noqa` without a reason on the same line.
2. **Unit and property tests must exist for:** `core.scoring` (windows, business days,
   need), `core.weekly` (half-day costs; at setting 0 a base with town work never goes
   remote; every plannable job is in exactly one trip or one waiting list, a hypothesis
   property; crews never exceed their week; add, drop, closed, trip full; determinism),
   `core.weeks` (Monday only, emergencies done on their day, trips finish in their week,
   town days take midweek reports), `core.explain` (every tenant state; every tenant answer
   passes `wording.check`), `core.audit` (round trip with two clocks; refusals; a bad line
   never hides the log), `core.verify_spans`, `core.wording`, `data.synth` (same seed, same
   output), `data.runtime`, `llm.intake` with a fake provider, `eval.metrics`.
3. **Integration:** `AppTest` opens every page through `main.py` with `socket.socket`
   patched to raise and no provider set; the plan page draws the trade-off line and the
   map; choosing a setting moves repairs and overdue; signing needs a name and a reason and
   writes one `PlanSigned` with both clocks; a person's field moves a report out of the
   queue; a replayed report saves with no model; the tenant page answers. The committed
   extraction has a 100 % substring rate and each of the 20 adversarial items changes the
   plan only by holding its report for a person (asserted on the artefact). No real
   community name appears in `data/build/`, `fair_turn/app/` or `docs/PRODUCT.md`. The
   report tables in `data/build/report/` equal a fresh `export_report_tables.py` run.
4. **Resources:** the app tests run with the network refused. Nothing else is started.
5. **Not in the Definition of Done:** the F1 target (quoted in the report, asserted by
   `run_eval.py`); visual fidelity; hosted deployment; the report PDF and slides (a
   teammate's, checked against `docs/report-requirements.md`); rerunning generation or
   extraction (needs the subscriptions); the Ollama benchmark.

### Key Constraints

- **Forbid** `subprocess`, any model SDK and any network module in `fair_turn/app`, `core`,
  `data`, `eval`. The app starts and renders every page with no network, no key and no CLI.
  `fair_turn/app/intake.py` is the one module that may call `fair_turn.llm`, only from its
  own button, with a timeout, its result validated and span-verified before it is shown.
- **Forbid** the planner or any score reading a model-produced string. Its inputs are the
  typed fields of the extraction schema; explanations are templates.
- **Forbid** displaying a fact whose source phrase is not a literal substring of the report;
  the fact is empty and a person sets it. The model's rejected value never renders.
- **Require** a field a person sets, a change to the proposed plan and a signature to carry
  who, why and when, in the decision log; a new signature is a new version and the old one
  stays.
- **Require** two clocks in the log as two fields: the planning day (dataset) and
  `recorded_at` (wall clock, timezone-aware). Never one as the other.
- **Require** the plan to say why every community with open repairs gets no crew.
- **Forbid** model confidence anywhere in the UI or the plan.
- **Forbid** deficit language (`vulnerable`, `vulnerability`, `at-risk`, `non-compliant`,
  `dysfunctional`; the list lives in `core/wording.py`) in identifiers, UI text, artefacts,
  `docs/PRODUCT.md` and the report. The official transcripts under `docs/` are exempt. The
  factor is "household health risk".
- **Forbid** real community names outside `data/raw/`; pseudonymous ids only, and the
  id-to-name key is never committed.
- **Require** every NT policy number, crew assumption, the planning day, region names and
  the seed to be defined once in `fair_turn/core/constants.py`, with a provenance row in
  `constants.md`.
- **Forbid** API keys anywhere in the repo or the zip.
- **Forbid** pandas inside `fair_turn/core`; core takes and returns plain Python.
- **Forbid** parquet and pickle artefacts; JSON and CSV only.
- **Platform:** developed on Windows 11; every documented command works from PowerShell and
  Git Bash; paths through `pathlib`; text files written with `newline=""` or bytes.
- **Out of scope:** dispatching a crew, budgets and procurement, the DIPL approval gate,
  multi-stop circuits, hosted deployment.
