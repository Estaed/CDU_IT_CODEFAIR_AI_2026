# Fair Turn — AI Challenge 2026, CDU IT Code Fair

Entry for brief 1, housing maintenance triage. Project name **Fair Turn**; Python package
`fair_turn`. Scope and decisions: `notes.md`; research: `reports/`.

**Theme: "How might we…" — trusted AI for decision support.**
Official page: <https://itcodefair.cdu.edu.au/ai-challenge/>
Task briefs: <https://itcodefair.cdu.edu.au/ai-challenge-task-details/>
Report format: <https://itcodefair.cdu.edu.au/data-innovation-challenge-requirement/>

Transcribed 11 September 2026. Re-check the live pages before any deadline.

---

## What this competition actually is

It is not a "build an AI app" competition. It is a **decision-support and trust**
competition. Every one of the six briefs pairs a real public-sector user with a decision they
have to make, and then adds what the organisers call a **trust twist**: a specific way that a
naive AI system would quietly do harm while looking like it was working.

The organisers state the frame in one line:

> scope it to one decision, one user, synthetic or public data — and remember the AI assists,
> a human decides.

That sentence is the whole rubric in miniature, and it decides how the work should be built:

- **One decision, one user.** A general-purpose assistant scores badly here. Pick a single
  decision made by a single named role and support exactly that.
- **Synthetic or public data.** You are not expected to obtain real government records. You
  are expected to construct or find data that is honest about what it represents.
- **The AI assists, a human decides.** A system that decides autonomously has failed the
  brief regardless of how well it performs. The human sign-off step is a feature, not a
  disclaimer.

## Pick exactly one of six briefs

Full text, with the user, the build and the trust twist for each, is in
[`docs/task-briefs.md`](docs/task-briefs.md). In short:

1. **Housing maintenance triage** — rank repair jobs across remote NT communities from
   free-text fault reports. Trust twist: "efficiency" always favours the town over remote
   communities; make the equity trade-off visible and let a human own it.
2. **Grant eligibility assessment** — map applications to published eligibility rules and
   draft challengeable reasons for a decision. Trust twist: consistency is good,
   rubber-stamping is not; do not penalise plainer or second-language English.
3. **Information-access (FOI) request triage** — retrieve relevant records and flag likely
   sensitive content for human redaction. Trust twist: nothing is released or redacted
   automatically; reason explicitly about the asymmetric cost of a missed exemption versus
   over-flagging.
4. **Risk-based inspection prioritisation** — rank premises for a regulator with too few
   inspectors, showing the factors behind each score. Trust twist: the feedback loop — a
   model trained on where you already inspected will "prove itself right" forever.
5. **Urgent message routing** — classify and escalate a vulnerable person's urgent message in
   a high-volume government inbox. Trust twist: the escalation path *is* the design goal;
   anything serious reaches a human immediately and the system never answers it itself.
6. **Long document analysis** — summarise policy or case documents for a caseworker with
   every claim linked back to its exact source passage, flagging uncertainty. Trust twist:
   speed breeds complacency; make verification easy and keep the human accountable.

## Eligibility

Teams of **2–4** enrolled CDU IT coursework students (undergraduate, postgraduate, TAFE and
short courses). Higher Degree by Research students are not eligible.

## What must be handed in

1. **Project report** — PDF, following the format specification in
   [`docs/report-requirements.md`](docs/report-requirements.md). Maximum 8 pages excluding
   title page, references and appendices. Roughly 2,500 words as a guideline. A4, Calibri or
   Arial, continuous page numbering, team number and page number in the header and footer.
2. **Source code** — Python, with remarks on the key steps, plus a README file containing
   reproduction instructions.

Both go in a **zip file, emailed to itcodefair@cdu.edu.au**. The subject line format the
organisers give is:

```
AI Challenge Submission – [Group] – IT Code Fair 2026
```

Group details must be stated properly in the email and every necessary file must be in the
zip. Note the organisers' wording: "send your **progress**" — this is a work-in-progress
submission, and the Challenge Day pitch is where the finished thing is shown.

## The submission date on the official page contradicts itself

The AI Challenge page states two different deadlines:

| Where on the page | Date given |
|---|---|
| "Competition process", step 2, Submission | 30 September 2026 |
| "Important Dates", Final Submission Deadline | 8 October 2026 |

The 30 September date is almost certainly copy-pasted from the Data Innovation Challenge
page, whose submission section is otherwise word-for-word identical. **Treat 30 September as
the working deadline and email itcodefair@cdu.edu.au to confirm.** Being early costs nothing;
being wrong about this costs the entry.

The same copy-paste is visible in the report requirements: the AI Challenge "Requirement
Link" points at the *Data Innovation Challenge Requirement* page, and the file naming rule on
that page reads `DataChallenge_Team xx(number)_Report.pdf`. Ask the organisers whether the AI
Challenge wants its own prefix, and until they answer, follow the published rule literally.

## A second live AI Challenge page contradicts this one (found 12 September 2026)

<https://itcodefair.cdu.edu.au/ai-challenge-2/> is live alongside `/ai-challenge/` and
gives different facts. Fetched and compared 12 September 2026:

| Item | `/ai-challenge/` (transcribed above) | `/ai-challenge-2/` |
|---|---|---|
| Registration closing | Tue 15 Sep 2026 | Fri 12 Sep 2026 |
| Final submission | Thu 8 Oct 2026 (30 Sep in process section) | Wed 30 Sep 2026 |
| Challenge Day | Thu 15 Oct 2026 | Wed 7 Oct 2026 |
| Judges | Cat Kutay (CDU), Rushi Vyas (OpenAI), 2 TBD | Bruno Braga, Sarah Strzelecki, Mohammad Aurangzeb Khan, Sandeep Rasali (all NT Govt DCDD) |
| Resources | none | connectivity datasets (ADII, NBN, ACCC, ACMA, ABS TableBuilder, First Nations Connectivity Mapping Tool) |

The `/ai-challenge-2/` resources list is connectivity-oriented and its judges match the
Data Innovation Challenge page, so it may be a stale copy. Not resolved. Registration is
done. **30 September is the only submission date safe under both pages; build for it.**
Ask the organisers which Challenge Day and which panel is real. Write the report so it
works for either panel: NT Government digital-services staff ("could we pilot this?") as
well as academic and industry AI judges.

## Challenge Day

**Thursday 15 October 2026, 09:00–17:00**, Festival Learning Space 1.12, Danala | ECP,
Darwin, Charles Darwin University. Ten-minute pitch plus five-minute Q&A per team, face to
face, in front of industry judges.

Two workshops run before it: **Week 3 of September 2026** and **Week 1 of October 2026**.
Attend them. The organisers use workshops to clarify exactly the kind of ambiguity flagged
above.

## How it is judged

Six criteria, no published weightings: **datasets**, **overall creativity and originality**,
**technical sophistication**, **contextual relevance and practicality**, **ethical
considerations**, **presentation**. A first winner and a runner-up are selected, announced
5 November 2026.

Judging panel: **Cat Kutay** (Charles Darwin University), **Rushi Vyas** (OpenAI), and two
judges to be confirmed.

Read the criteria against the trust twists. "Ethical considerations" is not a section added
at the end of the report. It is the axis the whole challenge is built on, and the twist in
the chosen brief is the specific thing the judges will probe in Q&A.

## Working notes for whoever builds this

- **The trust twist is the deliverable.** Any of the six tasks can be made to "work" with a
  model call and a ranking. What separates entries is whether the failure mode named in the
  twist was designed against, measured, and shown.
- **Explainability is required output, not a nice-to-have.** Four of the six briefs ask
  explicitly for reasons, factors, citations or source passages to be surfaced to the user.
- **Synthetic data is sanctioned, so generate it deliberately.** Build the dataset so it
  *contains* the failure mode you claim to defend against. A remote-versus-town skew that is
  not in the data cannot be shown to be handled.
- **Registration closes 15 September 2026** and the form is the shared PowerApps link in the
  workspace root README.

## Scaffolding in this folder

This folder is a Project Ignition clone. `CLAUDE.md` and its Codex twin `AGENTS.md` carry the
workflow: dump raw thinking into `notes.md`, then `create-prd`, then `create-architecture` to
write Blueprint, then `generate-tasks`, then `verify-task` per task. `.codex/hooks.json` has been
generated for this path. Blueprint of `CLAUDE.md` is still the placeholder and must be written
before any task is generated.
