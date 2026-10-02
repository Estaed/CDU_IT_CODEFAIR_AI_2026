# Data survey for Brief 6: policy, case material, corpora, ground truth

Date: 2026-10-03. Input to a decision, not a decision. Scope: the five questions in the research brief.
`reports/2026-10-03-landscape-verified-summaries.md` is not repeated here.

Discovery routes: WebSearch; DuckDuckGo via `web_ara.py` (it added the DSS Guide's "HTML only"
wording and a second index for the AustLII policy); the Hugging Face API (licences, dates);
`gh api` (repository licences, last push); the arXiv API (papers, dates); and the NT open-data CKAN
API (licence counts). NT Government sites (tfhc/dhlgcd/nt.gov.au), guides.dss.gov.au, ndis.gov.au and
AustLII all block plain fetches (HTTP 403 or a Cloudflare challenge, 2026-10-03). The NT policy PDFs
were read as text through the `r.jina.ai` reader, and their page and word counts come from that text.

## Headline findings

1. **The real NT housing policies exist and match the scenario's shape. Their licence is not CC BY.**
   DHLGCD publishes about 45 short versioned policy PDFs (5–23 pages each). Five of them add up to
   exactly 40 pages: Priority housing, Eligibility, Identification and documentation, Domestic and
   family violence, and Discretionary decision making. The NTG copyright statement allows reuse only
   under fair dealing (private study, research, criticism or review) or an explicit Creative Commons
   licence. The PDFs carry no CC statement.
2. **The real policy contradicts the scenario in `notes.md`.** NT Eligibility policy §3.4 says
   housing "will not be withheld based on a debt owed to the CEO (Housing)". So the planned plain-AI
   reading "rent arrears → does not meet priority criteria" is wrong under real NT policy. That also
   makes it a ready-made, *real* error for the demo. The scenario's "clause 4.3 waives arrears" does
   not exist in the DFV policy. Details are in §1.3.
3. **AustLII is off-limits for this build.** Its usage policy forbids using its materials, directly
   or indirectly, to "evaluate" or "provide inputs to" AI systems, including RAG and summarisation.
   NTCAT and ART/AAT decisions are published *only* there.
4. **No ready-made corpus covers Australian caseworker files.** OALC has no NT decisions and no
   tribunal decisions. GovReport and Multi-LexSum are US material. Labelled faithfulness sets
   (SummEdits, LLM-AggreFact, FABLES, RAGTruth, UniSumEval) are useful only as an *external* check of
   the claim verifier.
5. **Suggested shape (a suggestion):** real NT policy bundle plus a synthetic case file, with ground
   truth fixed *by construction*, and a mutation set on top. Three combinations are in §5.

---

## 1. Real policy documents a caseworker interprets

### 1.1 NT public housing policies (DHLGCD, formerly TFHC)

| Claim | Verdict | Source (date) | What it changes |
| --- | --- | --- | --- |
| The policy list page names about 45 PDFs in 9 sections, each with a size and month: Overview, Foundations, Accessing housing, Living, Leaving, Asset management, Initiatives, Debt management, Community housing | confirmed | [tfhc.nt.gov.au policies page](https://tfhc.nt.gov.au/publications-and-policies/housing/public-housing/policies), read 2026-10-03 via [r.jina.ai](https://r.jina.ai/https://tfhc.nt.gov.au/publications-and-policies/housing/public-housing/policies) | A real, current policy set exists, so the policy side need not be invented |
| Priority housing: 7 pages, ~1,540 words, v2.04, approved 26/03/2024 | confirmed | [priority-housing-policy.pdf](https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/accessing/priority-housing-policy.pdf), approved 2024-03-26, read 2026-10-03 | The scenario's core document is real |
| Eligibility for social housing: 8 pp, v7.1, approved 27/06/2024 | confirmed | [eligibility-for-social-housing-policy.pdf](https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/accessing/eligibility-for-social-housing-policy.pdf), 2024-06-27, read 2026-10-03 | Holds the debt and former-tenancy rules (§1.3) |
| Identification and documentation: 9 pp, v4.02 | confirmed | [identification-and-documentation-policy.pdf](https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/accessing/identification-and-documentation-policy.pdf), read 2026-10-03 | "must also provide evidence of those needs" for priority applicants |
| Domestic and family violence: 11 pp, ~3,500 words, v2.1 (07/26), approved 29/02/2024 | confirmed | [domestic-family-violence-policy.pdf](https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/living/domestic-family-violence-policy.pdf), listed as updated 29/06/2026, read 2026-10-03 | DFV is a real priority ground |
| Discretionary decision making: 5 pp, v2.02 (01/23) | confirmed | [discretionary-decision-making-policy.pdf](https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/foundations/discretionary-decision-making-policy.pdf), read 2026-10-03 | The "exception may apply" hinge is real policy |
| Also available: Allocation 8 pp (v6.0), Wait lists 8 pp, Debt management 8 pp (approved 13/12/2022), Appeals 7 pp (v2.0, 05/23, includes the Public Housing Appeals Board), Transfers 10 pp, Rent 12 pp, Income and assets 23 pp (v13.0, approved 25/09/2025) | confirmed | URLs in the Sources list, all read 2026-10-03 | Room for a second or third case type (transfer, arrears, income test) |
| Remote housing has its own policies: Remote housing leases, Remote rent safety net, Remote visitor management (updated 29/06/2026), Remote local-recruit rent concession | confirmed | [policies page](https://tfhc.nt.gov.au/publications-and-policies/housing/public-housing/policies), read 2026-10-03 | Remote and town-camp cases are possible, but see the next row |
| "There is no priority housing within remote communities and town camps" | confirmed | [priority-housing-policy.pdf](https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/accessing/priority-housing-policy.pdf) §3, read 2026-10-03 | A priority-housing scenario must be urban (Darwin fits) |
| Format: PDFs with numbered sections and "Page x of y" footers | confirmed | the PDFs above, read 2026-10-03 | Section and page anchors for source tags come free |
| NT Ombudsman 2024/25 Annual Report, Case Example 2 "The importance of transparency in housing allocation": found a "lack of available information about priority housing allocation in remote communities" | confirmed | [Ombudsman NT Annual Report 2024/25](https://ombudsman.nt.gov.au/__data/assets/pdf_file/0005/1567508/Ombudsmans-Office-24-25-Annual-Report.pdf) (91 pp), read 2026-10-03 | A real, citable NT problem statement for the pitch |

### 1.2 Licence of NT Government material

| Claim | Verdict | Source (date) | What it changes |
| --- | --- | --- | --- |
| nt.gov.au: "No part of this website may be reproduced or reused for any purpose whatsoever, apart from: fair dealing for the purposes of private study, research, criticism or review … or where expressly provided under a Creative Commons licence" | confirmed | [nt.gov.au copyright, disclaimer and privacy](https://nt.gov.au/page/copyright-disclaimer-and-privacy), read 2026-10-03 | NT housing policies are **not** CC BY. Shipping them inside the submission ZIP rests on a fair-dealing reading |
| The DHLGCD policy PDFs carry no Creative Commons statement | confirmed for the DFV policy; the others are not checked line by line | [DFV policy](https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/living/domestic-family-violence-policy.pdf), read 2026-10-03 | As above |
| Whether bundling NT policy PDFs in a student competition submission counts as fair dealing for research/study | **TBD — needs validation** | — | Settle it by emailing DHLGCD or asking the organisers. Two judges are NTG DCDD staff, so they can say. The fallback is a download script plus links instead of bundled copies |
| data.nt.gov.au: 1,010 of 1,075 datasets are `cc-by` | confirmed | [CKAN API facet query](https://data.nt.gov.au/api/3/action/package_search?rows=0&facet.field=%5B%22license_id%22%5D), read 2026-10-03 | The NT open-data portal *is* CC BY. The policy PDFs are not on it |
| "Urban Public Housing Wait Times, Wait List and Allocations" CSVs, CC BY, latest period 31 Dec 2020 (metadata modified 2024-09-23) | confirmed | [data.nt.gov.au dataset Dec 2020](https://data.nt.gov.au/dataset/urban-public-housing-wait-times-wait-list-and-allocations-december-2020), read 2026-10-03 | A real NT dataset under a clean licence, for the "datasets" criterion and for context ("priority wait times"). It is old data, so say so |

### 1.3 The scenario checked against the real policies

| Scenario element (`notes.md`) | Real NT policy says | Source (date) |
| --- | --- | --- |
| "$2,400 rent arrears, does not meet priority criteria" | Eligibility §3.4 Debts: "The provision of social housing will not be withheld based on a debt owed to the CEO (Housing)." Debt is recovered under the Debt Management policy | [Eligibility policy](https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/accessing/eligibility-for-social-housing-policy.pdf), approved 2024-06-27, read 2026-10-03 |
| "Policy clause 4.3 waives arrears" for DFV | No arrears or debt clause in the DFV policy; it only references the Debt Management policy. Its §4 is "Decision-making (delegation and discretion)" | [DFV policy](https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/living/domestic-family-violence-policy.pdf), read 2026-10-03 |
| Real exclusions a case could hinge on | Eligibility §3.5: a former tenant whose tenancy was terminated for breach is "ineligible to apply … for a period of 2 years". Priority §3.1: the applicant "must prove their urgent need … documentation that supports their claim". Priority §3.1: the CEO "has some discretion for extreme situations" | [Eligibility policy](https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/accessing/eligibility-for-social-housing-policy.pdf), [Priority policy](https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/accessing/priority-housing-policy.pdf), both read 2026-10-03 |

**What it changes.** With real policy, the plain-AI error becomes "the summary treats arrears as
disqualifying; Eligibility §3.4 says it is not". The citation then points at a real clause, which
NTG judges can check. The stale-ledger contradiction (p.8 against p.23) and the omitted DFV letter
still work as file-side errors. The "clause 4.3" wording has to change. This report does not edit
`notes.md`.

### 1.4 Commonwealth alternatives

| Claim | Verdict | Source (date) | What it changes |
| --- | --- | --- | --- |
| The Social Security Guide "is designed as a web publication (HTML). It is not available in a single electronic file or in paper format" | confirmed (search snippet of the page; direct fetch gave 403) | [guides.dss.gov.au/social-security-guide](https://guides.dss.gov.au/social-security-guide), read 2026-10-03 via DuckDuckGo | Pages must be saved by hand from a browser. No single PDF exists |
| The Guides to Social Policy Law are "designed to assist decision makers administering social policy law" | confirmed (snippet) | [guides.dss.gov.au/social-security-guide/updates](https://guides.dss.gov.au/social-security-guide/updates), read 2026-10-03 | A real caseworker document by design |
| Latest version 1.342, released 21 Sep 2026; next update 3 Nov 2026 | single source (WebSearch snippet) | [Social Security Guide Updates 2026](https://guides.dss.gov.au/social-security-guide/updates/previous-updates/2026), read 2026-10-03 | Current. Cite the version used |
| Licence: the guides site's disclaimer points to the DSS Copyright page, which says "All material presented on this website is provided under a … CC BY 4.0 licence", except logos, third-party content and images | confirmed in two hops; whether "this website" covers guides.dss.gov.au is an inference | [guides disclaimer (on 404 page)](https://guides.dss.gov.au/copyright), [DSS Copyright](https://www.dss.gov.au/using-our-website/copyright) (Published Time 2026-10-02), read 2026-10-03 | The cleanest licence of all the policy options |
| NDIS material is under "Creative Commons CC Attribution – Non-Commercial license, version 3.0" | confirmed | [NDIS copyright](https://www.ndis.gov.au/policies-and-rules/copyright), read 2026-10-03 via r.jina.ai | Usable for a non-commercial student demo |
| NDIS Our Guidelines are PDFs, e.g. "Reasonable and necessary" 24 pp (27 Aug 2026) and "Compensation" 75 pp (28 Aug 2026) | single source (search-result titles; direct fetch 403) | [R&N PDF](https://ndis.gov.au/media/7772/download?attachment=), [Compensation PDF](https://ndis.gov.au/media/8006/download?attachment=), read 2026-10-03 | Long, current policy documents |
| The Our Guidelines microsite was retired on 4 Sep 2025 and the content moved to ndis.gov.au | **TBD — needs validation** (search summary only) | [NDIS news](https://ndis.gov.au/news/10886-our-guidelines-moved-ndis-website), read 2026-10-03 | Cite ndis.gov.au URLs, not ourguidelines.ndis.gov.au |

---

## 2. Real case-like documents

| Source | Where published | Length | Identification | Usable here? | Source (date) |
| --- | --- | --- | --- | --- | --- |
| NTCAT (residential tenancies) | "NTCAT publishes decisions in significant cases on … AustLII" | varies | Parties are named unless a non-publication order applies, then "anonymising" | **No**: AustLII only (see below) | [NTCAT Published Decisions](https://ntcat.nt.gov.au/after-ntcat/published-decisions), no page date, read 2026-10-03 |
| ART (formerly AAT): social security, NDIS | "a selection of decisions … available on AustLII", ARTA and AATA databases | varies | Social security, child support and similar decisions "are redacted before publication by Tribunal staff". The Social Security (Administration) Act s201(1A) bars identifying a party | **No**: AustLII only | [ART Published decisions](https://www.art.gov.au/about-us/our-role/published-decisions), read 2026-10-03; [ART Publication of Decisions Policy](https://www.art.gov.au/sites/default/files/2024-11/Publication%20of%20Decisions%20Policy.pdf), dated 9 Feb 2026, commenced 1 Nov 2024 |
| NT Supreme Court / Court of Appeal | on the court's own site, as PDFs | e.g. *CEO (Housing) v Young & Anor* [2022] NTCA 1: 61 pp, on remote public housing habitability under RTA s48, NTCAT jurisdiction and damages | Named parties (remote community residents) | Possible as a **real long reading** under fair dealing (nt.gov.au terms). Not a case file, and it names people | [NTCA 1 PDF](https://supremecourt.nt.gov.au/__data/assets/pdf_file/0004/1084918/NTCA-1-Chief-Executive-Officer-Housing-v-Young-Anor-4-Feb-003.pdf), 2022-02-04, read 2026-10-03 |
| NT Coroner findings | "Inquest findings are published on the website unless the coroner orders otherwise" (AGD site) | long PDFs | Named deceased. Courts use cultural substitute names (e.g. "Kumanjayi") out of respect for mourning practice | **Not recommended**: deaths, many of Aboriginal people, often DFV. Unsuitable as demo fodder | [nt.gov.au coroner and inquests](https://nt.gov.au/law/courts-and-tribunals/coroner-and-inquests-folder/inquests) (search snippet), read 2026-10-03; [Kumanjayi Walker findings 2025 NTLC 8](https://agd.nt.gov.au/attorney-general-and-justice/courts/inquests-findings/kumanjayi-walker/files-exhibits-and-media/Inquest-into-the-death-of-Kumanjayi-Walker-2025-NTLC-8.pdf), 2025, read 2026-10-03 (search summary) |
| NT Ombudsman case examples | inside annual reports | one or two paragraphs each | De-identified | **As story seeds only**, too short to be a case file | [Ombudsman NT AR 2024/25](https://ombudsman.nt.gov.au/__data/assets/pdf_file/0005/1567508/Ombudsmans-Office-24-25-Annual-Report.pdf), read 2026-10-03 |
| Public Housing Appeals Board decisions | not found published | — | — | **TBD — needs validation** (ask DHLGCD) | [Appeals policy](https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/foundations/appeals-policy.pdf) v2.0, read 2026-10-03 |

**AustLII terms.**

| Claim | Verdict | Source (date) | What it changes |
| --- | --- | --- | --- |
| AustLII materials "may not be used, directly or indirectly, to train, fine-tune, evaluate, develop, operate, or provide inputs to artificial intelligence systems". The list covers RAG, and "AI-related use" includes "summarisation, or semantic retrieval" | confirmed (text from the policy page via two search indexes; direct fetch blocked by Cloudflare) | [AustLII Usage Policy](https://www.austlii.edu.au/austlii/usage.html), [copyright.html](https://www5.austlii.edu.au/austlii/copyright.html); policy date **unknown**, read 2026-10-03 | Pasting even a single AustLII decision into our summariser is "provide inputs to" an AI system. Do not use AustLII documents |
| Individual end users may "read, print and copy materials for their personal use" | confirmed (snippet) | [copyright.html](https://www.austlii.edu.au/austlii/copyright.html), read 2026-10-03 | Reading for background is fine. Feeding the demo is not |
| The policy date and any research or education exception | **TBD — needs validation** | — | Settle by opening the page in a browser. Low value, because the AI clause already decides the question |

**Ethics of named people's published decisions (reasoning, not a sourced finding).** The NT AI
policy bars entering personal information into third-party AI tools. That line is from the earlier
report's source; this report did not re-check it. A published decision still contains personal
information about real people. Re-processing it with an LLM in a demo, and showing it to judges
from NTG, invites exactly the question the brief's "trust" twist is about. Synthetic people avoid
the question entirely. A real judgment can still be cited as *inspiration* for the facts pattern.

---

## 3. Ready-made corpora and datasets

| Option | What it is | Status (date) | Licence | Fit |
| --- | --- | --- | --- | --- |
| Open Australian Legal Corpus (isaacus) | 232,560 Australian legislative and judicial documents | v7.1.0, sources last updated 10 Mar 2025; HF repo modified 2026-03-07 | Corpus CC BY 4.0; documents "relatively equally permissive" per its LICENCE.md | **Low.** Courts covered: High Court, Federal Court, NSW Caselaw. Legislation from Cth, NSW, Qld, WA, SA, Tas, Norfolk. **No NT, no tribunals** ([README](https://huggingface.co/datasets/isaacus/open-australian-legal-corpus), read 2026-10-03) |
| OALC fork (benrfairless) | same corpus, v7.2.0 | HF modified 2026-09-23 | CC BY 4.0 | Lists **NT legislation 3,739 docs** (384 primary, 305 secondary, 3,050 bills). Still no NT decisions ([card](https://huggingface.co/datasets/benrfairless/open-australian-legal-corpus), read 2026-10-03) |
| GovReport | long US GAO/CRS reports with expert summaries | 2021 paper; HF card modified 2022-11-09 | CC BY 4.0 ([HF](https://huggingface.co/datasets/launch/gov_report)) | Long government documents, but US. A possible stress test only ([arXiv 2104.02112](https://arxiv.org/abs/2104.02112), 2021-04-05) |
| Multi-LexSum | 9,280 expert summaries of US civil-rights cases; sources "often exceeding two hundred pages per case" | 2022; HF modified 2024-08-25 | ODC-By ([HF](https://huggingface.co/datasets/allenai/multi_lexsum)) | Real long case files with expert summaries, but US litigation, not casework ([arXiv 2206.10883](https://arxiv.org/abs/2206.10883), 2022-06-22) |
| LLM-AggreFact | unified benchmark for grounding/fact-checking (from MiniCheck) | HF modified 2024-12-20 | CC BY-ND 4.0; HF gate "auto" (accept terms) ([HF API](https://huggingface.co/api/datasets/lytang/LLM-AggreFact)) | **External verifier check**: report our claim checker's balanced accuracy on it. The subset list was not readable (gated) → TBD ([arXiv 2404.10774](https://arxiv.org/abs/2404.10774), 2024-04-16) |
| SummEdits | 10-domain inconsistency benchmark built by editing summaries; inter-annotator agreement "about 0.9" | HF modified 2026-04-30 | CC BY 4.0 ([HF](https://huggingface.co/datasets/Salesforce/summedits)) | **External verifier check**, open licence, small ([arXiv 2305.14540](https://arxiv.org/abs/2305.14540), 2023-05-23) |
| FABLES | 3,158 claims from LLM summaries of 26 books, human labels with evidence quotes and omission comments; cost $5.2K | repo pushed 2024-09-24 | MIT ([repo](https://github.com/mungg/FABLES)) | Shows how long-document labels are made. The README schema lists no book-text field, so it cannot be re-run on the sources ([arXiv 2404.01261](https://arxiv.org/abs/2404.01261), 2024-04-01) |
| UniSumEval | fine-grained faithfulness plus "keyfact" (completeness) labels, short and long inputs | repo pushed 2024-09-30 | **No licence on the repo → TBD** ([repo](https://github.com/DISL-Lab/UniSumEval-v1.0)) | The only one here with omission-style labels. Its licence blocks safe reuse until clarified ([arXiv 2409.19898](https://arxiv.org/abs/2409.19898), 2024-09-30) |
| DiverSumm | faithfulness benchmark for long-form and multi-document summarisation | repo pushed 2025-03-05 | MIT ([repo](https://github.com/HJZnlp/infuse)) | Long-document faithfulness. Domain fit unverified ([arXiv 2402.17630](https://arxiv.org/abs/2402.17630), 2024-02-27) |
| RAGTruth | ~18,000 RAG responses, word-level hallucination labels | repo pushed 2024-12-02 | MIT ([repo](https://github.com/ParticleMedia/RAGTruth)) | Span-level labels; short contexts ([arXiv 2401.00396](https://arxiv.org/abs/2401.00396), 2023-12-31) |

**Practice note.** LongEval surveyed 162 long-form summarisation papers and found "73% of these
papers do not perform any human evaluation" ([arXiv 2301.13298](https://arxiv.org/abs/2301.13298),
2023-01-30). A small, honest, hand-built gold set is therefore already above the field's norm.

---

## 4. Real vs synthetic ground truth

| Method | What it is | Source (date) | For this build |
| --- | --- | --- | --- |
| Rule-based perturbation (FactCC) | "a series of rule-based transformations to the sentences of source documents" turn a correct summary into an inconsistent one: entity, number and pronoun swaps, negation, noise | [arXiv 1910.12840](https://arxiv.org/abs/1910.12840), 2019-10-28; code BSD-3 ([salesforce/factCC](https://github.com/salesforce/factCC), pushed 2025-05-01) | Cheap and fully labelled. The label is known because we made the error |
| Edit-based benchmark (SummEdits) | an LLM edits a seed summary, humans verify; "20 times more cost-effective per sample", agreement ~0.9 | [arXiv 2305.14540](https://arxiv.org/abs/2305.14540), 2023-05-23 | Same idea with richer edits. One afternoon for ~50 edits checked by Tarık |
| Synthetic hard errors (MiniCheck) | "creating realistic yet challenging instances of factual errors via a structured generation procedure" | [arXiv 2404.10774](https://arxiv.org/abs/2404.10774), 2024-04-16 | Supports the planted-error approach |
| Human claim labels (FABLES) | annotators who read the whole source label each claim and quote evidence | [arXiv 2404.01261](https://arxiv.org/abs/2404.01261), 2024-04-01 | Gold standard, but $5.2K for 26 books. Out of reach in 5 days except for a tiny set |
| Position of the critical passage | performance "can degrade significantly when changing the position of relevant information" | [arXiv 2307.03172](https://arxiv.org/abs/2307.03172), 2023-07-06 | Plant the decisive passages mid-file (around p.23 and p.51 of 60), so the eval tests the known failure |

**Real public documents plus a synthetic case file, compared with fully synthetic (reasoning, not a
sourced finding).**
- **Real policy plus synthetic file.** The policy clauses can be checked by the NTG judges, and a
  citation to "Eligibility §3.4" is verifiable on their own website. The case file holds no real
  person, so the NT AI policy question does not arise. Ground truth is exact, because we wrote the
  facts. Costs: the fair-dealing question (§1.2), and the file's realism depends on us. Plant only
  facts that the real policy makes decisive.
- **Fully synthetic.** No licence question, total control. Its weakness is "you invented both the
  rules and the answer", the obvious judge question under the "datasets" criterion.
- **What judges are likely to find credible.** This is a judgment, not a source: a gold set written
  *before* running the model, an error taxonomy (stale value, contradiction, omitted exception,
  unsupported claim, number swap), numbers per error type, and an external benchmark number for the
  checker.

---

## 5. Three document combinations (suggestions; the choice is Tarık's)

### A. Real NT policy bundle (40 pp) + synthetic 60-page priority-housing file (suggested first try)
- **Real:** Priority housing (7), Eligibility (8), Identification and documentation (9), DFV (11),
  Discretionary decision making (5) = 40 pages, with real section numbers. Plus the CC BY wait-time
  CSV for context.
- **Synthetic:** the case file: application form, rent ledgers (January arrears, March cleared),
  a support-agency letter on DFV, a GP letter, a prior-tenancy record, interview notes. Pages are
  dated and numbered, and the people are invented.
- **Licence:** policies under NTG copyright, fair dealing (TBD, §1.2). If not cleared, ship a fetch
  script instead of the PDFs. The case file is ours.
- **Effort (5-day build):** about 0.5 day to fetch and parse the policies; 1–1.5 days to write the
  facts table and then the file; about 1 day for the eval set.
- **Ground truth:** first write a facts table (fact · value · page · which policy clause makes it
  decisive), then generate the file from it, so every gold label exists before any model runs. On
  top, build a mutation set from a hand-written correct summary: number and date swaps, negation,
  a stale value (Jan instead of Mar), the dropped DFV letter as an omission, and the arrears claim
  against Eligibility §3.4 as a policy misreading. Score per error type. Make 3–5 files, each with
  a different decisive fact: arrears, the 2-year former-tenancy exclusion, missing documentation,
  discretion for an extreme situation.

### B. As A, but with the file's fact pattern drawn from public NT cases
- **Real:** the same policy bundle. The *pattern* comes from public sources, cited: the Ombudsman
  2024/25 housing-allocation transparency case, and the remote-housing facts in *CEO (Housing) v
  Young* [2022] NTCA 1.
- **Synthetic:** all people and documents.
- **Licence:** as A. The judgment is cited, not ingested.
- **Effort:** A plus ~0.5 day.
- **Ground truth:** as A. It adds "grounded in a real NT situation" to the pitch. Note that remote
  communities have no priority housing (§1.1), so a remote pattern means an allocation or transfer
  case, not a priority one.

### C. Commonwealth variant: Social Security Guide sections + synthetic Centrelink-style file + external benchmark
- **Real:** chosen Social Security Guide sections (CC BY 4.0), saved from HTML. Plus SummEdits
  (CC BY 4.0) or LLM-AggreFact (CC BY-ND, gated) to give the checker an external accuracy number.
- **Synthetic:** the case file.
- **Licence:** cleanest of the three.
- **Effort:** about the same as A. The pages must be saved by hand (403 to scripts).
- **Ground truth:** as A, plus the benchmark's own labels.
- **Cost:** loses the NT and housing story that the NTG judges would recognise.

The external-benchmark piece of C can be added to A or B for about half a day, if time allows.

---

## Where this belongs
- **Blueprint → Decisions (open question):** which combination (A, B or C), and whether to bundle
  the NT policies or fetch them.
- **Blueprint → Constraints (candidate sentences):** "No AustLII material is used as model input."
  "No real person's data in any demo document."
- **Blueprint → Riskiest assumption:** the fair-dealing reading, or permission from DHLGCD.
- **`notes.md` scenario:** the arrears premise and "clause 4.3" conflict with real policy (§1.3).
  The owner of `notes.md` decides the rewrite.

## Open questions (recorded, not asked)
1. Is bundling NT policy PDFs in the submission acceptable (fair dealing), or should the README
   fetch them? DHLGCD or the organisers can answer.
2. Are Public Housing Appeals Board decisions published anywhere?
3. Which subsets and per-subset licences does LLM-AggreFact contain (gated page)? What is
   UniSumEval's licence (none on the repository)?
4. What is the AustLII usage policy's date? It does not change the decision.

## Sources
- https://tfhc.nt.gov.au/publications-and-policies/housing/public-housing/policies (no page date; read 2026-10-03 via r.jina.ai)
- https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/accessing/priority-housing-policy.pdf (v2.04, approved 2024-03-26; read 2026-10-03)
- https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/accessing/eligibility-for-social-housing-policy.pdf (v7.1, approved 2024-06-27; read 2026-10-03)
- https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/accessing/identification-and-documentation-policy.pdf (v4.02; read 2026-10-03)
- https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/living/domestic-family-violence-policy.pdf (v2.1, 07/26, approved 2024-02-29; read 2026-10-03)
- https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/foundations/discretionary-decision-making-policy.pdf (v2.02, 01/23; read 2026-10-03)
- https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/accessing/allocation-commencement-tenancy-policy.pdf (v6.0, approved 2024-03-26; read 2026-10-03)
- https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/accessing/wait-lists-policy.pdf (v2.0; read 2026-10-03)
- https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/debt-management/debt-management-policy.pdf (v4.0, approved 2022-12-13; read 2026-10-03)
- https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/foundations/appeals-policy.pdf (v2.0, 2023-05-25; read 2026-10-03)
- https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/living/social-housing-transfers-policy.pdf (v5.0; read 2026-10-03)
- https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/living/rent-policy.pdf (03/26; read 2026-10-03)
- https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/accessing/income-and-assets-policy-1.pdf (v13.0, approved 2025-09-25; read 2026-10-03)
- https://nt.gov.au/page/copyright-disclaimer-and-privacy (no page date; read 2026-10-03)
- https://data.nt.gov.au/api/3/action/package_search?rows=0&facet.field=%5B%22license_id%22%5D (read 2026-10-03)
- https://data.nt.gov.au/dataset/urban-public-housing-wait-times-wait-list-and-allocations-december-2020 (data to 2020-12-31, metadata 2024-09-23; read 2026-10-03)
- https://ombudsman.nt.gov.au/__data/assets/pdf_file/0005/1567508/Ombudsmans-Office-24-25-Annual-Report.pdf (2024/25; read 2026-10-03)
- https://guides.dss.gov.au/social-security-guide (no date; snippet read 2026-10-03)
- https://guides.dss.gov.au/social-security-guide/updates (snippet read 2026-10-03)
- https://guides.dss.gov.au/social-security-guide/updates/previous-updates/2026 (v1.342, 2026-09-21; snippet read 2026-10-03)
- https://guides.dss.gov.au/copyright (disclaimer text; read 2026-10-03)
- https://www.dss.gov.au/using-our-website/copyright (Published Time 2026-10-02; read 2026-10-03)
- https://www.ndis.gov.au/policies-and-rules/copyright (no date; read 2026-10-03)
- https://ndis.gov.au/media/7772/download?attachment= (27 Aug 2026; title read 2026-10-03)
- https://ndis.gov.au/media/8006/download?attachment= (28 Aug 2026; title read 2026-10-03)
- https://ndis.gov.au/news/10886-our-guidelines-moved-ndis-website (date unverified; read 2026-10-03)
- https://ntcat.nt.gov.au/after-ntcat/published-decisions (no page date; read 2026-10-03)
- https://www.art.gov.au/about-us/our-role/published-decisions (no page date; read 2026-10-03)
- https://www.art.gov.au/sites/default/files/2024-11/Publication%20of%20Decisions%20Policy.pdf (dated 2026-02-09, commenced 2024-11-01; read 2026-10-03)
- https://supremecourt.nt.gov.au/__data/assets/pdf_file/0004/1084918/NTCA-1-Chief-Executive-Officer-Housing-v-Young-Anor-4-Feb-003.pdf (2022-02-04; read 2026-10-03)
- https://nt.gov.au/law/courts-and-tribunals/coroner-and-inquests-folder/inquests (snippet read 2026-10-03)
- https://agd.nt.gov.au/attorney-general-and-justice/courts/inquests-findings/kumanjayi-walker/files-exhibits-and-media/Inquest-into-the-death-of-Kumanjayi-Walker-2025-NTLC-8.pdf (2025; search summary read 2026-10-03)
- https://www.austlii.edu.au/austlii/usage.html (date unknown; snippets read 2026-10-03)
- https://www5.austlii.edu.au/austlii/copyright.html (date unknown; snippets read 2026-10-03)
- https://huggingface.co/datasets/isaacus/open-australian-legal-corpus (v7.1.0, repo modified 2026-03-07; read 2026-10-03)
- https://huggingface.co/datasets/benrfairless/open-australian-legal-corpus (v7.2.0, modified 2026-09-23; read 2026-10-03)
- https://huggingface.co/datasets/launch/gov_report (modified 2022-11-09; read 2026-10-03)
- https://huggingface.co/datasets/allenai/multi_lexsum (modified 2024-08-25; read 2026-10-03)
- https://huggingface.co/api/datasets/lytang/LLM-AggreFact (modified 2024-12-20; read 2026-10-03)
- https://huggingface.co/datasets/Salesforce/summedits (modified 2026-04-30; read 2026-10-03)
- https://github.com/mungg/FABLES (pushed 2024-09-24; read 2026-10-03)
- https://github.com/DISL-Lab/UniSumEval-v1.0 (pushed 2024-09-30; read 2026-10-03)
- https://github.com/HJZnlp/infuse (pushed 2025-03-05; read 2026-10-03)
- https://github.com/ParticleMedia/RAGTruth (pushed 2024-12-02; read 2026-10-03)
- https://github.com/salesforce/factCC (pushed 2025-05-01; read 2026-10-03)
- https://arxiv.org/abs/1910.12840 (2019-10-28)
- https://arxiv.org/abs/2104.02112 (2021-04-05)
- https://arxiv.org/abs/2206.10883 (2022-06-22)
- https://arxiv.org/abs/2301.13298 (2023-01-30)
- https://arxiv.org/abs/2305.14540 (2023-05-23)
- https://arxiv.org/abs/2307.03172 (2023-07-06)
- https://arxiv.org/abs/2401.00396 (2023-12-31)
- https://arxiv.org/abs/2402.17630 (2024-02-27)
- https://arxiv.org/abs/2404.01261 (2024-04-01)
- https://arxiv.org/abs/2404.10774 (2024-04-16)
- https://arxiv.org/abs/2409.19898 (2024-09-30)

When you rewrite this, keep each link and date beside its claim and paste the Sources block unchanged.
