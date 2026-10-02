# Survey: UI patterns, working logic and v1 gaps for source-linked case summaries (brief 6)

Written 2026-10-03 by the `research` skill (one Opus worker, then a citation pass). This is input for
decisions, not a decision. Nothing here has been written into Blueprint, `notes.md` or a task file.
It covers new ground only; "LS" means `reports/2026-10-03-landscape-verified-summaries.md`.

**Citation pass:** see the section "Citation pass" at the end. A claim it could not re-find is marked there.

---

## Item 1: What users see and do in shipped products

| Product | Claim: what the user sees and does | Verdict | Source (date) | What it changes for us |
|---|---|---|---|---|
| Gemini Notebook | "To get the full quoted text, hover over any citation." Selecting a citation lets the user "navigate directly to the quote and review it in context". When a response is saved as a note, the "clickable inline citations" are kept. | confirmed | https://support.google.com/notebooklm/answer/16179559?hl=en (read 2026-10-03) | This is the baseline the judges know. Our reader has to at least do hover preview and jump-to-context. |
| Adobe Acrobat AI Assistant | Selecting a citation opens the source "with the relevant content highlighted". "Citations remain available when you resume a chat". The page also says: "Citations identify the content used to support a response, but they do not guarantee that the response is complete or correct." | confirmed | https://helpx.adobe.com/knowledge-base/web/user-guide-getting-started/ai-assistant-and-insights/chat-citations.html (updated 2026-09-23, read via r.jina.ai) | The vendor itself says a citation does not mean the answer is complete. That supports our omission check. |
| Copilot in Word (summary and chat) | Shows "references with citations". It "doesn't always provide citations to later document content". "If those answers aren't in the document, Copilot will generate content for you using the underlying large language models." | confirmed | https://support.microsoft.com/en-us/word/copilot/create-a-summary-of-your-document-with-copilot-in-word ; https://support.microsoft.com/en-us/office/chat-with-copilot-about-your-word-document-4482c688-a495-4571-bfcd-4a9fc6608090 (neither page dated, read 2026-10-03) | The NT-endorsed tool fills gaps from the model rather than saying "not in the file". That is a ready contrast for the pitch. |
| Microsoft Copilot application card | Copilot "may include information in its response that isn't present in its input sources". Uses that affect access to "housing, insurance, social welfare benefits" are listed under limitations to avoid. | confirmed | https://learn.microsoft.com/en-us/microsoft-365/copilot/microsoft-365-copilot-application-card (ms.date 2026-08-18, updated 2026-09-08) | Microsoft itself names housing and welfare decisions as the risky use. A strong line for the pitch. |
| Microsoft Legal Agent (Frontier, in Word) | It can "ingest your playbook, break it down into a series of instructions". Each topic is coloured gray (not relevant), green (complies), light red (needs a change) or dark red (whole clause to add or remove). Numbered citations "highlight the areas of the document". Edits arrive as tracked changes via Accept or "Accept with Comment". | confirmed | https://support.microsoft.com/en-us/word/get-started-with-the-legal-agent-frontier (no date, read 2026-10-03) | The closest shipped version of a per-clause evidence map. Its colour means compliance, not confidence. |
| Perplexity | "Every Perplexity answer links to numbered citations: hover to preview it, or click through". Users can "highlight answer text to check the sources referenced". Sources carry "Government, Academic, and Trusted" labels. | confirmed (vendor page) | https://www.perplexity.ai/hub/getting-started (read 2026-10-03 via r.jina.ai) | Reverse lookup (select text, see its sources) is an established pattern. |
| Elicit | In screening, "every decision shows the quote from the paper behind it". The reviewer sees "per-criterion decisions, exclusion reasons, and source quotes". Override is Include/Exclude, and "Excluding a paper also prompts for an exclusion reason". Clicking an extraction cell shows its supporting quotes. CSV export. | confirmed | https://support.elicit.com/en/articles/14759154-systematic-reviews-in-elicit ("updated over 2 weeks ago", read 2026-10-03) | Override-with-reason already ships, in a criterion-structured tool. |
| Harvey Review Tables | Moved to "sentence-based citations". Each result has an Answer and a Reasoning. Rows can be assigned and cells flagged. There are filters for "(un)verified, (un)flagged, and (un)assigned" and a status panel counting cells or rows that are "assigned, verified, or flagged". Users triage with red, orange and yellow flags. | confirmed | https://www.harvey.ai/blog/rebuilding-harveys-review-algorithm (2026-04-21); https://www.harvey.ai/blog/the-brief-aug-2025 (2025-08-05); https://www.harvey.ai/blog/collaborative-review-tables (2026-04-15) | A per-item human "verified" status with progress counts is standard in legal review. Our reading receipt is stronger because it records opening, not a tick. This **partly overlaps LS gap G4**. |
| CoCounsel Legal | "linked citations for verification". Tabular Analysis runs up to 10,000 documents against 100 questions, "every answer traceable back to its source". | confirmed (vendor page) | https://legal.thomsonreuters.com/en/products/cocounsel-legal (read 2026-10-03) | The grid-of-questions pattern again. |
| Hebbia Matrix | A grid (documents × questions) where hovering shows the highlight in the original. | **unknown** for the UI: secondary sources only | Mechanism in item 6 | Do not cite Hebbia's UI. |
| Abridge | The user highlights note text and "The corresponding passage in the transcript will be highlighted automatically in the Transcript & Linked Evidence panel". To hear it, "double-click the highlighted transcript passage or select the Play button". | confirmed | https://support.abridge.com/hc/en-us/articles/30235128433811-Verify-a-Note-With-Linked-Evidence (no date, read 2026-10-03 via r.jina.ai) | Side panel plus raw-evidence replay is the clinical standard. |
| Dragon Copilot | "Summarize evidence" gives insights "with referenced evidence from the transcript and draft note". The system "Includes a timeline of activities and versioning". Deployer guidance: "The UI should indicate AI‑generated sections distinctly and provide one‑click access to the source transcript." Limitations named: "omitted findings or hallucinated details". | confirmed | https://learn.microsoft.com/en-us/industry/healthcare/dragon-copilot/whitepapers/transparency (ms.date 2026-01-02, updated 2026-08-04) | Timeline and versioning are an audit-log pattern. Marking AI text distinctly is vendor guidance. |
| Beam Notes (formerly Magic Notes) | The whole transcript and audio open from a "Recording" button, with speaker timestamps; links are not per sentence. "Checking your work" runs an automated check against the source for "Clinical information, Risk factors, Safeguarding status". If it corrects something, "a notification banner will appear". "Source Check" audits uploaded information "against what your chosen template expects to find" and lists "missing data". | confirmed | https://magicnotes.zendesk.com/hc/en-gb/articles/4582767777695-Access-Your-Beam-Note-Transcript-and-Audio ; https://magicnotes.zendesk.com/hc/en-gb/articles/6196953197471-Checking-Your-Work ; https://magicnotes.zendesk.com/hc/en-gb/articles/4929025306527-How-to-use-the-Source-Check-Feature (no dates, read 2026-10-03 via r.jina.ai) | The social-care incumbent auto-corrects rather than making the human check. Its template coverage check **partly contradicts LS gap G3**: a shipped product does list missing items, though against a template, not unused source passages. |
| ChatGPT (uploaded files) | A user reported ChatGPT "falsely attributing a specific sentence to my uploaded files" and insisting the quote existed. | practice finding (one user) | https://community.openai.com/t/fabricated-citations-from-project-documents/1260660 (2025-05-14) | Supports checking quotes in code. ChatGPT's current file-citation UI is **TBD**: the help pages returned 403. |
| Claude consumer app | Citation UI | **unknown** | none found | The API mechanism is in item 6. |

**Pattern matrix.** Only from the rows above; "not found" means not in the pages read.

| Pattern | Seen in | Not found |
|---|---|---|
| Source pane next to the output | Abridge panel, Gemini Notebook in-context view, Acrobat highlighted file | Perplexity (opens a new tab) |
| Inline quote or hover preview | Gemini Notebook, Perplexity, Elicit (cell to quote) | — |
| Colour for model confidence | **none** in shipped products read. Legal Agent colour = compliance; Harvey flags = user triage | Research only (LS: Spatharioti; item 2: Do et al.) |
| Human "verified" tick | Harvey verify; Elicit Include/Exclude | — |
| Human edit or override | Abridge (edit note), Elicit (with reason), Legal Agent (Accept with Comment), Harvey | — |
| Export with citations | Gemini Notebook notes; Harvey Review table export with a reference-snippet column ([The Brief, 2025-08-05](https://www.harvey.ai/blog/the-brief-aug-2025)); Elicit CSV (whether quotes are included: TBD) | — |
| Audit log | Dragon Copilot timeline and versioning; Harvey status counts | **No product logs which sources the user opened.** G4 stands. |
| Automated support check before review | Abridge detector; Beam Checking your work | Most products show links only |

---

## Item 2: Research prototypes and user studies

| Claim | Verdict | Source (date) | What it changes |
|---|---|---|---|
| **Traceable Text.** Summary and source side by side. Claims are light blue; hovering a claim highlights its source passage, and hovering a passage highlights its claim (backlinks). N=20, within-subjects. Questions about hallucinations were answered correctly **70% with links vs 12.5% without**, in **1.8 vs 2.9 min**. On verified summaries: 90% vs 75% (p=.08, not significant). No difference in confidence. | confirmed in two versions | https://arxiv.org/abs/2409.13099 (2024-09-19); CHI EA 2025 PDF https://andrewhead.info/assets/pdf/traceable-text.pdf (DOI https://dl.acm.org/doi/10.1145/3706599.3719830) | The strongest measured case for two-way hover links, and cheap in HTML. |
| Traceable Text link quality: of 159 links, **129 (81%) fully correct, 18 (11%) with semantic issues, 12 (8%) wrong**. The authors say the study "does not examine adverse effects ... like potentially disincentivizing complete reading of a source text." | confirmed | same | Even a GPT-4 prompt chain mislinks about 1 in 5. Our code check and separate checker answer this. |
| **Attribute First, then Generate.** Select source spans, then plan sentences, then generate each sentence from its spans. Citations are about 45× shorter. Human fact-check time fell from **47 to 22 s** (multi-document summaries) and **59 to 35 s** (long-form QA). About 42% of sentences judged "unsupported" were partly supported by adjacent text. | confirmed | https://arxiv.org/abs/2403.17104 (2024-03-25, ACL 2024) | Writing the quote first and the claim second mirrors this. Shorter evidence means faster checks. |
| **VeriTrail.** Sentence IDs are assigned in code; "If a returned ID does not match an assigned ID, it is discarded". Verdicts are Fully Supported, Not Fully Supported or Inconclusive. It traces claims back through intermediate outputs. "research purposes only". | confirmed | https://www.microsoft.com/en-us/research/blog/veritrail-detecting-hallucination-and-tracing-provenance-in-multi-step-ai-workflows/ (2025-08-05); https://arxiv.org/abs/2505.21786 (May 2025, ICLR 2026) | Same ID-validation trick as our passage-id check. Adds a third verdict, "Inconclusive". |
| **Do et al.**, N=104 scenario study. Users preferred phrases colour-coded by factuality score. "participants increased their trust ratings when relevant sections of the source material were highlighted" or when reference numbers were added. | confirmed (abstract) | https://arxiv.org/abs/2405.20434 (2024-05-30, CHI 2024 TREW workshop) | Highlighting raises trust. The study measured trust, not accuracy, so it is a complacency warning for our UI. |
| **U-Lens**, N=18, compared with a confidence-cue baseline. Prioritised "inspection targets" with response options "improved verification efficiency and effort allocation, reduced perceived workload". | confirmed (the abstract gives no numbers) | https://arxiv.org/abs/2607.10604 (2026-07-12, v2 2026-09-11) | A prioritised list of what to inspect beats raw confidence colours. Supports a flagged-first queue. |
| **Verifiable EHR summaries**, 8 physicians. References were appended at the end of the summary. When physicians chose to use the summary: accuracy 88.0% vs 86.4% (p=0.51). Arm level, Summary+EHR vs EHR only: 86.7% vs 88.1% (p=0.42), so the summary arm was slightly lower. Time 9.45 vs 10.30 min (p=0.46). | confirmed (arm-level result added in the citation pass) | https://pmc.ncbi.nlm.nih.gov/articles/PMC12155021/ (medRxiv 2025-06-03) | End-of-summary references showed no gain. *Inference:* links have to sit on the claim. |
| **Citation granularity.** Forcing sentence-level citations "forfeits gains of 2-97% (median 40%)" in attribution quality; quality peaks at paragraph level. | confirmed | https://arxiv.org/abs/2604.01432 (2026-04-01) | **In tension with** Attribute-First, where finer citations made human checks faster. *Inference:* a paragraph-level passage id with a verbatim quote inside sits in the middle. |
| Deep-research agents: even the strongest frontier models keep link validity >94% and relevance >80%, yet reach only **39–77% factual accuracy**. 14 LLMs were benchmarked; fewer than half of the open-source models produced cited reports at all. | confirmed (wording corrected in the citation pass) | https://arxiv.org/abs/2605.06635 (2026-05-07) | A valid pointer is not support. This justifies the separate checker. |
| Planted errors in 90 synthetic oncology discharge summaries: Gemini 2.5 Pro found **97.8%**; six specialists averaged **47.8%**. | confirmed via abstract (full text blocked) | https://portal.fis.tum.de/en/publications/artificial-intelligenceassisted-error-detection-in-complex-clinic/ (Jan 2026); article https://ascopubs.org/doi/10.1200/CCI-25-00194 | Humans miss about half of planted errors even when they are looking. Supports flagging and a planted-error evaluation. |

---

## Item 3: Output structured per criterion instead of free bullets

| Claim | Verdict | Source (date) | What it changes |
|---|---|---|---|
| **TrialGPT** outputs, for each criterion, an explanation, "the locations of relevant sentences in the patient notes" and a label. Inclusion labels: {Included, Not included, **Not enough information**, Not applicable}. Criterion-level accuracy 0.873 vs experts 0.887–0.900. User study with **2 doctors**: about **42.6% time saved**, accuracy 97.2% vs 91.7%. The largest error causes were incorrect reasoning (30.7%) and ambiguous definitions (26.9%). | confirmed | https://pmc.ncbi.nlm.nih.gov/articles/PMC11574183/ (2024-11-18) | Gives us the model: sentence-ID evidence per clause plus a "not enough information" state. The user study is very small. |
| **Oncology prescreening RCT**, 355 charts, criterion-level extraction with traceability to source. Accuracy: Human+AI **76.1%**, human alone 71.5%, AI alone 59.9%. Time **37.4 vs 37.8 min**, no difference. Automation bias appeared only on ECOG, "due to the substantial inaccuracy of the AI". | confirmed | https://pmc.ncbi.nlm.nih.gov/articles/PMC12976108/ (2026-02-03) | Criterion structure helped accuracy, not speed. Where the AI was bad on one criterion, humans followed it, so per-criterion flags matter. |
| Elicit screening: criteria applied per paper, failing any one excludes, every decision carries a quote, the human can override with a reason. | confirmed | Item 1 row | Shipped precedent. |
| Microsoft Legal Agent: playbook turned into instructions, one compliance colour per topic, citations, tracked-change fixes. | confirmed | Item 1 row | Shipped precedent in Word. |
| LegalOn "flags risk with citations" against attorney-built playbooks. | lead only (vendor marketing, search excerpt) | https://www.legalontech.com/post/best-ai-contract-review-tools (read 2026-10-03) | Do not cite. |
| Beam Source Check lists missing items against a template. | confirmed | Item 1 row | A coverage check is shipped in social care. |
| **Nava caseworker chatbot RCT**, 125 caseworkers. Accuracy "estimated to improve ... by an average of 40%". RAG with "direct source citations". Accuracy when the chatbot was wrong is not reported. | confirmed | https://www.navapbc.com/case-studies/evaluating-ai-assistive-chatbot-caseworkers (2026-03-18) | The nearest caseworker RCT. It is not criterion-structured and says nothing on overreliance. |
| **Evaluative AI** (show evidence for and against, not a recommendation). Miller's position paper: https://arxiv.org/abs/2302.12389 (2023-02-24). Le et al. report "promising results in improving human decisions" (domains: housing *price prediction* and skin cancer). Kornowicz found "no significant improvement in decision-making performance and limited user engagement with the evidence". | **contradicted**: the two studies disagree | https://arxiv.org/abs/2402.01292 (v1 2024-02-02, v4 2025-08-27); https://arxiv.org/abs/2411.08583 (2024-11-13) | Showing the evidence does not make people engage with it. That argues for our open-before-sign-off forcing. |

---

## Item 4: Framing, bullet summary (a) or per-clause evidence map (b)

What the evidence shows:
- **Tools built for decisions are structured per criterion or question** with evidence in each cell: Harvey, Elicit, TrialGPT, the Legal Agent, CoCounsel Tabular Analysis and Beam's template. Free text with citation chips is the pattern for general Q&A: Gemini Notebook, Acrobat, Copilot chat, Perplexity (item 1).
- **Links on the claim help; references at the end did not.** Traceable Text: 70% vs 12.5% on hallucination questions. EHR study: no gain (item 2).
- **Criterion structure brings modest accuracy gains with mixed time effects.** TrialGPT: −42.6% time (2 doctors). Oncology RCT: no time change (item 3).
- **Omissions only become visible against a checklist.** TrialGPT's "Not enough information", the Legal Agent's dark red, Beam's Source Check, and LS Fox 2026.
- **Risk:** an AI verdict per clause can turn into a recommendation the officer rubber-stamps. The Evaluative AI evidence is mixed, and LS Fogliato shows anchoring.

*Inference (worker):* (b) fits the brief better as the primary output. The per-clause map holds the evidence:
quotes, support status, and "not found in file". The bullet summary becomes a secondary narrative whose
bullets link into the map. The open choice for Tarık is who sets each clause's outcome:
- **The AI pre-fills a proposed status** (TrialGPT, Elicit, Legal Agent style). Faster, but a higher anchoring risk.
- **The officer sets the status from the evidence** (Evaluative AI style). More accountable, but Kornowicz found engagement can stay low.

---

## Item 5: Gap check for v1

| Feature | What comparable tools do | In our draft? | Safe to leave until after v1? (inference) |
|---|---|---|---|
| Human override of a claim or clause, with a reason | Elicit prompts for an exclusion reason; Legal Agent "Accept with Comment"; Harvey verify/edit/flag (item 1). The NT framework asks for ways to "question and challenge" (LS). | No | **No.** A select box plus a text field is cheap, it is the accountability story, and the reading receipt should record it. |
| Explicit "not found in the file" | TrialGPT "Not enough information"; Abridge "Unmentioned"; Copilot generates from the model instead (items 1, 3, 6) | Implicit only | **No.** The scenario turns on presence or absence (DFV letter, ledger). It is one more state. |
| Contradiction between passages (stale ledger p.8 vs p.23) | Abridge classifies "Contradiction" against the transcript (item 6) | No. *Inference:* a per-claim check against the claim's own cited passage passes a claim that p.23 contradicts. | Risky to defer, because the planted stale-value error depends on it. The cheap version: one clause → several passages, checked against each. |
| Exportable decision record | Elicit CSV; Gemini Notebook notes keep citations; Dragon timeline and versioning | Receipt logged; no export stated | Partly. A JSON or printable HTML receipt is enough for v1; a formatted PDF can wait. |
| Multi-PDF case file | Acrobat collections; CoCounsel 10,000 documents; Harvey Vault | Already 6 documents (file + 5 policies) | Yes. Multi-file upload can wait; passage ids must carry a document id. |
| Scanned PDF / OCR | Claude: scanned PDFs "are not citable" (https://platform.claude.com/docs/en/build-with-claude/citations, read 2026-10-03). Acrobat OCR is search-snippet only (lead). | No (the synthetic file is text) | Yes. Say in the pitch that real files contain scans. |
| Prompt injection hidden in case documents | See the next table | No | Partly; see the next table. |
| Accessibility | WCAG 1.4.1 (Level A): "Color is not used as the only visual means of conveying information" (https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html, read 2026-10-03). The DTA Digital Inclusion Standard asks for the "latest version of ... WCAG" for Commonwealth agencies (https://www.digital.gov.au/policy/digital-experience/digital-inclusion-standard/dis-criterion-4-make-it-accessible, read 2026-10-03 via r.jina.ai). Dragon Copilot claims WCAG 2.1 (white paper above). | Not specified | Mostly. Icon or text labels next to colour, and keyboard opening of passages, are cheap and belong in v1. A full audit can wait. |
| Time to process about 60 pages | Claude PDFs use "1,500–3,000 tokens per page" of text plus image tokens per page (https://platform.claude.com/docs/en/build-with-claude/pdf-support, read 2026-10-03). By arithmetic: roughly 90k–180k text tokens. Bespoke-MiniCheck: ">500 docs/min" on an A6000 with vLLM (https://huggingface.co/bespokelabs/Bespoke-MiniCheck-7B, read 2026-10-03). Practice: one kotaemon user went from under 20 s for 40 pages to 30 min for a 6-page résumé after a local Ollama change (https://github.com/Cinnamon/kotaemon/issues/634, 2025-01-17). | Not measured | Yes for optimisation: precompute the demo case. But end-to-end time on the RTX 5060 is **TBD — needs one local timed run**. |

**Prompt injection: incidents and guidance**

| Claim | Verdict | Source (date) |
|---|---|---|
| A self-represented litigant hid instructions in "3-point white font" telling an AI to side with him. Connecticut Superior Court revoked his e-filing. The court "does not use AI to process documents in any way". | confirmed | https://www.404media.co/person-hides-prompt-injection-in-legal-filing-telling-ai-to-side-with-them/ (2026-08-13). Memorandum dated 2026-08-06, linked from https://news.ycombinator.com/item?id=49334546 (2026-08-17); PDF not opened. |
| 18 arXiv manuscripts held hidden "positive review" prompts. | confirmed. **Contradiction:** the Nikkei count is 17 (secondary, lead). | https://arxiv.org/abs/2507.06185 (2025-07-08); https://the-decoder.com/researchers-hide-prompts-in-scientific-papers-to-sway-ai-powered-peer-review/ (read 2026-10-03) |
| OWASP LLM01:2025 includes summarising content with hidden instructions, and a résumé attack ("Scenario #6: Payload Splitting"). Mitigations include "Segregate and identify external content" and "Require human approval for high-risk actions". | confirmed (wording corrected in the citation pass) | https://genai.owasp.org/llmrisk/llm01-prompt-injection/ (2025 edition, read 2026-10-03) |
| PhantomLint detects hidden prompts in PDFs and HTML with a false-positive rate of about 0.092% on 3,402 documents. | confirmed | https://arxiv.org/abs/2508.17884 (2025-08-25, v2 2025-10-23) |
| ASD defines prompt injection as an attack that inserts "malicious instructions or hidden commands". The page lists no injection-specific mitigations. | confirmed | https://www.cyber.gov.au/business-government/secure-design/artificial-intelligence/engaging-with-artificial-intelligence (no date on page, read 2026-10-03 via r.jina.ai) |

*Inference:* our verbatim quote check would accept a quote taken from invisible text. A cheap guard would
flag tiny or white text at parse time, but that is **TBD — needs a spike**. A planted-injection page in the
synthetic file would make a strong demo for the NT AI-advisory judges. A full defence can wait until after v1.

---

## Item 6: How these tools work underneath

| Tool | How documents are split | How citations are produced | How the citation maps to a location | Support check | Documented failure |
|---|---|---|---|---|---|
| Claude Citations API | Plain text and PDF "chunked into sentences"; custom content blocks are used as-is | Model-native: the model "outputs citations in a standardized format that are then parsed into cited text and document location indices" | `char_location` (0-indexed character offsets), `page_location` (1-indexed pages), `content_block_location`; "guaranteed to contain valid pointers" | None | Scanned PDFs are not citable. Citations cannot be combined with structured outputs (HTTP 400). (https://platform.claude.com/docs/en/build-with-claude/citations, read 2026-10-03) |
| Claude launch post | — | "outperform most custom implementations, increasing recall accuracy by up to 15%"; Endex: source hallucinations went "from 10% to 0%" | — | — | **Date contradiction:** the page shows June 23, 2025 (https://claude.com/blog/introducing-citations-api), but HN/Ars coverage is from 2025-01-27 (https://news.ycombinator.com/item?id=42837946) |
| OpenAI file search | Vector store; chunking not stated on the page | Retrieve, then generate | `file_citation` with `file_id`, `filename` and `index` (a position in the output text); the docs example carries no quote field | None | (https://developers.openai.com/api/docs/guides/tools-file-search, read 2026-10-03) |
| Vertex AI check grounding | "a sentence is considered a single claim" | Post-hoc check of a finished answer | Claim positions plus citation indices into the supplied facts | Support score from 0 to 1; `citation_threshold` default 0.6; up to 200 facts of at most 10,000 characters each | (https://docs.cloud.google.com/generative-ai-app-builder/docs/check-grounding, updated 2026-09-30) |
| Harvey | — | Old method: "model-generated text and fuzzy matching". New: "pointing to indices throughout the document", sentence-level | Indices into the document | Preferred 4× over the old method in side-by-side tests | (2026-04-21, item 1 link) |
| Hebbia | "contextually dense ... components" smaller than the context window | Post-hoc: it "reverse engineer[s] the highlight worthy document text" from the final answer | Its patent describes per-cell scores that set highlight intensity; whether this shipped is unknown | — | (https://www.hebbia.com/blog/goodbye-rag-how-hebbia-solved-information-retrieval-for-llms, 2025-02-14; https://patents.google.com/patent/US12393788B2/en, granted 2025-08-19) |
| Abridge | Transcript plus audio timestamps | How Linked Evidence is aligned: **TBD, not public** | Note text maps to a transcript span and an audio time | Separate detector with five classes: Directly Supported, Reasonable Inference, Questionable Inference, Unmentioned, Contradiction. Plus a severity axis. Then correct, delete, or mark a false alarm. Catches 97% of confabulations vs GPT-4o's 82% on 10,000+ internal encounters. | (https://www.abridge.com/ai/science-confabulation-hallucination-elimination, 2025-08-19) |
| Dragon Copilot | — | "Context Grounding" restricted to note data | One-click to transcript (guidance) | Prompt-injection checks | "omitted findings or hallucinated details" (white paper, 2026-08-04) |
| Gemini Notebook | **TBD, not publicly documented** (only secondary blogs) | — | Jumps to the quote | — | — |
| TrialGPT | Patient-note sentences numbered | The model returns relevant sentence locations, a label and an explanation per criterion | Sentence IDs | Label set includes "not enough information" | 30.7% of errors are incorrect reasoning (item 3) |
| VeriTrail | Sentence IDs assigned in code | An LLM selects IDs; non-matching IDs are discarded | IDs | Three-way verdict | Research use only |
| Traceable Text | — | Three-prompt GPT-4 chain: summarise, segment into claims, map claims to passages | Passage spans | None | 19% of links imperfect |
| Attribute First | — | Select spans, then generate | Spans | — | About 42% of "unsupported" sentences partly supported |
| kotaemon (open source) | Retrieval chunks | A post-hoc LLM "CitationPipeline" returns evidence, then text matching highlights it in a PDF viewer | Text match | Relevance score | With Llama3.1-8B on Ollama the highlight worked "less than once in ten times" (https://github.com/Cinnamon/kotaemon/issues/541, 2024-12-02) |
| PyMuPDF (PDF coordinates) | — | — | `page.search_for()` returns rectangles around each hit; "The search is case insensitive" | — | (https://pymupdf.readthedocs.io/en/latest/tutorial.html, via Context7 index 2026-09-10) |
| Copilot (long documents) | — | — | — | — | It may "focus only on the beginning of the document and then ignore anything beyond that", with "less attention to content that was in the middle" (https://support.microsoft.com/en-us/microsoft-365-copilot/how-reference-and-document-lengths-affect-copilot-responses, read 2026-10-03) |

**Documented failure modes, in brief:**
- **Misattribution:** Traceable Text 8% wrong links; deep-research agents reach only 39–77% factual accuracy even for the strongest frontier models.
- **Fabricated quotes:** the ChatGPT practice report.
- **Quote drift with small models:** kotaemon #541.
- **Position effects:** Microsoft's own support page; Lost in the Middle (in the data survey).
- **Granularity trade-off:** arXiv 2604.01432.
- **Ungrounded additions:** the Microsoft application card.
- **Hidden text:** the Elliott case and the arXiv hidden prompts.

**The pipeline these tools share, and where our draft stands:**
1. Extract text (OCR if scanned) and split it into addressable units with stable IDs or offsets. **We have**
   passage ids. **We lack** OCR and a check that text is visible.
2. Select evidence, by retrieval or by reading the full context, sometimes before writing (attribute-first).
   **We have** full context. Quote-first ordering is optional.
3. Generate claims with pointers: model-native, prompted IDs, or post-hoc matching. **We have** the Claude
   writer producing a quote plus passage id.
4. Validate pointers, discarding IDs or quotes that are not in the source. **We have** the code verbatim check.
5. Score support per claim with NLI, a second model or a judge, sometimes graded or auto-corrected. **We have**
   MiniCheck yes/no. **We lack** graded classes (inference, unmentioned, contradiction) and checks across passages.
6. Map pointers to the display: character offsets, page plus rectangles, audio time. **TBD:** it is easy if we
   render our own HTML.
7. Human review: hover or click to source, verify, flag, edit, accept with comment, status counts, export.
   **We have** the sign-off lock, forced opening and the reading receipt, which are beyond the tools surveyed.
   **We lack** override-with-reason, an explicit "not found" state, two-way links and export.

**Unique to our draft:** a coverage check against each decisive policy clause (Beam and the Legal Agent do
this only against templates or playbooks), plus forced opening before sign-off.

---

## Discovery routes and what each added
- **WebSearch:** the product help pages, the papers (Traceable Text, VeriTrail, TrialGPT, the oncology RCT,
  Do et al.) and the injection incidents.
- **`web_ara.py` (DuckDuckGo):** the granularity paper (2604.01432) and the CHI EA DOI for Traceable Texts.
- **`hn_ara.py`:** the Elliott v NY Bariatric injection sanction (2026-08) and the Claude Citations launch
  coverage that exposed the date contradiction.
- **`gh search` repos and issues:** kotaemon and its issues #541 (highlights fail with small LLMs) and #634
  (local latency).
- **arXiv API:** the Evaluative AI papers, including the contradicting Kornowicz study, and the granularity
  abstract. The first combined query returned 0 results.
- **Context7 (`docs_ara`):** PyMuPDF `search_for` behaviour.
- **r.jina.ai:** the Abridge, Adobe, Beam, Perplexity, ASD and DTA pages, which blocked direct fetches.

## Suggested v1 screens (a suggestion, not a decision)
1. **Clause map** (home screen for a case). One row per decisive policy clause, with a status (met / not met /
   not enough information in file / not applicable), evidence chips, flags (unsupported, quote not found,
   unused critical passage, contradiction) and an "opened x of y required" counter. *Job: see where to look.*
2. **Evidence reader.** The claim or clause on the left; the source scrolled to the highlighted passage on the
   right; two-way hover links; the policy clause text alongside. Actions: confirm, dispute with a reason, mark
   unclear. *Job: check one item against the original.*
3. **Case summary** (secondary; could be a tab of screen 1). Bullets with citation chips and hover preview,
   each linking into the map. *Job: a quick overview for handover.*
4. **Sign-off and receipt.** Locked until the required passages have been opened. Shows the reading receipt
   (what was opened and when, overrides and their reasons) and exports the decision record. *Job: take the
   accountable decision.*

## Where this belongs
- **Blueprint → Decisions (open question):** framing (b) with the summary secondary; whether the AI pre-fills
  clause status or the officer sets it.
- **Blueprint → Constraints (candidate sentences):** "Colour is never the only signal." "Document text is
  treated as data, never as instructions."
- **Blueprint → Riskiest assumption:** checks across passages, for the stale-ledger case.
- **Not in v1:** OCR, multi-file upload, full injection defence.

## Unknowns (TBD — needs validation)
- **How Gemini Notebook and Abridge Linked Evidence work underneath.** Settled only if the vendors publish it.
- **ChatGPT and Claude.ai citation UIs.** Settled by their help pages; ChatGPT's returned 403.
- **Hebbia UI and Adobe OCR / 600-page limits.** Settled by primary pages; only secondary sources and a search
  snippet were found.
- **Whether the Elicit export includes quotes.** Settled by its export docs. (Harvey's does: settled in the citation pass.)
- **Bespoke-MiniCheck speed on the RTX 5060 and end-to-end time for 60 pages.** Settled by one local timed run.
- **Whether a visible-text check catches white or tiny text in our parser.** Settled by a short spike.

## Citation pass
A separate worker re-opened every cited page on 2026-10-03 and found the supporting sentence for all 20
deciding claims, plus spot-checks of the other rows. The corrections are already applied above:
- **Deep-research row:** reworded. The 39–77% is for the strongest frontier models.
- **EHR row:** arm-level result added (86.7% vs 88.1%, p=0.42).
- **OWASP row:** mitigation wording corrected.
- **Harvey export:** confirmed to include a citation snippet column.
- **ASD page:** re-dated to "no date on page".

Precision notes:
- **Traceable Text:** 21 people were recruited and 20 analysed. The "no difference in confidence" result is
  from arXiv v1; the CHI EA version reports difficulty instead (p=.24).
- **Adobe:** the highlighting sentence is about "Collection citations".
- **Abridge:** the two inference classes carry the prefix "Circumstantially Supported,".
- **Beam:** "Checking your work" is available only to UK, EU and US customers, which matters for an NT pitch.
- **Claude Citations launch post:** the date contradiction (page 2025-06-23 vs HN/Ars 2025-01-27) is real.

## Sources
- https://support.google.com/notebooklm/answer/16179559?hl=en — read 2026-10-03
- https://helpx.adobe.com/knowledge-base/web/user-guide-getting-started/ai-assistant-and-insights/chat-citations.html — updated 2026-09-23
- https://support.microsoft.com/en-us/word/copilot/create-a-summary-of-your-document-with-copilot-in-word — no date, read 2026-10-03
- https://support.microsoft.com/en-us/office/chat-with-copilot-about-your-word-document-4482c688-a495-4571-bfcd-4a9fc6608090 — no date, read 2026-10-03
- https://support.microsoft.com/en-us/microsoft-365-copilot/how-reference-and-document-lengths-affect-copilot-responses — no date, read 2026-10-03
- https://support.microsoft.com/en-us/word/get-started-with-the-legal-agent-frontier — no date, read 2026-10-03
- https://learn.microsoft.com/en-us/microsoft-365/copilot/microsoft-365-copilot-application-card — ms.date 2026-08-18, updated 2026-09-08
- https://www.perplexity.ai/hub/getting-started — read 2026-10-03 (r.jina.ai)
- https://support.elicit.com/en/articles/14759154-systematic-reviews-in-elicit — "updated over 2 weeks ago", read 2026-10-03
- https://www.harvey.ai/blog/rebuilding-harveys-review-algorithm — 2026-04-21
- https://www.harvey.ai/blog/the-brief-aug-2025 — 2025-08-05
- https://www.harvey.ai/blog/collaborative-review-tables — 2026-04-15
- https://legal.thomsonreuters.com/en/products/cocounsel-legal — read 2026-10-03
- https://www.hebbia.com/blog/goodbye-rag-how-hebbia-solved-information-retrieval-for-llms — 2025-02-14
- https://patents.google.com/patent/US12393788B2/en — granted 2025-08-19
- https://support.abridge.com/hc/en-us/articles/30235128433811-Verify-a-Note-With-Linked-Evidence — no date, read 2026-10-03 (r.jina.ai)
- https://www.abridge.com/ai/science-confabulation-hallucination-elimination — 2025-08-19
- https://learn.microsoft.com/en-us/industry/healthcare/dragon-copilot/whitepapers/transparency — ms.date 2026-01-02, updated 2026-08-04
- https://magicnotes.zendesk.com/hc/en-gb/articles/4582767777695-Access-Your-Beam-Note-Transcript-and-Audio — no date, read 2026-10-03
- https://magicnotes.zendesk.com/hc/en-gb/articles/6196953197471-Checking-Your-Work — no date, read 2026-10-03
- https://magicnotes.zendesk.com/hc/en-gb/articles/4929025306527-How-to-use-the-Source-Check-Feature — no date, read 2026-10-03
- https://community.openai.com/t/fabricated-citations-from-project-documents/1260660 — 2025-05-14
- https://arxiv.org/abs/2409.13099 — 2024-09-19
- https://andrewhead.info/assets/pdf/traceable-text.pdf — CHI EA 2025 (https://dl.acm.org/doi/10.1145/3706599.3719830)
- https://arxiv.org/abs/2403.17104 — 2024-03-25 (ACL 2024)
- https://www.microsoft.com/en-us/research/blog/veritrail-detecting-hallucination-and-tracing-provenance-in-multi-step-ai-workflows/ — 2025-08-05
- https://arxiv.org/abs/2505.21786 — May 2025 (ICLR 2026)
- https://arxiv.org/abs/2405.20434 — 2024-05-30
- https://arxiv.org/abs/2607.10604 — 2026-07-12, v2 2026-09-11
- https://pmc.ncbi.nlm.nih.gov/articles/PMC12155021/ — medRxiv 2025-06-03
- https://arxiv.org/abs/2604.01432 — 2026-04-01
- https://arxiv.org/abs/2605.06635 — 2026-05-07
- https://portal.fis.tum.de/en/publications/artificial-intelligenceassisted-error-detection-in-complex-clinic/ — Jan 2026 (article https://ascopubs.org/doi/10.1200/CCI-25-00194 blocked)
- https://pmc.ncbi.nlm.nih.gov/articles/PMC11574183/ — 2024-11-18
- https://pmc.ncbi.nlm.nih.gov/articles/PMC12976108/ — 2026-02-03
- https://www.navapbc.com/case-studies/evaluating-ai-assistive-chatbot-caseworkers — 2026-03-18
- https://arxiv.org/abs/2302.12389 — 2023-02-24
- https://arxiv.org/abs/2402.01292 — v1 2024-02-02, v4 2025-08-27
- https://arxiv.org/abs/2411.08583 — 2024-11-13
- https://www.legalontech.com/post/best-ai-contract-review-tools — read 2026-10-03 (search excerpt, lead only)
- https://platform.claude.com/docs/en/build-with-claude/citations — read 2026-10-03
- https://claude.com/blog/introducing-citations-api — page date 2025-06-23
- https://news.ycombinator.com/item?id=42837946 — 2025-01-27
- https://platform.claude.com/docs/en/build-with-claude/pdf-support — read 2026-10-03
- https://developers.openai.com/api/docs/guides/tools-file-search — read 2026-10-03
- https://docs.cloud.google.com/generative-ai-app-builder/docs/check-grounding — updated 2026-09-30
- https://huggingface.co/bespokelabs/Bespoke-MiniCheck-7B — read 2026-10-03
- https://github.com/Cinnamon/kotaemon — pushed 2026-07-14
- https://github.com/Cinnamon/kotaemon/issues/541 — 2024-12-02
- https://github.com/Cinnamon/kotaemon/issues/634 — 2025-01-17
- https://pymupdf.readthedocs.io/en/latest/tutorial.html — Context7 index 2026-09-10
- https://genai.owasp.org/llmrisk/llm01-prompt-injection/ — 2025 edition, read 2026-10-03
- https://www.404media.co/person-hides-prompt-injection-in-legal-filing-telling-ai-to-side-with-them/ — 2026-08-13
- https://news.ycombinator.com/item?id=49334546 — 2026-08-17 (memorandum PDF dated 2026-08-06, not opened)
- https://arxiv.org/abs/2507.06185 — 2025-07-08
- https://the-decoder.com/researchers-hide-prompts-in-scientific-papers-to-sway-ai-powered-peer-review/ — read 2026-10-03 (search excerpt)
- https://arxiv.org/abs/2508.17884 — 2025-08-25, v2 2025-10-23
- https://www.cyber.gov.au/business-government/secure-design/artificial-intelligence/engaging-with-artificial-intelligence — no date on page, read 2026-10-03
- https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html — read 2026-10-03
- https://www.digital.gov.au/policy/digital-experience/digital-inclusion-standard/dis-criterion-4-make-it-accessible — read 2026-10-03 (r.jina.ai)
