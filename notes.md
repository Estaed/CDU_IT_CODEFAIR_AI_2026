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

## The scenario (rewritten 2026-10-03 against the real NT policies)
Jordan is a priority-housing officer in Darwin, NT. Priority housing exists only in urban areas,
not in remote communities or town camps (Priority policy §3). Jordan's queue holds 15 applicant files.
- **Policy, real:** five NT public-housing policies, 40 pages in total. Clauses below are real; the
  wording was checked in the PDF on 2026-10-03.
- **Case file, synthetic:** about 60 pages; people, pages and amounts are invented.

**Plain AI.** The summary says "$2,400 rent arrears, so not eligible". Jordan rejects the
application, but three things are wrong:
1. **Policy misread.** Eligibility §3.4 says: "The provision of social housing will not be withheld
   based on a debt owed to the CEO (Housing)."
2. **Stale value.** The January ledger (p.8) shows the arrears, but the March ledger (p.23) shows
   them cleared.
3. **Omission.** A support-agency letter (p.51) documents family violence. That is a real priority
   ground, and Priority §3.1 requires exactly this kind of documentation of urgent need. The summary
   never mentions it.

**Our app.** For each decisive policy clause, the app shows what the file says about it, with
passages and colours:
- **§3.4 Debt:** red. The claim "not eligible due to arrears" is not supported by the clause. Amber
  as well: p.8 and p.23 disagree.
- **Priority §3.1 Urgent need documented:** p.51, flagged *not used in the summary*.
- **Eligibility §3.5 Tenancy ended for breach in the last 2 years:** green. The prior-tenancy
  record (p.30) says it ended by agreement.

Sign-off stays locked until Jordan opens the red and amber items and the unused critical passage.
The receipt records what was read.

**The moment judges should remember:** the real §3.4 of their own policy opens on screen, and the
decision flips from reject to accept.

**More files for the evaluation set.** Each file turns on a different decisive fact:
- arrears (§3.4);
- the 2-year exclusion (§3.5);
- missing documentation (Priority §3.1);
- an extreme situation where discretion applies (Priority §3.1).

## System (draft, Eko, 2026-10-03)
Analogy: a newsroom. A reporter writes, a separate fact-checker checks, and the editor signs.
1. **Split.** The documents are cut into numbered passages (page, paragraph, policy §) in plain
   Python.
2. **Writer.** A large LLM summarises. Every sentence must carry a passage id and a verbatim quote.
   - **Recommendation: Claude (cloud).** Long context and quality matter here. Only public policy
     and synthetic files go in, so this is consistent with the NT AI Policy.
   - **For a real pilot:** the writer is any approved model, for example NT-endorsed Copilot or a
     local one. Our value is the checking layer.
3. **Code checks.** Deterministic code verifies that each quote exists word for word in the cited
   passage, and that the numbers, dates and negations in the sentence match the quote. This reuses
   the archive's `verify_spans.py`.
4. **Fact-checker (a Jev-style role).** A small model gives a typed verdict on each claim: "Does
   this passage support this claim? yes/no + score".
   - It must come from a different model family from the writer.
   - **Recommendation: Bespoke-MiniCheck-7B, local on Ollama.** It fits the 8 GB GPU.
   - Jev competes in the 1-hour, 50-pair test.
5. **Critical passages come from the policy.** For each decisive clause, the writer lists the file
   facts that bear on it (Fox 2026: list the source facts first). Facts the summary did not use
   become the omission map. Criticality is set by the policy, not guessed by the AI.
6. **Screen, gate and receipt.** Summary and passages side by side. Sign-off is locked until the
   flagged and unused-critical passages are opened. A log records what was opened and when, the
   decision and the reason.
7. **Evaluation.** Gold facts are written before any model runs. A mutation set of broken summaries
   covers number and date swaps, negation, stale values, omissions and policy misreadings. Scores
   are reported per error type.

## Data (2026-10-03, see the [data survey](reports/2026-10-03-data-survey-brief6.md))
- **Combination A is suggested.**
  - Real: the NT policy bundle (Priority 7 pp, Eligibility 8, Identification and documentation 9,
    DFV 11, Discretionary decision making 5).
  - Synthetic: a 60-page case file built from a facts table written first.
  - Real, CC BY: the NT wait-time CSV (data.nt.gov.au, latest Dec 2020; say that it is old).
- **B** adds a fact pattern taken from public NT cases (the Ombudsman 2024/25 report; *CEO (Housing)
  v Young* [2022] NTCA 1, cited, not ingested).
- **C** is the Commonwealth Social Security Guide (CC BY). It has the cleanest licence but loses the
  NT story.
- **Why the case file must be synthetic:**
  - Real case files cannot be obtained, and the NT AI Policy forbids personal data in third-party AI.
  - NTCAT and ART decisions are only on AustLII, whose usage policy forbids feeding its material to
    AI systems.
  - A fully synthetic set (rules and file both invented) is the weaker option under the "datasets"
    criterion.
- **Licence caveat.** NT policy PDFs are under NTG copyright, not CC BY. Whether bundling them counts
  as fair dealing is TBD; ask the organisers or DHLGCD.
- **Download caveat.** The PDFs sit behind a Cloudflare challenge: a plain `curl` got a "Just a
  moment" page on 2026-10-03, so a fetch script in the README may fail.

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

### Pitch material for the teammate
In the survey's §5:
- OVIC 2024: a ChatGPT court report called a sexually misused doll an "age-appropriate toy" even
  though the worker said they checked it.
- ASIC trial: AI summaries scored 47% against 81% for humans.
- NT AI Policy (2026-06-05) and NT AI Assurance Framework wording.

### Open questions (Tarık's to answer)
- Is the NT priority-housing officer the user? The real NT policies now back this scenario.
- Which data combination: A, B or C? Eko suggests A.
- Writer in the cloud (Claude) or local? Eko suggests Claude, because only public and synthetic text
  goes in.
- Should we ask the organisers whether bundling the NT policy PDFs counts as fair dealing, or ship
  links instead?

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
- [Data survey, 2026-10-03](reports/2026-10-03-data-survey-brief6.md): NT policies and their licence,
  case material, corpora, ground-truth methods, and combinations A, B and C.
- Reusable: span verification `fair_turn/core/verify_spans.py` on branch `archive/v2-weekly-plan`.
- Workshops: the Workshop 2 recording is in Otter (shared to Tarık's student mail by Dewa Pratama and
  Nikhitha Karne, 2026-10-02). The Workshop 1 transcript held only the first and last minutes.
