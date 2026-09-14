<!-- GENERATED FILE - DO NOT EDIT BY HAND.
     Source: CLAUDE.md. Make changes there, then run:
       python .claude/scripts/sync_agents_md.py <this-directory>
     Codex reads AGENTS.md rather than CLAUDE.md; this file is generated
     from it so the content remains identical. -->

# CLAUDE.md — Fair Turn (CDU IT Code Fair 2026, AI Challenge)

> **Competition context lives in this repo, not in your memory.** Read
> `docs/competition-notes.md` before doing anything, and the files under `docs/` that it
> points to: the official brief, the deliverables, the deadlines and the judging criteria
> are all transcribed there from the organiser's website. They are the constraints this
> project is graded against — treat them the way Part 2 treats the architecture.

---
# TarikOS (Second Brain) link — Eko identity

You are Eko, Tarik's primary AI assistant and second brain. You are currently in the
working directory of the **CDU IT Code Fair 2026 — AI Challenge** project.

1. Your real brain — your rules and general memory — lives in `D:\TarikOS`.
2. The TarikOS house rules (`Kurallar.md`) are **injected into every session here** by
   `.claude/hooks/brain-rules.sh`, registered in `.claude/settings.json`. They are not
   copied into this repo: one source of truth, and a copy drifts silently. They bind
   everywhere. Where a project rule in Part 1 / Part 2 contradicts one, the project rule
   wins **in this directory only**.
3. For anything else unrelated to this project (general knowledge, an Avenox transcript,
   a past decision), read `D:\TarikOS` directly.
4. You are not a fresh agent created for this project. You are **Eko**, working on this project.

The brain's path is resolved at runtime: `$TARIKOS_HOME` if set, else `D:\TarikOS`. If the
hook cannot find it, it says so loudly at session start rather than letting you work without
the rules and never know it. That failure mode is not hypothetical: this template hardcoded
`C:\TarikOS` until the vault moved to `D:`, and every clone silently pointed at a directory
that no longer existed.

**Codex gets the same injection.** `.codex/hooks.json` registers a `SessionStart` hook
pointing at `.claude/hooks/codex-brain-rules.cmd`, which runs the *same*
`brain-rules.sh` — one script, two CLIs, no second copy of the rule logic. The `.cmd`
shim is required, not stylistic: Codex runs hook commands **without a shell**, so a bare
`bash.exe script.sh` entry fails.

**`.codex/hooks.json` does not ship in this template, on purpose.** It is generated per
project and never hand-edited, because the command path has to be **absolute** — Codex
defines neither `CODEX_PROJECT_DIR` nor `CLAUDE_PROJECT_DIR` and runs the command without
a shell, so there is nothing to expand at runtime. A file shipped in the template would
carry the template's own path into every clone. The generator refuses to run while
`CLAUDE.md` still carries the unfilled project-name placeholder, so it cannot be
regenerated here by accident.

**Two setup steps, in this order, in the clone — after filling in the placeholders:**

    python D:/TarikOS/.claude/scripts/sync_agents_md.py .          # AGENTS.md <- CLAUDE.md
    python D:/TarikOS/.claude/scripts/render_codex_hooks.py --project .

    python D:/TarikOS/.claude/scripts/sync_agents_md.py . --check  # audit
    python D:/TarikOS/.claude/scripts/render_codex_hooks.py --project . --check

**`sync_agents_md.py` is not optional and it is easy to forget**, because forgetting it
produces no error: Codex never reads `CLAUDE.md`, so an `AGENTS.md` still carrying
the unfilled placeholder — or any later CLAUDE.md edit that was not synced — gives Codex a
different set of rules from Claude, quietly. Run the `--check` form whenever CLAUDE.md
changes.

`render_codex_hooks.py --project` also **writes the `.cmd` shim if it is missing**, so a
clone made before the shim existed repairs itself. `--check` reports `EKSIK` in a fresh
clone; that is the correct signal, not a fault — it means the setup step has not been run
yet. `--check` never repairs anything: a check that silently fixes what it finds is not a
check.

**One manual step remains per clone:** Codex asks for trust the first time it sees this
hook file, and an **unapproved hook is skipped silently** — the screen still says
`Completed`. So "no error" does not mean "the rules arrived". Approve it once in an
interactive `codex` session, or confirm the rules text actually appears in context.

Skills are not stored in this repo. They live in `D:\TarikOS\.claude\skills\` and are
junctioned into `~/.claude/skills/` and `~/.codex/skills/`, so the same version loads here.
See `.claude/skills-README.md`.

The text below defines this project's local rules and architecture (adapted from the
original CLAUDE.md for Codex).
---

## Part 1: Operational Principles & Workflow (IMMUTABLE)

**Core Workflow (Skill Routing).** Grouped by *when they run*, not numbered — only the
first group is a sequence. Nothing here is a ladder to climb once and leave behind.

**Once per project, in this order**
- **Scaffolding files**, created with the folder and grown from there: `notes.md` (raw
  dump), `reports/` (unattended research output), `BACKLOG.md` (what was deferred and
  why), `constants.md` (values that must not be retyped), `MODELS.md` (which model runs
  which lane here). Each carries its own instructions; delete the instructions, not the
  file. `constants.md` and `MODELS.md` may be deleted outright if this project genuinely
  has no such values or lanes — say so in Part 2 rather than leaving them empty.
- **`.gitattributes`** ships with the template and is not project-specific: it forces LF
  on shell scripts and CRLF on Windows launchers regardless of which OS commits, because a
  wrong-ending `.sh` fails its shebang and a wrong-ending `.cmd` can fail under cmd.exe.
- `notes.md` — before any skill runs, dump what the thing has to do while looking at it.
  Features, data sources, and the calls already being made ("not in v1", "their third
  party, our own build"). Two minutes of this is what `create-prd` needs as input; see
  the file's own instructions.
- `create-prd` — the spec, from `notes.md`, the user's inputs, or designs.
- `create-architecture` — turns the PRD into Part 2 below: the stack, the layer rule, the
  seams, the verification rules. Part 2 ships as a placeholder in this template, so this
  step is **required** before any task is written. Once Part 2 exists, amending it stays a
  decision to raise with the user rather than an edit made in passing.
- `generate-tasks` — breaks the PRD into atomic `tasks/Task-XX.md`. Refuses to run before
  Part 2 exists.

**Per task, in a loop**
- **Read the task file's `Execution` and `Lane` blocks first.** `Execution` names the agent,
  the effort and whether Plan mode opens; `Lane` carries the delegation contract (OWNS,
  MUST NOT TOUCH, GATE, DEPENDS ON). Both were written by `generate-tasks` with the PRD and
  Part 2 in view — a session reading the task cold does not have that context and must not
  re-litigate it.
- Native Plan mode — **only when the `Execution` block says so.** Map the file changes, wait
  for approval, then implement.
- `verify-task` — the goal-oriented fix loop, and **the gate**: nothing else marks a task
  DONE. **Run from the main loop, never by the lane that wrote the code** — the agent that
  produced the work must not be the one that relaxes its test.

**Unattended, when you want to leave the desk**
- `otopilot` — runs the tasks routed to `codex` with Plan mode closed, in parallel worktree
  lanes, and runs each lane's `GATE` command itself. You approve one wave plan; everything
  after that is unattended, and you come back to a report. It refuses to start on a dirty
  tree, a red baseline, a missing `Lane` block, or any unanswered blocking question — clear
  those before you walk away, not after.

**Per group of tasks, once they are green — not per task**
- `/code-review` over the accumulated diff — **not** a persona subagent: it is built to
  review a diff and takes an effort level, where a cold subagent reports every provisional
  value and deliberate omission Part 2 records as a defect. Feed it the task file and
  Part 2, and treat its findings as candidates, not verdicts.
- `review-visual` — only when the task produced something anyone looks at. Compares the
  built output against the source of truth Part 2 names, because `verify-task` cannot see a
  screen and reading the code to describe what it *would* render is the same guess that
  wrote it. Advisory like `/code-review` — never a gate.

**Any time, on their own — these are not stages and carry no place in the order**
- `idea-arena` — when the approach is genuinely open and more than one mechanism fits.
  Expensive; skip it whenever the approach is already decided or the call is cheap to
  reverse. Before the PRD its verdict is what the PRD describes; later it answers a question
  the PRD left open, and nothing about running it again means starting over.
- `research` — for a claim that can be checked: is this package maintained, does this API
  still exist, what is the current version, what is the known trap. It reports dated sources
  and hands the decision back; it never edits `docs/PRD.md`, Part 2 or a task file.
- `derin-akil` — for a problem that is stuck rather than open: a bug that survives the
  obvious fixes, a performance cliff, an architecture that will not close. It packages the
  relevant code, asks one non-agentic deep model, and then **verifies every finding against
  live code** before anything is applied. That verification half is the skill; a report from
  a model that cannot run the code is a hypothesis.
- `claude-chef` — the delegation policy itself: which tier of the stack a piece of work
  goes to. Read it before spawning subagents or Codex lanes, not after. Its mirror
  `codex-chef` applies when Codex is the main loop instead.
- `codex-swarm` — runs `codex exec` lanes directly, and generates image assets. Unlike
  `otopilot` it is not gated and not unattended: you are still at the desk. Its mirror
  `claude-swarm` spawns `claude -p` lanes from a Codex main loop.

  The prefix names **what gets spawned**, not who reads the file, and no CLI is shown the
  swarm that spawns its own kind — a Codex session reading `codex-swarm` would be reading
  "respawn yourself".

**Where the project currently stands** — which tasks are DONE, which is next — is
`docs/TASKS_INDEX.md`, never this file. Status written here goes stale within a week and
is then loaded into every session as a fact.

### 0. Three tiers of instruction — know which one you are using

A prompt, a rule and a protocol are not the same strength, and reaching for the
weak one where the strong one is needed is why the same mistake keeps returning.

1. **Prompt** — said once, in one turn. Gone next session. Fine for "use a table
   here", useless for anything that must hold every time.
2. **Rule** — written into this file or `Kurallar.md`. Survives sessions and is
   loaded into context, but it is still something the agent has to *remember to
   obey* while doing something else.
3. **Protocol** — structural. Not remembered, enforced. The work cannot proceed
   without it: `verify-task` is the only thing that marks DONE; `AGENTS.md` is
   generated from `CLAUDE.md` so the two cannot drift; a commit gate that refuses
   until the benchmark moves.

Escalate when a rule has failed twice. Repeating it louder a third time is how a
rule file grows into noise nobody reads. Ask instead: what would make this
impossible to get wrong?

Not everything deserves a protocol — they cost something to build and they bite
when the work legitimately needs an exception. Reserve them for the places where
a silent miss is expensive.

### 0. Vault / Brain Integration (Session Management)
**Projects are temporary, the Brain is permanent.**
Whenever a meaningful session ends (a task is completed, a major architectural decision is
made, or a difficult bug is resolved), you MUST NOT close the session without leaving a
trace in the vault.

- Summarize the core lessons learned, technical shifts, or completed milestones.
- **Never write to `D:\TarikOS\daily\<YYYY-MM-DD>.md` by hand.** `daily/` is owned by
  the SessionEnd flush worker; it records the conversation and the compiler later turns
  that machine log into `knowledge/`.
- Leave the relational handoff in `D:\TarikOS\850-Companion 🔮\`: PREPEND a new
  `## Session:` block at the TOP of `Last-Session.md`, update the specific active story
  in `Threads.md` rather than bulk-appending, and append a short entry to `Journal.md`
  when the session materially changes the shared story. The Last-Session archiver keeps
  only the newest three blocks live.
- Name the model in hand-written Last-Session and Journal entries.

### 1. Ask, don't assume
**Don't assume. Don't hide confusion. Surface tradeoffs.**
- If something is unclear, ask **before writing a single line**. Never make silent assumptions about intent, architecture, or requirements.
- State your assumptions explicitly, out loud, even the ones you're confident in.
- If multiple interpretations exist, present them — don't pick one silently.
- If a simpler approach exists, say so. Push back when warranted.

### 2. Simplicity first
**Simplest solution for simple problems, better solutions for harder problems. Minimum code that solves the problem.**
- No features beyond what was asked. MVP strictly.
- No abstractions for single-use code.
- If you write 200 lines and it could be 50, rewrite it.
- **The documents obey this too** — this file, the PRD, task files, skills. A paragraph that
  steers no decision gets cut; one that steers a decision in half the words gets rewritten.

### 3. Surgical changes
**Touch only what you must. Clean up only your own mess.**
- Don't "improve" adjacent code, comments, or formatting. Don't refactor things that aren't broken.
- Remove imports/variables/functions that **your** changes made unused.
- Report bad code or spec contradictions as a separate issue; do not silently fix or ignore them.
- **New files go where the existing structure already puts them.** Check what folders exist
  before creating one; a task file naming a folder that does not match reality loses to
  reality. Create a folder for 3+ related files, never for one or two that fit elsewhere,
  and say which existing folder you chose when the task named a different one.

### 4. Goal-driven execution
**Define success criteria. Loop until verified.**
- Transform tasks into verifiable goals (e.g., "Add Login validation" → "Write tests for invalid inputs, then make them pass").
- For multi-step tasks, state a brief plan up front.
- Strong success criteria let you loop independently. Implementation is not complete until `verify-task` confirms zero errors.

### 5. Flag uncertainty explicitly
If you're unsure about something, run a small, localized, low-risk experiment and bring the hypothesis *and* the results to discuss. Confidence without certainty causes damage. Say "I don't know" plainly.

### 6. Better ideas are welcome
Suggest better ways of doing things, especially ideas with lasting impact over tactical fixes. Suggest, then wait for a decision; don't unilaterally act on your own suggestion.

### 7. The repository is English-only, no matter what language we're speaking
Everything written to disk in this repo is English: identifiers (classes, methods,
variables, files, folders), comments, commit messages, test descriptions — and also
`CLAUDE.md`, `docs/`, `design/` and every `tasks/Task-XX.md`. Only the **conversation**
follows whatever language we are speaking.

Not a style preference. A codebase mixing languages in its identifiers is genuinely
harder to read later, and English is what every library and error message it will ever
consult is already written in. The documents share the constraint for a different reason:
they are read by delegate lanes, by reviewers and by whoever inherits this repo, none of
whom are in this conversation. Turkish lives in `D:\TarikOS` — the brain — and nowhere else.

### 8. Part 2 is binding until it is changed on purpose
Part 2 below is not advice; every task was written against it. When the code contradicts
it — a seam that does not fit, a pinned version that breaks, a layer rule that cannot hold
— stop and say so. Do not silently deviate, and do not edit Part 2 to match what you just
wrote: that makes the deviation invisible to every session afterwards. Changing it is the
user's call, and `create-architecture` is what amends it.

---

## Part 2: Technical Architecture

Written 2026-09-12 by `create-architecture` from `docs/PRD.md`. **Amended 2026-09-14** for
Phase 2 from the PRD amendment of the same day (five surfaces, live intake, cited policy
passages, visit plan, network allowed). Binding (Part 1 rule 8). Amendment lines are dated so
a reader can tell Phase 1 decisions from Phase 2 ones; the Phase 1 text is at `95b604b`.

### Stack

**Python 3.13.5**, verified installed 2026-09-12 (`py -0`: 3.13 default, 3.12, 3.9 also
present). `pyproject.toml` pins `>=3.13,<3.14`. Environment lives in **`venv/`** (not
`.venv`, Tarik's call): create with `uv venv venv --python 3.13`, sync with
`UV_PROJECT_ENVIRONMENT=venv uv sync`. uv is used only to lock and sync; **every run command
uses `venv/Scripts/python` directly** (`venv/bin/python` on POSIX), so nothing depends on
the env var being set. `requirements.txt` is exported from the lock (`uv export --no-dev
--no-hashes --no-emit-project -o requirements.txt`) so a judge can `pip install -r
requirements.txt` and never meet uv; re-export whenever `pyproject.toml` changes. Versions
below were read from the environment after `uv sync` on 2026-09-12; `uv.lock` is the record.

| Package | Version | Why it is here |
|---|---|---|
| uv | 0.12.13 | Lockfile and sync. Installed via `pip install uv`. |
| streamlit | 1.63.0 | The six screens. Bundles Vega-Lite and deck.gl in its own static JS (verified in `site-packages/streamlit/static/static/js`, 2026-09-12), so charts need no CDN. `streamlit.testing.v1.AppTest` runs pages headless: that is the build check. Trap: `use_container_width` is deprecated, use `width="stretch"`. Trap: the script reruns on every widget change, so nothing slow or networked may sit in a page body. |
| altair | 6.2.2 | Every chart **and the map**. Spike 2026-09-12: `mark_geoshape` over inline GeoJSON plus `mark_circle` at lon/lat renders through Streamlit's bundled Vega-Lite with no URL in the spec. Region zoom is a selectbox filter re-rendering the projection; Vega-Lite geo projections do not pan/zoom. |
| pydeck | 0.9.3 | **Added 2026-09-14; replaced as the workspace map the same night by MapLibre GL (next row), 2026-09-14 (night), Tarik's decision.** Was the workspace map: `st.pydeck_chart(deck, on_select="rerun", selection_mode="single-object")` over a `ScatterplotLayer`, Carto `light` basemap with attribution. Streamlit's own dependency, so no new pin. Spike 2026-09-14: renders through `AppTest` with `socket.socket` refused (the style URL is fetched by the browser, never by the server) and the emitted proto carries `selection_mode`. The Altair outline stays as the no-tile fallback and the map for tests. *Trap (2026-09-14, verified by execution):* pydeck turns every plain string kwarg into a data accessor (`radius_units="pixels"` serialises as `"@@=pixels"` and the layer silently falls back to metres, which is why markers were 1-3 px at NT zoom and swallowed a town when zoomed in); pass literal strings with inner quotes (`radius_units="'pixels'"`), and give every layer an explicit `id=` because `selection.objects` is keyed by layer id. |
| MapLibre GL JS | 6.9.0 | **Added 2026-09-14 (night), Tarik's decision** ("we set the JS limit ourselves"). The workspace map, because zoom-driven clustering needs client code: a cluster's size is the jobs it holds and it splits as the coordinator zooms in. Vendored, BSD-3, at `fair_turn/app/static/maplibre/` (ES modules `maplibre-gl.mjs`, `-shared.mjs`, `-worker.mjs`, CSS, licence), served by Streamlit static serving as `application/javascript`, mounted through `st.components.v2.component` (no npm build). Carto Positron style with attribution. *Spike 2026-09-14:* renders and splits clusters in headless Chrome (puppeteer-core, WebGL through SwiftShader). *Traps:* v2 loads the component module from a blob URL, so `import('/app/...')` fails; build the URL from `window.location.origin`. MapLibre 6 ships no UMD `maplibre-gl.js`. `AppTest` cannot see inside the component: tests cover the GeoJSON builder and the page wiring, and a browser script checks the map. If the module, style or tiles fail, the component reports it and the Altair outline renders instead. |
| pandas | 3.0.5 | Tables. pandas 3: strings are `str` dtype by default and copy-on-write is on, so chained assignment silently does nothing; assign with `.loc` or build new frames. |
| numpy | 2.5.3 | Transitive; the seeded generator `numpy.random.default_rng(SEED)` is the only randomness source in synthesis and simulation. |
| scikit-learn | 1.9.1 | Baseline bag-of-words classifier (TF-IDF + logistic regression) and per-field P/R/F1. |
| statsmodels | 0.15.0 | `proportion_confint(method="wilson")` for every reported proportion. |
| textstat | 0.7.13 | Flesch-Kincaid grade for tenant text (PRD §7). |
| Claude Code CLI | 2.1.269 | **Generator**, build time only, on Tarik's Claude subscription: `claude -p --model opus --output-format json --json-schema <schema>` with the prompt on **stdin** (a variadic flag such as `--tools` swallows a trailing prompt argument, and the CLI waits 3 s then errors if stdin is open with nothing on it). The JSON result's `structured_output` field is the schema-valid object. Spike 2026-09-12: one call, about 10 s, 24k cached-prompt tokens of CLI overhead per call, so reports are generated 20 per call. |
| Codex CLI | 0.154.0 | Wrapper kept (`fair_turn/llm/codex_cli.py`, tested with a fake) but **not used by the build since 2026-09-13**: Tarik chose to preserve the Codex weekly window, so the extractor is `claude -p --model sonnet` through the same wrapper as the generator (generator Opus, extractor Sonnet: the PRD's different-model rule holds, the different-vendor strengthening does not, and the report says so). Traps learned on the real run: the prompt must go on **stdin** with the positional `-` (through the `codex.CMD` shim an argv prompt is cut at its first newline); `subprocess` timeouts must kill the process tree (`taskkill /T`) or the node children hold the pipes forever; one call costs ~70-200 s whatever its size, so batch 20 reports per call. |
| Ollama | 0.34.0 | **Added 2026-09-14.** Local model server, already installed on Tarik's machine (`ollama --version`), reached over plain `urllib` at `http://localhost:11434` from `fair_turn/llm` only. Two jobs: embeddings for the policy index at build time (`bge-m3`, already pulled, 1024 dims, spike 2026-09-14: 7 s first call including model load) and, **as the last Phase 2 step only**, an intake extractor benchmark (`qwen3:8b`, 5.2 GB, **not pulled until then**, Tarik's call 2026-09-14: every earlier task runs on Claude). No Python client package: the two endpoints are a 30-line function each. |
| pypdf | 6.18.1 | **Added 2026-09-14** via `uv add pypdf`; `requirements.txt` re-exported. Reads FS17 (and any later fact sheet with a provenance row) into text for the policy index. Scripts only. |
| pydantic | 2.13.5 | The extraction schema is a pydantic model: it emits the JSON Schema both CLIs receive and validates every returned object and every artefact on load. Enums only, `additionalProperties: false`. |
| openpyxl | 3.1.5 | Reads the NT open-data coverage XLSX in `data/raw/`. |
| pytest | 9.1.1 | Test runner. `AppTest.run(timeout=60)`: the default 3 s times out on first Altair import (spike 2026-09-12). |
| hypothesis | 6.168.0 | Property test: ranking at λ = 0 is invariant under permutation of distances and road status. |
| ruff | 0.16.7 | Lint and format, rules `E F W B I UP N`, line length 100. |

Rejected, with reason, all 2026-09-12:

- **Dash**, **FastAPI + HTMX**: more code per screen; Streamlit chosen for speed and one-command run. Visual restyle stays a one-file change through the theme (Fidelity & UI).
- ~~**pydeck / `st.map`**: basemap styles are fetched from `basemaps.cartocdn.com` and the bundle carries Mapbox telemetry endpoints; bare layers with no basemap look worse than a geoshape outline.~~ *Reversed 2026-09-14:* the PRD now allows the network for the basemap; pydeck is the map (table above). `st.map` stays rejected (no selection events). **folium**: iframe with CDN Leaflet, no selection event back to Python. **plotly**: bundled, but a second chart grammar for nothing Altair lacks.
- ~~**MapLibre GL custom component** (the discovery brief's first pick, rejected 2026-09-14): needs an npm build and a custom component that `AppTest` cannot see; pydeck gives pan, zoom, markers and selection natively.~~ *Reversed 2026-09-14 (night), Tarik's decision:* pydeck cannot cluster by zoom; `st.components.v2` needs no npm build; the map's click path was already a human check, so the AppTest reason did not apply to it (stack table).
- **ChromaDB or any vector store** (rejected 2026-09-14): the corpus is one fact sheet, about a hundred chunks; retrieval runs at build time over a finite query set and the result is a JSON artefact. A store adds a native dependency with an unspiked Python 3.13 / Windows story for a `numpy` dot product. **Query-time retrieval** in the app: rejected with it, because it would put a model call in a page body and break the offline render.
- **`ollama` Python package, `httpx`, `requests`** (rejected 2026-09-14): two JSON POSTs to localhost do not earn a dependency; `urllib` from the standard library, in `fair_turn/llm` only.
- **`st.dialog` for sign-off or intake** (rejected 2026-09-14): `AppTest`'s element tree has no dialog node (grep of `streamlit/testing/v1/element_tree.py`), so nothing inside one is testable. Both are in-page containers toggled from session state.
- **mypy**: no typed boundary worth the friction in 18 days; ruff only. **pip-tools**: uv already gives the lockfile.
- **Open-Meteo / BoM live weather, NT road-report live feed, OSRM distances**: no network at demo time; road distance is undefined for barge and air communities anyway. Distances are haversine from the crew base times a road-access factor from BushTel, frozen in a build artefact.
- **Parquet / pickle artefacts**: judges read the files; JSON and CSV only.
- **Anthropic API (`anthropic` SDK, Batch API)**: worked, about 10 USD for 1,500 reports, but the subscriptions already paid for cover the same two jobs at zero marginal cost. Decided 2026-09-12; the SDK was removed from `pyproject.toml`. **OpenRouter**: a new account and key for nothing the CLIs lack. **Ollama local models**: free but untested against the F1 target and weaker text variety; the fallback if a subscription window runs dry, not the plan.
- **LLM fine-tuning, a Haiku injection pre-screen, LLM self-reported confidence**: rejected in the PRD (§5) with reasons; do not re-propose.

### Architecture

```
fair_turn/
  core/    pure Python, no pandas: constants, types, scoring, capacity_sim, feedback_sim,
           explain (sentence + tenant answer templates), verify_spans, wording (lexicon,
           reading level), audit; Phase 2 adds visit_plan (pooled crews: exact min-km crew
           assignment of the signed list, shortest stop order), assignment (exact
           min-cost assignment, pure Python), batch (frozen sign-off batch, version, invalidation), effect
           (the two-stage effect sentence)
  data/    frozen raw files in, tables out: geography, synth labels (seeded), artefact I/O;
           Phase 2 adds policy (passages artefact lookup by typed key) and runtime
           (intake and human-set records under data/runtime/, JSONL)
  llm/     subprocess wrappers for `claude -p` and `codex exec`, prompts, extraction schema;
           Phase 2 adds ollama (urllib: /api/embed, /api/chat with a JSON schema) and
           intake (provider setting -> one extract(text) call, verified with core)
  eval/    metrics (P/R/F1, Wilson, SemEval spans), baseline classifier, result tables
  app/     main.py (st.navigation), pages/ (one file per PRD section 3 surface: workspace,
           review_queue, visit_plan, tenant, evidence_lab), components/, theme.py,
           state.py; intake.py is the only app module that imports fair_turn.llm
scripts/   fetch_raw_sources.py, build_labels.py, generate_text.py, extract.py,
           run_eval.py, gate.py; Phase 2 adds build_policy_index.py
data/raw     frozen public sources, committed (PROVENANCE.md); Phase 2 adds the FS17 PDF
data/geo     nt_outline.geojson from Natural Earth admin-1 (public domain), fetched by script
data/build   generated artefacts (labels, report text, extraction, eval), committed so the
             app runs with no key; Phase 2 adds policy_passages.json
data/audit   audit log, JSONL; a seeded sample committed, runtime appends locally
data/runtime intake reports and human-set fields, JSONL, gitignored (Task 23 adds the rule)
tests/
```

**Layer rule**, enforced by `tests/test_layers.py`: `core` imports nothing from
`fair_turn` and never `streamlit`, `anthropic`, `pandas` or any network module; `data`
may import `core`; `eval` and `llm` may import `core` and `data`; `app` may import
`core`, `data`, `eval` and never `subprocess`, a model SDK or a network module. `scripts/`
may import anything. A violation fails the gate. *Amended 2026-09-14:* `llm` may import
`urllib` (Ollama); **exactly one** app module, `fair_turn/app/intake.py`, may import
`fair_turn.llm`, and nothing under `app/pages/` or `app/components/` may. Task 23 changes
the test to say so; until then the old rule holds and intake code cannot land.

**Deterministic steps pushed out of the model:** label drawing, scoring, the capacity
simulation, the feedback simulation, both explanation texts, span verification, reading
level and lexicon checks are plain Python. *Added 2026-09-14:* the effect sentence (a
template over two rankings), the visit plan (min-km crew assignment of the signed list; distance picks the crew, never the job), the
sign-off batch freeze and invalidation, and **policy retrieval**: the query is not the
report text but the job's typed key (safety class × town/remote × fault type), a finite
set, so `build_policy_index.py` embeds the chunks and every query once, applies the
threshold, and writes the top passages per key to `data/build/policy_passages.json`; the
app looks them up. Left with the model, on purpose: writing the tenant's words (natural
variety is the point) and reading typed fields out of free text (the NLP task itself). The
first runs once from `scripts/`; the second runs from `scripts/` for the synthetic set and
from `app/intake.py` for a submitted report, through the same schema and verification.

**Seams** (the PRD's deferred pilot decisions need exactly these; one implementation each,
no interface classes):

- `data/artefacts.py` loads reports and extractions from `data/build/`. A pilot would read
  intake instead. Today: JSON files.
- `core/audit.py` appends and exports the log. A pilot would write to the agency system.
  Today: JSONL under `data/audit/`.
- `app` reads extraction from artefacts only. Build time: Codex CLI; the no-model
  fallback for the report's comparison table is the baseline classifier in `eval/`.
  *Amended 2026-09-14:* plus `data/runtime/` for reports submitted in the app; the
  artefact loader merges both, and a pilot would replace the runtime file with intake.
- *Added 2026-09-14:* `llm/intake.py` reads `FAIR_TURN_PROVIDER` (`claude`, `ollama`, or
  unset = no provider, intake disabled with the reason) and calls one wrapper. Default
  `claude` (Sonnet through the existing wrapper) for every Phase 2 task; the last task
  scores `qwen3:8b` on the same 150-item and adversarial tables, and Ollama becomes the
  default only if it is not below Claude on both required fields (PRD §5, "running is
  not acceptance"). Nothing before that task pulls or calls an Ollama chat model. Not a
  secret, so an environment variable, documented in the README, never `secrets.toml`.
  *Amended 2026-09-14 (Task-48, Tarik's request):* the intake container offers a provider
  selectbox (`none`, `claude`, `ollama`) that overrides the variable for the session only,
  through `configured(override=...)`; the variable stays the default and nothing is
  written to disk. Still no model call outside the intake action.
- *Added 2026-09-14:* `data/policy.py` reads `policy_passages.json`. A pilot with a
  bigger corpus would swap the build script for a live index behind the same lookup;
  today a JSON file keyed by the typed key.

**Entry points.** App: `venv/Scripts/streamlit run fair_turn/app/main.py`; pages registered
with `st.navigation` in `main.py`. Build pipeline, in order, each idempotent from the repo
root: `fetch_raw_sources.py` (done, frozen), `build_labels.py`, `generate_text.py` (needs a
logged-in `claude`), `extract.py` (needs a logged-in `claude`; Sonnet), `run_eval.py`,
*added 2026-09-14:* `build_policy_index.py` (needs a running `ollama` with `bge-m3`; writes
`data/build/policy_passages.json`, committed). The app and the gate never need a CLI or
Ollama; with `FAIR_TURN_PROVIDER` set, intake needs the named one.

**Spikes.**
- *Question:* can the map render with no network? *Spike (2026-09-12):* Altair geoshape +
  circles over inline GeoJSON through `AppTest`; the emitted Vega-Lite spec contains no
  `url`, two layers, features inline; Streamlit serves Vega-Lite from its own bundle.
  *Result:* Altair for the map, no basemap, NT outline from a local file.
- *Question:* can the two subscription CLIs return schema-valid JSON non-interactively?
  *Spike (2026-09-12):* one call each with a three-field enum schema; both returned a valid
  object (`structured_output` from `claude -p`, `-o out.json` from `codex exec`). Both
  block when stdin is left open. *Result:* subscriptions replace the API; every wrapper
  passes the prompt on stdin (Claude) or closes stdin (Codex) and validates with pydantic.
- *Question:* does `AppTest` work as the build check? *Spike:* same run; passes with
  `timeout=60`, times out at the default 3 s. *Result:* AppTest is the build step, with the
  explicit timeout.
- *Question (2026-09-14):* can pydeck carry the workspace map without breaking the offline
  gate? *Spike:* `st.pydeck_chart(on_select="rerun")` and `st.dataframe(on_select="rerun")`
  through `AppTest` with `socket.socket` refused. *Result:* no exception, one deck element
  with `selection_mode` in its proto, Carto style URL left to the browser. `AppTest` has no
  API to simulate a selection on either widget, so sync tests set the session's selected id
  and assert the pane; the click path is a human check in Task 22 and `review-visual`.
- *Question (2026-09-14):* is Ollama usable from the standard library? *Spike:* one
  `urllib` POST to `/api/embed` with `bge-m3`, two inputs. *Result:* 1024-dim vectors, 7 s
  including model load. *Not spiked yet:* `/api/chat` with `format=<JSON schema>` for
  extraction; the last Phase 2 task owns it, with the decision rule above.
- *Question (2026-09-14):* can a dialog be tested? *Spike:* grep of the AppTest element
  tree. *Result:* no dialog node; sign-off and intake are in-page containers.

### Fidelity & UI

- **Source of truth:** `docs/PRD.md` section 3 for what each surface shows and which rules
  bind it; *added 2026-09-14:* `design/phase-2-wireframes.md` (§3–§9) for layout,
  controls, states and the keyboard path; `design/design-system/` (added 2026-09-12:
  `DESIGN.md`, `tokens.json`, `chart-palette.json`) for how it looks. On a conflict the
  PRD wins, then the wireframes. One wireframe deviation is fixed here, not there: the
  intake "dialog" is an in-page container (spike above). `tokens.json` maps 1:1 onto the `[theme]` keys
  in `.streamlit/config.toml`; `chart-palette.json` is the source of `theme.py`. The
  design's "Unverified" state does not exist in this product: an unverified field is
  empty and the job goes to the human queue (Key Constraints). Visual fidelity is not a
  quality bar.
- **Tokens, defined once:** `.streamlit/config.toml` `[theme]` (primary, background, text,
  font) and `fair_turn/app/theme.py` (chart palette: region colours, town/remote pair,
  factor colours, the "needs a human" colour). No page or chart carries a colour, size or
  font literal; a test greps `fair_turn/app` for hex literals outside `theme.py`. This is
  what makes a later restyle a one-file change.
- **Deviations:** the design's `Known Gaps` list (card padding, 48 px touch targets) is
  accepted as-is; Streamlit fixes those. *Amended 2026-09-14 (Tarik's decision after the
  UI research in `reports/research-ui-*-2026-09-14.md`):* the look is a government
  internal tool, set through `[theme]` keys first (`[theme.sidebar]`,
  `dataframeHeaderBackgroundColor`, `headingFontSizes`, `metricValueFontSize` and the
  rest reach six of the seven properties that matter); one scoped stylesheet,
  `fair_turn/app/static/theme.css`, injected by `theme.py` through `st.html` only, covers
  what the keys cannot (the tab underline and nothing structural). No JavaScript, no
  animation, no `st.markdown(unsafe_allow_html=True)` (it adds a phantom `markdown` node
  to every AppTest tree; `st.html` adds an `html` node reachable by `at.get("html")`).
  Every `data-testid` selector in that file is unofficial and carries a comment saying
  which Streamlit version it was checked against.
- **`review-visual`** compares a screen against PRD section 3 prose and stays advisory. It
  never gates.

### Verification Rules

#### Quality gate

From the repo root: `venv/Scripts/python scripts/gate.py` (run once, green, 2026-09-12).
It refuses to run under any other interpreter, sets `PYTHONUTF8=1` for its children, and
runs in order, stopping at the first failure: `ruff check .`, `ruff format --check .`,
`pytest -q` (unit, property and AppTest smoke tests together). Exit code is the verdict.
**No DONE without a green gate.**

#### Per-check detail

1. **Lint:** `ruff check .` and `ruff format --check .` from the repo root report nothing.
   Zero findings, no `# noqa` without a reason on the same line.
2. **Unit tests must exist for:** `core.scoring.score_job` and `rank`,
   `core.capacity_sim.simulate`, `core.feedback_sim.run`, `core.explain.why_sentence` and
   `tenant_answer` (every scored factor appears in the text), `core.verify_spans.verify`
   (substring rule, empty on failure), `core.wording.check` (lexicon and FK grade at most
   7), `core.audit` append/export round-trip, `data.synth.draw_labels` (same seed, same
   output), `eval.metrics` (P/R/F1, Wilson CI, SemEval exact/partial). Property test with
   hypothesis: at λ = 0 the ranking is unchanged under any permutation of distances and
   road status. Any job with an empty required field is in the human queue and not in the
   ranked list. *Added 2026-09-14 (PRD §7):* `core.visit_plan.plan` (membership equals
   the signed list, overflow leaves the lowest signed ranks unplanned and never the
   farthest, each crew's stop order is the brute-force shortest route, every edit carries
   a reason and the batch version; hypothesis over random signed lists; *amended
   2026-09-14 night*), `core.assignment` (equals brute force on small matrices),
   `core.capacity_sim` (with k free crews the day's served communities are the first k in
   rank order under any permutation of crew bases), `core.batch`
   (freeze, invalidate on any change, reject a second submit of the same version),
   `core.effect.sentence` (no wait or travel words before the first signature),
   `core.audit` (recorded-at is a real timestamp, decision day is the dataset day),
   `data.policy.lookup` (every passage a literal substring of its indexed document,
   carries title, section, effective date), `data.runtime` (a human-set field removes
   the job from the queue and enters the ranking), `llm.intake` with a fake provider
   (schema-invalid and timed-out results land in the queue as "not extracted"; the same
   draft token never writes twice), and the review-queue text renders no enum value for
   an unverified field.
3. **Integration:** `AppTest` opens every page in `fair_turn/app/pages/` against the
   committed `data/build/` artefacts, `timeout=60`, asserts no exception and at least one
   Vega-Lite chart on the board and simulation pages. *Added 2026-09-14:* with
   `FAIR_TURN_PROVIDER` unset, the workspace shows intake disabled with its reason; the
   provenance caption is on every page; wait and travel metrics are absent before a
   signature and present after one made through the form; the visit plan refuses before
   a signature. The committed extraction artefact has
   a 100 % substring-verification rate and the 20 adversarial items leave the rank
   unchanged (asserted on the artefact, so the gate needs no API key). No real community
   name from `data/raw/` appears in `data/build/`, `fair_turn/app/` or `docs/PRD.md`.
   *Added 2026-09-14 (measured on Streamlit 1.63.0):* `st.expander` emits an `expander`
   node, found with `at.get("expander")` (*corrected 2026-09-14 night*: an earlier line here
   said `status`; `st.status` is the one that emits `status`), `st.badge` emits a `markdown` node
   (`at.badge` raises), `st.html` is found with `at.get("html")`; page tests assert
   through those nodes.
4. **Resources:** the AppTest smoke test runs with `socket.socket` patched to raise, so any
   network call fails the gate. Nothing else is started.
5. **Not in the Definition of Done:** the F1 target of 0.85 (asserted by `run_eval.py`'s
   exit code and quoted in the report, not by the gate, because it needs an API run);
   visual fidelity; hosted deployment; the report PDF and slides (human checklist against
   `docs/report-requirements.md`); licence confirmation for the road report (the remaining
   part of PRD open question 1); rerunning generation or extraction (needs the subscriptions).
   *Added 2026-09-14:* the click path of list ↔ map ↔ pane selection (no AppTest API; a
   human check in Task 22 and `review-visual`; *added 2026-09-14 night:* the clustered map
   is checked by a headless-Chrome script that saves screenshots under `design/screenshots/`); the Ollama extraction benchmark (the last task's
   exit code, quoted in the report); rebuilding the policy index (needs Ollama); the
   basemap actually loading (needs network; a human check before the demo).

### Key Constraints

- **Forbid** `subprocess`, any model SDK and any network module in `fair_turn/app`,
  `core`, `data`, `eval`. The app must start and render every page with no network, no
  API key and neither CLI installed. *Amended 2026-09-14:* `fair_turn/app/intake.py` is
  the one exception and imports `fair_turn.llm` only; the offline render requirement is
  unchanged and is what the smoke test asserts.
- **Forbid** any model call in a Streamlit page body or callback. *Amended 2026-09-14:*
  the single exception is the intake action in `app/intake.py`, triggered by its own
  button, with a timeout, its result validated and span-verified before anything renders.
  Ranking, explanations, the tenant answer and policy lookup never call a model. Build
  model work still happens in `scripts/` only, writes to `data/build/`, and is committed.
- **Forbid** the rejected model value from rendering anywhere; an unverified field is
  empty and the value stays in the extraction audit record.
- **Require** a human-set field to carry actor, reason and time and to render with the
  "Set by coordinator" badge.
- **Forbid** the visit plan from changing membership of the signed list. *Amended
  2026-09-14 (night), Tarik's decision:* **distance decides which crew goes, never which job is served or
  when**, in the visit plan and the capacity simulation alike; when road jobs exceed crew
  slots the lowest signed ranks stay unplanned, never the farthest. A coordinator's stop
  edit needs a reason and references the batch version.
- **Require** two clocks in the audit log as two columns: decision day (dataset) and
  recorded-at (wall clock, ISO 8601). Never write one as the other.
- **Forbid** API keys anywhere in the repo or the zip. Model access is the two logged-in
  CLIs on Tarik's machine, called only from `scripts/` through `fair_turn/llm`; a judge
  rerunning the build needs their own `claude` or `codex` login, and the README says so.
- **Forbid** the ranking function reading any model-produced string. Its inputs are the
  typed fields of the extraction schema; explanations are templates over score factors.
- **Forbid** displaying a field whose source phrase is not a literal substring of the
  report; the field is empty and the job goes to the human queue.
- **Forbid** model confidence anywhere in the UI or the score.
- **Forbid** deficit language (`vulnerable`, `vulnerability`, `at-risk`, `non-compliant`,
  `dysfunctional`; the list lives in `core/wording.py`) in identifiers, UI text, artefacts,
  `docs/PRD.md` and the report. The official transcripts under `docs/` quote the
  organiser verbatim and are exempt. The factor is "household health risk".
- **Forbid** real community names outside `data/raw/`. Pseudonymous ids only; the
  id-to-name key is never committed.
- **Require** every NT policy number (window days, the 4 h make-safe, AUD 500), crew
  capacities, the date window, region names and the seed to be defined once in
  `fair_turn/core/constants.py`, with provenance rows in `constants.md`. No literal copies.
- **Forbid** hex colours, sizes and fonts outside `.streamlit/config.toml`,
  `fair_turn/app/theme.py` and, *added 2026-09-14*, `fair_turn/app/static/theme.css`
  (the only stylesheet; injected by `theme.py` with `st.html`; a test asserts no other
  module calls `st.html` with a `<style>` tag or `st.markdown` with
  `unsafe_allow_html`). ~~JavaScript, custom bidirectional components and npm builds
  stay forbidden: `AppTest` cannot see them.~~ *Amended 2026-09-14 (night), Tarik's decision:* exactly one
  JavaScript component, the workspace map (`app/components/cluster_map.py` + `.js` over
  vendored MapLibre), styled only inside its shadow root with the vendored MapLibre CSS
  and receiving every colour from `theme.py` through its data (no hex literal in the JS,
  tested). npm builds and any other custom component stay forbidden.
- **Forbid** live weather and road requests; frozen tables only. *Amended 2026-09-14:*
  map tiles are allowed from the map component only (pydeck until 2026-09-14 night,
  MapLibre after), with attribution, and the outline
  fallback must render when they do not load. Nothing in the server process fetches a tile.
- **Forbid** the policy index from being queried with report text; the key is typed fields
  and the lookup is a file read.
- **Forbid** parquet and pickle artefacts; JSON and CSV only.
- **Forbid** pandas inside `fair_turn/core`; core takes and returns plain Python.
- **Out of scope this phase:** everything in PRD section 8. Do not build a router, an
  intake integration, the DIPL gate or a hosted deployment.
- **Platform:** developed on Windows 11; every documented command must work from PowerShell
  and Git Bash; paths through `pathlib`; text files written with `newline=""` or bytes.
- `MODELS.md` stays empty until a delegation lane is actually measured here; the two API
  models are stack decisions and live in the table above.
