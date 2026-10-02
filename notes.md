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
summary opens its exact source passage. The human signs off, and the record shows which passages they
opened and for how long. It does not prove they read them; we say so rather than overclaim.

## The scenario (rewritten 2026-10-03 against the real NT policies)
Jordan is a **delegated officer** assessing priority-housing applications in Darwin, NT. The policy
says "Delegated officers make decisions as the Chief Executive Officer (Housing)" (Priority §4).
Priority housing covers only urban applicants (Priority §2–3). The real decision flow is:
1. eligibility (Eligibility policy; urban applicants must also meet the income and asset criteria);
2. one of four urgent-need categories (DFV is one);
3. documentation that supports the claim, with an interview if more information is needed;
4. a written determination.

Jordan's queue has 15 files; v1 demos one of them.
**Open after the pre-Blueprint review:** the scenario below still ends in "accept", which skips the
income criteria. See [review](reports/2026-10-03-pre-blueprint-review.md) #3.
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
   passage, and that every number and date in the claim appears in one of its cited quotes.
   - The archive's `verify_spans.py` (78 lines) covers only the whitespace-normalised substring match;
     the number and date check is new code.
   - Negation counting is dropped. It is brittle: "will not be withheld" vs "not eligible".
4. **Fact-checker: Jev in v1** (Tarık's decision). A different model family from the writer; Claude
   is the fallback.
   - **Second key:** a typed verdict on each claim: supports / contradicts / not enough information.
   - **Contradiction pairs, core v1:** the top 3–5 passages per decisive clause are compared pairwise
     (agree / contradict / unrelated). Without this, "arrears $2,400 [p.8]" passes against its own
     passage.
   - The contract allows 1..n citations per fact.
   - **After v1:** Bespoke-MiniCheck-7B, local on Ollama, as a third vote.
5. **Critical passages come from the policy.** For each decisive clause, the writer lists the file
   facts that bear on it (Fox 2026: list the source facts first). Criticality is set by the policy,
   not guessed by the AI.
   - **Omission map source:** the Jev relevance scan. Passages that score high and are cited nowhere
     become "possibly missed". Facts a summary under audit leaves out are found by comparing it with
     the writer's per-clause facts.
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
  as fair dealing is TBD. Decided (see Decisions): we do not bundle them and do not ask.
- **Download caveat.** The PDFs sit behind a Cloudflare challenge: a plain `curl` got a "Just a
  moment" page on 2026-10-03, so a fetch script in the README may fail.

## v1 scope (draft, Eko, 2026-10-03; input for Blueprint)
**Core v1:**
- **Input:** split the synthetic case file and the 5 NT policies into numbered passages. The decisive
  clause checklist is written once and approved.
- **Claude reads:** a goal, not steps, so it looks for evidence for and against, contradictions and
  what is missing. The output contract is a verbatim quote plus passage id per fact (1..n citations),
  and "not found" is allowed. Claude also writes a short summary for the second tab.
- **Code checks:** the quote is present, and every number and date in the claim appears in a cited
  quote.
- **Jev:**
  - a second key on every claim (supports / contradicts / not enough information);
  - contradiction pairs per decisive clause (moved into core by the review);
  - a relevance scan of every passage against **the approved decisive clauses only**, batched about
    20 passages per call. High-scoring passages that are cited nowhere become "possibly missed",
    deduplicated by fact, with the threshold set on one gold file before the evaluation.
- **Required reading:** quote-not-found, checker-disagrees, contradictions, and possibly-missed items
  above the threshold. Capped at **8 or fewer**, the rest shown as "suggested"; most decisive first.
- **Reproducibility:**
  - The replay cache of every model response is the README default; live runs need your own keys.
  - Each policy PDF is pinned by version and SHA-256, and a mismatch fails loudly.
  - The cache holds offsets and hashes, never policy text.
  - Variance across two Jev runs is reported.
- **Officer screen:**
  - the evidence map with a status word and colour on each claim;
  - a source pane with the highlighted quote;
  - dispute with a reason;
  - the officer sets each clause outcome; "not in file" leads to a request, never to an automatic
    "not met";
  - the plain-summary tab;
  - the sign-off lock;
  - the decision record, exported as HTML or JSON.
- **Measurement:**
  - The summary under audit (K1), run through the checks.
  - Short trap files and a set of mutated summaries, scored per error type.
  - The held-out file written by a separate agent from another model family (K4).
  - Jev vs Claude-as-checker on SummEdits pairs (K3).
  - (K5 timing test dropped; the gate's time cost is stated as untested.)
  - n is printed beside every number.
- **Dataset and technical upgrades (accepted by Tarık, 2026-10-03):**
  - **Grounded synthetic file.** Every document type in the file is one the real Identification and
    Documentation policy asks priority applicants for. The wait-time CSV (CC BY) appears on the case
    header as context, so the "datasets" claim is real.
  - **A released mini-benchmark.**
    - Publish the facts table, gold labels and mutation set as CSV, with a one-page datasheet
      covering: how it was generated, the trap taxonomy, licence, intended use and limits.
    - The synthetic set becomes a contribution rather than a weakness.
  - **Checker evaluation at scale.** Jev is fast and cheap, so run several hundred SummEdits pairs
    rather than 50. Report balanced accuracy and a calibration table, and set the "unsure" band from
    it. "Flags where unsure" then rests on a measured threshold.
  - **Ablation table.** Each layer's output is logged anyway, so the table is almost free to build.
    It shows what each layer adds:
    1. Claude alone;
    2. plus code checks;
    3. plus Jev second key;
    4. plus contradiction pairs;
    5. plus scan.
  - **Position test (if time allows).** Move the decisive passage to the start, middle and end of the
    generated file, and check whether the catch rate drops in the middle ("lost in the middle").
- **Submission:** a README with the official policy links and a manual download step; demo results
  precomputed.

**If time allows, in this order:**
1. The file heat strip.
2. Two-way hover links.

(Jev contradiction pairs moved into core v1 after the pre-Blueprint review.)

**After v1:** the list below.

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
- **Why Jev is not the main model (Eko, 2026-10-03, for Blueprint's rejected options):**
  - It answers typed questions (yes/no, choice, score) and writes no text, so it cannot produce the
    summary or the claims the brief asks for.
  - Its 32K context is smaller than the file plus policies (an estimate: roughly 60–70k tokens as
    plain text; 90k–180k through Claude's PDF input, which counts layout), so it
    judges one passage or pair at a time.
  - It cannot reason across distant pages.
  - Its scores are uncalibrated and unvalidated as a primary decision-maker.
  - Its sweet spot is a fixed-option decision, repeated many times, where speed matters. That is the
    vault's own note from Sept 2026, and it is exactly the checking and scanning half of this app.
  - **Split:** Jev decides *where to look*; Claude says *what it says*.
- **Jev-led alternative (recorded, not chosen):** the AI writes nothing. Jev ranks the original
  passages per clause and the officer reads only those.
  - **For:** nothing generated to over-trust; cheaper and faster.
  - **Against:** the brief asks for a summariser; the officer reads more raw text; Claude's
    cross-page reasoning is lost.
  - **What we take from it:** on the evidence map the verbatim quote comes first and the AI's
    sentence second.

### Pitch material for the teammate
In the survey's §5:
- OVIC 2024: a ChatGPT court report called a sexually misused doll an "age-appropriate toy" even
  though the worker said they checked it.
- ASIC trial: AI summaries scored 47% against 81% for humans.
- NT AI Policy (2026-06-05) and NT AI Assurance Framework wording.

### Hard questions judges will ask (Eko's honest review, 2026-10-03)
- **"Case text goes to Claude and Jev in the cloud. The NT AI Policy forbids that for real data."**
  The demo uses synthetic files. A pilot needs sovereign or local models, and both model slots are
  swappable.
- **"Opened is not read."** True. The receipt is an audit trail, not proof of understanding. Say so;
  do not overclaim.
- **"Does forcing people to read save time or cost it?"** Answer with the team timing test (Riskiest
  assumption). Without it there is no answer.
- **"You planted the traps your system finds."** Answer with the mutation set, a held-out file
  written by a teammate, and an external number for the checker.
- **"What about everything that is not flagged?"** Residual risk. The exhaustive Jev scan reduces it
  but does not remove it.
- **"Isn't the reading receipt staff surveillance?"** Frame it as the officer's protection ("I read
  it") and keep it to the officer and the appeal record.
- **"What if the applicant cannot provide documents?"** This matters for remote and Aboriginal
  applicants. "Not in file" must lead to a request for information, never to an automatic "not met".

### Decisions (Tarık, 2026-10-03)
- **User:** the NT priority-housing officer.
- **Data:** combination A. Five real NT policies (40 pp) plus a synthetic case file built from a facts
  table written first.
- **Models:**
  - **Writer:** Claude.
  - **v1 fact-checker:** Jev (Tarık, 2026-10-03). It is a different model family from the writer.
  - **After v1:** local models (Bespoke-MiniCheck, a local writer).
  - **Jev smoke test (2026-10-03, synthetic):** claim support 3/3 correct at ~0.4 s per call;
    relevance scan put the decisive passage first in 0.6 s for 6 parallel calls.
    [Report](reports/2026-10-03-jev-smoke-test.md).
- **Clause outcome:** the officer sets it (met / not met / not enough information). The AI only marks
  its own claims. The pitch says why: in the oncology RCT, humans followed the AI exactly where it was
  worst (ECOG).
- **Hidden-text injection demo:** dropped. Tarık's view is that new models do not fall for it.
- **Policy PDFs (Tarık left it to Eko):**
  - The PDFs are not bundled in the ZIP. The README lists the five official links with a manual
    download step, because the site blocks scripts.
  - The app shows only the short clause quotes it relies on, with attribution.
  - The organisers are not asked.
- **Pre-Blueprint review fixes, all accepted** (Tarık, 2026-10-03; see the
  [review](reports/2026-10-03-pre-blueprint-review.md)):
  - **K1:** a *summary under audit*. Claude with a one-line "summarise this file" prompt, the way
    officers use Copilot, frozen with its model id and prompt. We show the errors it really makes and
    fake none.
  - **K2:** the correct demo outcome is "cannot decide yet, request income evidence". The reason to
    reject collapses; DFV is documented; income evidence is missing.
  - **K3:** Jev stays the v1 checker, with Claude as fallback. It is measured against Claude-as-checker
    on SummEdits pairs at the start of the build.
  - **K4:** a teammate writes one held-out file before the first pipeline run.
  - **K5:** the timing test is redesigned:
    - two different files in counterbalanced order;
    - baseline = full file plus plain summary;
    - measure correct decision and minutes;
    - one trap left unflagged;
    - n stated.
  - **K6:**
    - one full 60-page demo file plus 10–15-page evaluation files;
    - numbers frozen for the teammate by 7 Oct;
    - dispute is a text field on the record.
  - **K7:** Tarık tells the team about the pivot to brief 6 today and asks whether the registration
    form named a brief.
- **Later the same day (Tarık):** "takım arkadaşlarını dert etme". Nothing in v1 depends on teammates.
  - **K4 changes:** the held-out file is written before the first pipeline run by a separate agent
    from a different model family that never sees the pipeline or its outputs.
  - **K5 dropped:** no team timing test. The time cost of the gate is stated as untested in v1 and
    becomes the first measure of the proposed pilot.
  - **K7 dropped.**
- **Dataset and technical upgrades accepted** (Tarık, 2026-10-03): grounded synthetic file, released
  mini-benchmark, checker evaluation at scale, ablation table. The position test runs if time allows.
- **Design A/B (Tarık's question):**
  - Build the review screen twice:
    - **A** with the `tasarim` skill (Tarik Base);
    - **B** by an agent told not to load the skill or read DESIGN.md.
  - Tarık compares them by eye and picks one.
  - The app keeps all styling in one theme file, so switching is a one-file change.

## Proposal: goal for the writer, contract for the checkers (draft, Eko, 2026-10-03, awaiting Tarık)
- **Claude gets a goal, not steps.** The prompt says only:
  - The officer decides this file against these clauses.
  - Find everything that could change the decision: for and against, contradictions, what is missing,
    and anything important the checklist does not name.
  - Give each fact with a verbatim quote and passage id. "Not found" is a valid answer.

  The output contract is the only fixed constraint.
- **The checkers stay narrow and fixed** (code plus Jev). Trust comes from a checker that is simple,
  fast and predictable. A free agent cannot be checked by itself, and the screen depends on the
  contract.
- **Four Jev jobs:**
  1. **Second key on every claim.** `noul` plus `choice` (supports / contradicts / not enough
     information).
  2. **Exhaustive scan.** A `score` for every passage × every decisive clause. High-scoring passages
     Claude never cited become "possibly missed". One reader can skip something; a scan of every
     paragraph does not.
  3. **Contradiction pairs.** A `choice` on the high-relevance passages of the same clause.
  4. **Reading order.** Required items are sorted by Jev score and disagreement, so the most decisive
     come first.
- **Disagreement rule.** Where Claude and Jev agree, the item can pass quickly. Where they disagree, or
  Jev finds something Claude skipped, the officer must read. The "flags where it's unsure" in the brief
  comes from measured disagreement and Jev probability bands, not from the model's self-report.
  Calibration is measured on the gold set.
- **File heat strip.** Per clause, a strip of the whole file coloured by Jev relevance, with the
  passages already read marked. The officer sees where in 60 pages the evidence sits and which
  relevant parts are still unread.
- **Evidence for and against each clause:** part of Claude's goal, so it costs only prompt text.

## Framing (draft, Eko, 2026-10-03; see the [UI and logic survey](reports/2026-10-03-ui-patterns-and-logic-brief6.md))
- **The main output is an evidence map by policy clause, not a bullet summary.**
  - Tools built for decisions structure their output per criterion, with a quote in each cell:
    Harvey, Elicit, TrialGPT and Microsoft's Legal Agent.
  - Free text with citation chips is the general Q&A pattern: NotebookLM, Acrobat, Perplexity.
  - The bullet summary stays as a secondary tab whose bullets link into the map.
- **Links must sit on the claim.**
  - Traceable Text (N=20): hallucination questions were answered correctly 70% of the time with
    claim-to-source links vs 12.5% without, in 1.8 vs 2.9 min.
  - References appended at the end of an EHR summary gave no gain.
- **Three separate status lists** (fixed after the pre-Blueprint review; they used to collide):
  - **Claim checks** on a claim: quote not found / checker disagrees / contradicted by another
    passage / supported.
  - **Coverage** for a clause: possibly missed / no evidence in file.
  - **Clause outcome, set by the officer only:** met / not met / cannot decide yet (= request
    information). Decided 2026-10-03: the AI does not pre-fill it, because in the oncology RCT humans
    followed the AI where it was badly wrong (ECOG).
- **Mock v0 known issues:**
  - The Priority §3.1 excerpt is not verbatim. The real sentence: "Applicants must prove their urgent
    need for priority housing and are required to provide documentation that supports their claim
    for priority."
  - It says "Read" instead of "Opened".
  - The checker is labelled MiniCheck instead of Jev.
  - It opens all sources at once.
  - Its "why" lines are AI explanations.

## Screens
**Mock v0:** [design/mock-v0.html](design/mock-v0.html), a single file for discussion, not approved.
- **Evidence by policy clause:** claims with status pills, and "must read" tags on flagged items.
- **Source pane:** highlighted quote, with real-policy or synthetic-file labels.
- **Plain AI summary tab:** for contrast.
- **Required-reading counter:** `0/4`.
- **Sign decision:** blocked with a banner until the required passages are opened, then a dialog
  asking for a decision and a reason, then a decision record listing the passages opened and when.

**Gaps against comparable tools (survey item 5):**

| Gap | v1? | Why |
|---|---|---|
| Dispute a claim, with a reason | v1 | Elicit and Harvey ship it, the NT framework asks for "question and challenge", and the receipt records it |
| Explicit "not in file" state | v1 | Already in the mock; TrialGPT uses "not enough information" |
| Contradiction check across passages | v1 | A claim checked only against its own cited passage passes the stale January ledger |
| Exportable decision record | v1 | A printable HTML or JSON receipt; a formatted PDF can wait |
| Colour never the only signal | v1 | WCAG 1.4.1; the pills carry a word and an icon |
| Two-way hover links (claim ↔ passage) | v1 if time allows | Cheap in HTML; this is how Traceable Text measured its gain |

## After v1
- 2026-10-03: Search across many documents (RAG). v1 is one case file plus the five-policy bundle.
- 2026-10-03: OCR for scanned PDFs. Claude cannot cite scans; say in the pitch that real files contain them.
- 2026-10-03: Multi-file upload. v1 ships the demo case; passage ids still carry a document id.
- 2026-10-03: Prompt-injection defence and the hidden-text demo. Tarık dropped the demo because new
  models do not fall for it. If a judge asks, the precedent is a Connecticut court filing in 3-point
  white font (Aug 2026).
- 2026-10-03: Local models: Bespoke-MiniCheck as a third vote, and a local writer. v1 runs on Claude
  plus Jev.
- 2026-10-03: A draft request to the applicant for items marked "not in file", citing the policy
  clause. Cheap, but not needed for v1.
- 2026-10-03: A plain-language decision letter to the applicant built from the decision record.
- 2026-10-03: A backlog queue that orders files by flag count, and a supervisor view of reading
  coverage across officers.
- 2026-10-03: A reason check, where Jev asks whether the officer's reason addresses the flagged
  evidence. It risks feeling paternalistic.
- 2026-10-03: Planted-trap vigilance check on the reviewer (survey G5). The ethics of testing staff
  this way has not been checked.
- 2026-10-03: Chat with the document. It is not what the brief asks for.

## Sources
- [Landscape survey, 2026-10-03](reports/2026-10-03-landscape-verified-summaries.md): products,
  research, checkers, Jev and Laya, AU/NT context, gaps.
- [Data survey, 2026-10-03](reports/2026-10-03-data-survey-brief6.md): NT policies and their licence,
  case material, corpora, ground-truth methods, and combinations A, B and C.
- [Pre-Blueprint review, 2026-10-03](reports/2026-10-03-pre-blueprint-review.md): independent logic
  review (3 blockers, 10 majors), quality assessment, real policy flow, Jev load test.
- [UI and logic survey, 2026-10-03](reports/2026-10-03-ui-patterns-and-logic-brief6.md): what comparable
  tools show, how they work underneath, the shared pipeline and v1 gaps. Citation pass done.
- Reusable: span verification `fair_turn/core/verify_spans.py` on branch `archive/v2-weekly-plan`.
- Workshops: the Workshop 2 recording is in Otter (shared to Tarık's student mail by Dewa Pratama and
  Nikhitha Karne, 2026-10-02). The Workshop 1 transcript held only the first and last minutes.
