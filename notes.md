# Notes

The first file of the project and the one place for ideas. Nothing here is binding; what holds
becomes Blueprint. Dump freely, then sort: v1 is the simplest complete version, and everything it
doesn't need moves to *After v1*. Eko points out when the v1 list grows past that.

Lines marked *(draft, Eko)* are notes taken for Tarık; his own words replace them.

## Brief
**Brief 6, chosen by Tarık on 2026-10-03:** "Making sense of long documents without over-trusting the AI".
- **HMW:** help a caseworker get through a backlog of long policy or case documents faster, without
  nudging them into trusting a summary they haven't verified.
- **User:** a caseworker who must read and interpret large volumes of policy or case material.
- **Build:** a summariser that links every claim back to the exact source passage, and flags where it's unsure.
- **Trust twist:** speed can breed complacency. Verification must be easy and the human stays accountable.

Source: <https://itcodefair.cdu.edu.au/ai-challenge-task-details/>, read 2026-10-03.

**Competition facts (site and organiser mail, read 2026-10-03):**
- **Submission, 8 Oct 2026:** a ZIP emailed to itcodefair@cdu.edu.au with subject
  "AI Challenge Submission – [Group] – IT Code Fair 2026". It holds the report, Python source with
  remarks and a README with reproduction steps.
- **Challenge Day, 15 Oct:** 10-minute pitch plus 5-minute Q&A, face to face.
- **Judges:** Sarah Strzelecki and Brett Riley (NTG, DCDD), Dr Cat Kutay (CDU), Rushi Vyas (OpenAI).
- **Criteria (unweighted):** datasets, creativity, technical sophistication, context and practicality,
  ethics, presentation.
- **Ownership:** Tarık owns the app. The report and slides are a teammate's.

## Goal
*(draft, Eko)* A caseworker gets through long policy and case documents faster, and the app makes them
read the passages that matter before they act. **The AI points, the human reads.** Every claim in the
summary opens its exact source passage. The human signs off, and the record shows what they actually read.

## The scenario (walkthrough, 2026-10-03)
Jordan is a housing caseworker in Darwin. Fifteen priority-housing files, each about 60 pages, wait
next to a 40-page policy. Names, pages and clause numbers below are invented.

**Plain AI.** The summary says "$2,400 rent arrears, does not meet priority criteria" and Jordan
rejects. Two things were wrong:
- The arrears were cleared in March (p.23). The AI read an old January ledger.
- A support letter (p.51) says the family is fleeing violence. Policy clause 4.3 then waives arrears,
  and the summary never mentioned it.

When the family appeals, Jordan can only say "the AI said so".

**Our app.** Summary on the left, document on the right. Each claim carries a source tag that
highlights the passage. Claims are shown in three states:
- green when supported;
- amber for a contradiction (Jan $2,400 at p.8 against "cleared" at p.23) or an exception that may
  apply (clause 4.3, p.51);
- grey "not found in the file" when the file is silent, with no guessing.

Jordan opens the two amber items and the decision flips. Sign-off stays locked until the flagged
passages are opened, and the record shows what was read.

**The moment judges should remember:** an amber flag opens p.23, and the decision flips from reject to accept.

## Riskiest assumption
*(draft, Eko)* The reading gate saves more time than it costs. In a UK social-work pilot the time
spent checking cancelled the time AI saved (Ada Lovelace Institute, 2026-02-11).

**Cheapest test:** each teammate reads the same file twice, once with a plain summary and once with
our app. Record minutes taken and how many planted traps they catch.

## Acceptance
- <what a command can check>
- (eye) <what Tarık looks at, and what "good" means>

## Ideas

### What makes it ours
These are gaps no surveyed product covers ([survey](reports/2026-10-03-landscape-verified-summaries.md) §6).
1. **Reading gate (G1).** Flagged and critical passages must be opened before sign-off. Elsewhere
   checking is always optional. Force it only where it matters, because forcing everything annoys
   users (Buçinca 2021).
2. **Cited ≠ supported (G2).** A second, independent model checks each claim against its passage. A
   valid link does not mean the passage supports the claim: legal RAG tools still hallucinate 17–33%
   of the time.
3. **Omission map (G3).** Show critical passages the summary did not use. Citation links can never
   reveal what was left out, and AI checkers miss omissions (Fox 2026).
4. **Reading receipt (G4).** Record which passages the human actually opened before deciding, for
   appeal and review. This matches the NT AI Assurance Framework's "clear lines of accountability",
   Robodebt recommendation 17.1, and OVIC 2024, where no one could establish what had been checked.

### Design rules from the research
- Show quotes, not paraphrase. Verifying paraphrase takes up to 3× longer (Worledge 2024).
- Show the passage, not an AI explanation of why it supports the claim. Explanations reduce
  evidence checking (Warren 2026).
- Phrase uncertainty in the first person ("I'm not sure, but…", Kim 2024) and colour each claim
  (Spatharioti 2025).
- No generic warning banners. They have the weakest effect (Blanchard 2026).
- Be careful with decide-before-reveal. It also lowers agreement when the AI is right (Fogliato 2022).

### Jev (Tarık's idea, 2026-10-03)
- **What it is:** TypeSafe's typed-decision API (yes/no, choice, 0–100 score). Tarık used it for
  TarikOS recall reranking in Sept 2026.
- **Where it could fit:**
  - the independent check "does this passage support this claim?" (`noul`);
  - a criticality score per passage for the omission map.
- **Against:**
  - early access through a waitlist (whether Tarık's September key still works is TBD);
  - case text leaves the machine, which the NT AI Policy forbids for real case data;
  - never benchmarked on claim support, and its own evaluations were graded against GPT/Claude answers.
- **Local alternatives:**
  - MiniCheck-Flan-T5-L (Apache-2.0);
  - Bespoke-MiniCheck-7B via Ollama (4.7 GB, fits the 8 GB GPU, #1 on LLM-AggreFact);
  - Laya (local, but its English `noul` can follow the option labels).
- **Settle it with a 1-hour spike:** about 50 labelled passage–claim pairs scored by MiniCheck,
  Bespoke-MiniCheck, Laya and Jev, comparing balanced accuracy. The winner goes in Stack.

### Data
- **Policy:** a real, public NT Government document (which one is TBD).
- **Case files:** synthetic, with no real person's data, and traps planted on purpose:
  - an outdated figure;
  - a hidden exception;
  - two passages that contradict;
  - an OVIC-style distortion.

### Pitch material for the teammate
In the survey's §5:
- OVIC 2024: a ChatGPT court report called a sexually misused doll an "age-appropriate toy" even
  though the worker said they checked it.
- ASIC trial: AI summaries scored 47% against 81% for humans.
- NT AI Policy (2026-06-05) and NT AI Assurance Framework wording.

### Open questions (Tarık's to answer)
- Which caseworker and which documents? The scenario uses housing.
- Should v1 cover both a policy and a case file, or only one?
- Should the summariser run in the cloud (Claude Citations) or locally?

## Screens
<only for a product with screens; Eko fills it by asking, before any mockup: who uses it and
where (phone in the field, desk); the v1 main flow step by step; the v1 screen list, one job per
screen; real data examples (field names, typical numbers, long names); each screen's empty, error
and loading state>

## After v1
- 2026-10-03: Search across many documents (RAG). v1 is one case file plus one policy.
- 2026-10-03: Planted-trap vigilance check on the reviewer (survey G5). The ethics of testing staff
  this way has not been checked.
- 2026-10-03: Chat with the document. It is not what the brief asks for.

## Sources
- [Landscape survey, 2026-10-03](reports/2026-10-03-landscape-verified-summaries.md): products,
  research, checkers, Jev and Laya, AU/NT context, gaps.
- Reusable: span verification `fair_turn/core/verify_spans.py` on branch `archive/v2-weekly-plan`.
- Workshops: the Workshop 2 recording is in Otter (shared to Tarık's student mail by Dewa Pratama and
  Nikhitha Karne, 2026-10-02). The Workshop 1 transcript held only the first and last minutes.
