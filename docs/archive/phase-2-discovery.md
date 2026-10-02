# Fair Turn Phase 2 — Product Redesign Decision Brief

**Status:** Draft for discussion; not yet binding

**Checked:** 2026-09-13

**Scope:** Product workflow, interface, online services, live AI, retrieval, and route planning

> This document uses “Phase 2” to mean the next delivery phase after Tasks 00–21. It is
> not a replacement for `CLAUDE.md` Blueprint. After the decisions below are approved,
> `docs/PRD.md` and the binding architecture must be amended deliberately, then new work
> starts at Task 22.

## 1. Why Phase 2 exists

Phase 1 proves the core idea but does not yet feel like a product a housing maintenance
coordinator would use. The main problem is not colour. It is the information architecture:

- six screens expose project concepts instead of supporting one operational workflow;
- the ranking table, map, job evidence, human review, and sign-off feel disconnected;
- controls such as the equity weight require the user to understand the implementation;
- the current map cannot pan or zoom and does not help plan work;
- large raw tables and identifier lists make the user interpret the system instead of the
  system helping the user decide;
- evaluation and simulation material compete with the coordinator's primary task.

The Phase 2 goal is to turn the prototype into a **dispatcher decision workspace**: one
place to understand the queue, inspect evidence, make the equity trade-off visible, approve
the order of work, and prepare a practical visit sequence.

## 2. Product definition

Fair Turn is a trusted-AI decision-support tool for a housing maintenance coordinator in
remote Northern Territory communities.

It should:

1. accept a new free-text repair report;
2. extract typed facts and show the exact phrases supporting them;
3. send missing or unverifiable facts to a human review queue;
4. rank valid jobs using a deterministic formula that balances urgency, safety, waiting
   time, and logistics;
5. make the effect of the equity setting visible rather than hiding it;
6. let the coordinator approve or override the proposed order;
7. turn approved work into a feasible suggested visit sequence; and
8. provide a plain-language, evidence-backed explanation for the tenant.

The AI reads and retrieves. Deterministic code ranks and checks constraints. A human owns
the operational decision.

## 3. UX north star

Field-service products commonly connect a work list, a map or schedule, and a details pane.
The useful pattern is not a generic analytics dashboard; it is a synchronized workspace in
which selecting a job updates every relevant view.

### Primary coordinator workspace

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Fair Turn   Live intake status   4 need review   Last update   New report   │
├───────────────┬─────────────────────────────────┬────────────────────────────┤
│ Filters       │ Ranked work / Map / Route plan  │ Selected job              │
│               │                                 │                            │
│ Region        │  1  FT-014  Immediate           │ Evidence from report       │
│ Trade         │  2  FT-088  Urgent              │ Score factors              │
│ Safety class  │  3  FT-031  Routine             │ Why this position?         │
│ Access mode   │                                 │ Review / approve / override│
├───────────────┴─────────────────────────────────┴────────────────────────────┤
│ Decision impact: 12 remote jobs moved earlier; estimated travel +4.2 hours │
└──────────────────────────────────────────────────────────────────────────────┘
```

Required behaviours:

- list selection highlights the map marker and opens the same job in the details pane;
- map selection scrolls to the corresponding job;
- zoom and clustering work normally;
- the default view shows what needs a decision now, not every available metric;
- the equity control uses named presets and a plain-language effect summary; the numeric
  value remains available under an advanced control;
- sign-off is a reviewable batch with counts and exceptions, not a comma-separated list of
  identifiers;
- every model-extracted field can be checked against highlighted source text;
- empty states explain the next action and never leave a blank page.

### Secondary surfaces

- **Review queue:** incomplete or unverifiable reports, with side-by-side source and fields.
- **Route plan:** approved jobs grouped into a proposed visit order for each crew.
- **Tenant answer:** a focused lookup and explanation surface, separate from dispatch tools.
- **Evidence lab:** model evaluation, fairness simulation, and audit export. This supports
  judges and governance but does not sit in the coordinator's main workflow.

## 4. Proposed decisions

### 4.1 Permit network access

**Proposed decision: approve.** The official 2026 challenge pages do not state an offline,
no-internet, or no-API requirement. They require a reproducible Python submission and frame
the task around AI-assisted, human-owned decisions.

This deliberately reverses the Phase 1 offline-only assumption. Approval requires later
changes to the PRD, architecture, layer rules, integration tests, README, and deployment
instructions.

Network access should enable live functions, but the demo should degrade safely:

- the hosted demo uses live map and AI services;
- API credentials live only in environment or deployment secrets;
- committed synthetic examples remain available when a credential or service is absent;
- failures are visible and actionable; the application must never pretend stale data is
  live;
- a model or map outage must not corrupt approved decisions or the audit log.

This is resilience, not a continuation of the offline-only product requirement.

### 4.2 Use a free interactive map and local visit-order planner

**Decision: MapLibre is the primary Phase 2 map.** Google Maps is deferred because it
requires billing and credentials, while Phase 2 should use a free option first.

The proposed map stack is:

- MapLibre GL JS for panning, zooming, markers, selection, and clustering;
- OpenStreetMap-derived data packaged as an NT-focused PMTiles file where practical;
- visible OpenStreetMap attribution and recorded tile-data provenance;
- a small Streamlit component, or a separate UI boundary only if the Task 22 spike proves
  Streamlit cannot keep the map, list, and details pane synchronized; and
- the existing local Altair outline as a simple fallback while the new map loads or if the
  interactive component is unavailable.

The first visit-order planner does not need a paid road API. It can use the existing
distance data or haversine distances and deterministic optimization to recommend a stop
order. If actual road geometry is later required, Valhalla or OSRM can be evaluated as a
self-hosted open-source route engine. Google Maps and Google Routes remain a documented
future option, not a Phase 2 dependency.

### 4.3 Add local live AI extraction and RAG

**Decision: add runtime extraction for newly submitted reports.** New data does
not require rebuilding committed artefacts before it appears in the application.

The runtime path should be:

```text
report → schema-constrained extraction → exact-span verification → human review if needed
       → deterministic score and rank → human decision → audit entry
```

The model must not directly assign the final rank. Existing safeguards remain:

- enum-constrained structured output;
- literal evidence spans for displayed fields;
- no model-reported confidence;
- required-field failure goes to the human queue;
- deterministic scoring receives typed, verified fields only;
- model name, prompt version, latency, and validation result are recorded for audit.

#### Required retrieval layer

**Decision: Phase 2 includes RAG with a local vector index.** It is used where the answer
depends on maintained knowledge, while direct report extraction remains a separate step.
The initial indexed corpus covers:

- published maintenance policies and urgency definitions;
- approved operational procedures;
- current public road notices or access guidance; and
- the source passages used in a coordinator or tenant explanation.

Retrieved passages must be visible and cited. Retrieval may supply context, but it must not
silently override the verified report facts or deterministic ranking. If no suitable source
is retrieved, the interface says so and asks for human review.

The incoming repair reports themselves are records to process, not automatically a RAG
knowledge base. Approved historical cases may become a separate retrieval collection only
after a privacy and leakage review.

The initial local retrieval stack is:

- `qwen3-embedding:0.6b` through Ollama for embeddings;
- a local ChromaDB persistent collection containing chunk text, source identity, version,
  and effective date;
- deterministic top-k retrieval with a minimum relevance threshold; and
- source-level citations shown beside every retrieved claim.

ChromaDB is the default candidate, subject to a short Windows and Python 3.13 compatibility
spike before it is pinned. The corpus is small, so the store remains embedded and local
rather than becoming a separately operated database server.

#### Local model decision

**Decision: local inference is the primary Phase 2 runtime path.** Claude remains an
alternative evaluation and development path.

The development machine was checked on 2026-09-13:

- AMD Ryzen 7 250, 16 logical processors;
- 31.3 GB usable system memory; and
- NVIDIA GeForce RTX 5060 Laptop GPU with 8,151 MiB VRAM.

The recommended first candidate is `qwen3:8b` through Ollama. Its published Q4_K_M package
is 5.2 GB, which should fit the 8 GB GPU with a controlled context window. The fast fallback
candidate is `gemma3:4b` at 3.3 GB. `gemma3:12b` is 8.1 GB before runtime overhead and is
therefore too tight for a reliable all-GPU demo. Models above this class are not Phase 2
candidates unless a benchmark demonstrates acceptable latency with CPU offload.

Ollama supports JSON-schema-constrained structured output, so the current pydantic
extraction contract can remain the validation boundary. Model selection is provisional
until `qwen3:8b` and `gemma3:4b` are run against the existing labelled and adversarial set.
The current extractor scores only 0.564 macro-F1 for `safety_class` against the provisional
0.85 target; a local model is not accepted merely because it runs.

Claude Max is available to the project, but the subscription is not treated as a deployed
API credential. Claude Code can remain a local development, comparison, and recovery path
on the project machine. A future hosted deployment would require a separate provider and
privacy decision.

### 4.4 Include route planning in Phase 2

**Decision: include route planning, defined as a visit-plan recommendation rather than
turn-by-turn navigation.**

Route planning happens only after ranking and human sign-off. It must not quietly use travel
efficiency to undo the equity decision.

Inputs:

- approved jobs and priority order;
- crew starting points, daily capacity, trade or skill, and availability;
- estimated service duration;
- road travel time or distance where available; and
- access mode and current road-status information.

Outputs:

- a numbered suggested stop order for each crew;
- estimated travel and work time;
- capacity or skill conflicts;
- jobs that cannot be road-routed or fitted into the plan; and
- the effect of any route-driven reorder on the approved priority list.

Remote NT work cannot be treated as an ordinary city vehicle-routing problem. Air, barge,
seasonal access, and unavailable road routes must be explicit states. The planner should
leave these jobs for manual coordination instead of inventing a road journey.

The coordinator can accept, edit, or reject the plan. Any override is recorded with a short
reason.

## 5. Design and implementation approach

### Design model recommendation

Use **Claude Fable 5.1 as the primary product/UX designer for the first complete workflow**.
Use **GPT-6 Astra as an independent critic and challenger** before the design is approved.

The reason is practical rather than absolute: on the 2026-09-11 Arena WebDev leaderboard,
Astra Max ranks first and Fable 5.1 Max second. Both vendors describe these as high-capability
models for demanding, long-running work; neither official model page proves that one has
universally better visual taste. The final choice should therefore be made from this
product's screens, not brand claims. The project has Claude Max access, and Fable's
long-horizon reasoning is a better fit for carrying the product definition, screenshots,
interaction states, and full workflow through one coherent design pass. Astra's role is to
attack that proposal and identify missing states rather than independently implement a
second application.

Give both models the same package:

- screenshots of every current screen;
- the product definition and primary user task above;
- three concrete scenarios: review a new report, approve a ranking, prepare a crew visit
  plan;
- reference screenshots from mature field-service dispatch products;
- the requirement to redesign structure and interaction, not merely colours; and
- fixed comparison criteria: first-use clarity, decision speed, evidence visibility,
  accessibility, and implementation feasibility.

Do not ask either model to implement the full redesign before one end-to-end wireframe is
approved.

### Framework decision gate

Do not choose a new framework based on appearance alone. Task 22 should first prototype the
hardest interaction: synchronized ranked list, interactive map, and details pane.

- If Streamlit can deliver that interaction cleanly, retain the Python application and
  avoid a rewrite.
- If the spike requires fragile workarounds or cannot preserve state and selection reliably,
  keep the tested Python core and move only the UI boundary to a web frontend with a small
  Python API.

The framework decision is made from the spike, before the remaining screens are rebuilt.

## 6. Phase 2 verification

Phase 2 is not complete when the pages merely render. The gates should include:

- a first-time user can explain Fair Turn's purpose after the opening screen;
- a coordinator can process a new report, verify evidence, approve an order, and create a
  visit plan without reading project documentation;
- list, map, selected job, and route plan stay synchronized;
- network, map, route, and model failures have tested visible fallback states;
- runtime extraction passes the existing field and adversarial evaluation before release;
- ranking remains deterministic and independent of model-written prose;
- route planning respects capacity, skill, access-mode, and signed-priority constraints;
- all AI-derived claims and all human overrides remain auditable; and
- keyboard navigation, contrast, focus state, and readable empty/error states are checked
  visually as well as by automated tests.

## 7. Decisions required before amending the PRD

1. Confirm whether the initial RAG corpus includes policy documents only, or policy plus
   public road notices.
2. Approve the synchronized list–map–details workspace as the primary interface.
3. Approve the Task 22 framework spike before committing to retain or replace Streamlit.
4. Confirm `qwen3:8b` as the first local extraction benchmark and `gemma3:4b` as the fast
   fallback benchmark.

## 8. Draft task horizon after approval

These are planning labels, not task files:

- **Task 22:** approve the product flow and prototype the synchronized workspace interaction;
- **Task 23:** amend the application architecture for Ollama, retrieval, and online data;
- **Task 24:** benchmark local extraction models and lock the accepted model and prompt;
- **Task 25:** implement live report intake, extraction, verification, and audit;
- **Task 26:** implement the local RAG corpus, vector index, retrieval, and citations;
- **Task 27:** implement the interactive map and map/list/details synchronization;
- **Task 28:** implement visit-plan recommendation and human override;
- **Task 29:** rebuild the coordinator workspace around the approved design;
- **Task 30:** rebuild the review, tenant-answer, and evidence-lab surfaces;
- **Task 31:** add local-AI, retrieval, network-failure, privacy, and route evaluations;
- **Task 32:** update the report, README, screenshots, and competition demo.

The PRD, binding architecture, and real task files are created only after the decisions in
Section 7 are settled.

## 9. Research sources

Checked on 2026-09-13:

- [CDU AI Challenge overview](https://itcodefair.cdu.edu.au/ai-challenge/)
- [CDU AI Challenge task details](https://itcodefair.cdu.edu.au/ai-challenge-task-details/)
- [Microsoft Dynamics 365 Field Service schedule board](https://learn.microsoft.com/en-us/dynamics365/field-service/work-with-schedule-board)
- [Microsoft schedule board map and filters](https://learn.microsoft.com/en-us/dynamics365/field-service/schedule-board-filtering)
- [ServiceNow Field Service Dispatcher Workspace](https://www.servicenow.com/docs/r/field-service-management/field-service-scheduling/t_AssignATask.html)
- [Salesforce Field Service map views](https://help.salesforce.com/s/articleView?id=service.fs_scheduling_console_map_views.htm&language=en_US&type=5)
- [Google Routes API](https://developers.google.com/maps/documentation/routes)
- [Google Routes usage and billing](https://developers.google.com/maps/documentation/routes/usage-and-billing)
- [MapLibre PMTiles example](https://maplibre.org/maplibre-gl-js/docs/examples/pmtiles/)
- [Valhalla routing engine](https://github.com/valhalla/valhalla)
- [OSRM routing engine](https://github.com/Project-OSRM/osrm-backend)
- [OpenAI file search](https://developers.openai.com/api/docs/guides/tools-file-search)
- [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs)
- [Ollama Qwen3 8B](https://ollama.com/library/qwen3:8b)
- [Ollama Gemma 3](https://ollama.com/library/gemma3)
- [Ollama Qwen3 Embedding](https://ollama.com/library/qwen3-embedding)
- [Claude Fable 5.1 overview](https://platform.claude.com/docs/en/models/fable-5-1/overview)
- [GPT-6 Astra model](https://developers.openai.com/api/docs/models/gpt-6-astra)
- [Arena WebDev leaderboard](https://arena.ai/leaderboard/code/webdev?rankBy=labs)
