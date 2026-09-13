# Fair Turn Phase 2 — coordinator workspace wireframes

**Status:** v2, revised 2026-09-14 by Claude Fable 5.1 after the independent critique by
GPT-6 Astra (`design/phase-2-critique.md`). **Binding for layout and interaction** since
the PRD amendment of 2026-09-14: `docs/PRD.md` §3 fixes each surface's rules and points
here for its layout; on a conflict the PRD wins. What the critique changed, and what it did
not, is in §13. §12 records what the amendment changed.

**Inputs:** `docs/phase-2-discovery.md` §2–3 (product definition, north star),
`design/screenshots/` (the six Phase 1 screens, captured 2026-09-14), the visual review of
those screens against PRD §3 (findings listed in §10), `design/design-system/DESIGN.md`
(tokens and component rules; unchanged by this document), `design/phase-2-critique.md`.

**Frame that does not move:** one user (the regional tasking desk, titled "maintenance
coordinator"), one decision (which open jobs get today's crews, in what order). The AI reads
and retrieves; deterministic code scores, ranks and checks constraints; the human decides and
signs. Nothing is dispatched by the system. Everything below serves that one decision or
explains it to the tenant.

## 1. Three scenarios the design is judged against

1. **Review a new report.** A report arrives (pasted or typed). Fields are extracted with
   source phrases. One required field has no verified phrase. The coordinator sees it in the
   review queue, reads the source next to the fields, sets the field, and the job becomes
   rankable without leaving the screen. The coordinator is told where it landed.
2. **Approve today's order.** The coordinator opens the workspace, sees what is proposed
   within today's capacity under the default efficiency-first weighting, switches to
   "Balanced", reads which jobs moved in and out, moves one job with a reason, reviews the
   frozen batch and signs it. Only then do the wait and travel outcomes appear.
3. **Prepare a crew visit plan.** After sign-off, the coordinator opens the visit plan. Each
   crew's stops follow the signed order. The planner offers one swap that shortens the
   drive; the coordinator accepts it with a reason. One job is barge-only and stays listed
   as signed work needing manual coordination. The tenant of the swapped job can read both
   the signed rank and the visit order, with the recorded reason.

## 2. Information architecture

Five surfaces replace the six project-shaped pages. Sidebar order, top to bottom:

| Surface | Purpose | Phase 1 pages absorbed |
|---|---|---|
| **Workspace** | The decision: ranked list, map, selected job, weighting, sign-off | Triage board, Job card, Sign-off |
| **Review queue** (count badge) | Jobs with an unverified required field; new-report intake lands here when incomplete | part of Triage board |
| **Visit plan** | Post-sign-off stop order per crew | new |
| **Tenant answer** | Lookup by registration number, plain-language explanation | Tenant view |
| **Evidence lab** | Extraction quality, feedback-loop simulation, audit log | Feedback loop, Audit log |

"New report" is a button in the workspace header, not a page: intake is an action inside
the coordinator's flow, not a destination.

**Fixed on every surface**, as PRD §3 requires: the provenance caption *"Geography real
(BushTel/ABS); events synthetic"*. The intake dialog adds "Sample data: this report joins the
synthetic set" so a more operational layout never implies real work orders.

## 3. Workspace

```text
+ Fair Turn - Day 2025-12-30 - Region: All - 4 need review - Status: Draft - [New report]  +
+ Geography real (BushTel/ABS); events synthetic                                           +
+--------------+---------------------------------------------+------------------------------+
| Weighting    | [Today's list 12]  [Backlog 494]  [Map]     | JR-2025-01347   Katherine    |
| (*) Effic.   | [ ] Compare with efficiency-first           | cooling - Urgent - 3 of 5 d  |
|     first    |                                             |                              |
| ( ) Balanced | #  D  Job         Community      Fault  Due Score | Why it sits here       |
| ( ) Need     | 1  -  JR-..-01347 Katherine      cool.  2d  8.4 | "Ranked 1: urgent       |
|     first    | 2  ^3 JR-..-00997 CENTRAL AUS-14 sewer  1d  8.1 |  window, day 3 of 5..." |
| > Advanced   | 3  -  JR-..-00795 Alice Springs  hot w  4d  7.9 |                         |
|              | ... (score bar per row, four factor colours)| Score 8.4                    |
| Travel-cost  |                                             |  urgency 3.0  from NT window |
| weight 0.50  |                                             |  safety  2.5  "smoke fills"  |
|              |                                             |  household health risk -     |
| Effect       |                                             |  logistics 2.9 from geography|
| "Balanced    |                                             |                              |
| moves 5      |                                             | Evidence  v                  |
| remote jobs  |                                             | [report text, phrases        |
| into today   |                                             |  highlighted per factor,     |
| and 5 town   |                                             |  legend phrase -> factor]    |
| jobs to the  |                                             | field - value - phrase - ok  |
| backlog"     |                                             |                              |
|              |                                             | Policy reference v (cited)   |
| Filters      |                                             |                              |
| Region       |                                             | [Move up/down + reason]      |
| Trade        |                                             | [Send to review + reason]    |
| Safety class |                                             |                              |
| Access mode  |                                             |                              |
+--------------+---------------------------------------------+------------------------------+
| Today: 12 jobs proposed within capacity (6 crews x 2) - 7 remote / 5 town - 1 moved by   |
| hand - 4 in review - [Review and sign v]                                                  |
+-------------------------------------------------------------------------------------------+
```

**Today's list, not the whole backlog.** The default tab shows the jobs proposed within
today's job-count capacity (crews times jobs per crew per day, from `core/constants.py`),
ranked. The backlog tab holds the rest, same columns, with its count in the tab label. This
answers the Phase 1 finding that the board and the sign-off page printed all 506 open jobs.
"Within capacity" means the job count only; travel, trade and access feasibility are the
visit plan's job (§6) and the strip never claims them.

**Compare with efficiency-first.** A checkbox above the list. Off (default): one list with a
delta column against efficiency-first (arrow glyph and number, `mono`). On: the current
ranking and the efficiency-first ranking side by side in two `feature-card`s with identical
columns, changed rows carrying the glyph, as PRD 3.1 and the design system describe. The
delta column is the everyday view; the side-by-side is one click away, never removed.

**Weighting control.** Three named presets, default "Efficiency first" (λ = 1.0, the PRD's
decide-before-reveal rule is unchanged), "Balanced" (λ = 0.5) and "Need first" (λ = 0.0).
Beneath the presets a read-only caption always shows the number: "Travel-cost weight 0.50.
0 ignores travel cost, 1 applies the full penalty." Balanced is described as the middle
preset, not a fairness guarantee. The numeric slider lives under "Advanced", labelled in
words at both ends ("Ignore travel cost" ↔ "Full travel-cost penalty"); moving it sets the
preset label to "Custom (0.35)". Every change re-renders the effect sentence and the list.

**Effect sentence, in two stages.** Before the first signature it states composition only,
computed from the two rankings: "Balanced moves 5 remote jobs into today's list and 5 town
jobs to the backlog." After the first signature (PRD 3.1: metrics appear after the commit
and update live) it gains the outcomes: "Simulated over the 90-day set against
efficiency-first: town median wait +0.5 days, remote median wait −3.1 days, travel cost
+8 %." Baseline, period and units are always in the sentence. A template over the rankings
and the capacity simulation; no model writes it.

**Ranked row.** Rank, delta against efficiency-first, job id (`mono`), community id, fault
type, safety class badge, "days used of window" as `3 of 5 d`, numeric score to one decimal,
a stacked score bar in the four factor colours. The bar's text equivalent is the numeric
score in the row and the four factor values in the details pane; the one-sentence "why" is
readable in the pane and additionally a row tooltip, never tooltip-only. Rows with a
required field unverified do not appear here; they live in the review queue (unchanged
rule). Human-set fields carry a gray "Set by coordinator" badge in the pane.

**Selection sync.** Selecting a row, a map marker, or a stop in the visit plan sets one
session value, the selected job id. The details pane, the map highlight and the row
highlight all read it. A "Select job" selectbox in the details pane header is the
list-based, keyboard-reachable equivalent of every click. A map marker that holds several
jobs opens a short job list in the pane instead of picking one arbitrarily. A selected job
that a filter hides, or that moves to the review queue, stays selected with a caption
saying where it went. Sorting the table never changes the selection. Streamlit 1.63
provides `on_select` for dataframes, pydeck charts and Altair charts; the Task 22 spike
proves the three-way sync, the multi-job marker, the keyboard path and a rerun-safe
highlight before anything else is built.

**Filters** change what is visible in the list and on the map. They never change today's
capacity, the proposed batch or the signed list; a caption under the filters says so.

**Map tab.** pydeck scatter layer on an attributed Carto basemap (PRD 3.1 already allows an
attributed optional basemap); markers coloured by region, sized by open jobs, region
clusters at NT zoom, pan and zoom native. Selected job's marker enlarged with a terracotta
ring. If tiles fail to load, the existing Altair outline renders with the same markers and
one `st.info` saying the basemap is unavailable; the marker layer never depends on tiles.
No route lines on this map; routes belong to the visit plan.

**Details pane.** Header: "Select job" selectbox, then job id, community, fault, safety
class badge, days used of window. "Why it sits here" sentence. Score to one decimal, then
four factor lines, each with its value and its source:

- *Extracted factors* (safety class, household health risk): the source phrase, or an em
  dash with "No source phrase found" when the field is empty.
- *Computed factors* (urgency from the NT window and the reported date; logistics from
  geography and access mode): the policy or geography they came from ("from NT window:
  Urgent, day 3 of 5"; "from geography: 180 km road, open"). Never "no source phrase":
  the model did not produce them.
- A factor computed from partial inputs shows "Based on N of M fields".

Evidence expander: the verbatim report with phrases highlighted in the factor colour, a
plain-text legend beneath it (phrase → factor → field, so colour is never the only
channel and a repeated phrase is mapped unambiguously), then a table of **field, extracted
value, source phrase, status badge** (Phase 1 omitted the value column). Policy reference
expander: retrieved passages that bear on this job's class or window, each with source
title, section and effective date; "No policy passage found above the relevance threshold"
when retrieval falls short; a different message for "policy index unavailable".
Actions: move up or down with a required reason; promote from the backlog with a reason
(the pane names the job it displaces); send to review with a reason; undo a hand move
before signing. Actions are disabled, with the reason, only for closed jobs and jobs in the
review queue. A hand move is stored as job id, target rank and reason; changing the
weighting re-ranks around it and the strip's "moved by hand" count keeps it visible.

**Decision strip (bottom).** Counts only: jobs proposed within capacity with the capacity
formula, remote/town split, hand-moved jobs, review-queue size, and the single primary
button "Review and sign", which opens the sign-off form (§5) in place. Wait and travel
outcomes never appear in the strip before the first signature.

## 4. Review queue

```text
+ Review queue (4) --------------------------------------- [< Previous]  [Next >] ------+
| JR-2025-00106  BARKLY R-09  - 1 of 4 - fault type needs review                        |
| + Report (verbatim) ------------------+ + Fields -----------------------------------+  |
| | "...the rangehood over the stove    | | fault type    -  Needs review        [v]  |  |
| |  stopped pulling air..."            | | safety class  Urgent  "smoke fills..." ok |  |
| |                                     | | health risk   -  Not recorded             |  |
| +-------------------------------------+ +-------------------------------------------+  |
| Fault type needs review: the proposed source phrase was not found in the report.       |
| Reason (required)  [text input]                                                        |
| [Set fault type v]  [Mark rankable]   [Request clarification]   [Leave in queue]       |
+----------------------------------------------------------------------------------------+
```

One job at a time, source and fields side by side, previous/next through the queue. The
message names the field and why it needs review (phrase not found, field absent, schema
invalid), never the fixed "missing fault type, safety class" of Phase 1, and **never the
rejected model value**: PRD §5 keeps an unverified field empty, and printing the model's
guess in nearby prose would anchor the human. The rejected value stays in the extraction
audit record only.

The coordinator picks the value from the enum and writes a reason; the field is stored as
human-set with actor, reason and time, displays with the gray "Set by coordinator" badge
everywhere, and the job moves to the ranked queue on the next rerun. The success line says
where it landed: "JR-2025-00106 is now rank 14, in the backlog" with a button that opens
the workspace with it selected. Focus moves to the next job in the queue. If the report
cannot support the fact, "Request clarification" leaves the job in the queue with that
status. Empty queue: "All reports reviewed" and a button back to the workspace. Leaving the
queue with an unsaved choice discards nothing: the choice is applied only by "Mark
rankable".

**New report intake**, despite the "dialog" language below, is implemented as an in-page
bordered container toggled from session state, not `st.dialog` (Part 2 spike, 2026-09-14: `AppTest` has no dialog node).

**New report intake** opens a dialog from the workspace header: a text area, community
(selectbox over pseudonymous ids), reported date (defaults to the dataset day and says so),
"Extract". The registration id is assigned by the system. Validation keeps the entered text:
empty or whitespace-only text and text over the length limit show the error under the field.
While the model runs, a status line shows the provider, model and elapsed seconds; closing
the dialog keeps the draft text and cancels the request. On return, the fields table above is
shown in the dialog; if every required field verified, **"Add to ranked queue"**, and the
confirmation states the resulting rank and whether it falls inside today's proposed batch
(it never alters an existing signature); otherwise "Send to review queue". Double-clicking
or retrying after a timeout cannot create a second job or audit entry: the dialog holds one
draft token per report. On model failure or timeout, the report is saved to the queue with
status "not extracted" and an `st.error` names the cause. Three provider states have
distinct labels: no provider configured (sample-artefact mode, intake disabled with the
reason), provider unavailable (retry offered), provider running. Extraction provider is a
setting (Claude via the existing CLI wrapper, or Ollama); the audit entry records provider,
model, prompt version, latency and validation result.

## 5. Sign-off (an in-page form in the workspace, not a page and not a dialog)

```text
+ Review and sign - 2025-12-30 - batch v3 --------------------------------------+
| Weighting  Balanced (travel-cost weight 0.50)                                 |
| Today's list  12 jobs - 7 remote - 5 town      Backlog  494                   |
| Moved by hand  1   JR-2025-00997 ^3  "crew already passing R-14"              |
| In review queue  4  (not ranked)                                              |
| > Open today's list (12 rows, same columns as the workspace)                  |
| Signer  [text input, required]                                                |
| Decision  [Approve today's list | Defer]                                      |
| Reason for today's weighting  [text area, required]                           |
| Date  2025-12-30 (dataset day; recorded time is the wall clock)               |
| [Sign today's list]                                                           |
+-------------------------------------------------------------------------------+
```

A bordered `st.form` opened in place under the list by "Review and sign", following the
design system's sign-off rules (read-only summary above, single primary button, inline
validation in red text under the field, `st.success` with the audit reference in `mono`).
It shows counts and exceptions, and the exact frozen batch is one expander away. Opening the
form freezes a batch version; any change to the list, a field or the weighting before
submission replaces the summary with "The list changed since you opened this review; open it
again." Double submission is blocked. If the audit write fails, `st.error` names it and the
status stays Draft. After signing: the status in the header becomes "Signed 10:42 by
A. Coordinator", the wait-metrics sentence and panel appear, the visit plan unlocks. A later
weighting change or hand move sets the status to "Changed since signature"; the metrics stay
live (PRD 3.1) and the change is logged as a revision, but the signed list is the last signed
batch until the form is submitted again as revision 2.

## 6. Visit plan

```text
+ Visit plan - signed list 2025-12-30 v3 by A. Coordinator ---------------------+
| Crew Katherine (base Katherine, 2 jobs/day, road)                             |
| 1. JR-2025-01347  Katherine        0 km            cooling   signed rank 1    |
| 2. JR-2025-00997  BIG RIVERS R-14  180 km road, open  sewer  signed rank 2    |
| Within job-count capacity - 180 km                                            |
|                                                                               |
| Suggested change (not applied)                                                |
| Crew Alice Springs: visit rank 7 before rank 5, saves 240 km; same day for    |
| both, windows unchanged.  Reason [text]  [Accept change]  [Dismiss]           |
|                                                                               |
| Signed work needing manual coordination                                       |
| JR-2025-01207  EAST ARNHEM R-01  barge access, no road route                  |
| Next action: book barge freight - owner: coordinator                          |
|                                                                               |
| Plan status: Draft   [Accept plan]  [Edit order]  [Reject with reason]        |
+-------------------------------------------------------------------------------+
```

**The signed order is the plan.** Jobs are assigned to the crew whose base serves their
region, in signed order, up to jobs per crew per day. Distance (haversine times the road
factor, deterministic) is used to *measure* each crew's day and to *suggest* swaps, never to
order the stops by default. A suggestion is offered only when it shortens the drive and keeps
every affected job on the same day within its window; it is listed with old and new order
and the saving, and applies only when the coordinator accepts it with a reason. Accepted
suggestions and order edits are audit entries that reference the signed batch version; the
tenant answer reads them (§7). Membership never changes here: a signed job that does not
fit a crew's day is shown as "signed, unplanned" with the reason, and the plan never claims
"within capacity" while any such job exists.

Air and barge jobs are never routed. They stay listed as signed work with a next action and
an owner, and remain visible after the road portion is accepted. Work and travel *hours*
are not shown: the capacity model has no service durations (PRD 6.3), so the plan shows
kilometres and the job count against capacity, nothing invented.

"Edit order" uses labelled native controls (a stop-number selectbox per row), a required
reason, and keeps the moved job selected after the rerun. A new signed revision marks an
accepted plan "Superseded" and blocks acceptance of a draft built on the old batch. States:
no signed list yet; no road jobs signed; road closed or unknown (the job is listed as
unplanned with the reason); everything manual.

## 7. Tenant answer

Content from PRD §3.4 in the design system's structure: question-headed bordered blocks
"What did we understand from your report?", "Where is your repair in the queue, and why?",
"What happens next?", "Who can you ask?". Additions and fixes:

- The empty state explains what a registration number looks like and where to find it.
- "Where is your repair" distinguishes the **signed rank** from the **visit order** when
  they differ, using the recorded reason in plain words: "Your repair is number 5 on the
  signed list. The crew will visit it second on the day, because the coordinator accepted a
  shorter drive that keeps both repairs on the same day." Formula rank, human move and
  accepted visit order are named as what they are. The λ = 0 counterfactual stays an exact
  formula comparison, never described as an alternative itinerary.
- "What happens next" states the NT window for the class and its source document and date
  (a "Policy source" line), and says plainly that the window is a policy target, not a
  promised visit time. No date is invented: "We do not have a visit date yet."
- "Who can you ask" names the Community Housing Officer as the person who can look the job
  up (PRD §2's secondary user); no phone number or address is invented.
- Distinct copy for: unknown or malformed id, in the review queue, in the backlog, on an
  unsigned draft list, needing manual coordination, and a decision that has been superseded
  (the answer names the signed revision it uses).
- The article and unit errors seen in Phase 1 ("a urgent", "2 days" for business days) are
  corrected in the template.

## 8. Evidence lab

Three tabs, for judges and governance, outside the coordinator's flow:

- **Extraction quality.** Per-field precision, recall, F1 with Wilson intervals; baseline
  classifier beside the model; adversarial set result; provider and model named.
- **Feedback loop.** Both runs drawn from the first render: efficiency-only against the
  page's own default λ = 0.5, so the comparison the page exists for is visible without a
  click. Decay slider unchanged.
- **Audit log.** The design system's audit table, columns renamed for reading and none
  removed: recorded at (ISO 8601, local zone stated once in a caption), decision day, audit
  reference, kind, job id, previous weighting, new weighting, reason, signer, hash, and
  "unverified at decision time" as a gray badge. Event-specific detail (plan id, extraction
  provider and validation result) sits in a detail column. Newest first, append-only, no
  index column, filters restated in a caption, CSV export of exactly the filtered rows.
  Override rate by **decision day** on a daily axis. Two clocks are shown as two labelled
  columns, never merged: the decision day belongs to the dataset, the recorded time is
  real. The workspace header links to this tab ("Override rate: 6 %"), so the coordinator
  sees the oversight signal PRD 3.6 asks for without leaving the flow.

## 9. States every surface must have

**Rendering states**

| State | Where | What the user sees |
|---|---|---|
| Nothing selected | Details pane | "Select a job from the list, the map, or the box above." |
| No open reports | Workspace | `st.info`: no open reports for this day and region; suggest widening the region. |
| Filters exclude everything | Workspace | `st.info`: N jobs hidden by filters; button to clear them. |
| No crews for the region | Workspace | `st.info`: capacity is zero; the list shows as backlog only. |
| All jobs in review | Workspace | List empty, banner linking to the queue with the count. |
| Model running / failed / no provider | Intake dialog | Provider, model, elapsed seconds; `st.error` with cause; disabled with reason. |
| Basemap unavailable | Map | Altair outline with the same markers; `st.info` names the failure. |
| No policy passage / index unavailable | Details pane | Two distinct messages. |
| Job closed or in review | Details pane | Actions disabled with the reason. Backlog jobs keep "Promote". |
| Queue empty | Review queue | "All reports reviewed", button to the workspace. |
| Audit export empty or failed | Evidence lab | "No rows match the filters" / `st.error` naming the failure. |

**Decision states** (shown in the workspace header and on the visit plan)

| State | Meaning | What remains possible |
|---|---|---|
| Draft | No signature today | Everything; metrics hidden |
| Review open (batch vN) | Sign-off form open on a frozen batch | Submit; any change invalidates the review |
| Saving / Save failed | Audit write in flight or failed | Retry; status stays Draft on failure |
| Signed vN | Batch vN written to the audit log | Metrics live; visit plan open; changes create a revision |
| Changed since signature | A move or weighting change after signing | Re-sign as vN+1; last signed batch stays authoritative |
| Plan draft / accepted / superseded | Visit plan built on batch vN | Accept, edit, reject; superseded when vN+1 is signed |

Every state uses the design system's empty and unverified rules: em dash for missing, gray
badge for unverified or human-set, yellow badge for needs-a-human, one alert per section.

**Keyboard and announcements.** Every action is a native focusable control: the "Select
job" selectbox is the keyboard path into the pane, move and promote are buttons with a
reason field, the sign-off form is a `st.form`. Streamlit has no live-region API; state
changes are announced by re-rendered text in the header status and in success lines, and
this is recorded as a known gap. The Task 22 spike walks list → pane → move → sign by
keyboard alone before the design is treated as feasible.

## 10. Phase 1 review findings this design absorbs

From the 2026-09-14 visual review against PRD §3:

- Board printed all 506 open jobs and hid most PRD columns behind horizontal scroll: today's
  list tab, score bar in row, "why" in the pane.
- Queue message said "missing fault type, safety class" for all 21 jobs while most were
  missing one field: per-field reason in the review queue.
- Job card fields table had no value column: field, value, phrase, status.
- Sign-off printed 506 identifiers: counts and exceptions with the batch one expander away.
- Feedback page drew one run at the default: own default λ = 0.5, both runs.
- Audit table used internal column names and an hourly axis for daily data: readable
  columns, daily axis, two clocks labelled.
- Tenant copy "a urgent", "2 days": template fix.
- Towns labelled "community Darwin": "town Darwin"; community ids stay pseudonymous.

## 11. Criteria the critique scored against

Fixed before the critique, scored in `design/phase-2-critique.md` §A:

1. **First-use clarity.** Can a first-time user say what the product decides and who decides
   it from the workspace alone?
2. **Decision speed.** Steps from opening the workspace to a signed list, scenario 2.
3. **Evidence visibility.** Is every model-derived field one click from its source phrase?
4. **Accessibility.** Colour never the only channel; keyboard path through list, pane, sign.
5. **Implementation feasibility.** Buildable in Streamlit 1.63 with native selection events
   and no custom CSS; the Task 22 spike is the proof.

## 12. What changes in the PRD after this draft is approved

- **§2:** "crew routing" leaves the "not the decision" list and becomes "a visit-plan
  recommendation that elaborates the signed decision and never changes it". "Nothing is
  dispatched by the system" stays.
- **§3:** rewritten as the five surfaces above; the six-screen numbering retired. Content
  changes stated explicitly, not called "absorbed": the delta column is the default view
  with the side-by-side one click away; "days used of window" replaces days open and days
  left as two columns; the row's "why" sentence moves to the details pane; sign-off is a
  daily batch with counts, exceptions and the openable order; wait and travel outcomes
  appear only after the first signature, as today.
- **§5:** the model also runs at intake time, through the same schema and verification; a
  retrieval layer supplies cited policy passages to the details pane and tenant answer, and
  nothing else. Human-set fields are a named case: enum value, actor, reason, gray badge.
- **§8:** crew visit order moves in as "visit-plan recommendation after sign-off"; live
  intake moves in; offline-only leaves.
- **§9:** the prototype runs with internet; the artefact path stays as the no-model fallback.
- **No PRD change for the basemap:** §3.1 already allows an attributed optional basemap
  with a no-network fallback. The map-tile ban lives in `CLAUDE.md` Part 2 and is amended
  by `create-architecture`, not here.

## 13. Response to the critique

Scores in `design/phase-2-critique.md` §A ranged 2 to 4 of 5; the verdict was "reject:
signed priority is not authoritative". Disposition, by the critique's numbering:

**Accepted, changed above:** C1 (outcomes before commitment, §3 two-stage sentence), C2
(rejected value on screen, §4), C4 ("Add to ranked queue", §4), C6 and B3 (signed order is
the plan, distance suggests, §6), C7 (tenant reads the move, §7), C8 (two clocks, §8), C9
(provenance line, §2), C11 (backlog promotion, §3), C13 (text equivalents and legend, §3),
C14 (tenant structure, §7), C16 (computed versus extracted factors, §3), C17 (audit
identity, §8), B1 (λ caption and "Custom", §3), B4 and the decision-state half of §D (§9),
the visit-plan feasibility score (hours dropped, §6).

**Accepted in part:** C3, human corrections get actor, reason and a visible badge, but
selecting a supporting phrase is not required: PRD 3.1 authorises the coordinator to fill
the field, and the grounding rule in §5 governs model output; phrase selection goes to the
backlog. C5, "fit" is reworded, but job-count capacity is what PRD 6.3 defines. C10, the
numeric score and a persistent "why" return, and the side-by-side is one click away rather
than the default; the column changes are declared as PRD amendments in §12. C12, the form
moves in-page, but for a different reason than the critique gives: the design system's "no
modal" governs validation errors, not the form's placement; the in-page form is chosen
because it is simpler to build and to test with `AppTest`, and leaves room for the batch
expander.

**Not accepted:** C15's basemap point, PRD 3.1 already permits an attributed optional
basemap. The verdict's severity: the equity decision is membership in today's list, which
the draft never let distance change; the tie-break rule was one sentence and is fixed, and
the repair is inside the same workspace, as the critique itself says a second design is
unnecessary.

**Deferred to `BACKLOG.md`** with dates: the remaining §D items that describe production
hardening rather than the competition prototype (partial tile loading, provider retry
policies, phrase selection for human-set fields, contradictory-evidence workflows).
