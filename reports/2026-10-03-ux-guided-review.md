# Survey: a review screen that always says what is done and what is next (Readmark, 2026-10-03)

**Question.** The product owner, who knows every concept, opened the Task-00 review screen and "did
not understand what I did and what I need to do". How should the screen guide an NT delegated
officer through one AI-checked application (8 policy clauses, required passages, outcomes,
disputes, sign-off) so the officer always knows what is done and what is next?

**How it was run.** Four research workers (`opus`), one strand each: government service-design
patterns, commercial caseworker workspaces, human–AI interaction guidance, known traps. Discovery
routes: WebSearch, `web_ara.py` (DuckDuckGo), `gh` (dates and source code), `hn_ara.py` (nothing
usable). A separate citation pass re-checked the deciding claims (see the end). The first section
is the orchestrator's own look at the screen. Input for a decision, not a decision: the layout
choice is Tarık's.

## 1. Why the current screen loses its user (orchestrator, from the Task-00 screenshots)

Screens: `reports/screens/2026-10-03-wave1/task-00-r0-01`, `-05`, `-07`, `-12` (1440 wide).

1. **No statement of the job.** Nothing says "you are deciding this application: check the flagged
   passages, set an outcome for each of the 8 clauses, then sign". The page opens on a list.
2. **Ordered by passage, while the officer thinks by question.** The page starts with "Required
   reading" (passages); the 8 clauses, where the decisions are made, start below the fold and run
   for several screens. NN/g: 57% of viewing time is above the fold, 74% in the first two
   screenfuls (https://www.nngroup.com/articles/scrolling-and-attention/, 2018-04-15).
3. **Internal language.** Rows read "p. 4 ¶1 · Quote not found · claim c15"; the header shows
   `claude-opus-5-5` and `jev-1.13.0`. Three of the five required rows come from one claim, with
   no sentence saying why the officer must look.
4. **Half the progress is invisible.** The counter shows passages (5/5) but not outcomes (0/8), so
   at 5/5 the sign-off is still locked and the reason is a wall of text listing 8 clause names.
5. **Two views of the same passages** (the required list and the clause cards) in different words.
6. **No "next" control.** After an action, nothing points to the next one.

## 2. Findings

Format: claim · verdict · source with its date · what it changes for Readmark.

### 2.1 Government service design

- **Task list ("Complete multiple tasks").** One list of tasks, each with a status; "Completed" in
  plain black so unfinished rows stand out; "Cannot start yet" in grey and not a link; start with
  the fewest statuses. · confirmed ·
  https://design-system.service.gov.uk/patterns/complete-multiple-tasks/ (source edited
  2026-01-26; read 2026-10-03); component released in GOV.UK Frontend v5.0.0 on 2023-12-08, last
  changed v5.5.0 on 2024-08-09
  (https://github.com/alphagov/govuk-design-system/blob/main/src/components/task-list/changelog.yml).
  · **Changes:** one list as the screen's spine: the 8 clause rows with a status each, and a
  "Sign off: cannot start yet" row.
- **Why it exists.** Users needed every task at a glance, the order, how to plan their time, and
  which are done; tested with 34 users over 5 rounds. · confirmed ·
  https://designnotes.blog.gov.uk/2017/04/04/weve-published-the-task-list-pattern/ (2017-04-04).
  · **Changes:** these are the owner's complaint, word for word.
- **Research details.** Users clicked status tags as if they were buttons, so the whole row became
  the link · confirmed ·
  https://designnotes.blog.gov.uk/2023/12/15/working-as-a-community-to-iterate-the-task-list-pattern/
  (2023-12-15). Once some tasks were done, the unfinished ones were hard to spot, and GOV.UK still
  needs to user-test the new component · confirmed ·
  https://design-system.service.gov.uk/components/task-list/ (read 2026-10-03). · **Changes:** the
  whole clause row is clickable; status is an adjective, not a button.
- **Wording checked independently.** HMRC's pattern is based on the status tags of three HMRC
  services (AMLS, Register a trust, Manage a registered pension scheme); there is evidence users
  found "Not started / In progress / Completed" easy to understand, and no findings supported
  coloured boxes (pattern now archived). · confirmed ·
  https://design.tax.service.gov.uk/hmrc-design-patterns/status-tags-in-task-list-pages/ (read
  2026-10-03). · **Changes:** a second source for plain-text statuses.
- **Counter.** The Australian Government agriculture design system (AgDS) task list heading shows
  "{tasksCompleted} of {totalTasks} tasks completed" and briefly highlights a task just completed;
  NSW's progress indicator allows "Step _ of _". · confirmed ·
  https://github.com/agriculturegovau/agds-next/blob/main/packages/react/src/task-list/TaskListHeading.tsx
  (file last changed 2025-01-06; repo pushed 2026-09-30); https://design-system.agriculture.gov.au/components/task-list and
  https://designsystem.nsw.gov.au/components/progress-indicator/index.html (read 2026-10-03). ·
  **Changes:** "3 of 8 outcomes set · 5 of 5 passages opened", and a brief highlight on the row
  just decided ("what did I just do").
- **Step by step navigation is not for this.** GOV.UK: do not use it inside a transactional
  service; use Complete multiple tasks. · confirmed ·
  https://design-system.service.gov.uk/patterns/step-by-step-navigation/ (read 2026-10-03). ·
  **Changes:** no stepper.
- **Check answers before submitting.** A summary with Change links and a declaration. · confirmed
  (one origin) · https://design-system.service.gov.uk/patterns/check-answers/ (source edited
  2026-09-01). · **Changes:** sign-off shows the 8 outcomes, disputes and the reason, each with
  Change, then locks.
- **Staff tools are allowed density.** Admin users may need to see everything in one place to
  decide; staff know the process, so optimise for speed, more on a page, full width. · confirmed by
  two origins · https://www.gov.uk/service-manual/design/services-for-government-users
  (2018-01-11); https://designnotes.blog.gov.uk/2015/09/25/design-principles-for-admin-interfaces/
  (2015-09-25); https://design-system.dwp.gov.uk/get-started/internal-systems (read 2026-10-03). ·
  **Changes:** keep the evidence dense; "one thing per page" is not the rule here. The next step
  must still be stated.
- **Keep the case and its next action in view.** MOJ identity bar (2021, "to be reviewed"); DWP
  quick reference (page updated 2025-08-04). · confirmed ·
  https://design-patterns.service.justice.gov.uk/components/identity-bar/ and
  https://design-system.dwp.gov.uk/components/quick-reference (read 2026-10-03). · **Changes:** a
  persistent case bar: applicant, file, counter, the one next action.
- **DWP "Design for" questions.** Status (what is the case doing now), Instruction (what action is
  required now), Evidence (what must the user know to decide), Outcome (what happened after the
  last action). · confirmed, one source (a lead) · https://design-system.dwp.gov.uk/design-for
  (undated; read 2026-10-03). · **Changes:** a checklist for the redesign: each screen area
  answers one question.
- **The old Australian Government Design System is gone** (DTA support ended September 2021; the
  GOLD fork's last commit 2021-09-22). · confirmed ·
  https://www.itnews.com.au/news/dta-abandons-open-source-govt-design-system-568669 (2021-08-17);
  https://github.com/designsystemau/gold-design-system. · **Changes:** cite GOV.UK and AgDS, not
  the old AU system.

### 2.2 Caseworker and review workspaces

| Option | What it is | Status with date | Practice findings | Fit for Readmark |
|---|---|---|---|---|
| Relativity Review Center | Legal document review: a queue serves documents one at a time, a coding pane beside the viewer | Shows "Total Remaining", "Reviewed Today", "Save and Next", and an end-of-batch dialog "Check in as complete & start next batch" (page modified 2026-09-16) https://help.relativity.com/RelativityOne/Content/Relativity/Review_Center/Reviewing_documents_using_Review_Center.htm | Practice: reviewers report coding-panel latency (Dec 2024) and a slow review UI (Dec 2019), https://www.softwareadvice.com/ediscovery/relativity-profile/reviews/ (read 2026-10-03) | High: required reading is one small batch; copy the remaining-count, "next", and the end-of-batch prompt that names the next step |
| Dynamics 365 business process flow | Stage bar on the form; required steps gate "Next stage" ("stage-gating"); a stage can be pinned to a side pane | Overview (2026-08-15) https://learn.microsoft.com/en-us/power-automate/business-process-flows-overview | Practice: builders found the default Next/Previous stage buttons "well hidden" and added their own (2025-04-17) https://dev.to/kkazala/business-process-flow-with-custom-buttons-3o71; many required fields in a stage hurt the experience (2022-04-07) https://www.bendenblanken.com/set-form-fields-required-based-on-business-process-flow-stage/ | High for the lock: the gate lists exactly what blocks it, and "next" must be visible |
| Pega case life cycle | Stages → processes → steps; a chevron indicator; "Get Next Work" serves the next assignment | Stages "visualize the milestones" (2026-06-16) https://docs.pega.com/bundle/platform/page/platform/case-management/stages-case-life-cycle.html; stage names are 1–2 nouns that read in "This Case is in <Stage>" https://academy.pega.com/topic/case-lifecycle/v7 (read 2026-10-03) | Practice: users may wish to move freely between stages; Pega says the indicator "is not intended to function as a navigation control" (2026-09-03) https://support.pega.com/support-doc/case-lifecycle-stages-are-not-clickable-navigation; complex flows "challenging for new users" (2025-08-08) https://www.peerspot.com/products/pega-customer-service-reviews | Medium: noun-named stages; whatever looks clickable must be |
| Salesforce Path, Actions & Recommendations, Public Sector Solutions | Chevron bar with key fields and "guidance for success" per stage; a to-do list with mandatory items; a guided benefit review | Path guidance shown under the path (read 2026-10-03) https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/aura-path.html; mandatory actions and a history tab https://developer.salesforce.com/docs/service/salesforce-guided-engagement/guide/guided-engagement-sample-user-experience.html; PSS "Check Eligibility" and a Decision Explainer https://trailhead.salesforce.com/content/learn/modules/benefit-management-with-public-sector-solutions/process-benefit-applications | Practice: Path limited to 5 key fields and 1,000 characters of guidance; Path vanishing on closed records (2021, updated 2023-10-20) https://www.salesforceben.com/implement-salesforce-path/ | Medium-high: one line of "what to do here" under the current step is the cheapest fix |

Suggested first try from this strand: a Relativity-style "remaining / next" loop over the flagged
passages, inside a stage idea of three nouns (Reading → Clauses → Sign-off).

### 2.3 Human–AI interaction

- **Say first what the system does** (HAX G1: an introductory blurb, example outputs). · confirmed
  · https://www.microsoft.com/en-us/haxtoolkit/guideline/make-clear-what-the-system-can-do/ (read
  2026-10-03); paper https://www.microsoft.com/en-us/research/publication/guidelines-for-human-ai-interaction/
  (May 2019). PAIR: "Be up-front about what your product can and can't do the first time";
  "Onboard in stages" https://pair.withgoogle.com/chapter/mental-models/ (read 2026-10-03). ·
  **Changes:** one header line: "Claude drafted claims from this file; code checked each quote; a
  second model re-checked each claim; you set every outcome."
- **How well, without per-claim scores.** HAX G2 asks to report system performance
  (https://www.microsoft.com/en-us/haxtoolkit/guideline/make-clear-how-well-the-system-can-do-what-it-can-do/,
  read 2026-10-03); Passi & Vorvoreanu: "Do not uncritically present high performance scores
  because they cause user overreliance"
  (https://www.microsoft.com/en-us/research/wp-content/uploads/2022/06/Aether-Overreliance-on-AI-Review-Final-6.21.22.pdf,
  June 2022). · confirmed · · **Changes:** the frozen evaluation numbers, with n, behind "How reliable are these
  checks"; no probability on each claim row (the current "Checker: supports 0.90" goes).
- **Why, on demand** (HAX G11, with its warning that explanations can raise overreliance) and
  **efficient correction** (HAX G9). · confirmed ·
  https://www.microsoft.com/en-us/haxtoolkit/guideline/make-clear-why-the-system-did-what-it-did/ and
  https://www.microsoft.com/en-us/haxtoolkit/guideline/support-efficient-correction/ (read
  2026-10-03). · **Changes:** each status opens its reason in plain words; outcome and dispute one
  click from the claim, reversible until sign-off.
- **Tutorials are overused; help should be at the moment of need, dismissible and recallable.** ·
  confirmed · https://www.nngroup.com/articles/onboarding-tutorials/ (2023-02-12);
  https://www.nngroup.com/articles/new-AI-users-onboarding/ (2024-03-29). · **Changes:** a short
  first-run panel and a "?" to bring it back, not a tour.
- **Complex apps: help users keep a record of their actions; make critical elements salient.** ·
  confirmed · https://www.nngroup.com/articles/complex-application-design/ (2020-11-08). ·
  **Changes:** the counters and the next action stay on screen.
- **Sources next to claims; explanations grounded in familiar rules for domain experts.** ·
  confirmed · https://www.nngroup.com/articles/explainable-ai/ (2025-12-12);
  https://www.nngroup.com/articles/crafting-ai-explanations/ (2026-07-03, single source). ·
  **Changes:** keep quote-in-passage highlighting; name clauses in words ("Debts, Eligibility
  §3.4").
- **Forcing functions work and are disliked.** Buçinca et al. (N=199): cognitive forcing reduced
  overreliance, and "people assigned the least favorable subjective ratings to the designs that
  reduced the overreliance the most". · confirmed · https://arxiv.org/abs/2102.09692 (2021-02-19);
  Passi & Vorvoreanu (June 2022, above). · **Changes:** the reading gate will feel like friction by
  design; the screen must say why it exists in one sentence.
- **Explanations help when they make verifying cheap.** Vasconcelos et al. (N=731; 5 studies, a
  maze task with a simulated AI). · confirmed ·
  https://arxiv.org/abs/2212.06823 (2022-12-13); Fok & Weld https://arxiv.org/abs/2305.07722
  (2023-05-12). · **Changes:** a required passage opens with its quote already highlighted, beside
  the claim it bears on (today's pane already does this).
- **Alert fatigue.** Clinicians accepted alerts less as they received more, especially repeated
  ones. · confirmed, single source · https://link.springer.com/article/10.1186/s12911-017-0430-8
  (2017-04-10). · **Changes:** keep the cap of 8 and never show the same passage twice as two tasks.
- **Show the system erring during onboarding** ("never seeing the system err makes users
  over-trust"). · confirmed, single source (Passi & Vorvoreanu, above). · **Changes:** the
  first-run panel shows one supported claim and one failed claim.
- **No internal ids.** "Backend codes and internal jargon … mean nothing to the user". · confirmed
  · https://www.nngroup.com/articles/status-tracker-progress-update/ (2019-02-03); Australian
  Government Style Manual, "Remove jargon, slang and idioms"
  https://www.stylemanual.gov.au/writing-and-designing-content/clear-language-and-writing-style/plain-language-and-word-choice
  (updated 2024-12-20). · **Changes:** "page 4, paragraph 1", no "claim c15", no model ids in the
  header (move them to "About these checks").

### 2.4 Traps

- **Wizards annoy experts and repeat users; a wizard should not be the only way; allow any order.**
  · confirmed · https://www.nngroup.com/articles/wizards/ (2017-06-25);
  https://ui-patterns.com/patterns/Wizard (read 2026-10-03); GOV.UK complete-multiple-tasks
  (above). · **Changes:** clauses in any order, plus a "next unresolved" shortcut.
- **Banners get skipped; a short linked summary plus a message at each item works.** · confirmed ·
  https://www.nngroup.com/articles/banner-blindness-old-and-new-findings/ (2018-04-22);
  https://design-system.service.gov.uk/components/error-summary/ (read 2026-10-03);
  https://www.nngroup.com/articles/errors-forms-design-guidelines/ (2019-02-03, reviewed
  2024-12-12). · **Changes:** replace the text-wall banner with "3 things before you can sign",
  each a link, with the same message on its row.
- **Too many statuses.** Carbon: "more than five or six indicators can overwhelm users"; use two
  of colour, shape and symbol. · confirmed (guidance, not a study) ·
  https://carbondesignsystem.com/patterns/status-indicator-pattern/ (updated 2026-08-12); WCAG
  1.4.1 https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html (updated 2025-09-16). ·
  **Changes:** the list level shows only "outcome set / not set" and "opened / not opened"; the
  four claim-check statuses stay inside the clause detail.
- **Disabled buttons confuse; keep the button and explain on click.** · confirmed ·
  https://design-system.service.gov.uk/components/button/ (read 2026-10-03);
  https://www.smashingmagazine.com/2021/08/frustrating-design-patterns-disabled-buttons/
  (2021-08-05). · **Changes:** "Sign decision" stays enabled and opens the linked summary
  (Task-00 already does; the summary is what needs fixing).
- **Hard stops work and breed workarounds.** Of 32 studies, 79% of those measuring health
  outcomes (15) and 88% of those measuring process outcomes improved; 11 reported unintended
  consequences, including avoidance of the hard-stopped workflow and delay to care. · confirmed · https://academic.oup.com/jamia/article-abstract/25/11/1556/5101436
  (2018-09-18); barcode-system workarounds https://pmc.ncbi.nlm.nih.gov/articles/PMC2442264/
  (2008). · **Changes:** expect open-to-unlock; the record already says "opened", never "read".
- **Progress indicators.** GOV.UK: start without one; Carer's Allowance removed a 12-step
  indicator with no effect on completion
  (https://design-system.service.gov.uk/patterns/question-pages/, read 2026-10-03); a meta-analysis
  of 32 experiments found no drop-off reduction
  (https://research.google/pubs/where-am-i-a-meta-analysis-of-experiments-on-the-effects-of-progress-indicators-for-web-surveys/,
  2013); Baymard: if you show steps, map them 1:1 and make past steps clickable
  (https://baymard.com/blog/checkout-flow-ux-optimization, 2026-04-23). · confirmed, and see
  Contradictions · **Changes:** plain counts, not a step bar.
- **List–detail.** Microsoft recommends list/details to locate and prioritise a collection and to
  work back and forth (https://learn.microsoft.com/en-us/windows/apps/develop/ui/controls/list-details,
  2026-09-27); overview+detail gave the highest comprehension but the slowest reading (Cockburn et
  al. review, https://www.csse.canterbury.ac.nz/andrew.cockburn/papers/fc.pdf, 2008). · confirmed,
  with a trade-off · **Changes:** two panes, not three, where possible.

## 3. Contradictions (reported, not resolved)

- **Task list scope.** GOV.UK: use the task list only if there is evidence users cannot finish in
  one sitting and need to choose the order; the page lists both conditions without "or", so it may
  require both (https://design-system.service.gov.uk/components/task-list/, read 2026-10-03).
  Readmark is probably one sitting, while the officer does choose the clause order: one condition
  holds. If both are required, this weakens Option A.
- **Progress.** GOV.UK and a 32-experiment meta-analysis find progress indicators do little for
  completion; Baymard says a step indicator matters if steps exist. Both measure completion or
  drop-off, not understanding, which is the owner's problem.
- **Statuses named by action.** Plain-language guidance favours saying what to do; GOV.UK says tag
  names are adjectives, not verbs, because verbs look clickable
  (https://design-system.service.gov.uk/components/tag/, read 2026-10-03). Resolution used in
  the options below: the tag is an adjective, the action is a separate button.
- **Overview vs speed.** Overview+detail improves comprehension and slows reading (Cockburn et al.,
  above). Staff-tool guidance asks for speed and density (GDS, DWP, above).

## 4. Unknown (TBD — needs validation)

- How many statuses users can track: guidance says 5–6, no study found. Settle with a first-click
  test on the status legend with 5 people.
- Whether list–detail beats the current long page for desktop case review: no study specific to
  case-review tools. Settle with a hallway test: 5 first-time viewers, current page vs a prototype,
  "what would you do next?" after 10 seconds.
- How many required passages to force: no source gives a number. The held-out run will show flag
  counts and time.
- Published research on task lists in caseworker (staff) tools: none found; all of it is
  citizen-facing.
- Guidewire ClaimCenter workplan UI (docs behind a login); whether Salesforce Path is collapsed by
  default; Pega review quotes on G2 and Gartner (blocked).

## 5. Three layouts for 1280–1440 px

Common to all three (cheap, evidence-backed, independent of the layout):
- a **case bar** that stays on screen: applicant and file, "Outcomes 3 of 8 · Flagged passages 5 of
  5", and the one next action as a button;
- a **one-line job statement** and a dismissible first-run panel ("? How this works") showing what
  the AI did, what the checks did, what the officer decides, with one supported and one failed claim;
- **plain language**: "page 4, paragraph 1"; no claim ids; model names under "About these checks";
  each flag says why in one sentence ("The claim gives a date (16 Feb 2026) that none of its quotes
  contains");
- **sign-off**: the button stays enabled; clicking it early shows "3 things before you can sign",
  each a link; when ready, a check-answers summary (8 outcomes, disputes, reason, Change links), then
  the record.

**Option A — Task list home, one clause per page** (GOV.UK Complete multiple tasks).
A home list: "Check flagged passages (5)", the 8 clause rows (Not started / In progress / Outcome:
Met), "Sign off: cannot start yet". A row opens the clause page: policy sentence, evidence rows,
source pane on the right, outcome control, "Save and go to the next clause".
- Fixes: orientation and "what next" most directly; matches the research users' own needs (34
  users, 5 rounds).
- Costs: loses the all-clauses overview the staff-tool guidance asks for; more clicks for an expert;
  the pattern is citizen-tested, not staff-tested; the most rework (routing, new pages).

**Option B — Clause list on the left, the clause and its sources on the right** (list–detail,
Relativity/Dynamics style). Left rail (about 300 px): the counter, "Flagged passages 5", the 8
clause rows with status, "Sign off". Right: the selected clause's evidence rows with the source
passage beside them, the outcome control at the bottom, "Next clause" button.
- Fixes: the whole job stays visible while working on one clause; any order; next is one click;
  status at a glance without scrolling.
- Costs: three columns at 1280 px is tight (rail + evidence + source), so the source pane needs to
  overlay or collapse; switching costs between list and detail (Cockburn); a medium rework of
  `web/app.js` layout, none of the pipeline.

**Option C — Keep the long page, add the guidance layer.** Same page, reordered: clause cards
first with their flagged passages inside each card (one place per passage), the case bar and
counters on top, the linked sign-off summary, plain language.
- Fixes: the cheapest; keeps everything the gate and record already do; removes the duplicate
  view.
- Costs: the long scroll stays (attention falls off below the first two screens); the officer still
  has to find the next undecided clause by scrolling.

**Suggestion (labelled as a suggestion; Tarık decides):** Option B, with the common parts above.
It answers the owner's complaint (what is done, what is next) without hiding the whole case from an
expert, and it reuses the source pane and gate Task-00 already built. Before building it, the
hallway test in §4 on a static mock costs an hour and settles the main unknown.

## Where this belongs

Input to the next UI wave (`plan-wave` acceptance criteria) and an open question for Blueprint →
Decisions (the review screen's layout, A/B/C). Nothing here changes Blueprint by itself.

## Citation pass

A separate worker re-opened the cited page for 22 deciding claims on 2026-10-03: 19 found as
written, 3 partly (the overreliance quote is in the Passi & Vorvoreanu PDF, not on the HAX G2 page;
the hard-stop percentages apply to subsets of the 32 studies; the GOV.UK task-list conditions may
both be required), 0 not found. All corrections are applied above.

## Sources

- https://www.nngroup.com/articles/scrolling-and-attention/ — 2018-04-15
- https://design-system.service.gov.uk/patterns/complete-multiple-tasks/ — source edited 2026-01-26; read 2026-10-03
- https://github.com/alphagov/govuk-design-system/blob/main/src/components/task-list/changelog.yml — 2023-12-08, 2024-08-09
- https://designnotes.blog.gov.uk/2017/04/04/weve-published-the-task-list-pattern/ — 2017-04-04
- https://designnotes.blog.gov.uk/2023/12/15/working-as-a-community-to-iterate-the-task-list-pattern/ — 2023-12-15
- https://design.tax.service.gov.uk/hmrc-design-patterns/status-tags-in-task-list-pages/ — read 2026-10-03
- https://github.com/agriculturegovau/agds-next/blob/main/packages/react/src/task-list/TaskListHeading.tsx — file last changed 2025-01-06; repo pushed 2026-09-30
- https://design-system.agriculture.gov.au/components/task-list — read 2026-10-03
- https://designsystem.nsw.gov.au/components/progress-indicator/index.html — read 2026-10-03
- https://design-system.service.gov.uk/patterns/step-by-step-navigation/ — read 2026-10-03
- https://design-system.service.gov.uk/patterns/check-answers/ — source edited 2026-09-01
- https://www.gov.uk/service-manual/design/services-for-government-users — 2018-01-11
- https://designnotes.blog.gov.uk/2015/09/25/design-principles-for-admin-interfaces/ — 2015-09-25
- https://design-system.dwp.gov.uk/get-started/internal-systems — read 2026-10-03
- https://design-patterns.service.justice.gov.uk/components/identity-bar/ — read 2026-10-03
- https://design-system.dwp.gov.uk/components/quick-reference — page updated 2025-08-04
- https://design-system.dwp.gov.uk/design-for — undated; read 2026-10-03
- https://www.itnews.com.au/news/dta-abandons-open-source-govt-design-system-568669 — 2021-08-17
- https://github.com/designsystemau/gold-design-system — last commit 2021-09-22
- https://help.relativity.com/RelativityOne/Content/Relativity/Review_Center/Reviewing_documents_using_Review_Center.htm — modified 2026-09-16
- https://www.softwareadvice.com/ediscovery/relativity-profile/reviews/ — read 2026-10-03
- https://learn.microsoft.com/en-us/power-automate/business-process-flows-overview — 2026-08-15
- https://dev.to/kkazala/business-process-flow-with-custom-buttons-3o71 — 2025-04-17
- https://www.bendenblanken.com/set-form-fields-required-based-on-business-process-flow-stage/ — 2022-04-07
- https://docs.pega.com/bundle/platform/page/platform/case-management/stages-case-life-cycle.html — 2026-06-16
- https://academy.pega.com/topic/case-lifecycle/v7 — read 2026-10-03
- https://support.pega.com/support-doc/case-lifecycle-stages-are-not-clickable-navigation — 2026-09-03
- https://www.peerspot.com/products/pega-customer-service-reviews — 2025-08-08
- https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/aura-path.html — read 2026-10-03
- https://developer.salesforce.com/docs/service/salesforce-guided-engagement/guide/guided-engagement-sample-user-experience.html — read 2026-10-03
- https://trailhead.salesforce.com/content/learn/modules/benefit-management-with-public-sector-solutions/process-benefit-applications — read 2026-10-03
- https://www.salesforceben.com/implement-salesforce-path/ — 2021, updated 2023-10-20
- https://www.microsoft.com/en-us/haxtoolkit/guideline/make-clear-what-the-system-can-do/ — read 2026-10-03
- https://www.microsoft.com/en-us/research/publication/guidelines-for-human-ai-interaction/ — May 2019
- https://pair.withgoogle.com/chapter/mental-models/ — read 2026-10-03
- https://www.microsoft.com/en-us/haxtoolkit/guideline/make-clear-how-well-the-system-can-do-what-it-can-do/ — read 2026-10-03
- https://www.microsoft.com/en-us/research/publication/overreliance-on-ai-literature-review/ — June 2022
- https://www.microsoft.com/en-us/haxtoolkit/guideline/make-clear-why-the-system-did-what-it-did/ — read 2026-10-03
- https://www.microsoft.com/en-us/haxtoolkit/guideline/support-efficient-correction/ — read 2026-10-03
- https://www.nngroup.com/articles/onboarding-tutorials/ — 2023-02-12
- https://www.nngroup.com/articles/new-AI-users-onboarding/ — 2024-03-29
- https://www.nngroup.com/articles/complex-application-design/ — 2020-11-08
- https://www.nngroup.com/articles/explainable-ai/ — 2025-12-12
- https://www.nngroup.com/articles/crafting-ai-explanations/ — 2026-07-03
- https://arxiv.org/abs/2102.09692 — 2021-02-19
- https://arxiv.org/abs/2212.06823 — 2022-12-13
- https://arxiv.org/abs/2305.07722 — 2023-05-12
- https://link.springer.com/article/10.1186/s12911-017-0430-8 — 2017-04-10
- https://www.nngroup.com/articles/status-tracker-progress-update/ — 2019-02-03
- https://www.stylemanual.gov.au/writing-and-designing-content/clear-language-and-writing-style/plain-language-and-word-choice — updated 2024-12-20
- https://www.nngroup.com/articles/wizards/ — 2017-06-25
- https://ui-patterns.com/patterns/Wizard — read 2026-10-03
- https://www.nngroup.com/articles/banner-blindness-old-and-new-findings/ — 2018-04-22
- https://design-system.service.gov.uk/components/error-summary/ — read 2026-10-03
- https://www.nngroup.com/articles/errors-forms-design-guidelines/ — 2019-02-03, reviewed 2024-12-12
- https://carbondesignsystem.com/patterns/status-indicator-pattern/ — updated 2026-08-12
- https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html — updated 2025-09-16
- https://design-system.service.gov.uk/components/button/ — read 2026-10-03
- https://www.smashingmagazine.com/2021/08/frustrating-design-patterns-disabled-buttons/ — 2021-08-05
- https://academic.oup.com/jamia/article-abstract/25/11/1556/5101436 — 2018-09-18
- https://pmc.ncbi.nlm.nih.gov/articles/PMC2442264/ — 2008
- https://design-system.service.gov.uk/patterns/question-pages/ — read 2026-10-03
- https://research.google/pubs/where-am-i-a-meta-analysis-of-experiments-on-the-effects-of-progress-indicators-for-web-surveys/ — 2013
- https://baymard.com/blog/checkout-flow-ux-optimization — 2026-04-23
- https://learn.microsoft.com/en-us/windows/apps/develop/ui/controls/list-details — 2026-09-27
- https://www.csse.canterbury.ac.nz/andrew.cockburn/papers/fc.pdf — 2008
- https://design-system.service.gov.uk/components/task-list/ — read 2026-10-03
- https://design-system.service.gov.uk/components/tag/ — read 2026-10-03
- https://www.microsoft.com/en-us/research/wp-content/uploads/2022/06/Aether-Overreliance-on-AI-Review-Final-6.21.22.pdf — June 2022

When you rewrite this, keep each link and date beside its claim and paste the Sources block unchanged.
