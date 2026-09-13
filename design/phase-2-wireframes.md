# Fair Turn Phase 2 — coordinator workspace wireframes

**Status:** design draft for critique, not binding. Written 2026-09-14 by Claude Fable 5.1
(product design pass). Next: independent critique by GPT-6 Astra, then the PRD §3 amendment.

**Inputs:** `docs/phase-2-discovery.md` §2–3 (product definition, north star),
`design/screenshots/` (the six Phase 1 screens, captured 2026-09-14), the visual review of
those screens against PRD §3 (findings listed in §10 below), `design/design-system/DESIGN.md`
(tokens and component rules; unchanged by this document).

**Frame that does not move:** one user (the regional tasking desk, titled "maintenance
coordinator"), one decision (which open jobs get today's crews, in what order). The AI reads
and retrieves; deterministic code scores, ranks and checks constraints; the human decides and
signs. Everything below serves that one decision or explains it to the tenant.

## 1. Three scenarios the design is judged against

1. **Review a new report.** A report arrives (pasted or typed). Fields are extracted with
   source phrases. One required field has no verified phrase. The coordinator sees it in the
   review queue, reads the source next to the fields, fills the field, and the job becomes
   rankable without leaving the screen.
2. **Approve today's order.** The coordinator opens the workspace, sees what fits today's
   capacity under the default efficiency-first weighting, switches to "Balanced", reads the
   plain-language effect, moves one job with a reason, and signs the batch.
3. **Prepare a crew visit plan.** After sign-off, the coordinator opens the visit plan, sees
   a numbered stop order per crew, one job flagged as barge-only and left for manual
   coordination, accepts the plan, and the tenant of the moved job can read why.

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

## 3. Workspace

```text
+ Fair Turn - Day 2025-12-30 - Region: All - 4 need review - Signed: not yet - [New report] +
+--------------+---------------------------------------------+------------------------------+
| Weighting    | [Today's list 12]  [Backlog 494]  [Map]     | JR-2025-01347   Katherine    |
| (*) Effic.   |                                             | cooling - Urgent - 3 of 5 d  |
|     first    | #  D  Job         Community      Fault   Due|                              |
| ( ) Balanced | 1  -  JR-..-01347 Katherine      cooling 2d | Why it sits here             |
| ( ) Need     | 2  ^3 JR-..-00997 CENTRAL AUS-14 sewer   1d | "Ranked 1: urgent window..." |
|     first    | 3  -  JR-..-00795 Alice Springs  hot wtr 4d |                              |
| > Advanced   | ... (score bar per row, four factor colours)| Score  ####.. urgency        |
|              |                                             |        ###... safety         |
| Effect       |                                             |        ...... health risk -  |
| "Balanced    |                                             |        ##.... logistics      |
| moves 5      |                                             |                              |
| remote jobs  |                                             | Evidence  v                  |
| into today;  |                                             | [report text, phrases        |
| town median  |                                             |  highlighted per factor]     |
| wait +0.5 d" |                                             | field - value - phrase - ok  |
|              |                                             |                              |
| Filters      |                                             | Policy reference v (cited)   |
| Region       |                                             |                              |
| Trade        |                                             | [Move up/down + reason]      |
| Safety class |                                             | [Send to review]             |
| Access mode  |                                             |                              |
+--------------+---------------------------------------------+------------------------------+
| Today: 12 jobs fit 6 crews - 7 remote / 5 town - 1 moved by hand - [Review and sign >]     |
+-------------------------------------------------------------------------------------------+
```

**Today's list, not the whole backlog.** The default tab shows the jobs that fit today's
capacity (crews times jobs per crew per day, from `core/constants.py`), ranked. The backlog
tab holds the rest, same columns, with its count in the tab label. This answers the Phase 1
finding that the board and the sign-off page printed all 506 open jobs. Capacity is the
existing simulation's input, not a new number.

**Weighting control.** Three named presets, default "Efficiency first" (lambda = 1.0, the
PRD's decide-before-reveal rule is unchanged). "Balanced" (lambda = 0.5) and "Need first"
(lambda = 0.0). The numeric slider lives under "Advanced"; choosing a preset sets it, moving
it clears the preset name. Beneath the control, one computed sentence states the effect of
the current weighting against efficiency-first: how many remote jobs moved into today's
list, the change in town median wait, the change in travel cost. The sentence is a template
over the two rankings and the capacity simulation; no model writes it.

**Ranked row.** Rank, change against efficiency-first (arrow glyph and number), job id
(mono), community id, fault type, safety class badge, "days used of window" as `3 of 5 d`,
a stacked score bar in the four factor colours. The one-sentence "why" moves to the details
pane; in the row it is a tooltip. Required-field-missing rows do not appear here at all;
they live in the review queue (unchanged rule).

**Selection sync.** Selecting a row, a map marker, or a job in the visit plan sets one
session value, the selected job id. The details pane, the map highlight and the row
highlight all read it. Streamlit 1.63 provides `on_select` for dataframes, pydeck charts
and Altair charts, so the sync needs no custom component (Task 22 spike confirms this
before anything else is built).

**Map tab.** pydeck scatter layer on a Carto basemap with attribution; markers coloured by
region, sized by open jobs, region clusters at NT zoom, pan and zoom native. Selected job's
marker enlarged with a terracotta ring. If tiles fail to load, the existing Altair outline
renders with the same markers and an `st.info` saying the basemap is unavailable. No route
lines on this map; routes belong to the visit plan.

**Details pane.** Header: job id, community, fault, safety class badge, days used of
window. "Why it sits here" sentence. Four factor metrics with the phrase that drove each,
an em dash and "No source phrase found" where none. Evidence expander: the verbatim report
with phrases highlighted in the factor colour, then a table of **field, extracted value,
source phrase, status badge** (Phase 1 omitted the value column). Policy reference expander:
retrieved passages that bear on this job's class or window, each with source title, section
and effective date; "No policy passage found" when retrieval falls below threshold.
Actions: move up or down with a required reason; send to review with a reason.

**Decision strip (bottom).** Counts only: jobs fitting today, remote/town split, hand-moved
jobs, review-queue size, and the single primary button "Review and sign". Metrics that the
PRD hides until sign-off stay hidden here.

## 4. Review queue

```text
+ Review queue (4) ----------------------------------------------------------------------+
| JR-2025-00106  BARKLY R-09  - fault type missing                                       |
| + Report (verbatim) ------------------+ + Fields -----------------------------------+  |
| | "...the rangehood over the stove    | | fault type    -  No verified phrase  [v]  |  |
| |  stopped pulling air..."            | | safety class  Urgent  "smoke fills..." ok |  |
| |                                     | | health risk   -  Not recorded             |  |
| +-------------------------------------+ +-------------------------------------------+  |
| Model proposed "ventilation" but its phrase was not found in the report.               |
| [Set fault type v]  [Mark rankable]        [Leave in queue]                            |
+----------------------------------------------------------------------------------------+
```

One job at a time, source and fields side by side. The message names the field that is
missing and why (phrase not found, field absent), never the fixed "missing fault type,
safety class" of Phase 1. The coordinator picks the value from the enum, the choice is
logged as a human-set field, and the job moves to the ranked list on the next rerun. This
closes the Phase 1 gap where human-set values never reached the ranking.

**New report intake** opens a dialog from the workspace header: a text area, "Extract".
While the model runs, a status line shows the model name and elapsed time. On return, the
fields table above is shown in the dialog; if every required field verified, "Add to
today's list"; otherwise "Send to review queue". On model failure or timeout, the report is
saved to the queue with status "not extracted" and an `st.error` names the cause. Extraction
provider is a setting (Claude via the existing CLI wrapper, or Ollama); the audit entry
records provider, model, prompt version, latency and validation result.

## 5. Sign-off (a dialog from the workspace, not a page)

```text
+ Review and sign - 2025-12-30 -----------------------------------------------+
| Weighting  Balanced (lambda = 0.50)                                         |
| Today's list  12 jobs - 7 remote - 5 town      Backlog  494                 |
| Moved by hand  1   JR-2025-00997 ^3  "crew already passing R-14"            |
| In review queue  4  (not ranked)                                            |
| Reason for today's weighting  [text area, required]                         |
| Signer  [text input, required]                                              |
| [Sign today's list]                                                         |
| The full ranked list is written to the audit log and exported as CSV.       |
+-----------------------------------------------------------------------------+
```

Counts and exceptions, not identifiers. After signing: the wait-metrics panel appears on the
workspace, the visit plan unlocks, and later weighting changes are logged as revisions
(PRD rule unchanged).

## 6. Visit plan

```text
+ Visit plan - signed 2025-12-30 by A. Coordinator ---------------------------+
| Crew Katherine (base Katherine, 2 jobs/day)         Crew Alice Springs ...  |
| 1. JR-2025-01347  Katherine        0 km   cooling                           |
| 2. JR-2025-00997  BIG RIVERS R-14  180 km road, open   sewer                |
| Travel 3.1 h - work 4.0 h - within capacity                                 |
|                                                                             |
| Left for manual coordination                                                |
| JR-2025-01207  EAST ARNHEM R-01  barge access, no road route                |
|                                                                             |
| Order changes against the signed list: none                                 |
| [Accept plan]  [Edit order]  [Reject with reason]                           |
+-----------------------------------------------------------------------------+
```

Deterministic: nearest-neighbour from each crew base over haversine distance times the road
factor, respecting jobs per crew per day and the signed priority as a tie-break. Air and
barge jobs are never routed. Any stop order that departs from signed priority is listed as
a change with the travel saving, and the coordinator accepts or rejects it; the plan never
reorders silently. Accepted and rejected plans are audit entries.

## 7. Tenant answer

Content unchanged from PRD §3.4. Two additions and two fixes: the empty state explains what
a registration number looks like and where to find it; a "Policy source" line cites the
window's source document and date; the article and unit errors seen in Phase 1 ("a urgent",
"2 days" for business days) are corrected in the template.

## 8. Evidence lab

Three tabs, for judges and governance, outside the coordinator's flow:

- **Extraction quality.** Per-field precision, recall, F1 with Wilson intervals; baseline
  classifier beside the model; adversarial set result; provider and model named.
- **Feedback loop.** Both runs drawn from the first render: efficiency-only against the
  page's own default lambda = 0.5, so the comparison the page exists for is visible without
  a click. Decay slider unchanged.
- **Audit log.** Readable column names (kind, day, previous weighting, new weighting,
  reason, signer, at), no index column, override rate by day on a daily axis, CSV export.
  Timestamps of runtime entries follow the dataset day, not the wall clock, so a demo does
  not show two calendars.

## 9. States every surface must have

| State | Where | What the user sees |
|---|---|---|
| Nothing selected | Details pane | "Select a job from the list or the map." |
| No jobs today | Workspace | `st.info`: no open jobs for this day and region; suggest widening the region. |
| All jobs in review | Workspace | List empty, banner linking to the queue with the count. |
| Model running | Intake dialog | Provider, model, elapsed seconds. |
| Model failed | Intake dialog | `st.error` with cause; report saved to the queue as "not extracted". |
| Basemap unavailable | Map | Altair outline with the same markers; `st.info` names the failure. |
| No policy passage | Details pane | "No policy passage found above the relevance threshold." |
| Not signed yet | Visit plan | `st.info`: sign today's list first; button to the sign-off dialog. |
| Job not in today's set | Details pane | Actions disabled with the reason, as in Phase 1. |

Every state uses the design system's empty and unverified rules: em dash for missing, gray
badge for unverified, yellow badge for needs-a-human, one alert per section.

## 10. Phase 1 review findings this design absorbs

From the 2026-09-14 visual review against PRD §3:

- Board printed all 506 open jobs and hid most PRD columns behind horizontal scroll: today's
  list tab, score bar in row, "why" in the pane.
- Queue message said "missing fault type, safety class" for all 21 jobs while most were
  missing one field: per-field reason in the review queue.
- Job card fields table had no value column: field, value, phrase, status.
- Sign-off printed 506 identifiers: counts and exceptions dialog.
- Feedback page drew one run at the default: own default lambda = 0.5, both runs.
- Audit table used internal column names and an hourly axis for daily data: readable
  columns, daily axis.
- Tenant copy "a urgent", "2 days": template fix.
- Towns labelled "community Darwin": "town Darwin"; community ids stay pseudonymous.

## 11. Criteria for the critique

Fixed before the critique, scored by the critic against each scenario in §1:

1. **First-use clarity.** Can a first-time user say what the product decides and who decides
   it from the workspace alone?
2. **Decision speed.** Steps from opening the workspace to a signed list, scenario 2.
3. **Evidence visibility.** Is every model-derived field one click from its source phrase?
4. **Accessibility.** Colour never the only channel; keyboard path through list, pane, sign.
5. **Implementation feasibility.** Buildable in Streamlit 1.63 with native selection events
   and no custom CSS; the Task 22 spike is the proof.

Questions the critic should attack: does the preset control hide lambda too well for a
judge who wants to see the number; is a dialog the right home for sign-off or does it lose
the decide-before-reveal ceremony; does the visit plan reintroduce the efficiency pull the
equity setting exists to resist; which states in §9 are missing.

## 12. What changes in the PRD after critique

- §3 rewritten as the five surfaces above; the six-screen numbering retired.
- §5: the model also runs at intake time, through the same schema and verification; a
  retrieval layer supplies cited policy passages to the details pane and tenant answer, and
  nothing else.
- §8: crew visit order moves in as "visit-plan recommendation after sign-off"; live intake
  moves in; offline-only leaves.
- §9: the prototype runs with internet; the artefact path stays as the no-model fallback.
