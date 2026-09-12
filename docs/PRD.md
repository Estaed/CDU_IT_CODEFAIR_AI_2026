# Fair Turn — PRD

Entry for AI Challenge brief 1, housing maintenance triage (`docs/task-briefs.md`).
Written 2026-09-12 from `notes.md` and the eight reports under `reports/`. This document
says what and why. How (stack, folders, commands) is `CLAUDE.md` Part 2.

There is no design file. **This PRD is the source of truth for every screen.** Visual
fidelity is not a quality bar; `review-visual` findings are advisory.

Values marked *provisional* were set by us without a published source. They are
decisions, not facts; the report says so wherever one is quoted.

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
- **Decision:** which open jobs get the available crews today, in what order.
- **Not the decision:** budgets, procurement, tenant eligibility, crew routing, the
  DIPL approval gate for non-urgent work over AUD 500. Out of scope (section 8).
- **AI assists, human decides.** Nothing is dispatched by the system. The coordinator
  commits a setting and a reason, may move individual jobs with a reason, and signs.
  The signed list is the output. Everything is logged.
- **Secondary user:** a tenant (or the Community Housing Officer on their behalf) who
  looks up a job by its registration number.

## 3. Screens

Each screen's source of truth is this section. A provenance line — *"Geography real
(BushTel/ABS); events synthetic"* — is fixed on every screen.

### 3.1 Triage board

- Ranked list of open jobs for a chosen day and region. Each row: rank, community id,
  fault type, safety class, health-risk factors, days open, days left in the NT window,
  score with its factor breakdown (bar per factor), and a one-sentence "why it sits here".
- **Equity slider** λ from 1.0 (efficiency) to 0.0 (need only), default λ = 1.0 so the
  efficiency-first ranking is what the coordinator sees first and must consciously move
  away from.
- **Two rankings side by side** — the current λ against λ = 1.0 — with rank changes
  highlighted.
- **Metrics panel:** remote median wait, town median wait, the gap, total travel cost.
  **Decide before reveal:** the panel is hidden until the coordinator has committed a λ
  and a reason for today (3.3). After the first commit it updates live; every later
  change of λ is logged as a revision.
- **Needs-a-human queue** at the top of the board: jobs where a required field (fault
  type or safety class) has no verified source phrase. They are not ranked until the
  coordinator fills the field on the job card.
- **Map:** one dot per community at its real coordinates, coloured by region, sized by
  open jobs, clustered by region at NT scale, zoom to region. Works with no network; a
  basemap is optional and attributed if shown.

### 3.2 Job card

- The original free-text report.
- Every extracted field with the source phrase it came from, highlighted in the report.
  A field with no verified phrase is shown empty, never guessed.
- Factor breakdown of the score at the current λ, and the same sentence as the board.
- **Override:** move this job up or down in today's list with a written reason. Logged.

### 3.3 Sign-off

- Choose λ, write a reason, sign (name + timestamp). Until this happens today's metrics
  are hidden (3.1). The signed list, λ, reason, revisions and per-job overrides are
  written to the audit log.

### 3.4 Tenant view

- Enter a job registration number. Get a plain-language answer: what was understood from
  the report, where the job sits, why (the factors in words), where it would sit if
  distance were ignored (λ = 0 counterfactual, exact, not searched), the NT window for
  its class, and the coordinator's reason and setting for the day.
- Reads at year-7 level, active voice, no blame, no deficit language. No live model
  call; the text is assembled from the score's factors.

### 3.5 Feedback-loop simulation

- Replay the 90-day dataset at λ = 1.0 and at a chosen λ. Reporting rate in a community
  is a function of whether its past reports were served; the decay rate is a labelled
  assumption on a slider, not a fitted parameter. Charts: reports per week by
  town/remote, median wait by town/remote, and the gap, for both runs.
- Purpose: show that efficiency-only allocation makes remote demand look like it dried
  up, and that the equity setting prevents it. Framed with Ensign 2018, D'Amour 2020,
  Kontokosta & Hong for under-reporting; the decay rate is ours (report 6).

### 3.6 Audit log

- Every signed day: λ, reason, revisions, per-job overrides with reasons, signer.
- Override rate over time, shown to the coordinator (report 6: an owned override rate is
  the oversight signal).
- Exportable as a table. This is the "decision-maker's reasoning record" the NT AI
  assurance framework asks for (report 7).

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
formula reads **only typed fields**, never model free text.

Rejected: a second, separate "equity weight" alongside λ (two levers, harder to defend
in Q&A, no extra information). A learned ranker (post-hoc explanations, cannot show
factors honestly; and nothing real to train on).

## 5. The language model — what it does and does not do

- **Does:** turn each free-text report into typed fields, each with a source phrase.
  Runs once, offline, as a build step. Drafts the synthetic reports' text (a different
  model from the extractor, report 6).
- **Does not:** rank, explain the rank, or run inside the app. The app makes no model
  call and needs no API key. "Why it sits here" and the tenant answer are assembled from
  the score's factors, which is what lets them change instantly when λ moves.
- **Grounding rule:** a field is shown only if its source phrase is a literal substring
  of the report. Otherwise the field is empty and the job joins the needs-a-human queue.
  Model-reported confidence is never shown and never a ranking input (report 6).
- **Injection:** report text is untrusted content. Enum-only output schema, substring
  verification, the formula never reads free text, and a 20-item adversarial subset in
  the eval asserts the rank is unchanged.
- **Baseline:** a classical text classifier (bag-of-words) for fault type and safety
  class, trained and scored on the same labelled set. Gives the report a measured
  "why a language model" answer and the app a no-model fallback path.

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

### 6.3 Capacity model — *provisional*

The wait-time metrics need a toy dispatch model, not a router:

- Each region has a fixed number of crews (*provisional:* 2 per remote region, 3 in the
  town region). A crew completes up to 4 jobs per day.
- A crew visiting a remote community serves all its pending jobs up to capacity in one
  visit (batching). A community over 200 km from base costs the crew a travel day.
- A closed road blocks the visit until the road reopens.
- Wait = completion day − report day. Median wait is computed per town/remote.

Everything above is a labelled assumption exposed in the report; none of it is claimed as
NT practice. The September workshop interview may revise the numbers (open question 4).

### 6.4 Evaluation set

150 held-out synthetic reports with labels known by construction, plus 20 adversarial
items (injected instructions, fake priority claims, fake system tags). Twenty graded
items are hand-read to check the grader itself.

## 7. Quality bars and how each is verified

| Bar | Verified by |
|---|---|
| Extraction: fault type and safety class | Per-field precision, recall, F1 on the 150-item set, Wilson 95 % CI. **Target macro-F1 ≥ 0.85 each** (*provisional*). Report the number either way. |
| Extraction: health-risk factors, location, logistics | Same per-field P/R/F1. Reported; no pass mark. |
| Source phrases | 100 % of displayed fields have a phrase that is a literal substring of the report. Hard invariant, tested. Exact and partial span scores (SemEval-2013 naming) reported for the record. |
| Injection | 20/20 adversarial items leave the final rank unchanged. Tested. |
| Formula honesty | The ranking function reads only typed fields; property test: at λ = 0 the ranking is invariant under any permutation of distances and road status. |
| Explanations | Every factor in a job's score appears in its sentence and tenant answer (unit test). Tenant text scores Flesch–Kincaid grade ≤ 7 (machine-checked). No word from the deficit-language blocklist kept in code appears in UI text, code identifiers, this PRD or the report (lint). |
| Baseline comparison | Table: baseline vs model, per field, same 150 items, same CI. |
| Human queue | Any job with an empty required field appears in the queue and never in the ranked list (unit test). |
| Audit | Every sign-off, revision and override is in the log with a reason (unit test); the exported table round-trips. |
| Runs in the room | The app starts and every screen renders with network access disabled and no API key set (integration test, run once before submission). |
| Feedback loop | With decay > 0, the λ = 1 run shows a falling remote reporting rate and a widening gap; the λ = 0 run does not (assertion on the simulation output). |
| Deliverables | Report ≤ 8 pages, Calibri/Arial, sizes per `docs/report-requirements.md`, team number in header and footer; sections as required, Discussion = ethics, AI usage declaration in appendix. Slide deck: 10-minute version and 5-minute cut. Checked by a person against the checklist in that file. |

## 8. Out of scope (v1)

- Real tenant data, real work orders, any live intake integration (1800 line, TMS,
  ASNEX). Synthetic data is also the compliance answer: NT AI policy forbids personal
  and sensitive data in third-party AI tools (report 7).
- Crew routing or scheduling. We rank; we do not route. The capacity model is a
  measurement device, not a scheduler.
- The DIPL approval gate (AUD 500) and the exempt fix-at-triage list (report 8).
- Mobile app, multi-language UI, tenant-facing submission of new reports.
- Merits-review path, NT self-assurance, transparency statement (report 7) — named in
  the report as the pilot's obligations, not built.
- Housing Reference Group involvement in repair order: proposed in the report as an
  extension of an existing structure, not built.
- Live weather or road feeds at demo time.
- Model self-reported confidence in the UI.

## 9. Deliverables (30 September 2026, zip by email)

1. Interactive prototype (screens 3.1–3.6), runnable offline without an API key.
2. Python source with remarks, README with reproduction steps (data build, extraction
   build step, eval, app).
3. Project report PDF per `docs/report-requirements.md`; Discussion mapped to the six NT
   AI Assurance Framework principles; references with dates; AI usage declaration.
4. Slide deck, 10-minute pitch plus a 5-minute cut.

## 10. Open questions

Numbered for reference from task files. Never renumbered.

1. BushTel and NT road-report licence terms (© NT Government, no licence stated). Ask
   opendata@nt.gov.au or confirm on the nt.gov.au copyright page before the report cites
   derived tables.
2. Which Challenge Day and which judging panel is real (two live pages disagree, see
   `README.md`). Tarik asks the organisers; 30 September stays the deadline either way.
3. Team members, roles and team number (2–4 enrolled students required; needed on the
   report title page and in the file name).
4. Real-coordinator interview at the September workshop: may revise the persona (2), the
   capacity numbers (6.3) and the volume (6.2).
5. Report file-name prefix for AI Challenge teams (the requirement page's rule names the
   Data Challenge).

## 11. Deferred decisions

Unanswered on purpose; they belong to a real pilot, not to this entry, and block nothing.

1. Who holds the id-to-community-name key (agency and community representatives, CARE
   "authority to control").
2. Whether Housing Reference Groups get a formal role in repair ordering.
3. How the signed list enters the contractor's tasking system.
4. The merits-review path for a tenant who disputes their position.
