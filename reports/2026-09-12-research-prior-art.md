# Prior art, judges, and cultural safety — research items 5, 6, 8

Checked: **12 September 2026**. Method: each item stated as a falsifiable claim, checked
against the primary source where reachable. Several Australian Government domains
(industry.gov.au, digital.gov.au, dcdd.nt.gov.au, aiatsis.gov.au) returned HTTP 403 or
timed out to automated fetching on the check date; where that happened the claim is
marked **secondary-verified** and must be confirmed by opening the URL in a browser
before the citation goes in the report.

---

## Item 5 — Prior art

### 5a. Claim: the efficiency/equity trade-off in allocation has a named, citable cost, so our slider is not something we invented.
**Verdict: TRUE.** Bertsimas, Farias & Trichakis, "The Price of Fairness", *Operations
Research* 59(1):17–31, 2011, defines the *price of fairness* as the relative system
efficiency lost under a fair allocation versus the utilitarian optimum, for proportional
and max-min fairness, applied to communication networks, air transport and organ
transplantation. Sources (checked 2026-09-12):
<https://pubsonline.informs.org/doi/10.1287/opre.1100.0865>;
<https://dl.acm.org/doi/10.1287/opre.1100.0865>.
**What it changes:** our slider position is a *price of fairness* measurement. Report the
efficiency loss in the same currency as the equity gain (extra travel cost vs remote
median wait reduced) and cite this as the framing. It also gives Q&A a defensible answer
to "isn't this just arbitrary?" — no, it traces a known trade-off curve.

### 5b. Claim: presenting a Pareto front of equity-vs-efficiency to a human decision maker is established practice in public services.
**Verdict: PARTLY — the public-service-specific citation is TBD.** Fairness-aware
multi-objective optimisation is an active field ("Towards fairness-aware multi-objective
optimization", *Complex & Intelligent Systems*, 2024,
<https://link.springer.com/article/10.1007/s40747-024-01668-w>), and Pareto-front
trade-off curves shown to an aggregator so it can choose a fairness/efficiency balance
appear in energy allocation work (arXiv:2403.15616). I did **not** find a primary study of
a *human-set equity weight inside a public-service triage UI*. **TBD — needs validation**
if the report wants to claim precedent. Claim novelty of the *application*, not of the
method.

### 5c. Claim: Wachter et al. 2017 is the base citation for counterfactual explanations.
**Verdict: TRUE.** Wachter, Mittelstadt & Russell, "Counterfactual Explanations without
Opening the Black Box: Automated Decisions and the GDPR", *Harvard Journal of Law &
Technology* 31(2), 2018; preprint arXiv:1711.00399, posted 6 November 2017; SSRN 3063289.
Sources: <https://arxiv.org/abs/1711.00399>,
<https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3063289>.
**What we take:** the *unconditional counterfactual* — the smallest change to the world
that yields the desired outcome — delivered without exposing internal logic. That is
exactly the tenant view's sentence shape ("3rd instead of 14th if distance were ignored").

### 5d. Claim: counterfactual explanation of a *ranked list* is a distinct, less-settled sub-problem.
**Verdict: TRUE, and the gap is real.** Closest citable work: Tan, Xu, Ge, Li, Chen &
Zhang, "Counterfactual Explainable Recommendation", CIKM 2021, pp. 1784–1793, DOI
10.1145/3459637.3482420 (<https://dl.acm.org/doi/10.1145/3459637.3482420>). A survey of
contrastive/counterfactual explanation *for rankings* states that beyond Tan et al. (2021)
and Salimiparsa (2023) there is essentially no other contribution in the literature
("Evaluative Item-Contrastive Explanations in Rankings",
<https://arxiv.org/html/2312.10094>). Also relevant: Rorseth et al., CREDENCE,
counterfactual explanations for document ranking (arXiv:2302.04983).
**What it changes:** the honest positioning is "counterfactuals are well established for
classification, thin for rankings; our contribution is a ranking counterfactual a *tenant*
can read". Note our rank is a transparent weighted score, so the counterfactual is exact
rather than searched or approximated — say that; it is a genuine strength over the
ML-ranker literature.

### 5e. Claim: Ensign et al. 2018 is the canonical runaway-feedback-loop reference, and there is a public-enforcement follow-up.
**Verdict: TRUE, twice.** (1) Ensign, Friedler, Neville, Scheidegger &
Venkatasubramanian, "Runaway Feedback Loops in Predictive Policing", *Proceedings of the
1st Conference on Fairness, Accountability and Transparency*, PMLR 81:160–171, 2018
(<https://proceedings.mlr.press/v81/ensign18a.html>; arXiv:1706.09847). Proves the loop
mathematically and shows a black-box input change that stops it. (2) Altenburger & Ho,
"When Algorithms Import Private Bias into Public Enforcement: The Promise and Limitations
of Statistical Debiasing Solutions", *Journal of Institutional and Theoretical Economics*
175(1):98–122, 2019 — targeting food-safety *inspections* using consumer ratings
disproportionately harms Asian establishments, and a standard debiasing fix is shown to be
limited (<https://dho.stanford.edu/wp-content/uploads/JITE-FinalVersion.pdf>).
**What it changes:** Ensign is the model for our 90-day simulation (demand is observed
only where you go). Altenburger & Ho is the better citation for *inspection / service
allocation* specifically, and its "the obvious debias does not fix it" result is worth one
line — it is the argument for a human-owned weight rather than a statistical patch.

### 5f. Claim: Australia has published AI ethics principles and a government AI policy with human-oversight wording, and the NT has its own.
**Verdict: TRUE; exact wording secondary-verified only.**
- **Australia's AI Ethics Principles** (Dept. of Industry, Science and Resources), 8
  voluntary principles: human, societal and environmental wellbeing; human-centred values;
  fairness; privacy protection and security; reliability and safety; **transparency and
  explainability**; **contestability** ("when an AI system significantly impacts a person,
  community, group or environment, there should be a timely process to allow people to
  challenge the use or outcomes of the AI system"); **accountability** (responsible people
  identifiable, and "human oversight of AI systems should be enabled").
  <https://www.industry.gov.au/publications/australias-ai-ethics-principles> — **403 to
  automated fetch on 2026-09-12; verify the wording in a browser before quoting it.**
- **Policy for the responsible use of AI in government** (DTA / digital.gov.au), released
  15 August 2024, effective 1 September 2024, now Version 2.0: mandates accountable
  officials for non-corporate Commonwealth entities and public AI transparency statements.
  <https://www.digital.gov.au/ai/ai-in-government-policy> — timed out; secondary-verified
  via <https://www.dta.gov.au/articles/responsible-choices-new-policy-using-ai-australian-government>.
- **NT Government AI Policy + AI Assurance Framework** (Dept. of Corporate and Digital
  Development): applies to AI designed, built, procured or used by NTG agencies and
  government-owned corporations; self-assurance and quick risk assessment; stronger
  controls for medium and high risk; Chief Executives ultimately accountable; aligned to
  the national AI Ethics Principles.
  <https://dcdd.nt.gov.au/publications/artificial-intelligence-policy> and
  <https://digitalterritory.nt.gov.au/digital-government/strategies-and-guidance/policies-standards-and-guidance/artificial-intelligence-assurance-framework>
  (both 403 on 2026-09-12).
  **CONTRADICTION, unresolved:** one secondary source dates the Assurance Framework
  **November 2025**; regulations.ai dates it **26 June 2024**
  (<https://regulations.ai/regulations/RAI-AU-NT-NTAAXXX-2024>). Do not cite a date until
  the document itself is opened.
**What it changes:** the highest-value find for the ethics section. Coordinator sign-off
maps to *accountability / human oversight*; the tenant counterfactual view maps to
*contestability* and *transparency and explainability*; the two-ranking display maps to
*fairness*. The NT framework makes this locally binding rather than generic — "a Territory
agency deploying this would run it through the NTG AI Assurance Framework" is a strong Q&A
answer.

---

## Item 6 — The judges

Panel as published on 2026-09-12 (<https://itcodefair.cdu.edu.au/ai-challenge/>): **Cat
Kutay — Charles Darwin University**, **Rushi Vyas — Open AI**, two TBC.

### Claim: Cat Kutay's research is Indigenous knowledge systems and community-engaged technology, and she has published on remote housing.
**Verdict: TRUE, and the housing overlap is direct.** CDU research profile
(<https://researchers.cdu.edu.au/en/persons/cat-kutay/>, checked 2026-09-12): Senior
Lecturer in Information Technology, Faculty of Science and Technology; Indigenous
knowledge sharing, human-computer interaction, computer-supported collaborative learning,
NLP and speech-to-speech translation for local languages. Second source: CDU supervisor
profile
(<https://www.cdu.edu.au/research-and-innovation/higher-degree-research/find-supervisor/eng-tech/dr-cat-kutay>).
Recent work: Walker & Kutay, "Indigenous data sovereignty for Yinhamah", *International
Journal on Digital Libraries* 26, art. 14, 2025, DOI 10.1007/s00799-025-00420-0
(<https://link.springer.com/article/10.1007/s00799-025-00420-0>); *Engineering with
Country: First Nations Engineering in Practice*, CDU, 2025; Kutay et al. (eds),
*Indigenous Engineering for an Enduring Culture*; and — most relevant — Bazli, Ashrafi,
Rajabipour & Kutay, "3D printing for remote housing: benefits and challenges",
*Automation in Construction*, 2023, her most-cited paper (~178 citations; Google Scholar
<https://scholar.google.com/citations?user=M9lK3vwAAAAJ>).
**What she is likely to probe:** who was consulted and who holds decision-making power
over the data (Indigenous leadership, not merely consultation); whether the
"vulnerability" factor encodes a deficit stereotype; whether the tenant-facing language
works for second-language English speakers; whether community voice enters the loop
anywhere or only the coordinator's; Indigenous data sovereignty over anything the tool
stores. Have an answer ready for "what would have to change before a community agreed to
run this?"

### Claim: the judge Rushi Vyas works at OpenAI.
**Verdict: TRUE for employer; TITLE TBD.** Two independent sources: the CDU judging panel
lists "Rushi Vyas — Open AI"; a public LinkedIn profile shows OpenAI, Sydney NSW, as
current employer, with the title not rendered publicly
(<https://au.linkedin.com/in/therushivyas>, checked 2026-09-12). A UNSW staff page for the
same name lists a casual academic role focused on AI, higher education, sustainability,
student belonging and public-interest innovation, and does **not** mention OpenAI
(<https://www.unsw.edu.au/staff/rushi-vyas>). One secondary search result described an
"ANZ Network AI Ecosystems & ChatGPT for Startups Partner" role at OpenAI — **unconfirmed,
treat as TBD**. Whether the UNSW academic and the judge are the same person is **TBD —
needs validation**; same name plus Sydney plus OpenAI is suggestive, not proof.
**What an OpenAI judge is likely to probe:** how the LLM extraction is *evaluated* (a
labelled set, accuracy per field, what happens on a miss — not a demo anecdote); why an
LLM at all where it is used, and why it is kept out of ranking; prompt injection and
adversarial fault reports; cost and latency per report; what the system does when
uncertain; whether the human sign-off is real oversight or a rubber stamp. Building an
eval table is the cheapest way to satisfy both this judge and "technical sophistication".

---

## Item 8 — Cultural safety

### Claim: there is binding published guidance on research with, and writing about, Aboriginal and Torres Strait Islander peoples.
**Verdict: TRUE.** The **AIATSIS Code of Ethics for Aboriginal and Torres Strait Islander
Research** (AIATSIS, October 2020) supersedes GERAIS 2012. Four principles: Indigenous
self-determination; Indigenous leadership; impact and value; sustainability and
accountability — with explicit guidance not to apply stereotypes to communities or
individuals, and to identify diversity within a community.
<https://aiatsis.gov.au/research/ethical-research/code-ethics>; PDF at
<https://aiatsis.gov.au/sites/default/files/2020-10/aiatsis-code-ethics.pdf> (both 403 to
automated fetch on 2026-09-12 — **open in a browser to confirm sub-principle numbering
before citing a specific clause**). Companion: *A Guide to applying the AIATSIS Code of
Ethics* (2020). Also relevant: NHMRC ethical guidelines for research with Aboriginal and
Torres Strait Islander peoples
(<https://www.nhmrc.gov.au/research-policy/ethics/ethical-guidelines-research-aboriginal-and-torres-strait-islander-peoples>).

### Claim: Indigenous data sovereignty principles apply to data *about* communities, not only data collected *from* them.
**Verdict: TRUE.** **CARE Principles for Indigenous Data Governance** — Carroll, Garba,
Figueroa-Rodríguez, Holbrook, Lovett, Materechera, Parsons, Raseroka, Rodriguez-Lonebear,
Rowe, Sara, Walker, Anderson & Hudson, *Data Science Journal* 19:43, 2020, DOI
10.5334/dsj-2020-043 (primary text retrieved 2026-09-12,
<https://datascience.codata.org/articles/10.5334/dsj-2020-043>). Collective benefit;
**Authority to control** — Indigenous Peoples determine governance protocols for
Indigenous data held by other entities; Responsibility; Ethics — Indigenous rights and
wellbeing are the focus across the whole data lifecycle. Australian counterpart: **Maiam
nayri Wingara** Aboriginal and Torres Strait Islander Data Sovereignty Collective
(established 2017; key principles articulated 2018), including the right to control the
data ecosystem and the right to data that is *contextual and disaggregated* and
*protective* of collective interests (<https://www.maiamnayriwingara.org/>).

### The question the user must decide: real community names with real coordinates, or fictional names on real geography?
**What the principles imply — this is not the decision, the decision is the user's:**
- *Authority to control* (CARE) and *Indigenous leadership* (AIATSIS) point away from
  attaching a real named community to fabricated performance data without that community's
  agreement. A synthetic record reading "Community X: 14 overdue urgent repairs" is a
  claim about a real named place that nobody there authorised, and it is indexable.
- *Ethics* (CARE) and the AIATSIS anti-stereotyping guidance point the same way: our
  dataset is *deliberately built to contain a town/remote skew*. Rendering that
  deliberately unfavourable pattern under real community names risks publishing an invented
  deficit narrative about identifiable people.
- *Contextual and disaggregated* (Maiam nayri Wingara) cuts the other way: collapsing
  everything into an undifferentiated "remote" erases real difference, and the map's
  credibility rests on real distances and real wet-season road closures.
- **The middle path all three imply:** real geography (coordinates, road network, distance,
  seasonal closure) with **fictional settlement names**, plus an explicit statement in the
  report *and on the UI itself* that names are fictional and all records are synthetic.
  Real named communities may still appear where the data is genuinely public and not about
  performance — a cited population or location source — kept visually separate from the
  synthetic layer.
- Whatever is chosen, the report should cite CARE and AIATSIS by name rather than assert
  cultural safety in its own voice. **Decision: the user's.**

---

## References ready for the report

1. Bertsimas, D., Farias, V. F., & Trichakis, N. (2011). The Price of Fairness. *Operations Research*, 59(1), 17–31. https://doi.org/10.1287/opre.1100.0865
2. Wachter, S., Mittelstadt, B., & Russell, C. (2018). Counterfactual Explanations without Opening the Black Box: Automated Decisions and the GDPR. *Harvard Journal of Law & Technology*, 31(2). arXiv:1711.00399. https://arxiv.org/abs/1711.00399
3. Tan, J., Xu, S., Ge, Y., Li, Y., Chen, X., & Zhang, Y. (2021). Counterfactual Explainable Recommendation. *CIKM '21*, 1784–1793. https://doi.org/10.1145/3459637.3482420
4. Ensign, D., Friedler, S. A., Neville, S., Scheidegger, C., & Venkatasubramanian, S. (2018). Runaway Feedback Loops in Predictive Policing. *PMLR*, 81, 160–171. https://proceedings.mlr.press/v81/ensign18a.html
5. Altenburger, K. M., & Ho, D. E. (2019). When Algorithms Import Private Bias into Public Enforcement. *Journal of Institutional and Theoretical Economics*, 175(1), 98–122. https://dho.stanford.edu/wp-content/uploads/JITE-FinalVersion.pdf
6. Department of Industry, Science and Resources (Australia). *Australia's AI Ethics Principles*. https://www.industry.gov.au/publications/australias-ai-ethics-principles (accessed 12 Sep 2026)
7. Digital Transformation Agency (Australia). *Policy for the responsible use of AI in government*, v2.0, effective 1 Sep 2024. https://www.digital.gov.au/ai/ai-in-government-policy
8. Northern Territory Government, Department of Corporate and Digital Development. *Artificial Intelligence Policy* and *AI Assurance Framework*. https://dcdd.nt.gov.au/publications/artificial-intelligence-policy (date unresolved — see 5f)
9. AIATSIS (2020). *AIATSIS Code of Ethics for Aboriginal and Torres Strait Islander Research*. https://aiatsis.gov.au/research/ethical-research/code-ethics
10. Carroll, S. R., et al. (2020). The CARE Principles for Indigenous Data Governance. *Data Science Journal*, 19(1), 43. https://doi.org/10.5334/dsj-2020-043
11. Maiam nayri Wingara Aboriginal and Torres Strait Islander Data Sovereignty Collective (2018). *Key Principles*. https://www.maiamnayriwingara.org/
12. Walker, J., & Kutay, C. (2025). Indigenous data sovereignty for Yinhamah. *International Journal on Digital Libraries*, 26, 14. https://doi.org/10.1007/s00799-025-00420-0
13. Bazli, M., Ashrafi, H., Rajabipour, A., & Kutay, C. (2023). 3D printing for remote housing: benefits and challenges. *Automation in Construction*.

## Where this belongs

References 1–5 → **report references** (Related Work / Discussion), plus one line each in
the PRD's positioning section. References 6–8 → **report references** (Ethics /
Discussion) and the PRD as a named constraint the design answers. References 9–11 →
**report references**, plus a PRD constraint on the synthetic dataset. References 12–13 →
**nowhere in the report**; they are judge preparation for Q&A. Item 6's Q&A predictions →
**nowhere else on disk**; they belong in pitch prep.
