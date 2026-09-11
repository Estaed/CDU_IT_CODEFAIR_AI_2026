# Research — synthetic data, extraction, heat, stack

Checked live: **2026-09-12**. Every source was fetched or searched on that date; publication dates are given where the source states one. Unverified items are marked **TBD — needs validation** rather than guessed.

---

## 1. Synthetic free-text fault reports

**Claim: persona-conditioned generation is the documented way to get diversity without hand-writing prompts.**
Verdict: **supported.** Tencent AI Lab, *Scaling Synthetic Data Creation with 1,000,000,000 Personas* (arXiv 2406.20094 v3; repo `tencent-ailab/persona-hub`) routes each generation through a persona description; the released persona data is stated **research-use only**. Follow-up work measures whether it works: *Measuring Lexical Diversity of Synthetic Data Generated through Fine-Grained Persona Prompting* (arXiv 2505.17390); *Persona-Based Synthetic Data Generation Using Multi-Stage Conditioning* (arXiv 2507.13380).
**Changes for us:** our persona is the *household*, not a writer — household composition, tenure, register/literacy, community, season. We write our own persona list from NT context; we do **not** import Persona Hub (licence + irrelevant personas).

**Claim: label distribution must be fixed before generation, not discovered after.**
Verdict: **supported — this is the controllable part.** *String Seed of Thought* (arXiv 2510.21150) documents that LLMs asked to sample from a target distribution do not, and proposes seeding to force distribution-faithful generation. Practitioner guidance converges on the same shape: seed a small gold set, expand, then verify by embedding-clustering the synthetic set against the intended distribution (futureagi.com *Synthetic Test Data for LLM Evaluation in 2026*; premai.io 2026 guide — both secondary/vendor, corroboration only).
**Changes for us:** the town/remote skew is a **sampling plan executed in Python** — draw the label tuple first, then ask the LLM to write text for that tuple. Never "ask the LLM for 300 varied reports". This also yields free ground truth for section 2.

**Claim: generator and extractor must not be the same model.**
Verdict: **weakly supported; treat as our own design rule.** The leakage concern recurs in 2026 practitioner guides ("mix teachers, include a real-data seed"), but no primary paper quantifying generator→extractor leakage for this setup was found. **TBD — needs validation.**
**Changes for us:** generate with one model, extract with another, and state it in the report as a design choice, not a cited result.

**Claim: an open dataset of real free-text maintenance/repair requests exists.**
Verdict: **largely NO — the decisive negative finding.**
- **Chicago 311** (`data.cityofchicago.org/api/views/v6vf-nfxy.json`, fetched 2026-09-12): 39 columns, **no free-text narrative field at all** — `SR_TYPE` / `SR_SHORT_CODE` are categorical. Licence shown as "See Terms of Use"; CC BY 4.0 is asserted by secondary listings, **not** confirmed in portal metadata. TBD before we cite a licence.
- **NYC 311, 2020–Present** (`data.cityofnewyork.us/api/views/erm2-nwe9.json`, fetched 2026-09-12): 48 columns. `complaint_type`, `descriptor`, `descriptor_2` are **controlled vocabularies**; `resolution_description` is **agency boilerplate**, not the resident's words. NYC Open Data has **no explicit open licence** — only NYC.gov Terms of Use plus per-agency terms (opendata.cityofnewyork.us/overview, fetched 2026-09-12).
- **UK council repairs free text:** **TBD — needs validation.** Nothing found 2026-09-12.

**Changes for us:** 311 is a **taxonomy seed, not a style seed.** We can justify our fault-type taxonomy and its relative frequencies against NYC's `complaint_type`/`descriptor` pairs (HEAT/HOT WATER, PLUMBING, DOOR/WINDOW, ELECTRIC), and must write the *voice* ourselves from NT context. Saying "no public corpus of tenant-voice repair text exists" is a stronger dataset answer than a vague citation.

**Where this belongs:** PRD (data-generation method + the "no real corpus" limitation); Part 2 Key Constraints (label tuple drawn in Python first; generator ≠ extractor).

---

## 2. Structured extraction with source spans

**Claim: structured outputs are GA on the Claude API and need no beta header.**
Verdict: **confirmed** (platform.claude.com/docs/en/build-with-claude/structured-outputs, fetched 2026-09-12). Two features: `output_config.format` (JSON matching a schema) and `strict: true` on tools. The old `structured-outputs-2025-11-13` header and `output_format` field still work transitionally, but **the Python SDK v1.0+ raises `TypeError` on `output_format=`** — use `output_config`. Schema subset: basic types, `enum`, `const`, `anyOf`/`allOf`, `$ref`/`$defs`, `required`, `additionalProperties: false` (mandatory). **Not supported:** recursion, external `$ref`, `minimum`/`maximum`, `minLength`/`maxLength`, `minItems` other than 0/1.

**Claim: the Citations feature can give us the source phrase per field.**
Verdict: **NO — a hard blocker we must design around.** platform.claude.com/docs/en/build-with-claude/citations (fetched 2026-09-12): *"Citations cannot be used together with structured outputs. If you enable citations on any user-provided document ... and also include the `output_config.format` parameter ... the API returns a 400 error."* Citations return `char_location` blocks interleaved with prose — incompatible with a strict JSON schema by construction. All active models support citations.
**Changes for us:** the "every field shows its source phrase" UI is built by putting the span **in our own schema** — each field an object `{value, evidence_text, start, end}` — then **verifying in Python that `evidence_text` is a literal substring of the report**. A field whose evidence does not match is flagged in the UI, not silently shown. Cheap, deterministic, and a strong answer to an OpenAI judge asking about grounding.

**Claim: evaluation should be per-field, not one accuracy number.**
Verdict: **supported.** `FAIRmat-NFDI/extract-eval` (schema-driven per-field P/R/F1 for LLM JSON extraction with per-field comparators; accessed 2026-09-12) argues exact string match fails on semantically equal values and one score hides which field is wrong. Span-level NER convention — exact boundary match counts a near-miss as both FP and FN — is described in SEER (arXiv 2510.03490); relaxed/normalised matching is the documented alternative.
**Changes for us:** eval set of ~50 reports whose label tuple is known *by construction* (section 1). Report **per-field precision/recall**: categorical fields exact-match after normalisation; evidence spans scored by substring containment, not exact boundaries.

**Claim: current model names and prices.**
Verdict: **confirmed from the official pricing page only** (platform.claude.com/docs/en/about-claude/pricing, fetched 2026-09-12). USD per million tokens, input / output:
Opus 5 **$5 / $25** · Sonnet 5 **$2 / $10** · Sonnet 4.6 $3 / $15 · Haiku 4.5 **$1 / $5** · Fable 5.1 $10 / $50. Batch API = **50% off both directions** (Haiku 4.5 batch $0.50 / $2.50). Cache hits = 0.1x base input. Note: **Claude 4.7 and later use a newer tokenizer producing ~30% more tokens for the same text** — cost estimates written against older figures under-count.
**Changes for us:** extraction on **Haiku 4.5**, batched, for the per-report cost line the report needs. Compute the real figure from the response `usage` at build time rather than asserting it.

**Where this belongs:** Part 2 stack table (SDK, model IDs, `output_config`); Part 2 Key Constraints (citations forbidden with structured outputs; evidence substring check mandatory); PRD (eval method).

---

## 3. Heat as a documented urgency factor

**Claim: there is an official NT heat-health trigger we can cite.**
Verdict: **yes.** NT Health issues **heat health warnings** before and during severe and extreme heatwaves, when BoM forecasts unusually high **maximum and minimum** temperatures over a **3-day** period; **October to March is extreme heat season in the NT** (health.nt.gov.au heat-health / heat-stress). BoM's heatwave service classifies severity **low-intensity / severe / extreme** via the **Excess Heat Factor (EHF)**, which is acclimatisation-relative — three or more consecutive days of unusually high temperatures **relative to the previous 30 days** — not a fixed °C threshold (bom.gov.au heatwave-services; CAWCR Technical Report 060, the citable primary).
**Caveat:** both health.nt.gov.au and bom.gov.au returned **HTTP 403** to automated fetch on 2026-09-12; the above comes from indexed search summaries. **Re-verify by hand before the report cites them.**

**Claim: vulnerability groups are named in official guidance.**
Verdict: **yes, two independent sources.** NT Health / nt.gov.au: newborns, infants and young children warm faster and are very vulnerable; also elderly and people with chronic conditions. Independently, Boyd et al., *Emergency Department Presentations During Dry and Humid Heatwaves: A Case-Crossover Study in the Northern Territory* (GeoHealth, 2026, doi 10.1029/2025GH001562), and the Human Rights Law Centre "Climate Safe Housing" project, tie NT heat exposure to ED presentations and to poor remote-housing thermal performance.
**Changes for us:** "aircon failed + infant in household + extreme-heat season" is a **documented** urgency multiplier, not our invention. Use **EHF-style relative** framing plus the Oct–Mar season window; do **not** invent a "40 °C = urgent" rule — BoM explicitly does not work that way. Wet season for road logistics: BoM NT seasonal summaries use **October–April**.

**Claim: a free no-key daily forecast API exists.**
Verdict: **BoM no, Open-Meteo yes.** BoM's API is explicitly **not for public use without express permission**; FTP products are personal/in-organisation use only, no onward supply, no commercial use (bom.gov.au/copyright; bom.gov.au/catalogue/data-feeds.shtml). **Open-Meteo**: no API key, no sign-up, free non-commercial to 10,000 calls/day, data under **CC BY 4.0** with required attribution and a link (open-meteo.com/en/licence, /en/pricing).
**Changes for us:** use **Open-Meteo** if we pull live temperatures, attributed in the UI footer. Safer for a demo: **ship a small static CSV of NT climate normals** so the prototype runs offline for judges, citing BoM climate pages as the source of the numbers rather than calling BoM.

**Where this belongs:** PRD (urgency factor definition + citations); Part 2 stack table (Open-Meteo, optional, CC BY attribution); Part 2 Key Constraints (no BoM API calls).

---

## 4. Prototype stack

**Claim: Streamlit current version.**
Verdict: **1.63.0**, `requires_python >=3.10`, supports 3.10–3.14 (pypi.org/pypi/streamlit/json, fetched 2026-09-12). Secondary coverage dates 1.63.0 to **2026-09-01**; docs.streamlit.io release notes is the primary to re-check. **Install, then read the lockfile** — Part 2's stack table must not carry this number on my word.

**Claim: NT-scale maps render with no API key.**
Verdict: **yes with free tiles; NOT offline.** `st.map` uses **Carto** tiles by default and needs **no Mapbox key**; a Mapbox key is only required if you choose Mapbox in a `pydeck.Deck` (docs.streamlit.io st.map, fetched 2026-09-12). Folium ships the `xyzservices` tilesets — `OpenStreetMap`, `CartoDB Positron`, `CartoDB Voyager` — all keyless; Carto basemaps are free to **5 million tile requests/month** with **Carto + OpenStreetMap attribution required on every map** (docs.carto.com/faqs/carto-basemaps).
**True offline (no network) is TBD — needs validation**; it would require bundling tiles or drawing NT boundaries from a local GeoJSON with no basemap.
**Changes for us:** decide now whether the demo must survive dead conference wi-fi. A **pydeck/`st.map` scatter over a local NT-region GeoJSON, basemap optional**, is the version that cannot fail in front of judges. Attribution line is mandatory if a basemap is shown.

**Claim: known Streamlit + LLM traps.**
Verdict: **supported, mechanism confirmed by Streamlit's own caching docs; specifics from secondary tutorials** (theneuralbase.com Streamlit-for-AI, accessed 2026-09-12):
- Streamlit **reruns the whole script on every widget interaction**. An un-cached LLM call in the script body fires on every slider drag — for us, the equity slider would re-extract the entire inbox. **The single biggest trap for this prototype.**
- `@st.cache_resource` for the **client object**; `@st.cache_data` for **deterministic results**. `cache_data` on a client tries to pickle it and fails.
- Secrets: `.streamlit/secrets.toml` via `st.secrets`, never hardcoded, never committed.
**Changes for us:** extraction runs **once, offline, as a build step** writing a JSON/parquet artefact the app loads; the Streamlit app makes **zero LLM calls during ranking**, so judges can run it **without an API key**. Only the tenant-explanation draft is a live call, cached on job id. This falls out of the architecture anyway — the LLM extracts and explains, it does not rank.

**Where this belongs:** Part 2 stack table (Streamlit 1.63.0, pydeck/folium, Python >=3.10 — versions re-read from the lockfile); Part 2 Architecture (extraction as an offline build step, app reads artefacts); Part 2 Key Constraints (no LLM call in a rerun path; no API key required to run the demo).

---

## Open items carried forward

1. UK council repairs free-text open data — **TBD**, nothing found.
2. Generator→extractor leakage — **TBD**, no primary quantification found.
3. NT Health and BoM pages returned **403** to automated fetch — **re-verify by hand** before citing.
4. Chicago 311 CC BY 4.0 — **TBD**, asserted by secondary listings only.
5. True offline map rendering — **TBD**, needs a spike.
