# Landscape survey: source-linked summaries that keep the caseworker verifying

Written 2026-10-03 by the `research` skill. This is input for decisions, not a decision. Nothing here
has been written into Blueprint, `notes.md` or a task file.

**Brief 6 (CDU IT Code Fair 2026, AI Challenge):** help a caseworker get through long policy and case
documents faster without nudging them into trusting a summary they haven't checked. Link every claim to
its exact source passage, flag uncertainty, keep the human accountable.
**Our idea:** the AI points to the passages and the human reads them. The app makes the caseworker read
the critical passages, not just trust the summary.

**The claims this survey tests (each one could turn out false):**
1. Existing tools already make the user verify before using a summary. *(Result: not found. Every tool
   surveyed makes verification optional.)*
2. Research shows source links and highlights reliably reduce overreliance. *(Result: partly true. Links
   and citations can also increase blind trust.)*
3. A local, maintained model can check whether a cited passage supports a claim. *(Result: true. MiniCheck
   family and HHEM.)*
4. Jev and Laya can serve as that checker. *(Result: unknown. Nobody has benchmarked either on this task.)*
5. NT and Australian rules bear on how the app may handle case text. *(Result: true. See section 5.)*

**Discovery routes and what each one added:**
- WebSearch: products, papers and government documents.
- `web_ara.py` (DuckDuckGo): the Jev/Laya benchmark pages, the Claude citations practice posts, and the
  check for "forced verification" tools.
- `gh search repos` and `gh api`: the Laya ecosystem and the repo status of the grounding checkers.
- `hn_ara.py`: Jev and Laya practice threads.
- PyPI JSON: Laya release dates.
- The arXiv API returned 429/503, so the paper details come from arxiv.org/abs pages and the publishers'
  own pages.

---

## 1. Products: what they do and what they do *not* do about verification

| Option | What it does | Status (source, date) | What it does NOT do | Fit for us |
|---|---|---|---|---|
| **Claude Citations API** | Splits the document into sentences and returns `cited_text` with character indices (plain text) or page numbers (PDF) for each claim. | GA, and "All active models support citations" ([docs](https://platform.claude.com/docs/en/build-with-claude/citations), read 2026-10-03) | It guarantees only that "citations are guaranteed to contain valid pointers to the provided documents". The pointer is valid; that does not mean the passage *supports* the claim. Citations combined with structured outputs return a 400 error. Scanned PDFs without a text layer "are not citable" (same page). | Strong base layer for the summary with links. Not a support check. |
| **Gemini Notebook (formerly NotebookLM)** | "To navigate directly to the quote and review it in context, select a citation." | The help page now names the product "Gemini Notebook" ([help](https://support.google.com/notebooklm/answer/16179559?hl=en), read 2026-10-03) | Clicking is optional. The page itself says "can make mistakes … Be sure to double check it." | The judges will know it. It is the baseline we have to beat on accountability, not on linking. |
| **Adobe Acrobat AI Assistant** | "Intelligent citations … so customers can easily verify the source" | Press release, 2024-02-20 ([Adobe](https://news.adobe.com/news/news-details/2024/adobe-brings-conversational-ai-to-trillions-of-pdfs-with-the-new-ai-assistant-in-reader-and-acrobat)) | Click-to-verify is optional. No support score and no sign-off step. | Same pattern as Gemini Notebook. |
| **Gemini "double-check response"** | Searches Google for each sentence and highlights it green (similar content found) or orange (different or not found). | **Contradiction:** secondary sources describe the feature ([Techloy](https://www.techloy.com/google-gemini-introduces-double-check-response-feature-to-verify-the-accuracy-of-gemini-ai-responses/), read 2026-10-03), but the current help page ([help](https://support.google.com/gemini/answer/14143489?hl=en-gb), read 2026-10-03) no longer mentions it. Whether it still exists is TBD. | It checks against the web, not your document, and it is a button the user has to choose to press. | Shows that sentence-level colour flags are a known pattern. |
| **Elicit** | Reports in which "each claim [is] backed by sentence-level citations" | ([elicit.com](https://elicit.com/), read 2026-10-03) | An independent study (Research Synthesis Methods, 2026-05-29) found the extracted values matched across reruns for about 90%, but the supporting quotes matched for only 46% and the reasoning for 30% ([Lagisz et al.](https://www.cambridge.org/core/journals/research-synthesis-methods/article/using-elicit-ai-research-assistant-for-data-extraction-in-systematic-reviews-a-feasibility-study-across-environmental-and-life-sciences/C97DAEC70C3173A260F0B12E729E7250)). | Evidence that the quote attached to a claim is not stable. |
| **Lexis+ AI / Westlaw AI / Practical Law AI** (legal RAG tools) | Cited legal answers. | A peer-reviewed study found they "each hallucinate between 17% and 33% of the time". "Misgrounded" means a source is cited but it "misinterpret[s] the source or reference[s] an inapplicable source" (Magesh et al., *J. Empirical Legal Studies* 2025, accepted 2025-03-14, [PDF](https://dho.stanford.edu/wp-content/uploads/Legal_RAG_Hallucinations.pdf)). | Citations are present but no support is checked. Harvey and CoCounsel were not in this study; no comparable independent number for them was found (TBD). | The strongest evidence that "it has citations" ≠ "it is supported". |
| **Microsoft 365 Copilot (Word)** | Shows "references with citations" from the document. | Only seen in a search excerpt of [support.microsoft.com](https://support.microsoft.com/en-us/office/chat-with-copilot-about-your-word-document-4482c688-a495-4571-bfcd-4a9fc6608090) (read 2026-10-03, page not opened) | No forced reading was found. | This is the NT-endorsed tool (section 5), so it is the realistic thing NT staff use today. |
| **UK i.AI Consult** | Proposes themes for each consultation response. Reviewers "could accept, add, or remove themes". | Evaluation 2025-05-14: 60% exact agreement, median 23 s per response ([ai.gov.uk](https://ai.gov.uk/blogs/evaluating-consult-an-ai-tool-for-enhanced-public-consultation-analysis/)) | The evaluation found "no explicit discussion of automation bias or anchoring". A second evaluation (DWP Pathways to Work) is reported as "73% unchanged, 19 s", but the PDF returned 403, so that figure is unverified ([PDF](https://ai.gov.uk/docs/DWP_pathways_to_work_evaluation_report.pdf)). | The closest government analogue. A human is in the loop, but the AI's answer is shown first. |
| **Magic Notes (Beam)** | Transcribes and summarises social-care conversations. | Used by "65,000 practitioners" (vendor claim via search excerpt, [magicnotes.ai](https://magicnotes.ai/), read 2026-10-03). Kent evaluation: assessment time −49% ([HI-KSS](https://healthinnovation-kss.com/ai-scribe-reduces-admin-time-by-almost-50-in-adult-social-care-assessments-independent-evaluation/), read 2026-10-03). | Practitioners quoted: "I wouldn't just copy and paste … sometimes it makes assumptions" ([Community Care, 2025-02-10](https://www.communitycare.co.uk/content/news/ai-tool-improves-direct-work-in-adult-social-care-despite-accuracy-concerns-practitioners-report)). Whether it links claims to the transcript is TBD. | The incumbent in social work. It speeds up writing, not reading. |
| **Hebbia, Harvey** | Document analysis grids and legal assistant. | Hebbia's homepage says nothing about how citations work ([hebbia.com](https://www.hebbia.com/), read 2026-10-03). Harvey was not checked. | TBD. Needs their own docs. | Not needed for the decision. |

**What changes for the decision:** linking each claim to its passage is already common (Claude, Gemini
Notebook, Acrobat, Elicit, Copilot). On its own it will not stand out to the judges. Every tool surveyed
leaves verification **optional**.

---

## 2. Research: overreliance and which interventions work

| Claim | Verdict | Source (date) | What it means for us |
|---|---|---|---|
| Generative search answers often cite badly: only 51.5% of sentences were fully supported, and 74.5% of citations supported their sentence. | confirmed | Liu, Zhang & Liang, [arXiv 2304.09848](https://arxiv.org/abs/2304.09848) (2023-04-19) | The reason to check support, not just whether a link exists. |
| Citations raise trust **even when they are random**; trust drops when people actually check them. | confirmed | Ding et al., [arXiv 2501.01303](https://arxiv.org/abs/2501.01303) (2025-01-02) | Links alone can *increase* complacency. This is the strongest argument for making the human read. |
| The more abstractive an output is, the harder it is to verify: up to 3× the verification time compared with quoted output, and up to 50% fewer properly cited sentences. | confirmed | Worledge, Hashimoto & Guestrin, [arXiv 2411.17375](https://arxiv.org/abs/2411.17375) (2024-11) | Keep the summary close to the source wording. Show quotes, not paraphrase. |
| Overreliance is a cost–benefit choice: explanations reduce it only when they make verification cheaper. | confirmed | Vasconcelos et al., [arXiv 2212.06823](https://arxiv.org/abs/2212.06823) (2022-12-13, CSCW 2023) | Make reading the passage the cheapest path (inline, one keypress). |
| Cognitive forcing functions reduce overreliance, but users rate them least favourably, and they help people high in Need for Cognition most. | confirmed | Buçinca, Malaya & Gajos, CSCW 2021 ([Harvard page](https://scholar.harvard.edu/zbucinca/publications/trust-or-think-cognitive-forcing-functions-canreduce-overreliance-ai-ai), [arXiv 2102.09692](https://arxiv.org/abs/2102.09692)) | Forcing works but feels annoying. Force only on the critical passages, not on everything. |
| Registering your own answer before seeing the AI's lowers agreement with the AI **whether the AI was right or wrong**. | confirmed | Fogliato et al., FAccT 2022 ([PDF](https://facctconference.org/static/pdfs_2022/facct22-3533193.pdf)) | Decide-before-reveal has a cost: it can also discard correct AI help. |
| First-person uncertainty ("I'm not sure, but…") reduced overreliance and raised accuracy (N=404). A general-perspective phrasing had a weaker effect that was not significant. | confirmed | Kim et al., FAccT 2024 ([PDF](https://facctconference.org/static/papers24/facct24-56.pdf)) | How the uncertainty flag is worded matters. |
| Colour highlighting by confidence "substantially increased the rate at which users spot incorrect information". | confirmed | Spatharioti et al., CHI 2025 ([MSR](https://www.microsoft.com/en-us/research/publication/effects-of-llm-based-search-on-decision-making-speed-accuracy-and-overreliance/)) | Supports per-claim colour flags. |
| A disclaimer, uncertainty highlighting and implicit answers each reduced overreliance but "generally fail to improve appropriate reliance". Some users became *more* confident after wrong decisions. | confirmed | Bo, Wan & Anderson, CHI 2025, [arXiv 2412.15584](https://arxiv.org/abs/2412.15584) (v3 2025-10-29) | Do not claim our flags make reliance "appropriate" without measuring it. |
| Higher confidence in GenAI goes with less critical thinking (survey, N=319). | confirmed | Lee et al., CHI 2025 ([PDF](https://www.microsoft.com/en-us/research/wp-content/uploads/2025/01/lee_2025_ai_critical_thinking_survey.pdf)) | Context for the trust twist. |
| People use evidence to validate AI claims, but use it *less* when a natural-language explanation is present. | confirmed | Warren et al., [arXiv 2601.11387](https://arxiv.org/abs/2601.11387) (2026-01-16) | Show the passage, not an AI explanation of why it supports the claim. |
| General hallucination warnings have "the weakest and most mixed effects". | confirmed | Blanchard et al., [arXiv 2606.23491](https://arxiv.org/abs/2606.23491) (2026-06-22, rev. 2026-07-30) | A banner warning is not a design. |
| LLM judges catch *added* content well (0.79–0.94) but miss *omissions* (0.50–0.63). Listing the source's facts first and then checking the note for each one recovers some of this. | confirmed | Fox et al., [arXiv 2608.31016](https://arxiv.org/abs/2608.31016) (2026-08-31) | Linking claims to sources cannot reveal what the summary left out. See gap G3. |
| Experts deferred more to AI than to humans when the error was *harsh*, but corrected lenient errors equally whatever the source (N=1,339 teachers). | confirmed | Goulas et al., *PNAS Nexus* 2026-06-09 ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC13248211/)) | Automation bias can depend on which way the error points. |
| Reviewers become habituated: approval rate +14.5 pp with experience on AI pull requests. | **unknown** (lead only) | Only a secondary blog was found ([tianpan.co](https://tianpan.co/blog/2026/04/15/human-in-the-loop-rubber-stamp), 2026-04-15) | Do not cite until the primary study is found. |

---

## 3. Checking that a claim is supported by its cited passage

| Option | What it is | Status (date) | Practice and limits | Fit (local, 8 GB GPU, Python) |
|---|---|---|---|---|
| **MiniCheck-Flan-T5-Large** | 770M model that scores (document, sentence) in [0,1]. | Repo last commit **2025-08-27**, Apache-2.0 ([GitHub](https://github.com/Liyan06/MiniCheck), checked 2026-10-03). LLM-AggreFact 75.0 ([leaderboard](https://llm-aggrefact.github.io/), read 2026-10-03) | Claims must be split into sentences "to achieve optimal performance" (README). The repo is quiet after 2025. | Good: runs on CPU or a small GPU, and the licence is permissive. |
| **Bespoke-MiniCheck-7B** | Same task at 7B. | Leaderboard #1 at **77.4**, ahead of Claude-3.5 Sonnet at 77.2. Licence **CC BY-NC 4.0**. 32K chunks ([HF card](https://huggingface.co/bespokelabs/Bespoke-MiniCheck-7B), read 2026-10-03). On Ollama at 4.7 GB, last updated "2 years ago" ([Ollama](https://ollama.com/library/bespoke-minicheck), read 2026-10-03) | Prompt format is `Document: … Claim: …` and the answer is `Yes`/`No`. | Fits 8 GB of VRAM through Ollama. Non-commercial use is fine for a student prototype. |
| **HHEM-2.1-Open (Vectara)** | FLAN-T5-base classifier on (premise, hypothesis). | Apache-2.0, "around 1.5 second for a 2k-token input" on CPU, under 600 MB ([HF](https://huggingface.co/vectara/hallucination_evaluation_model), read 2026-10-03). Leaderboard repo pushed 2026-09-23 ([GitHub](https://github.com/vectara/hallucination-leaderboard)) | It was not in the top-11 shown on LLM-AggreFact, so no direct comparison was found. | Lightest option, CPU only. |
| **Granite Guardian 3.3 (8B)** | IBM guardrail model with a groundedness check. | LLM-AggreFact 76.5. Repo pushed 2026-08-26 ([GitHub](https://github.com/ibm-granite/granite-guardian)) | Not tested here. | Possible; same size class as Bespoke. |
| **AlignScore / SummaC** | Older checkers for factual consistency of summaries. | AlignScore last commit **2024-03-11**; SummaC **2025-01-30** (GitHub API, checked 2026-10-03) | Effectively unmaintained. | Skip. |
| **Cloud APIs** (Azure groundedness detection, Vertex check-grounding, Bedrock contextual grounding) | Managed support scores. | Azure: preview, English only, 55k-character source limit, regions US/France/Canada; seen only in a search excerpt of [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/ai-services/content-safety/quickstart-groundedness) (read 2026-10-03). Vertex returns a 0–1 "support score" with citations for each claim ([docs](https://docs.cloud.google.com/generative-ai-app-builder/docs/check-grounding), excerpt). Bedrock uses a 0–1 threshold ([docs](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-contextual-grounding-check.html), excerpt) | All three send case text to a cloud service, which conflicts with the NT policy (section 5). | Poor fit for the story. |

---

## 4. TypeSafe Jev and Convai Laya

**Jev (TypeSafe), hosted**
- **Primitives.** Typed `noul` (yes/no probability), `choice` and `score`. Endpoint is
  `POST https://api.typesafe.ai/v1/systemone`. Source: [docs.typesafe.ai/api](https://docs.typesafe.ai/api), read 2026-10-03.
- **Status.** Early access since **2026-09-15**, through a waitlist ([RuntimeWire, 2026-09-15](https://runtimewire.com/article/typesafe-jev-system-one-ai-model-early-access);
  [eesel, 2026-09-21](https://www.eesel.ai/blog/typesafe-jev-pricing)). It is also exposed through the
  AI/ML API reseller at `POST /v1/decisions` ([docs.aimlapi.com](https://docs.aimlapi.com/api-references/decision-models/typesafe/jev), read 2026-10-03).
  Whether Tarık can get a key before 8 Oct is **TBD**: try the waitlist and the reseller today.
- **Price.** "$42 per billion input tokens", output free ([typesafe.ai](https://typesafe.ai/), published 2026-09-28).
- **Context.** 32K ([eesel, 2026-09-21](https://www.eesel.ai/blog/typesafe-jev-pricing); AI/ML API docs say "32K context").
- **Fit to our task.** The official Patterns page has no grounding or fact-check pattern
  ([docs](https://docs.typesafe.ai/patterns), read 2026-10-03). TypeSafe's own evaluations used
  "reference answers [from] GPT-6 Astra and Claude Fable 5.1 rather than an independently established
  ground truth" ([RuntimeWire](https://runtimewire.com/article/typesafe-jev-system-one-ai-model-early-access)).
- **Data handling.** Where data is processed and how long it is kept: **TBD** (the legal index only links
  to the DPA, [docs.typesafe.ai/legal](https://docs.typesafe.ai/legal), read 2026-10-03).

**Laya (Convai Innovations), local**
- **Model and licence.** Apache-2.0. The English checkpoint is ModernBERT-large plus decision heads,
  **421M**, with a **512-token** window ([HF card](https://huggingface.co/convaiinnovations/laya), read 2026-10-03).
- **Install and version.** `pip install laya`; latest **0.3.23 on 2026-10-01**
  ([PyPI](https://pypi.org/project/laya/), checked 2026-10-03).
- **Long documents.** The multilingual checkpoint reads up to 8,192 tokens. It got 16–18 of 20 requests
  right up to about 4,000 tokens and 8–17 of 20 beyond that (PyPI README).
- **Limitations the model card states itself:**
  - "Ships over-confident" (ECE 0.466 → 0.081 after temperature scaling).
  - Base checkpoints are "near chance on typed-decisions zero-shot" (0.362).
  - **"`noul` can follow its option labels instead of the state"** on the English variant. This is
    exactly the failure that would matter for "does this passage support this claim".

**Practice: what users report**
- **harrymunro benchmark.** Jev 92.9% vs Laya 65.3% on 1,470 synthetic items (noul 98.6 vs 71.3).
  Laya was faster on a single short question (42 ms vs 136 ms). No NLI task was included
  ([GitHub](https://github.com/harrymunro/jev-laya-benchmark), read 2026-10-03; repo date not shown).
- **HN thread (2026-09-22/24).** One user got Laya 38% vs Jev 76% on banking77. Another got Jev 98% vs
  Laya 15% on a synthetic set ([HN 49806080](https://news.ycombinator.com/item?id=49806080)).
- **Routing test.** Laya 37/40 vs a rule-based router 33/40, not compared with Jev
  ([astgl, 2026-09-22](https://astgl.com/p/local-laya-vs-hosted-jev-typed-decisions)).
- **A third entrant (lead).** "OpenAI … Decision API built on Luna" was reported 2026-09-29
  ([HN 49896979](https://news.ycombinator.com/item?id=49896979)). Not checked further.

**How they compare with MiniCheck for claim support**
- **Verdict: unknown.** No benchmark of Jev or Laya on LLM-AggreFact, NLI or claim support was found.
- MiniCheck-type models are trained and scored on exactly this task (section 3).
- Either decision model could be asked a `noul` question ("Does PASSAGE support CLAIM?"). The appeal is a
  check that comes from a different model family than the summariser. The risks:
  - Laya: the label-following failure mode, plus 512 tokens (English).
  - Jev: waitlist access, and case text would leave the machine.
- What would settle it: a 1-hour spike. Score about 50 labelled (passage, claim) pairs, for example
  drawn from the LLM-AggreFact datasets, with MiniCheck-FT5, Bespoke-MiniCheck (Ollama), Laya `noul`,
  and Jev `noul` if a key arrives. Compare balanced accuracy and calibration.

---

## 5. Australian and NT context

**Victoria: child protection worker and ChatGPT (OVIC, 2024-09-24)**
- A child protection worker used ChatGPT to draft a Protection Application Report for the Children's Court.
- The report described a doll the father "used … for sexual purposes" as a strength: "age-appropriate toys".
- The worker "said that … they would check the content". **The check still failed.**
- The department's review found 100 cases with indicators that ChatGPT may have been used.
- The compliance notice bans ChatGPT, Claude, Gemini, Copilot and similar tools for child protection
  staff, "implemented by 5 November 2024 and maintained until **5 November 2026**". That end date is
  one month after the Fair.
- The department accepted "the significant risk … that insufficiently checked outputs of even secure and
  sanctioned GenAI can present, including internally tenanted Microsoft 365 Copilot".
- Sources: [report PDF](https://ovic.vic.gov.au/wp-content/uploads/2024/11/DFFH-ChatGPT-investigation-report-20240924-Re-upload.pdf), pp. 5, 7, 9, 18, 35; [media release](https://ovic.vic.gov.au/mediarelease/ovic-finds-department-responsible-for-breaches-of-privacy-through-use-of-chatgpt/).
- **For our pitch:** this incident shows that "the human will check" does not hold up on its own. It
  supports making verification a structural part of the app.

**ASIC summarisation trial (Jan–Feb 2024, AWS, Llama2-70B)**
- AI summaries of submissions scored **47%** against **81%** for human summaries.
- ASIC concluded that generative AI should "augment and not replace" human work.
- Sources: [Crikey, 2024-09-03](https://www.crikey.com.au/2024/09/03/ai-worse-summarising-information-humans-government-trial/); [ACS Information Age](https://ia.acs.org.au/article/2024/humans-outperform-ai-in-australian-govt-trial.html) (2024).
- **For our pitch:** an Australian government test of exactly this task.

**Robodebt Royal Commission (report 2023-07-07)**
- Recommendation 17.1: "a clear path for those affected by decisions to seek review"; business rules
  "available … to enable independent expert scrutiny".
- Sources: [APH FlagPost](https://www.aph.gov.au/About_Parliament/Parliamentary_departments/Parliamentary_Library/Research/FlagPost/2023/July/Robodebt-RC-legislative-recommendations) (2023-07); [Govt response](https://www.pmc.gov.au/sites/default/files/resource/download/gov-response-royal-commission-robodebt-scheme.pdf).
- **For our pitch:** supports an audit trail of what the human actually read.

**NT Government AI Policy (published 2026-06-05)**
- Officers "must not enter or upload personal or sensitive information into public or third-party AI tools".
- Officers "must validate AI-generated content for accuracy, bias, relevance and appropriateness before use".
- Microsoft Copilot with enterprise data protection is endorsed.
- Systems with material effect must be assessed under the AI Assurance Framework.
- Source: [dcdd.nt.gov.au](https://dcdd.nt.gov.au/publications/artificial-intelligence-policy), read 2026-10-03 via r.jina.ai.
- **For our pitch:** the demo should use synthetic or de-identified documents. A local checker, or local
  summarisation, is the policy-consistent design.

**NT AI Assurance Framework (Nov 2025; page updated 2026-06-05)**
- Staff "retain ultimate responsibility for decisions using AI. This requires meaningful human oversight
  and clear lines of accountability".
- There must be "clear mechanisms" to "question and challenge AI-assisted outcomes". Medium- and
  high-risk projects are supported by an NT AI advisory service.
- Source: [digitalterritory.nt.gov.au](https://digitalterritory.nt.gov.au/digital-government/strategies-and-guidance/policies-standards-and-guidance/artificial-intelligence-assurance-framework).
- **For our pitch:** use these exact words. The judges include NT AI advisory staff.

**DTA Policy for the responsible use of AI in government v2.0 (effective 2025-12-15)**
- Requires an accountable official, a use-case register, an impact assessment before deployment, and a
  transparency statement.
- It applies to non-corporate **Commonwealth** entities, **not to the NT**.
- Source: [digital.gov.au](https://www.digital.gov.au/ai/ai-in-government-policy), updated 2025-12-01.
- **For our pitch:** cite it as national context only.

**UK social work: Ada Lovelace Institute "Scribe and prejudice?" (2026-02-11)**
- Based on interviews with 39 social workers and senior staff.
- In one pilot, "time was saved generating documentation, this was offset by the time taken to check
  the documentation for hallucinations".
- Human-in-the-loop practice "var[ies] significantly".
- Sources: [report](https://www.adalovelaceinstitute.org/report/scribe-and-prejudice/). Press examples
  (invented suicidal ideation; "fishfingers or flies or trees"): [Local Government Lawyer](https://www.localgovernmentlawyer.co.uk/adult-social-care/391-adult-care-news/99712-ai-transcription-tools-in-social-work-introducing-new-risks-to-people-and-society-such-as-bias-and-hallucinations-report-warns), read 2026-10-03.
- **For our pitch:** checking time eats the speed gain. Our app has to make checking *cheap*, not just
  *mandatory*.

---

## 6. Gaps: what nobody surveyed does yet

These come from finding nothing in this survey, not from proof that nothing exists. The search for tools
that force verification ([web_ara.py and gh search](#sources), 2026-10-03) returned only checklists and
blog posts.

- **G1. Reading as a precondition.** Every tool in section 1 makes checking the source a click the user
  may skip. None found requires the human to open the critical passages before the summary can be used
  or signed off.
- **G2. "Cited" vs "supported" made visible.** The products show a link. None found shows the user an
  independent per-claim support verdict against *their own document*:
  - Gemini double-check used the web and its current status is unclear.
  - The Azure, Vertex and Bedrock checks are developer APIs, not caseworker screens.
  - Claude only guarantees that the pointer is valid.
- **G3. Omissions.** Linking claims to sources cannot show what the summary left out. Fox et al. (2026)
  show that judges miss omissions unless they first list the source's facts. No product found surfaces
  "critical passages the summary did not use".
- **G4. Proof of verification.** No product found records which passages the human actually read before
  signing off. The NT framework asks for "clear lines of accountability". OVIC could not establish what
  had been checked.
- **G5. Measured vigilance.** Planted-error checks of reviewers exist only in research (Goulas 2026;
  Fox 2026). No product was found that occasionally plants a known-false claim to show the reviewer, or
  their supervisor, whether verification is really happening. **Lead only:** idea-level, not checked
  against the ethics of doing this to staff.

---

## 7. Contradictions (reported, not resolved)

- **Gemini double-check:** described as a live feature in secondary sources, but absent from the current
  help page (both read 2026-10-03).
- **Laya context:** the model card says English is 512 tokens. The README says the multilingual
  checkpoint reads 8,192, with accuracy that varies above about 4,000 tokens. The astgl post cites a
  "1,024-token limit". Each source seems to describe a different checkpoint or default.
- **Consult acceptance numbers:** 60% exact agreement and 23 s (2025-05-14 evaluation) against
  "73% unchanged, 19 s" (DWP evaluation, unverified). Probably two different evaluations.
- **Do citations help?** Citations lower overreliance in the 2026 review (Blanchard), but raise blind
  trust even when random (Ding 2025). The difference seems to be whether people actually check.

## 8. Unknown: TBD, needs validation

- **Jev or Laya accuracy on claim support.** Settled by the 50-pair spike in section 4.
- **Jev access before 8 Oct, and where its data is processed.** Settled by trying the waitlist and the
  reseller, and by reading the DPA.
- **Whether Magic Notes, Harvey or Hebbia link claims to source passages.** Settled by their product docs.
- **Bespoke-MiniCheck speed on Tarık's RTX 5060 for a 20-page document.** Settled by a local run.
- **The primary source for the code-review habituation study.**

---

## Suggested first try (a suggestion, not a decision)

Build a three-layer check in Python:
1. **Summary with sentence-level citations.** Claude Citations, or a local model with a quote-only prompt.
2. **Independent support score per claim.** MiniCheck-Flan-T5-L, or Bespoke-MiniCheck through Ollama:
   local, maintained by a leaderboard, built for this task.
3. **A reading gate.** Claims that score low on support, and source passages the summary did not use
   but that look risk-critical (G3), must be opened before sign-off. The app logs what was read (G4).

**Why this design:** it answers G1–G4, follows the research (make verification cheap, show quotes not
explanations, force only where it matters), and keeps case text local, as the NT AI Policy requires.

**Where Jev and Laya fit:** a side spike. Do not put them on the critical path until the 50-pair test
says they match MiniCheck.

## Where this belongs

- **Blueprint → Riskiest assumption:** that a reading gate on flagged passages costs less time than it
  saves. The Ada Lovelace finding is the warning.
- **Blueprint → Stack (Why column):** MiniCheck vs Laya vs Jev as the support checker, using the
  section 3–4 table.
- **Blueprint → Constraints:** no real case data sent to cloud models, per the NT AI Policy (2026-06-05).
- **Blueprint → Decisions (open question):** whether summarisation itself runs in the cloud (Claude
  Citations) or locally.
- **Pitch:** sections 2 and 5. The report and slides are the teammate's; Tarık decides what to pass on.

## Sources

- https://platform.claude.com/docs/en/build-with-claude/citations — read 2026-10-03
- https://support.google.com/notebooklm/answer/16179559?hl=en — read 2026-10-03
- https://news.adobe.com/news/news-details/2024/adobe-brings-conversational-ai-to-trillions-of-pdfs-with-the-new-ai-assistant-in-reader-and-acrobat — 2024-02-20
- https://www.techloy.com/google-gemini-introduces-double-check-response-feature-to-verify-the-accuracy-of-gemini-ai-responses/ — read 2026-10-03
- https://support.google.com/gemini/answer/14143489?hl=en-gb — read 2026-10-03
- https://elicit.com/ — read 2026-10-03
- https://www.cambridge.org/core/journals/research-synthesis-methods/article/using-elicit-ai-research-assistant-for-data-extraction-in-systematic-reviews-a-feasibility-study-across-environmental-and-life-sciences/C97DAEC70C3173A260F0B12E729E7250 — 2026-05-29
- https://dho.stanford.edu/wp-content/uploads/Legal_RAG_Hallucinations.pdf — JELS 2025 (accepted 2025-03-14)
- https://support.microsoft.com/en-us/office/chat-with-copilot-about-your-word-document-4482c688-a495-4571-bfcd-4a9fc6608090 — read 2026-10-03 (search excerpt only)
- https://ai.gov.uk/blogs/evaluating-consult-an-ai-tool-for-enhanced-public-consultation-analysis/ — 2025-05-14
- https://ai.gov.uk/docs/DWP_pathways_to_work_evaluation_report.pdf — not opened (403), read 2026-10-03
- https://magicnotes.ai/ — read 2026-10-03 (search excerpt)
- https://healthinnovation-kss.com/ai-scribe-reduces-admin-time-by-almost-50-in-adult-social-care-assessments-independent-evaluation/ — read 2026-10-03 (search excerpt)
- https://www.communitycare.co.uk/content/news/ai-tool-improves-direct-work-in-adult-social-care-despite-accuracy-concerns-practitioners-report — 2025-02-10
- https://www.hebbia.com/ — read 2026-10-03
- https://arxiv.org/abs/2304.09848 — 2023-04-19
- https://arxiv.org/abs/2501.01303 — 2025-01-02
- https://arxiv.org/abs/2411.17375 — 2024-11
- https://arxiv.org/abs/2212.06823 — 2022-12-13
- https://scholar.harvard.edu/zbucinca/publications/trust-or-think-cognitive-forcing-functions-canreduce-overreliance-ai-ai — CSCW 2021, read 2026-10-03
- https://facctconference.org/static/pdfs_2022/facct22-3533193.pdf — FAccT 2022
- https://facctconference.org/static/papers24/facct24-56.pdf — FAccT 2024
- https://www.microsoft.com/en-us/research/publication/effects-of-llm-based-search-on-decision-making-speed-accuracy-and-overreliance/ — CHI 2025
- https://arxiv.org/abs/2412.15584 — 2024-12-20, v3 2025-10-29
- https://www.microsoft.com/en-us/research/wp-content/uploads/2025/01/lee_2025_ai_critical_thinking_survey.pdf — 2025-01 (CHI 2025)
- https://arxiv.org/abs/2601.11387 — 2026-01-16
- https://arxiv.org/abs/2606.23491 — 2026-06-22, rev. 2026-07-30
- https://arxiv.org/abs/2608.31016 — 2026-08-31
- https://pmc.ncbi.nlm.nih.gov/articles/PMC13248211/ — 2026-06-09
- https://tianpan.co/blog/2026/04/15/human-in-the-loop-rubber-stamp — 2026-04-15 (lead only)
- https://github.com/Liyan06/MiniCheck — last commit 2025-08-27, checked 2026-10-03
- https://llm-aggrefact.github.io/ — read 2026-10-03
- https://huggingface.co/bespokelabs/Bespoke-MiniCheck-7B — read 2026-10-03
- https://ollama.com/library/bespoke-minicheck — read 2026-10-03
- https://huggingface.co/vectara/hallucination_evaluation_model — read 2026-10-03
- https://github.com/vectara/hallucination-leaderboard — pushed 2026-09-23
- https://github.com/ibm-granite/granite-guardian — pushed 2026-08-26
- https://github.com/yuh-zha/AlignScore — last commit 2024-03-11
- https://github.com/tingofurro/summac — last commit 2025-01-30
- https://learn.microsoft.com/en-us/azure/ai-services/content-safety/quickstart-groundedness — read 2026-10-03 (search excerpt)
- https://docs.cloud.google.com/generative-ai-app-builder/docs/check-grounding — read 2026-10-03 (search excerpt)
- https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-contextual-grounding-check.html — read 2026-10-03 (search excerpt)
- https://docs.typesafe.ai/api — read 2026-10-03
- https://docs.typesafe.ai/patterns — read 2026-10-03
- https://docs.typesafe.ai/legal — read 2026-10-03
- https://typesafe.ai/ — published 2026-09-28
- https://runtimewire.com/article/typesafe-jev-system-one-ai-model-early-access — 2026-09-15
- https://www.eesel.ai/blog/typesafe-jev-pricing — 2026-09-21
- https://docs.aimlapi.com/api-references/decision-models/typesafe/jev — read 2026-10-03
- https://huggingface.co/convaiinnovations/laya — read 2026-10-03
- https://pypi.org/project/laya/ — 0.3.23 uploaded 2026-10-01
- https://github.com/harrymunro/jev-laya-benchmark — read 2026-10-03
- https://news.ycombinator.com/item?id=49806080 — 2026-09-22
- https://astgl.com/p/local-laya-vs-hosted-jev-typed-decisions — 2026-09-22
- https://news.ycombinator.com/item?id=49896979 — 2026-09-29
- https://ovic.vic.gov.au/wp-content/uploads/2024/11/DFFH-ChatGPT-investigation-report-20240924-Re-upload.pdf — 2024-09-24
- https://ovic.vic.gov.au/mediarelease/ovic-finds-department-responsible-for-breaches-of-privacy-through-use-of-chatgpt/ — 2024-09-24
- https://www.crikey.com.au/2024/09/03/ai-worse-summarising-information-humans-government-trial/ — 2024-09-03
- https://ia.acs.org.au/article/2024/humans-outperform-ai-in-australian-govt-trial.html — 2024
- https://www.aph.gov.au/About_Parliament/Parliamentary_departments/Parliamentary_Library/Research/FlagPost/2023/July/Robodebt-RC-legislative-recommendations — 2023-07
- https://www.pmc.gov.au/sites/default/files/resource/download/gov-response-royal-commission-robodebt-scheme.pdf — read 2026-10-03
- https://dcdd.nt.gov.au/publications/artificial-intelligence-policy — published 2026-06-05
- https://digitalterritory.nt.gov.au/digital-government/strategies-and-guidance/policies-standards-and-guidance/artificial-intelligence-assurance-framework — Nov 2025, page updated 2026-06-05
- https://www.digital.gov.au/ai/ai-in-government-policy — v2.0 effective 2025-12-15, updated 2025-12-01
- https://www.adalovelaceinstitute.org/report/scribe-and-prejudice/ — 2026-02-11
- https://www.localgovernmentlawyer.co.uk/adult-social-care/391-adult-care-news/99712-ai-transcription-tools-in-social-work-introducing-new-risks-to-people-and-society-such-as-bias-and-hallucinations-report-warns — read 2026-10-03

When you rewrite this, keep each link and date beside its claim and paste the Sources block unchanged.
