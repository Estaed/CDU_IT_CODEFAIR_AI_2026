# UI and human-in-the-loop guidance for Fair Turn — what the screens must say

Checked **14 September 2026**. Primary sources where reachable. Two NT/Commonwealth pages
return HTTP 403 to the automated fetch tool; for those this report reuses the verbatim text
recorded in `reports/2026-09-12-research-assurance.md` (browser-read on 12 Sep 2026) and says
so at the citation. Anything not confirmed against a primary source is marked
**TBD — needs validation**.

Scope: presentation and usability only. Nothing here proposes weakening the trust design
(span verification, human queue, decide-before-reveal, deterministic ranking).

---

## 1. Human–AI interaction guidelines that map to UI elements

### 1.1 Microsoft HAX — the 18 Guidelines
**Claim:** there is a stable, citable set of 18 guidelines with named phases, several of which
name a screen element directly.
**Verdict: TRUE.** Introduced in a 2019 CHI paper; published as the HAX Toolkit.
**Sources:** <https://www.microsoft.com/en-us/haxtoolkit/ai-guidelines/> (checked 2026-09-14;
confirms "18 guidelines", 2019 CHI paper, four phases: initial interaction / during interaction /
when wrong / over time); <https://www.microsoft.com/en-us/haxtoolkit/library/> (checked
2026-09-14; the 18 titles).
The seven that bind Fair Turn, verbatim, and what each implies:

| # | Guideline | Concrete element for Fair Turn |
|---|---|---|
| G1 | "Make clear what the system can do" | A one-sentence purpose line at the top of every page, stating what the model does *and does not* do here (see §"Copy"). |
| G2 | "Make clear how well the system can do what it can do" | A persistent accuracy chip near the extracted fields: per-field F1 from `data/build/` eval, with the sample size and the date, linking to Evidence lab. Not model confidence (Blueprint forbids it) — measured, dated performance. |
| G4 | "Show contextually relevant information" | The source phrase shown beside each extracted field, in place, not on another page. |
| G9 | "Support efficient correction" | Override and "set by coordinator" must be reachable from the row itself, one control, not a separate screen. |
| G11 | "Make clear why the system did what it did" | The why-sentence sits next to the rank number, always visible — not behind a tooltip. |
| G16 | "Convey the consequences of user actions" | Before signing: state plainly what signing does (freezes the batch, releases the outcome view, writes the audit record). |
| G17 | "Provide global controls" | The equity weighting λ is exactly this: one global control, labelled, with its effect visible. Keep it above the list, not in a sidebar corner. |
| G18 | "Notify users about changes" | When a human edit invalidates a frozen batch, say so on screen with the old and new version, not silently. |

**Contradiction to note:** G2 ("how well") and Blueprint's ban on model confidence are *not* in
conflict — G2 asks for aggregate, measured performance; the ban is on per-item self-reported
confidence. Say this out loud in the report; a judge may otherwise read the missing confidence
as a gap.

### 1.2 Google PAIR People + AI Guidebook
**Claim:** PAIR gives concrete, citable rules on when and what to explain, on partial
explanations, and on user control.
**Verdict: TRUE.**
**Sources (checked 2026-09-14):** Explainability + Trust —
<https://pair.withgoogle.com/guidebook-v2/chapter/explainability-trust/>; Feedback + Controls —
<https://pair.withgoogle.com/guidebook-v2/chapter/feedback-controls/>. Guidebook is undated on
page (CC BY-NC-SA 4.0); v2 numbering. **TBD — needs validation:** exact publication date.
What it says a screen should show:
- Explain **in response to a user action**, **in high-stakes moments**, and **when missing data
  affects output quality**. → Fair Turn: the explanation belongs at the moment of ranking and at
  the moment of signing, not in a help page.
- Prefer **partial explanations** over total transparency — the impactful elements only. →
  Show the top three scoring factors inline; put the full factor table behind a disclosure.
- **Data sources: scope, reach, removal.** → A provenance caption on every page (already a
  Blueprint verification rule) is the scope element; name the dataset and that it is synthetic.
- Trust is built from **ability, reliability, benevolence** and "the process … is slow and
  deliberate". → Do not front-load one big disclaimer; repeat small, honest statements per page.
- Feedback + Controls: let people **turn the feature off** and offer a **manual fallback**;
  people want control most when stakes are high. → The intake panel must show its disabled
  state with a reason (already required), and the queue is the manual fallback — label it that way.

### 1.3 Governance frameworks that name what a screen must carry
**Claim:** NT, Commonwealth, EU and NIST instruments each name an on-screen obligation.
**Verdict: TRUE for NT, Commonwealth, EU; PARTLY for NIST (system-level, not screen-level).**

- **NT Government AI Assurance Framework (November 2025)**, six principles. Transparency:
  "Decisions and outputs from AI systems must be understandable and explainable to those they
  affect, **in proportion to the level of risk**. Clear mechanisms must be available for
  individuals to **question and challenge** AI-assisted outcomes." Accountability: "…retain
  ultimate responsibility … This requires **meaningful human oversight**."
  Source: <https://digitalterritory.nt.gov.au/digital-government/strategies-and-guidance/policies-standards-and-guidance/artificial-intelligence-assurance-framework>
  and <https://dcdd.nt.gov.au/publications/artificial-intelligence-assurance-framework> —
  both 403 to the fetch tool on 2026-09-14; verbatim text as recorded browser-read 2026-09-12 in
  `reports/2026-09-12-research-assurance.md`. **Contradiction:** regulations.ai dates the framework
  26 June 2024; the two primary NT pages say November 2025. Cite November 2025.
  → **Element:** the tenant page must carry a visible "how to question this" line, not just an
  explanation. That is the framework's own word, "challenge".
- **Australia's AI Ethics Principles** (8, DISR), including *Transparency and explainability* and
  a separate *Contestability*: "when an AI system significantly impacts a person … there should
  be a timely process to allow people to challenge the use or outcomes".
  <https://www.industry.gov.au/publications/australias-ai-ethics-principles> — fetch timed out
  2026-09-14; wording as recorded 2026-09-12 in `reports/2026-09-12-research-prior-art.md`.
- **DTA Policy for the responsible use of AI in government v2.0**, in effect **15 December 2025**,
  requires each agency to publish an **AI transparency statement**, keep a use-case register with a
  named accountable owner, and complete an AI impact assessment before deployment.
  <https://www.digital.gov.au/ai/ai-in-government-policy>,
  <https://www.digital.gov.au/ai/ai-in-government-policy/standard-ai-transparency-statements>
  (checked 2026-09-14 via search index; page fetch 403). → **Element:** an "About this AI" page or
  expander written in the shape of a transparency statement — what it is used for, who is
  accountable, what it does not decide. That is free marks on the ethics criterion.
- **EU AI Act Article 14(4)(b)**: the overseer must be enabled "to remain aware of the possible
  tendency of automatically relying or over-relying on the output produced by an AI system
  (automation bias)". <https://artificialintelligenceact.eu/article/14/> (checked 2026-09-14).
  → **Element:** show the coordinator their **own override rate** over the last N days on the
  workspace. This is the one metric that makes rubber-stamping visible to the person doing it.
- **NIST AI RMF 1.0 (NIST AI 100-1, January 2023), MEASURE 2.9**: "The AI model is explained,
  validated, and documented, and AI system output is interpreted within its context … to inform
  responsible use"; "it is critical to ensure that users know how to interpret system behavior and
  outputs, **including the limitations** of both the system and any explanations provided."
  <https://www.nist.gov/itl/ai-risk-management-framework> (secondary readings consulted
  2026-09-14; **TBD — needs validation** of the MEASURE 2.9 wording against the PDF).
  → **Element:** a "what this does not do" line on the same screen as the explanation.
- **ISO/IEC 42001:2023** — an AI management-system standard; it sets organisational controls, not
  screen content. **Not useful for UI.** Cite only in the governance paragraph of the report.

---

## 2. Onboarding and empty states for expert tools

### 2.1 Empty states
**Claim:** a blank screen is a defect, and there is a three-part fix.
**Verdict: TRUE.** Kate Kaplan, "Designing Empty States in Complex Applications: 3 Guidelines",
NN/g, **19 September 2021**, <https://www.nngroup.com/articles/empty-state-interface-design/>
(checked 2026-09-14). The three: (1) communicate **system status** — "Totally empty states cause
confusion about how and whether the system is working"; (2) provide **learning cues**; (3) provide
**direct pathways** (links/buttons) to the task that fills the container.
Second source, same guidance: NN/g video "Empty States in Application Design: 3 Guidelines",
<https://www.nngroup.com/videos/empty-states-in-application-design-guidelines/> (checked
2026-09-14).
→ **Element:** every Fair Turn empty state is three lines: status ("No batch signed for
12 March yet."), cue ("Outcome metrics appear here after you sign."), pathway (a button that goes
to the ranked list). No bare blanks anywhere.

### 2.2 Onboarding: contextual help beats a tour
**Claim:** an upfront guided tour is the wrong first move for an expert tool.
**Verdict: TRUE, with a caveat.** Page Laubheimer, "Onboarding Tutorials vs. Contextual Help",
NN/g, **12 February 2023**, <https://www.nngroup.com/articles/onboarding-tutorials/> (checked
2026-09-14): tutorials "don't result in better task performance"; prefer **pull revelations** —
"help content triggered by some signal that the user would benefit from that information at that
moment"; make it dismissible and retrievable. Second source: NN/g "Instructional Overlays and Coach
Marks for Mobile Apps", <https://www.nngroup.com/articles/mobile-instructional-overlay/> (checked
2026-09-14): overlays force memorisation, must be brief, optional, dismissible.
**Caveat / contradiction:** a judged demo is not ordinary first use — a judge watches for 10
minutes and never returns. The tour that NN/g warns against is exactly what a judge needs.
Resolve it the way both sources allow: **contextual help by default, plus one optional,
dismissible "Take the tour" control** that a presenter can trigger. Do not auto-open it.

### 2.3 Progressive disclosure and dashboard layout
**Claim:** put a small number of high-value items first, detail on request.
**Verdict: TRUE.** Jakob Nielsen, "Progressive Disclosure", NN/g, **3 December 2006**,
<https://www.nngroup.com/articles/progressive-disclosure/> (checked 2026-09-14): "defers advanced
or rarely used features to a secondary screen, making applications easier to learn and less
error-prone."
Page Laubheimer, "Dashboards: Making Charts and Graphs Easier to Understand", NN/g,
**18 June 2017**, <https://www.nngroup.com/articles/dashboards-preattentive/> (checked 2026-09-14):
dashboards "impart at-a-glance information on which users can act quickly"; favour **length and
2D position** (bars, lines) because they are preattentive; avoid pie, donut, gauge and 3D; use
colour as a secondary cue reinforcing something already encoded, and remember colour blindness.
Fair Turn's workspace is Laubheimer's **operational** dashboard, not the analytical one.
→ **Element:** workspace = a short KPI row (jobs today, in queue, overridden, λ in force) above the
map and list; factor detail behind an expander. Score factors as a **horizontal bar** (length),
never a gauge or donut.
**Caution:** the widely repeated "users abandon dashboards with more than 7 elements above the fold"
and "reduces cognitive load by 55%" lines circulating on SEO blogs are **not** in the NN/g articles
above. **TBD — needs validation; do not quote them.**

---

## 3. Explainable ranking and decision-support patterns

### 3.1 Factor contributions: bar or text?
**Claim:** a visual contribution chart beats a sentence.
**Verdict: MIXED — use both, and do not drop the sentence.** Evidence that format matters more
than method, and that text alone can produce an "illusion of understanding" — high self-reported
trust with low objective comprehension: "Exploring the Effect of Explanation Content and Format on
User Comprehension and Trust" (checked 2026-09-14 via
<https://lacuna.tiptreesystems.com/work/exploring-the-effect-of-explanation-content-and-format-on-user-comprehension-and/>;
**TBD — needs validation** of authors/venue/date against the primary paper). Second, independent:
"Visual or Textual: Effects of Explanation Format and Personal Characteristics on the Perception of
Explanations in an Educational Recommender System", within-subject n=54,
<https://arxiv.org/abs/2603.25624> (checked 2026-09-14) — format interacts with personal
characteristics; no single winner.
→ **Element:** keep the deterministic why-sentence (it is auditable and Blueprint owns the template)
**and** add a small horizontal bar of the same factors, drawn from the same numbers. Same data,
two encodings; the bar is not a second source of truth.

### 3.2 Counterfactual explanations
**Claim:** "if distance were ignored you would be #3" is a recognised, defensible pattern.
**Verdict: TRUE, and it is the pattern the law literature recommends for affected people.**
Wachter, Mittelstadt & Russell, "Counterfactual Explanations Without Opening the Black Box:
Automated Decisions and the GDPR", arXiv 1711.00399 (posted **6 November 2017**); Harvard Journal
of Law & Technology **31(2), 841–887, 2018**. <https://arxiv.org/abs/1711.00399>,
<https://jolt.law.harvard.edu/assets/articlePDFs/v31/Counterfactual-Explanations-without-Opening-the-Black-Box-Sandra-Wachter-et-al.pdf>
(both checked 2026-09-14). Three aims: understand *why*, get **grounds to contest**, and know
**what would need to change**.
→ **Element:** the tenant answer gets one counterfactual line, and it is the contestability hook
the NT framework asks for. Fair Turn can generate it deterministically by re-running `rank` with
one factor zeroed — no model, no new dependency. Word it as fact, not promise
("Your job is 7th today. With travel distance ignored it would be 3rd."), because a counterfactual
that reads like an offer becomes a commitment the agency has not made.

### 3.3 Decide before reveal
**Claim:** showing outcome metrics before the decision anchors the decision, so withholding them
until signature is defensible.
**Verdict: TRUE — supported from two independent directions.**
- **Anchoring:** "adherence to algorithmic recommendations is larger when these are revealed
  initially rather than after eliciting provisional human judgements" — overview of algorithm
  effects on judgmental biases, *International Journal of Forecasting*,
  <https://www.sciencedirect.com/science/article/pii/S0169207024001018> (checked 2026-09-14;
  **TBD — needs validation** of authors and issue). Corroborating, independent: algorithmic
  recommendations measurably shift judges' bail decisions —
  <https://arxiv.org/abs/2012.02845> (Imai et al., pretrial PSA field experiment, checked 2026-09-14).
- **Cognitive forcing:** Buçinca, Malaya & Gajos, "To Trust or to Think: Cognitive Forcing
  Functions Can Reduce Overreliance on AI in AI-assisted Decision-making", *Proc. ACM
  Hum.-Comput. Interact.* 5(CSCW1), **April 2021**, <https://arxiv.org/abs/2102.09692>. Making the
  person commit to their own answer *before* seeing the AI reduced overreliance — but was
  **less liked** and helped high Need-for-Cognition participants most. Independent replication and
  extension: "Cognitive Forcing for Better Decision-Making: Reducing Overreliance on AI Systems
  Through Partial Explanations", PACM HCI, <https://dl.acm.org/doi/10.1145/3710946> (checked
  2026-09-14).
- **Counter-evidence to carry honestly:** explanations alone do not fix overreliance and can make
  it worse ("The effects of explanations on automation bias", *Artificial Intelligence*,
  <https://dl.acm.org/doi/10.1016/j.artint.2023.103952>, checked 2026-09-14).
→ **Element:** keep decide-before-reveal, and **name it on screen** with its cost. A locked
outcome panel captioned with the reason is a stronger judging artefact than a hidden one. Expect
a judge to say "that is annoying" — Buçinca found exactly that; answer with the finding.

### 3.4 Override friction: does a written reason help?
**Claim:** requiring a typed reason improves oversight.
**Verdict: TRUE in the accountability literature, CONTESTED as policy.**
- For: Skitka, Mosier & Burdick — accountability for performance or decision accuracy lowers
  automation bias, through fewer omission and commission errors; summarised with citation in
  "Check the box! How to deal with automation bias in AI-based personnel selection",
  *Frontiers in Psychology*, 2023,
  <https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2023.1118723/full>
  (checked 2026-09-14). Independent: Mosier et al., "Automation Bias, Accountability, and
  Verification Behaviors", HFES Proceedings 40, 1996,
  <https://journals.sagepub.com/doi/10.1177/154193129604000413> (checked 2026-09-14).
- Against, and worth quoting rather than hiding: Ben Green, "The Flaws of Policies Requiring Human
  Oversight of Government Algorithms", arXiv 2109.05067 (checked 2026-09-14; journal of record
  **TBD — needs validation**) — oversight policies fail twice over: "people are unable to perform
  the desired oversight functions", and they "legitimize government uses of faulty and
  controversial algorithms without addressing the fundamental issues".
- Also relevant: **EU AI Act Art. 14(4)(b)** above makes awareness of automation bias a design duty,
  not a training slide.
→ **Element:** keep the mandatory reason, and answer Green directly on screen: the override-rate
strip, a sample of recent reasons, and the audit export. Oversight you can *measure* is the reply
to "oversight is theatre". Keep the friction low — a short free-text box with two or three
suggested reasons, not a form.

---

## 4. Presentation for judges
**Claim:** there is reliable, citable guidance on demoing a decision-support prototype.
**Verdict: WEAK — the available sources are practitioner blogs, not research. Treat as craft, not
evidence.** Consulted 2026-09-14: <https://info.devpost.com/blog/6-tips-for-making-a-hackathon-demo-video>,
<https://gist.github.com/dabit3/caef5eee4753dd7d23767bc31e70da28>. Consistent advice across them:
open with one person in one situation; state what you built in one sentence; then a short live run
down **one rehearsed path** with **seeded, non-empty data**; say what you cut and why.
**TBD — needs validation** against any peer-reviewed source; none found.
For the in-app "explainer", use §2.2's resolution: a dismissible tour control, contextual help
otherwise. NN/g's warning about tours is about repeat users and does not forbid a presenter-driven
one.
→ **Element:** a **Demo** entry in the nav (or a "Take the tour" button) that loads one named
scenario at a known day with the batch unsigned — so the first screen a judge sees is populated,
and the human decision is the thing they watch happen.

---

## Screen-by-screen implications

**Workspace**
- Purpose line at top (HAX G1) plus a dated per-field accuracy chip (G2, NIST MEASURE 2.9).
- KPI row above the map and list; factor detail behind an expander (Nielsen 2006; Laubheimer 2017).
- λ presented as the one global control with its effect visible (HAX G17); score factors as
  horizontal bars, never gauges (Laubheimer 2017).
- The coordinator's own override rate, last N days (EU AI Act Art. 14(4)(b); Green's critique).
- Intake disabled state states its reason and points at the queue as the manual fallback
  (PAIR Feedback + Controls).

**Review queue**
- Frame it as the designed safety path, not a failure bucket: status + cue + pathway in the empty
  state (Kaplan 2021).
- Source phrase shown in place beside each field; an empty field labelled "no source phrase found"
  (HAX G4; the Blueprint rule that an unverified field renders empty).
- Set-by-coordinator control on the row itself, with a short reason box and suggested reasons
  (HAX G9; Skitka/Mosier accountability, kept low-friction).
- One line naming what the model does not do here: it never sets a field, it only proposes one
  (NIST MEASURE 2.9 "including the limitations").

**Visit plan**
- Empty until a signature: status line + the pathway back to the batch (Kaplan 2021).
- Every distance suggestion carries its reason and the batch version, shown not stored
  (HAX G16, consequences of user actions).
- If a later edit invalidates the batch, say so on screen with old and new version (HAX G18).

**Tenant answer**
- Plain-language why-sentence, year-7 reading level, no deficit words (Blueprint `core/wording.py`).
- One counterfactual line, generated deterministically, phrased as fact not promise
  (Wachter et al. 2017/2018).
- A visible "how to question this" line — the NT framework's own word is "challenge"
  (NT AI Assurance Framework, November 2025, Transparency).
- A short provenance/"about this" note: synthetic data, a person decided, the model only read the
  text (PAIR data-source scope; DTA transparency-statement shape).

**Evidence lab**
- This is where G2 lives in full: per-field P/R/F1 with Wilson intervals, sample size, date,
  and the baseline comparison.
- State the limitations next to the numbers, not below the fold (NIST MEASURE 2.9).
- Name decide-before-reveal as a designed control and cite its cost — people dislike it
  (Buçinca et al. 2021) — rather than presenting it as free.
- Carry the audit export and the override-rate history, as the measurable answer to Green's
  "oversight is legitimising theatre".

---

## Copy to put on screen

*Drafts. Year 7 reading level, active voice, no deficit language. Substitute real numbers before
use; `{ }` marks a value the page already has.*

**Workspace — purpose**
> Fair Turn reads today's repair reports and puts them in a suggested order. You decide the order
> that is signed. Nothing here is sent to a crew until you sign it.

**Workspace — accuracy chip**
> Field accuracy measured on {n} reports on {date}. See Evidence lab.

**Workspace — empty (no jobs for the chosen day)**
> No reports for {date} yet. Jobs appear here as they arrive. Pick another day to see a full list.

**Workspace — intake off**
> Report intake is off because {reason}. You can still add a report by hand in the review queue.

**Workspace — outcome panel, locked**
> Wait times and travel cost appear after you sign. We hide them until then so the numbers do not
> steer your ordering.

**Review queue — purpose**
> Some reports do not say enough for the system to fill a field. Those jobs come here so a person
> can fill it in. The system never fills a field on its own.

**Review queue — empty**
> Every job for {date} has the fields it needs. Jobs arrive here when a field has no matching words
> in the report.

**Review queue — field with no source phrase**
> No matching words in the report. Set this field yourself, and say why.

**Visit plan — purpose**
> This is the run sheet for the jobs you signed. The order is yours. Distance suggestions are only
> suggestions, and each one shows its reason.

**Visit plan — empty**
> Nothing to plan yet. Sign today's batch on the workspace and the run sheet appears here.

**Visit plan — invalidated batch**
> This plan was built from batch {old}. A field changed, so the batch is now {new}. Check the order
> again before you send it.

**Tenant answer — purpose**
> Here is where your repair sits today, and what moved it there. A housing officer checked and
> signed this list.

**Tenant answer — counterfactual**
> Your job is {k} of {n} today. If travel distance were left out, it would be {j}.

**Tenant answer — contest line**
> If this looks wrong, you can ask for it to be checked. Call {contact} or ask at your local
> housing office.

**Tenant answer — empty (id not found)**
> We could not find that job number. Check the number on your repair receipt and try again.

**Evidence lab — purpose**
> This page shows how well the system reads reports, measured on {n} reports. It shows what it gets
> wrong as well as what it gets right.

**Evidence lab — empty (no runs)**
> No measured run yet. Results appear here after the build script runs.

**About this AI (expander, every page footer)**
> Fair Turn reads free-text repair reports and suggests an order. It does not approve, refuse or
> schedule a repair. A housing coordinator decides and signs, and every decision is logged with
> who made it and when. Data on this demo is synthetic.
