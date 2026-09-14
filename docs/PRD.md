# Fair Turn — PRD

Entry for AI Challenge brief 1, housing maintenance triage (`docs/task-briefs.md`).
Written 2026-09-12 from `notes.md` and the eight reports under `reports/`. Amended
2026-09-14 for Phase 2 from `docs/phase-2-discovery.md` and `design/phase-2-wireframes.md`
§12; the Phase 1 text is in git history at `2d8c349`. This document says what and why. How
(stack, folders, commands) is `CLAUDE.md` Part 2.

**Three sources of truth, one per question.** *What* each surface shows and which rules
bind it: this document, section 3. *How it is laid out and behaves* (panes, controls,
states, keyboard path): `design/phase-2-wireframes.md`, by section. *How it looks*
(tokens, components, wording): `design/design-system/DESIGN.md`. Where the design system's
examples contradict this PRD (its per-job sign-off, its "Unverified" value shown with a
badge), this PRD wins: sign-off is a daily batch and an unverified field is empty. Visual
fidelity is not a quality bar; `review-visual` findings are advisory.

Values marked *provisional* were set by us without a published source. They are
decisions, not facts; the report says so wherever one is quoted.

Phase 1 (Tasks 00–21, all done 2026-09-13) built six screens from committed artefacts
with no network. Phase 2 turns them into one coordinator workspace, adds live intake,
cited policy passages and a visit plan after sign-off, and lets the prototype use the
network while still rendering every surface offline. Struck-through lines below are Phase 1
rules that Phase 2 reverses, kept with the reason so they are not re-proposed.

---

## 1. Purpose

Help a housing maintenance coordinator in the Northern Territory order today's repair jobs
across remote communities and towns, so that "efficiency" does not quietly push remote
tenants to the back of the queue. The AI reads free-text fault reports into structured
fields. A transparent formula ranks. A human chooses the trade-off, signs, and owns it. A
tenant can ask why their job sits where it does and get a real answer.

Why this is worth doing: NT policy already gives remote tenants longer windows (Urgent 2
business days town / 5 remote; Routine 10 / 25 — FS17, 10/2025), the tenant-facing site
publishes no timeframes, and the NT's own evaluator states the department cannot currently
measure the time between a tenant's report and the completed repair (Menzies 2023 §7.6.2).
Fair Turn makes the gap visible and measurable, then hands the decision to a person.

The trust twist is the deliverable. Every screen exists to make the equity trade-off
visible, decided, logged, and explainable to the tenant.

## 2. User and decision

- **User:** the regional tasking desk that holds the daily list. Under Healthy Homes this
  is the contractor's scheduler (often an Aboriginal Business Enterprise) with agency
  oversight (report 8). UI title: "maintenance coordinator", matching the brief.
- **Decision:** which open jobs get the available crews today, in what order. The signed
  list is that decision.
- **Not the decision:** budgets, procurement, tenant eligibility, the DIPL approval gate
  for non-urgent work over AUD 500. Out of scope (section 8).
  ~~Crew routing.~~ *Amended 2026-09-14:* a **visit plan** elaborates the signed list into
  a stop order per crew. It never changes which jobs are on the list, it orders stops in
  signed order by default, and any departure is a suggestion the coordinator accepts with
  a reason. It is a recommendation, not a dispatch.
- **AI assists, human decides.** Nothing is dispatched by the system. The coordinator
  commits a setting and a reason, may move individual jobs with a reason, and signs.
  The signed list is the output. Everything is logged.
- **Secondary user:** a tenant (or the Community Housing Officer on their behalf) who
  looks up a job by its registration number.

## 3. Surfaces

Five surfaces in one Streamlit app, replacing the six Phase 1 screens. For each, this
section fixes the rules; the named wireframe section fixes the layout, controls and
states. A provenance caption — *"Geography real (BushTel/ABS); events synthetic"* — is
fixed on every surface.

Phase 1 numbering, kept for code written against it (docstrings cite "PRD 3.x"; the
Phase 2 tasks that rewrite those files update the citations): 3.1 Triage board, 3.2 Job
card, 3.3 Sign-off, 3.4 Tenant view, 3.5 Feedback-loop simulation, 3.6 Audit log.

### 3.1 Workspace — layout: wireframes §3, sign-off form §5

The decision surface: ranked list, map, selected job, weighting, sign-off, all in one
place. Absorbs the Phase 1 board, job card and sign-off page.

- **Today's list and backlog.** The default view is the jobs proposed within today's
  job-count capacity (crews × jobs per crew per day, section 6.3), ranked; the rest is
  the backlog, same columns. *Amended 2026-09-14 (night):* capacity is one NT-wide crew
  pool, so the list is always ranked and split NT-wide; the region filter narrows the
  rows and the map only. A third tab, **Needs a human**, lists every open job in the
  review queue with what is missing in words and a Review action, so the jobs a person
  must handle are part of the daily view, not only a count. "Within capacity" means the job count only; travel, trade
  and access feasibility belong to the visit plan (3.3) and the workspace never claims
  them.
- **Make safe now.** *Added 2026-09-15, Tarik's decision:* Immediate jobs leave the ranked
  queue and sit in a "Make safe now" section above the To decide tab. The weighting does not
  move them and they take no place in today's crew capacity: an emergency make-safe
  contractor does this work within the FS17 four hours. Each has one "Sent to make-safe
  contractor" action with a required reason, logged as an audit record with actor and both
  clocks; the job then leaves the section. A job in the review queue stays there until its
  fields are set. Today's steps do not count these jobs.
- **Row content.** Rank, change against efficiency-first, job id, community id, fault
  type, safety class, days used of the NT window (one column, replacing the Phase 1 pair
  days open / days left), score to one decimal with its factor bar. Household health
  risk factors and the one-sentence "why it sits here" are in the selected-job pane,
  always readable; the row may repeat the sentence as a tooltip but never only there.
- **Equity weighting.** Three named presets — Efficiency first (λ = 1.0, default),
  Balanced (0.5), Need first (0.0) — with the number always visible as a caption and a
  slider under "Advanced" labelled in words at both ends; a slider value off a preset is
  labelled "Custom (0.xx)". Balanced is the middle preset, never described as a fairness
  guarantee. Default λ = 1.0 so the efficiency-first ranking is what the coordinator sees
  first and must consciously move away from.
- **Comparison with efficiency-first.** The delta column is the default view; a toggle
  shows the current ranking and the λ = 1.0 ranking side by side with identical columns
  and changed rows marked. Both views exist; neither is removed.
- **Effect sentence, two stages.** Before the first signature it states composition only:
  how many remote and town jobs move into or out of today's list under the current
  weighting. After the first signature it adds the outcomes.
- **Metrics — decide before reveal.** Remote median wait, town median wait, the gap and
  total travel cost are hidden until the coordinator has signed today's list with a
  weighting and a reason. After the first signature they update live; every later change
  of weighting is logged as a revision and sets the status "changed since signature". Any
  outcome shown states its baseline (efficiency-first), the simulated period and units.
- **Selected-job pane.** The verbatim report with source phrases highlighted per factor
  and a plain-text phrase → factor → field legend; a table of field, extracted value,
  source phrase, status. Extracted factors (safety class, household health risk) show
  their source phrase or are empty with "No source phrase found". Computed factors
  (urgency from the NT window and reported date; logistics from geography and access)
  show the policy or geography they came from, never "no source phrase". A factor from
  partial inputs says "Based on N of M fields". Retrieved policy passages that bear on
  the job's class or window, each with source title, section and effective date (section
  5); a distinct message when none clears the threshold and when the index is
  unavailable.
- **Overrides.** Move a job up or down in today's list, promote a job from the backlog
  (the pane names the job it displaces), send a job to the review queue, undo a hand move
  before signing; each with a written reason, each logged. Actions are disabled, with
  the reason shown, only for closed jobs and jobs in the review queue.
- ~~**Checking the AI's reading**: ✓ Fields are right / ✗ Fix a field as feedback, with no
  per-job accept.~~ *Replaced 2026-09-15, Tarik's decision, restated twice after the
  rubber-stamp risk in `reports/research-review-workflow-2026-09-14.md` was put to him:*
- **Deciding each job.** Today's proposed jobs are a queue: **To decide**, **Accepted**,
  **Needs a human**, **Backlog**. At the bottom of the selected-job pane, after the report,
  the reasons, the score and the policy passages, the coordinator ticks "I have read the
  report and the reasons above" (per job), then presses **Accept for today** (green) or
  **Reject** (red, with a required reason and one of: not today, move to the backlog;
  needs a person, send to the review queue; a field is wrong, fix it). Accepting moves the
  job to Accepted, so To decide shrinks by one; rejecting it as not today lets the next
  ranked job into To decide. A decision can be undone before signing. Every decision is an
  audit record with actor and both clocks. Kept against rubber-stamping: the read tick per
  job, no accept-all, a reason for every rejection, and the counts on the sign-off summary.
  Keyboard: J next job, K previous, A accept (only after the read tick), X reject.
- **Today's steps.** A strip at the top of the workspace shows the day's four steps with
  live state, so a first-time user needs no document: 1 Jobs that need a person (N left),
  2 Decide today's jobs (N left; *amended 2026-09-15*), 3 Choose the weighting and sign,
  4 Open the visit plan. Each step says in one line what to do next. No auto-opened tour.
- **Selection.** One selected job, shared by the list, the map, the pane and the visit
  plan. A keyboard-reachable selectbox is the equivalent of every click. A map marker
  holding several jobs offers the choice; it never picks one.
- **Map.** One dot per community at its real coordinates, coloured by region, sized by
  open jobs, clustered by region at NT scale, pan and zoom. *Amended 2026-09-14 (night):*
  clusters form and split with zoom (a cluster's size is the jobs it holds), and the map
  shows either today's list or all open jobs. An attributed basemap may be
  shown; if it cannot load, the local outline renders with the same markers. No route
  lines here.
- **Sign-off.** A daily batch, signed in an in-page form under the list: read-only
  summary of weighting, counts, hand moves with reasons and review-queue size; the exact
  frozen list one expander away; signer, decision (approve or defer), reason, the
  decision date stated as the dataset day. *Amended 2026-09-15:* the batch is the
  **accepted** jobs in rank order, and signing opens only when no proposed job is left to
  decide; after signing, the workspace says so and links the visit plan. Opening the form freezes a batch version; any
  change before submission invalidates the review. The signed list, weighting, reason,
  revisions and per-job overrides are written to the audit log with an audit reference
  shown on success. Later changes require a new signed revision to become the signed
  list; until then the last signed batch is authoritative.
- **Decision states**, visible in the header: draft; review open; saving or save failed;
  signed vN; changed since signature. Wireframes §9 lists them with what remains
  possible in each.

### 3.2 Review queue — layout: wireframes §4

- Jobs with a required field (fault type or safety class) that has no verified source
  phrase, or that failed schema validation, or that were not extracted. They are not
  ranked until the coordinator sets the field here.
- One job at a time, verbatim report beside the fields. The message names the field and
  the reason it needs review. **The rejected model value is never shown**: the field is
  empty (section 5), and printing the model's guess nearby would anchor the human. The
  rejected value lives in the extraction audit record only.
- The coordinator sets the value from the enum with a written reason. The field is
  stored as **human-set** with actor, reason and time, is shown everywhere with a gray
  "Set by coordinator" badge, and the job joins the ranked queue; the coordinator is told
  its resulting rank and can open it. "Request clarification" leaves the job in the queue
  with that status when the report cannot support the fact.
- **New report intake** is an action from the workspace header, not a page. Free text,
  community id and reported date in; the same extraction schema and verification as the
  build (section 5); the result lands in the ranked queue ("Add to ranked queue", with
  its proposed rank and whether it falls inside today's proposed batch, never altering a
  signature) or in this queue. A failed or timed-out extraction saves the report here as
  "not extracted" with the cause. Repeated submission cannot create a second job or audit
  entry. Provider states are distinct: none configured (intake disabled with the reason),
  unavailable, running.

### 3.3 Visit plan — layout: wireframes §6

- Opens after today's list is signed; before that it says so and offers the sign-off.
- ~~Jobs are assigned to the crew whose base serves their region, **in signed order**, up
  to jobs per crew per day. Distance measures each crew's day and may **suggest** a swap
  that shortens the drive; a suggestion applies only when accepted with a reason.~~
  *Amended 2026-09-14 (night), Tarik's decision:* regional assignment left 10 of the 14
  signed jobs of the demo day unplanned, because the list pools capacity NT-wide and the
  plan split it by region. Crews are now one pool, each driving from its home base.
- **Distance decides which crew goes to a job; it never decides which job is served or
  when.** That is the signed list. *Refined the same night after the first run sent the
  Alice Springs crew 1,290 km to a Darwin door lock:* a crew **reaches** its own region
  and any community within the travel-day distance of its base (6.3). In signed-rank order,
  each road job takes a free slot of the nearest crew that reaches it; a job no crew with a
  free slot reaches stays "signed, unplanned: no crew within reach", with that reason.
  Each crew's stops run in the shortest order (exact over its few stops). Order inside one
  crew's day changes no job's day, so the Phase 1 rule "signed order by default" protected
  nothing and is dropped. If road jobs exceed the slots, the lowest signed ranks are left
  "signed, unplanned", never the farthest.
- The plan states the price of the equity choice instead of hiding it: road kilometres
  for the signed list, the kilometres the efficiency-first list (λ = 1.0, same day and
  capacity) would need, and the difference. A leg over the travel-day distance of 6.3 is
  flagged. The coordinator may still reorder a crew's stops with a reason.
- Air and barge jobs are never routed: they stay listed as signed work needing manual
  coordination, with a next action and an owner, and remain visible after the road plan
  is accepted. A signed job that does not fit a crew's day is shown as "signed,
  unplanned" with the reason; while any exists the plan does not claim "within capacity".
- Kilometres and job counts only. No work or travel hours: the capacity model has no
  service durations (6.3) and none are invented.
- Accepted plans, edits and rejections are audit entries that reference the signed batch
  version. A new signed revision marks an accepted plan superseded.

### 3.4 Tenant answer — layout: wireframes §7

- Enter a job registration number. Get a plain-language answer in question-headed
  blocks: what was understood from the report; where the job sits and why (the factors
  in words), where it would sit if distance were ignored (λ = 0 counterfactual, exact,
  not searched, described as a formula comparison and never as an alternative
  itinerary); what happens next — the NT window for its class with its source document
  and date, stated as a policy target, not a promised visit time, and "We do not have a
  visit date yet" when none exists; who can look the job up (the Community Housing
  Officer; no contact details are invented); the coordinator's reason and setting for
  the day.
- When the signed rank and the visit order differ, the answer says both and gives the
  recorded reason in plain words, naming the human move or accepted plan as what it is.
- Distinct answers for: unknown or malformed id, in the review queue, in the backlog, on
  an unsigned draft list, needing manual coordination, and a superseded decision (the
  answer names the signed revision it uses).
- Reads at year-7 level, active voice, no blame, no deficit language. No live model
  call; the text is assembled from the score's factors and the audit record.

### 3.5 Evidence lab — layout: wireframes §8

For judges and governance, outside the coordinator's flow. Three tabs:

- **Extraction quality.** Per-field precision, recall, F1 with Wilson intervals; baseline
  classifier beside the model; adversarial set result; provider and model named. The
  same table for any runtime provider that is accepted for intake (section 7).
- **Feedback-loop simulation.** Replay the 90-day dataset at λ = 1.0 and at a chosen λ
  (page default 0.5, both runs drawn on first render). Reporting rate in a community is
  a function of whether its past reports were served; the decay rate is a labelled
  assumption on a slider, not a fitted parameter. Charts: reports per week by
  town/remote, median wait by town/remote, and the gap, for both runs. Purpose: show
  that efficiency-only allocation makes remote demand look like it dried up, and that
  the equity setting prevents it. Framed with Ensign 2018, D'Amour 2020, Kontokosta &
  Hong for under-reporting; the decay rate is ours (report 6).
- **Audit log.** Every signed day: weighting, reason, revisions, per-job overrides with
  reasons, signer, plan acceptances, intake and human-set events with actor and
  provider detail. Two clocks as two columns, never merged: the **decision day**
  (dataset) and the real **recorded-at** timestamp (ISO 8601, local zone stated once).
  Audit reference, job id and hash are kept. Append-only, newest first, filterable,
  exportable as exactly the filtered rows. Override rate by decision day, shown to the
  coordinator from the workspace header too (report 6: an owned override rate is the
  oversight signal). This is the "decision-maker's reasoning record" the NT AI assurance
  framework asks for (report 7).

## 4. The ranking — what the coordinator controls

```
score = need − λ · logistics
need  = urgency + safety + household health risk
```

- **urgency:** how far the job is into its NT window (immediate / urgent / routine, town
  or remote timeframes from FS17). A job past its window keeps rising.
- **safety:** the NT class of the fault (immediate 4 h make-safe, urgent, routine), with
  the QLD precedent of escalating cooling and hot-water faults in remote communities
  during the heat season.
- **household health risk:** infant or young child, elderly, pregnancy or chronic
  condition, overcrowding, extreme-heat exposure (cooling fault × Oct–Mar), no working
  water or sanitation. Our extension, not an NT class; say so.
- **logistics:** travel cost from the crew's base, road status (closed roads block the
  job), crew already scheduled nearby.
- **λ** is the only lever. λ = 1 is what the contractor's tasking system implicitly does
  today; λ = 0 ignores distance entirely. The "price of fairness" (Bertsimas 2011) is the
  travel cost difference between the two, shown in the metrics panel.

Exact weights and normalisation are Part 2's; the PRD fixes the shape and that the
formula reads **only typed fields**, never model free text. Human-set fields are typed
fields and enter the formula like any other.

Rejected: a second, separate "equity weight" alongside λ (two levers, harder to defend
in Q&A, no extra information). A learned ranker (post-hoc explanations, cannot show
factors honestly; and nothing real to train on). The visit plan choosing jobs by
distance (it would let travel efficiency undo the signed equity decision one crew-day at a
time; struck at the 2026-09-14 critique, and still the rule after the pooled-crew
amendment: distance picks the crew, never the job).

## 5. The language model — what it does and does not do

- **Does:** turn each free-text report into typed fields, each with a source phrase — at
  build time for the synthetic set, and **at intake time for a newly submitted report**,
  through the same schema and the same verification. Drafts the synthetic reports' text
  (a different model from the extractor, report 6). Embeds and retrieves policy passages
  (below).
- **Does not:** rank, explain the rank, write the tenant answer, or run in any page body
  or callback. ~~Runs once, offline, as a build step; the app makes no model call.~~
  *Amended 2026-09-14:* intake is a model call, made from the intake action only,
  through a provider setting (the existing Claude CLI wrapper, or a local Ollama model),
  and the result is validated and verified before anything is shown. With no provider
  configured the app still renders every surface from the committed artefacts and intake
  is disabled with the reason. "Why it sits here" and the tenant answer are assembled
  from the score's factors, which is what lets them change instantly when λ moves.
- **Grounding rule:** a field is shown only if its source phrase is a literal substring
  of the report. Otherwise the field is empty and the job joins the review queue; the
  rejected value is never rendered. A **human-set field** is the one exception, and it is
  visibly a human's: enum value, actor, reason, time, gray badge. Model-reported
  confidence is never shown and never a ranking input (report 6).
- **Retrieval, cited, bounded.** A local index over the NT public-housing repair policy
  documents the reports cite (FS17 "Repairs and maintenance", 10/2025, first; others
  only with a provenance row) supplies passages to the selected-job pane and the tenant
  answer, each with source title, section and effective date, above a fixed relevance
  threshold. Retrieval informs the human; it never overrides a verified field, enters the
  formula, or supplies a field's value. Road notices stay a frozen table in the logistics
  factor, not a retrieval corpus (decided 2026-09-14: the notices are structured data
  already; a passage about a closure is worse than the closure row). Historical reports
  are records to process, never a retrieval corpus (privacy and leakage; section 8).
- **Injection:** report text is untrusted content. Enum-only output schema, substring
  verification, the formula never reads free text, and a 20-item adversarial subset in
  the eval asserts the rank is unchanged. Intake text is the same untrusted content and
  passes the same defences.
- **Baseline:** a classical text classifier (bag-of-words) for fault type and safety
  class, trained and scored on the same labelled set. Gives the report a measured
  "why a language model" answer and the app a no-model fallback path.
- **Provider acceptance:** a model is accepted for intake only after it is scored on the
  150-item set and the adversarial set with the same table as the build extractor
  (section 7). Running is not acceptance.

Rejected: fine-tuning (nothing real to train on; train/test on the same synthetic set is
a question we cannot answer). A pre-screen classifier for injection (defences above make
the attack a no-op; rejecting a distressed tenant's wording is the worse failure).

## 6. Data

### 6.1 Geography — real, frozen

From `data/raw/` (fetched 2026-09-12, see `data/raw/PROVENANCE.md`): the 96 BushTel
Major and Minor communities with coordinates, population, region, road access and
distance to town; road-report obstructions snapshot; NT open-data coverage list as a
licence-clean coordinate cross-check. Five remote regions as BushTel names them —
Central Australia, Big Rivers, Barkly, Top End, East Arnhem — plus the Darwin,
Palmerston and Litchfield region as town. Crew bases: the regional service towns
(*provisional:* Darwin, Katherine, Tennant Creek, Alice Springs, Nhulunbuy).

**Community identity: pseudonymous, not fictional** (decided 2026-09-12). Each community
is a region-coded id ("Big Rivers R-07") shown with its real attributes and at its real
map position. The id-to-name key is not in the repo. The pseudonym stops synthetic events
from attaching to a community's name in text or search; it does not prevent geographic
inference, and the report says so plainly. Real geography is kept because a jittered map
would make the distance and road-closure logic false. No invented Aboriginal-sounding
names anywhere.

### 6.2 Events — synthetic, labelled

- **Window:** 1 October – 29 December 2025 (90 days, heat season and wet-season onset).
  *Provisional.*
- **Volume:** about 1,500 reports, roughly 60 % remote / 40 % town. *Provisional.*
  NT work-order volumes are unpublished (report 8); ours is a modelling choice, stated
  as such, never presented as an NT figure.
- **Labels first, text second:** the label tuple (community, fault type, safety class,
  health-risk factors, date) is drawn in code, then a model writes the tenant's words
  conditioned on a household persona (composition, register, season). Ground truth is
  free. Extractor model ≠ generator model.
- **Fault types:** electrical; plumbing and water; sewer and drainage; cooling (aircon,
  fans); hot water; roof and structure; doors, locks and security; stove and cooking;
  pests; other. Drawn from NT FS17 and the Australian taxonomies in report 5.
- **Safety classes:** immediate, urgent, routine — NT's own three.
- **Skew built in on purpose** (three mechanisms, each documented): crews are based in
  towns so remote logistics cost is higher; wet-season closures hit remote roads only;
  remote reporting rate is lower and, in the simulation only, decays when reports go
  unserved. Nothing else differs between town and remote by construction.
- **Wet-season closures:** synthetic, labelled, since no closure history exists; the
  road-report snapshot fixes which roads can close.
- **Heat:** a frozen climate table for the window; no weather API at demo time.
- **Intake reports** (Phase 2) join this set as synthetic events with the same schema,
  a system-assigned registration id and a "sample data" caption; they are never
  presented as real work orders.

### 6.3 Capacity model — *provisional*

The wait-time metrics need a toy dispatch model, not a router:

- Each region has a fixed number of crews (*provisional:* 1 per remote region, 2 in the
  town region). A crew completes up to 2 jobs per day. *Amended 2026-09-14 (night):* the
  crews form one NT-wide pool, each based at its region's service town, and a crew reaches
  its own region plus any community within the travel-day distance of its base. Each day,
  in rank order, every open community takes the nearest free crew that reaches it. Reach is
  physical feasibility; within it, distance never changes which community is served first. (Tightened 2026-09-13 from 2 / 3 / 4:
  those values left the median remote wait at 2 days at every λ, so neither the equity
  slider nor the feedback loop had anything to show; the sweep is in
  `reports/otopilot-2026-09-13-report.md`.)
- A crew visiting a remote community serves all its pending jobs up to capacity in one
  visit (batching). A community over 200 km from base costs the crew a travel day.
- A closed road blocks the visit until the road reopens.
- *Added 2026-09-15:* Immediate jobs are completed on the day they are reported by the
  emergency make-safe contractor (section 3.1): they spend no crew slot, no travel and are
  not held by a closed road, and they count in the medians with a wait of 0.
- Wait = completion day − report day. Median wait is computed per town/remote.
- No service durations exist, so nothing downstream shows work or travel hours.

Everything above is a labelled assumption exposed in the report; none of it is claimed as
NT practice. The September workshop interview may revise the numbers (open question 4).

### 6.4 Evaluation set

150 held-out synthetic reports with labels known by construction, plus 20 adversarial
items (injected instructions, fake priority claims, fake system tags). Twenty graded
items are hand-read to check the grader itself. The same set scores every intake
provider.

## 7. Quality bars and how each is verified

| Bar | Verified by |
|---|---|
| Extraction: fault type and safety class | Per-field precision, recall, F1 on the 150-item set, Wilson 95 % CI. **Target macro-F1 ≥ 0.85 each** (*provisional*). Report the number either way. The same table, same set, for any provider offered for intake; a provider below the build extractor is not offered by default. |
| Extraction: health-risk factors, location, logistics | Same per-field P/R/F1. Reported; no pass mark. |
| Source phrases | 100 % of displayed fields have a phrase that is a literal substring of the report, or are human-set with actor and reason. Hard invariant, tested on the artefact and on every intake result. Exact and partial span scores (SemEval-2013 naming) reported for the record. |
| Rejected values | The review queue renders no enum value for an unverified field (unit test over the queue text). |
| Injection | 20/20 adversarial items leave the final rank unchanged. Tested. |
| Formula honesty | The ranking function reads only typed fields; property test: at λ = 0 the ranking is invariant under any permutation of distances and road status. |
| Explanations | Every factor in a job's score appears in its sentence and tenant answer (unit test). Tenant text scores Flesch–Kincaid grade ≤ 7 (machine-checked). No word from the deficit-language blocklist kept in code appears in UI text, code identifiers, this PRD or the report (lint). |
| Baseline comparison | Table: baseline vs model, per field, same 150 items, same CI. |
| Human queue | Any job with an empty required field appears in the queue and never in the ranked list (unit test). A human-set field takes the job out of the queue and into the ranking (unit test; closes the Phase 1 gap in `BACKLOG.md`). |
| Decide before reveal | Wait and travel outcomes are absent from the workspace before the first signature and present after (AppTest). |
| Sign-off integrity | A change to the list, a field or the weighting between opening and submitting the form invalidates the review; a second submission of the same batch is rejected (unit test). |
| Visit plan | Plan membership equals signed membership; a job is planned only by a crew that reaches it, and slots go in signed-rank order, so overflow leaves the lowest signed ranks unplanned, never the farthest; each crew's stop order is the shortest route (checked against brute force); every coordinator edit carries a reason and references the batch version (property tests over random signed lists). *Amended 2026-09-14 (night).* |
| Audit | Every sign-off, revision, override, human-set field, intake and plan action is in the log with a reason or provider detail (unit test); recorded-at is a real timestamp and decision day is the dataset day (unit test); the exported table round-trips. |
| Provenance | The provenance caption is on every surface (AppTest). |
| Runs in the room | With network access disabled and no provider configured, the app starts and every surface renders from the committed artefacts: intake disabled with the reason, outline map, policy passages from the local index or a clear "unavailable" (integration test, run once before submission). With network and a provider, intake and the basemap work (checked by a person before the demo). |
| Feedback loop | With decay > 0, the λ = 1 run shows a falling remote reporting rate and a widening gap; the λ = 0 run does not (assertion on the simulation output). |
| Retrieval | Every shown passage carries source title, section and effective date and is a literal substring of an indexed document (unit test). |
| Keyboard path | List → pane → move → sign is walkable with native controls only (checked by a person in the Task 22 spike, then by `review-visual`). |
| Deliverables | Report ≤ 8 pages, Calibri/Arial, sizes per `docs/report-requirements.md`, team number in header and footer; sections as required, Discussion = ethics, AI usage declaration in appendix. Slide deck: 10-minute version and 5-minute cut. Checked by a person against the checklist in that file. |

## 8. Out of scope

- Real tenant data, real work orders, any integration with an agency intake system
  (1800 line, TMS, ASNEX). Synthetic data is also the compliance answer: NT AI policy
  forbids personal and sensitive data in third-party AI tools (report 7).
  ~~Any live intake.~~ *Amended 2026-09-14:* a coordinator can submit a new synthetic
  report in the app (3.2); the report is processed as sample data and no external
  system is read or written.
- ~~Crew routing or scheduling. We rank; we do not route.~~ *Amended 2026-09-14:* the
  visit plan (3.3) is in. Still out: turn-by-turn navigation, a road-geometry routing
  engine, crew rostering, and any plan that changes membership of the signed list. The
  capacity model remains a measurement device, not a scheduler.
- The DIPL approval gate (AUD 500) and the exempt fix-at-triage list (report 8).
- Mobile app, multi-language UI, tenant-facing submission of new reports.
- Merits-review path, NT self-assurance, transparency statement (report 7) — named in
  the report as the pilot's obligations, not built.
- Housing Reference Group involvement in repair order: proposed in the report as an
  extension of an existing structure, not built.
- Live weather or road feeds at demo time. ~~Offline-only.~~ *Amended 2026-09-14:* the
  prototype may use the network for the basemap and the intake provider; the official
  brief states no offline requirement (`docs/phase-2-discovery.md` §4.1). Every surface
  still renders offline (section 7, "Runs in the room").
- Historical reports as a retrieval corpus (privacy and leakage review first).
- Hosted deployment; a hosted demo needs its own provider and privacy decision
  (section 11).
- Model self-reported confidence in the UI.

## 9. Deliverables (30 September 2026, zip by email)

1. Interactive prototype (surfaces 3.1–3.5). Renders every surface offline from the
   committed artefacts with no key and no provider; uses the network for the basemap and
   live intake when available.
2. Python source with remarks, README with reproduction steps (data build, extraction
   build step, policy index build, eval, app; how to configure an intake provider, and
   that none is required to run).
3. Project report PDF per `docs/report-requirements.md`; Discussion mapped to the six NT
   AI Assurance Framework principles; references with dates; AI usage declaration.
4. Slide deck, 10-minute pitch plus a 5-minute cut.

## 10. Open questions

Numbered for reference from task files. Never renumbered.

1. **Partly answered 2026-09-14:** the BushTel team confirmed by email that BushTel follows
   the NT Open Data Creative Commons licence. Required attribution: Department of Housing,
   Local Government and Community Development, Northern Territory, BushTel community data,
   sourced 12 September 2026, https://bushtel.nt.gov.au/. The NT road-report licence remains
   open and must be confirmed before the report cites derived road-report tables.
2. Which Challenge Day and which judging panel is real (two live pages disagree, see
   `README.md`). Tarik asks the organisers; 30 September stays the deadline either way.
3. Team members, roles and team number (2–4 enrolled students required; needed on the
   report title page and in the file name).
4. Real-coordinator interview at the September workshop: may revise the persona (2), the
   capacity numbers (6.3) and the volume (6.2).
5. Report file-name prefix for AI Challenge teams (the requirement page's rule names the
   Data Challenge).
6. Licence terms for indexing and quoting the NT DHLGCD fact sheets (FS17 first) in the
   policy index (section 5). *Resolved 2026-09-14 from the NT Government copyright page: material may be reused only as fair dealing for private study, research, criticism or review, or under a Creative Commons licence where one is expressly stated. FS17 carries no CC statement, so this competition entry quotes short passages with attribution as research and review; a pilot would need DHLGCD permission before republishing the text.* Passages stay quoted with attribution and the
   index is built by script from the public PDF, not committed as text.
7. *Added 2026-09-14:* which WCAG conformance target the report claims. The research
   (`reports/research-ui-streamlit-2026-09-14.md` §6a.8) found 2025-2026 sources saying
   the Australian Human Rights Commission affirmed WCAG 2.2 AA as the minimum, while the
   DTA page still read as 2.1 AA and could not be fetched. Tarik reads the DTA page; until
   then the report says "designed against WCAG 2.1 AA" and names no audit.

## 11. Deferred decisions

Unanswered on purpose; they belong to a real pilot, not to this entry, and block nothing.

1. Who holds the id-to-community-name key (agency and community representatives, CARE
   "authority to control").
2. Whether Housing Reference Groups get a formal role in repair ordering.
3. How the signed list enters the contractor's tasking system.
4. The merits-review path for a tenant who disputes their position.
5. Provider and privacy decision for a hosted deployment: which model may see intake
   text, where it runs, and under which NT AI policy clause.
