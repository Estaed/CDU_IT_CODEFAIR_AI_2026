# AI assurance policy and plain-language rules — NT, Commonwealth, Style Manual

Checked: **12 September 2026**, against primary sources. The NT and DTA sites return HTTP 403
to the automated fetch tool but serve normally to a browser user-agent; every NT and
Commonwealth quotation below was taken from the live page HTML on the check date, not from a
secondary summary. Where a document is not published in full, that is said rather than filled in.

---

## 1. NT Government AI Policy and AI Assurance Framework (DCDD)

### Claim: the NT has two distinct published documents, and the 2024-vs-2025 date conflict resolves.
**Verdict: TRUE, and the conflict resolves to November 2025.** The live DCDD page states, verbatim:
"The Northern Territory (NT) Government Artificial Intelligence (AI) Assurance Framework
(November 2025) outlines guidelines for the responsible use of AI in government". The companion
document is the **Artificial Intelligence Policy** ("The Artificial Intelligence (AI) policy for
public sector officers in the Northern Territory (NT) Government"), undated on its page.
Sources (both retrieved 2026-09-12; page-generated stamps 11–12 Sep 2026):
<https://dcdd.nt.gov.au/publications/artificial-intelligence-assurance-framework> and
<https://digitalterritory.nt.gov.au/digital-government/strategies-and-guidance/policies-standards-and-guidance/artificial-intelligence-assurance-framework>
(identical text, two hosts — two independent confirmations of the November 2025 date);
<https://dcdd.nt.gov.au/publications/artificial-intelligence-policy>.
The regulations.ai date of 26 June 2024 (cited in the prior-art report) is **not** supported by
either primary page. Do not cite 2024.
**What it changes:** cite as "NT Government AI Assurance Framework (November 2025)". The prior
report's contradiction is closed.

### Claim: the framework publishes named ethics principles we can map features to.
**Verdict: TRUE — six, quoted verbatim from the page.**
- **Community benefit** — "AI must serve the public interest by delivering demonstrable, positive outcomes for the community."
- **Safety** — "AI must be used safely and responsibly and should reliably operate as intended."
- **Fairness** — "Use of AI systems must be proactively and continuously managed to identify, mitigate and include safeguards against bias, preventing the risk of data bias, or creating or perpetuating unjust outcomes."
- **Privacy and security** — "AI systems must incorporate the highest levels of security and assurance to safeguard all forms of sensitive information..."
- **Transparency** — "Decisions and outputs from AI systems must be understandable and explainable to those they affect, **in proportion to the level of risk**. Clear mechanisms must be available for individuals to **question and challenge** AI-assisted outcomes."
- **Accountability** — "Public sector organisations and public sector staff retain ultimate responsibility for decisions using AI. This requires **meaningful human oversight** and clear lines of accountability for the outcomes of AI systems."
**What it changes:** these six are the ethics section's spine. Note NT folds contestability *into*
Transparency — do not quote the Commonwealth's separate contestability principle as if it were NT's.

### Claim: the framework defines risk tiers and named assessment instruments.
**Verdict: PARTLY — tiers named, instruments named, contents not published.** Primary text:
"a **quick risk assessment** determines the initial risk level of AI projects. **Low-risk** projects
can proceed with agency-level oversight, while **medium and high-risk** projects require additional
assurance steps supported by a specialised AI advisory service within NT Government"; "The agency
chief executive is accountable for all ICT projects, including AI"; and it "applies stronger controls
for medium and high-risk activities, while simplifying measures for low-risk activities". A
**self-assurance assessment** is named. The actual assessment questions, the tier thresholds and the
mandatory control list are **not on the public page and no PDF is linked** (checked 2026-09-12;
zero `.pdf`/`.docx` hrefs on either host). **TBD — needs validation** by request to DCDD if we
want to cite a specific question number.
**What it changes:** we can say our tool "would be assessed under the AI Assurance Framework and is
designed to sit in the low-to-medium band — it recommends, a human decides" and cite the tier
sentence. We cannot claim to have completed a named NT assessment. Say so in the report.

### Claim: the NT AI Policy adds binding conditions on tools like ours.
**Verdict: TRUE.** Verbatim: "**AI systems that have a tangible impact on government services,
operations or the public must be assessed against the AI Assurance Framework**"; "public sector
officers must not enter or upload personal or sensitive information into public or third-party AI
tools"; "public sector officers must validate AI-generated content for accuracy, bias, relevance
and appropriateness before use". "Sensitive information" under the *Information Act 2002* (NT)
expressly includes **racial or ethnic origin** and **health information**.
**What it changes:** two direct design consequences. (a) Our free-text fault reports would, in a real
deployment, carry health and possibly ethnicity signals — NT's own definition makes them sensitive,
so the pipeline must be an in-boundary model, not a public chatbot; our synthetic-data choice is the
demo-safe form of exactly that rule. (b) The extraction-confidence queue *is* the "validate
AI-generated content before use" control, implemented rather than promised.

---

## 2. Commonwealth

### Claim: the DTA policy is current at v1.1 (Sept 2024) as our prior report says.
**Verdict: FALSE — superseded.** "Policy for the responsible use of AI in government —
**Version 2.0**", effective **15 December 2025** (v1.1 took effect 1 September 2024). PDF: *Policy
for the responsible use of AI in Government 2.0.pdf*, 630 KB, page last updated 1 Dec 2025.
Mandatory requirement headings, verbatim: accountable official(s); transparency statements;
developing a strategic approach to AI adoption; operationalising the responsible use of AI; **AI use
case accountability**; internal use case registers; staff training on AI; **AI use case impact
assessment**. Source: <https://www.digital.gov.au/ai/ai-in-government-policy> (retrieved 2026-09-12);
corroborated by the section page
<https://www.digital.gov.au/ai/ai-in-government-policy/ai-use-case-impact-assessment>.
**What it changes:** update the prior-art report's reference 7. Citing v1.1 in front of DCDD judges
would date us by a year.

### Claim: there is a named, structured impact-assessment instrument with sections we can map to.
**Verdict: TRUE.** The **Australian Government AI impact assessment tool** has numbered sections:
1 Basic information · 2 Purpose and expected benefits · 3 Inherent risk assessment · 4 Threshold
assessment outcome · **5 Fairness** · **6 Reliability and safety** · 7 Privacy protection and
security · **8 Transparency and explainability** · **9 Contestability** · 10 Human-centred values ·
**11 Accountability** · 12 Use case review and next steps. Policy text: in-scope use cases "must"
complete it, "must" enter a register with risk rating and accountable use case owner, and once
deployed "must regularly monitor and evaluate their use case to ensure it is operating as intended".
High-risk cases must be reported to the accountable official and reviewed "every 12 months at a
minimum". Sources: guidance pages under
<https://www.digital.gov.au/ai/impact-assessment-tool/guidance/> (contestability, transparency-and-
explainability, fairness, reliability-safety, human-centred-values, accountability), all retrieved
2026-09-12.
Two clauses are worth quoting in the report because they describe *our* domain:
- **9.1** — a "significant effect" includes an effect on "critical government services or support,
  such as **housing**, insurance, education enrolment...". Housing is named. Notification "should
  state that the action was materially influenced by an AI system and include information on
  available review rights", and "should be clear, up-to-date, concise and understandable, and should
  not be complex, lengthy, legalistic or vague."
- **9.2** — people "should be provided with a timely opportunity to challenge an administrative
  action"; "Ensure a person within your agency is able to answer questions in a court or tribunal".
- **11.1** — mechanisms must define how "ultimate responsibility for the decision is retained, even
  when AI is used to analyse data or generate recommended outcomes", including whether the
  decision-maker "will have the ability to override or disregard decisions made by AI" and "What
  records will be kept of the decision-maker's reasoning at any decision point."
- **6.2 Indigenous data** — APS agencies must implement the *Framework for Governance of Indigenous
  Data*, which is informed by **CARE**. This is the Commonwealth hook for the CARE argument already
  in our prior-art report.

### Claim: the national framework (June 2024) is still the umbrella and has a named structure.
**Verdict: TRUE.** *National framework for the assurance of artificial intelligence in government*,
**Version 1.0, published 21 June 2024**, CC BY 4.0, 34 pp, agreed at the Data and Digital Ministers
Meeting **held in Darwin**. Primary PDF retrieved and read 2026-09-12:
<https://www.finance.gov.au/sites/default/files/2024-06/National-framework-for-the-assurance-of-AI-in-government.pdf>.
**Five cornerstones of assurance:** Governance · Data governance · A risk-based approach · Standards
· Procurement. Then Australia's 8 AI Ethics Principles, each broken into numbered practices —
including **5.4 Monitor and evaluate**, **6.1 Disclose the use of AI**, **6.3 Provide clear
explanations**, **7.2 Communicate rights and protections clearly**, **8.4 Avoid overreliance**.
**What it changes:** this is the document that lets us say the NT framework and the DTA policy are
two implementations of one national agreement — and the agreement was signed in Darwin. Cheap,
accurate, and it lands with a DCDD panel.

---

## Feature-to-requirement map

| Our feature | Named requirement | Document (date) | Clause |
|---|---|---|---|
| Coordinator sign-off with reason, logged | Accountability — "meaningful human oversight and clear lines of accountability" | NT AI Assurance Framework (Nov 2025) | Ethics principle: Accountability |
| Coordinator sign-off log (record of reasoning) | "What records will be kept of the decision-maker's reasoning at any decision point"; ability to "override or disregard" AI output | AI impact assessment tool guidance (v2.0 era) | 11.1 Accountability |
| Coordinator sign-off; LLM excluded from ranking | "Avoid overreliance" — governments "remain responsible for all outputs" | National framework (21 Jun 2024) | 8.4 |
| Factor breakdown + "why it sits here" | Transparency — "understandable and explainable to those they affect, in proportion to the level of risk" | NT AAF (Nov 2025) | Ethics principle: Transparency |
| Factor breakdown | "Provide clear explanations ... inputs and variables and how these have influenced the reliability of the system ... the implementation of human oversight" | National framework (21 Jun 2024) | 6.3 |
| Tenant counterfactual view | "Clear mechanisms must be available for individuals to question and challenge AI-assisted outcomes" | NT AAF (Nov 2025) | Transparency |
| Tenant counterfactual view | Notification of AI affecting rights; "significant effect" expressly includes **housing**; notice must not be "complex, lengthy, legalistic or vague" | AI impact assessment tool guidance | 9.1 Contestability |
| Tenant view + a named review path (we do not build the review path — see below) | "timely opportunity to challenge an administrative action" | AI impact assessment tool guidance | 9.2 Contestability |
| Tenant view | "Communicate rights and protections clearly ... create an avenue to voice concerns" | National framework | 7.2 |
| Two rankings + equity slider | Fairness — "safeguards against bias ... or creating or perpetuating unjust outcomes" | NT AAF (Nov 2025) | Ethics principle: Fairness |
| Extraction confidence queue | "public sector officers must validate AI-generated content for accuracy, bias, relevance and appropriateness before use" | NT AI Policy (undated page, retrieved 2026-09-12) | Conditions for assistive AI tools |
| Extraction confidence queue + eval table | "Test and verify the performance of AI systems" | National framework | 5.3 |
| Feedback-loop (90-day) simulation | "regularly monitor and evaluate their use case to ensure it is operating as intended" | DTA policy v2.0 (eff. 15 Dec 2025) | AI use case impact assessment — in-scope, deploy |
| Feedback-loop simulation | "Monitor and evaluate ... including feedback from those impacted by AI-influenced outcomes" | National framework | 5.4 |
| Synthetic data, fictional settlement names, documented skew | Indigenous data → *Framework for Governance of Indigenous Data* / CARE | AI impact assessment tool guidance | 6.2 Reliability and safety |
| Data provenance / documented generation | "Data governance" cornerstone; data provenance and lineage | National framework; tool guidance 6.1 | Cornerstone 2 |
| Whole-of-project assurance claim | "AI systems that have a tangible impact on government services, operations or the public **must** be assessed against the AI Assurance Framework" | NT AI Policy | Acceptable use of AI |

**Not claimable:** we do not build a merits-review or internal-review pathway (9.2), we have not
completed an NT self-assurance assessment (contents unpublished), and we publish no AI transparency
statement (a Commonwealth entity obligation, not ours). List these as out of scope in the report
rather than letting a judge find them.

---

## Wording rules for tenant text

All from the Australian Government Style Manual (retrieved 2026-09-12) unless noted.

1. **Reading level: year 7** (12–14 years old). WCAG 3.1.5 Reading level, level AAA, cited on both
   the *Sentences* and *Plain language and word choice* pages.
2. **Sentences: average 15 words, never more than 25**, "especially for digital content"
   (*Sentences*). Break longer ones with lists.
3. **Active voice, personal pronouns.** "We will assess your application within 30 days", not
   "Applications are assessed within 30 days". So: "We put your job 14th today", not "The job was
   ranked 14th."
4. **Everyday words; no jargon or idiom.** The manual's substitution table forbids *utilise*,
   *in order to*, *prior to*, *pursuant to*, *require*, *commence*, *provide assistance with*,
   *implement*, *impact on*. Ban list for us: *prioritisation*, *triage score*, *weighting
   coefficient*, *equity term*, *counterfactual*. Say "what would change your place in the line".
5. **Expand every acronym on first use**; avoid double negatives.
6. **Aboriginal and Torres Strait Islander peoples** (*Inclusive language* → that page): use
   **plurals** for collectives (peoples, nations, communities); **present tense**; "empowering,
   **strengths-based language**"; **specific names before broad terms**. Explicitly listed as
   discriminatory or offensive: "ATSI", "Aborigines", "Islanders", blood quantums, possessives such
   as "our Aboriginal peoples", and — the one that governs our design — **"'us versus them' or
   deficit language"**. Also: don't italicise words from First Nations languages; never call a
   language "extinct" (use "sleeping").
7. **Therefore the "household health risk" factor stays named that way.** "Vulnerable household" is
   deficit language about the person; "household health risk" is a statement about the *condition of
   the house in this weather*. Keep the subject the dwelling and the hazard, never the tenant:
   "This house has no working air conditioner and a baby lives here" — not "This is a vulnerable
   household." Note honestly that the Style Manual does not name the word "vulnerable"; the
   deficit-language rule is the basis, and the *National framework* itself uses "vulnerable people
   or groups" at 6.4 — so this is our editorial call, defended by rule 6, not a quotable prohibition.
   **Flagged as interpretation, not citation.**
8. **Consult, don't assume.** The Style Manual's Aboriginal and Torres Strait Islander page:
   "Authoritative guidance lives with the relevant community or individual" and "there are very few
   hard rules". The impact assessment tool 8.1 is stronger: "If your project has the potential to
   significantly impact First Nations individuals, communities or groups, it is critical that you
   meaningfully consult with relevant community representatives", citing AIATSIS. We have not
   consulted. Say that plainly in the Discussion as a limitation; it is the honest answer to Cat
   Kutay's likely question, and claiming otherwise is worse than admitting it.
9. **NT-specific:** the NT Government website standard requires only "Language is written in plain
   English" (Website standards, digitalterritory.nt.gov.au, retrieved 2026-09-12). There is **no
   separate NT plain-language style guide** — NT defers to plain English and nt.gov.au as the single
   source of truth for public content. **Confirmed absence, not a gap in the search.**
10. **Second-language English readers.** Nothing in the Style Manual sets a rule beyond plain
    language and WCAG. Any claim that our tenant text is suitable for speakers of an Aboriginal
    language as a first language would be **TBD — needs validation** by testing, which we cannot do.
    Do not claim it.

---

## Where this belongs

Section 1 and the feature map → **report Discussion/Ethics section** and the PRD as named
constraints (the map is close to a ready-made table — one column of it belongs on a pitch slide).
Section 2 → **report references**, replacing prior-art reference 7 with DTA v2.0 (15 Dec 2025) and
adding the National framework (21 Jun 2024) and the AI impact assessment tool. The wording rules →
**a constraint block in the PRD** governing the tenant view's copy and the factor names, plus one
line in the report's Discussion on why the factor is called "household health risk". The
"not claimable" list → **report Limitations**. The unpublished NT assessment contents and the
untested second-language claim → **BACKLOG.md**, as validations we did not do.
