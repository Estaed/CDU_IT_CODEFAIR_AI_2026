# Research — NT remote housing maintenance: scale, response targets, documented delays; and Australian fault/urgency taxonomies

Research items 3 and 4 from `notes.md`. Checked against the live web on **2026-09-12**.
Method: each question is stated as a falsifiable claim and checked against primary sources
(NT Government, ANAO, Commonwealth Ombudsman, WA Auditor General, Productivity Commission,
state housing departments). News articles are marked as leads, not facts.

---

## Item 3 — NT remote public housing: scale, targets, evidence of delay

### Claim 3.1 — "The NT remote housing program covers roughly 73 remote communities plus Alice Springs town camps."

**Verdict: CONFIRMED (two independent primary sources).**

- ANAO, *Remote Housing in the Northern Territory*, Auditor-General Report No. 18 2021–22: the National
  Partnership for Remote Housing NT (signed 30 Mar 2019; $550m Australian Government funding 2018–2023)
  aims to "improve housing conditions and reduce overcrowding in **73 NT remote communities and the
  17 Alice Springs town camps**". Also: $2.65bn invested over 15 years to 2022–23; 27,600 Indigenous
  people in overcrowded houses in the NT in 2016; 1,857 dwellings needed immediately plus 74/year.
- NT DHLGCD, *Remote housing* page (page stamp 11 Sep 2026; checked 2026-09-12): same 73 communities /
  17 Alice Springs town camps wording; "$1.1 billion over 10 years" for Our Community. Our Future. Our Homes.
- NT DHLGCD *Annual Report 2024-25*: "$4 billion in improving remote housing over the next 10 years";
  "the Territory's 73 remote communities"; 222 new homes delivered in 2024-25; only 50% of remote households
  live in appropriately sized dwellings (a 1% improvement on 30 June 2024).

**Changes for us:** the geography layer should carry ~70–75 named remote communities plus a town-camp class,
across the six service regions NT itself publishes (Greater Darwin, Palmerston, Top End, Arnhem, Big Rivers,
Barkly, Central Australia).

### Claim 3.2 — "There is a published count of remote public housing dwellings under NT management."

**Verdict: CONFIRMED, with one usable figure; the departmental KPI table is unusable.**

- Grealy, L., Su, J.-Y. & Thomas, D. (2025), *Healthy Homes: Repairs and Maintenance in Remote Northern
  Territory Housing*, *Int. J. Environ. Res. Public Health* 22(6):836, published **26 May 2025**
  (Menzies School of Health Research / CDU): **5,498 dwellings** subject to the Healthy Homes R&M program —
  5,084 remote, 298 Alice Springs town camps, 116 Tennant Creek community living areas.
- The NT DHLGCD *Annual Report 2024-25* does report a KPI "Remote public housing dwellings managed", but the
  target/actual columns in the published PDF are **misaligned** and cannot be read reliably. I am not quoting a
  number from it.

**TBD — needs validation:** the exact current remote dwelling count under NT management. Would be settled by the
AIHW / Productivity Commission *Report on Government Services* chapter 18 housing data tables, or a direct/FOI
request to DHLGCD.

**Changes for us:** generate ~5,000–5,500 remote dwellings and cite the 2025 peer-reviewed figure, not the annual report.

### Claim 3.3 — "NT publishes repair response-time targets, and they are the same for town and remote."

**Verdict: CONTRADICTED — and this is the single most important finding for the project.**

NT DHLGCD fact sheet **FS17 "Repairs and maintenance", dated 10/25 (October 2025)** states verbatim:

- "Immediate maintenance – response time within **4 hours**."
- "Urgent maintenance – response time is within **2 business days**. **Remote housing response time is within 5 business days**."
- "Routine maintenance – response time is within ten (10) business days. **Remote housing response time is within 25 business days**."
- "In remote areas, Remote Housing Maintenance Officers will step in to assess and make safe if a contractor isn't available."

The town/remote gap is therefore **written into the Territory's own published policy**: 2.5x for both urgent and routine.

Cross-check, same date: the public nt.gov.au page *Repairs and maintenance of your public housing home* and the
DHLGCD *Remote housing maintenance* page publish **no timeframes at all** — only "Things that are dangerous will be
repaired first". That is a contradiction in *disclosure*, not in policy, and it is recorded, not resolved: a remote
tenant reading the website cannot learn their own service standard.

**Changes for us:** the equity slider stops being hypothetical. The efficiency-only baseline can be calibrated to the
official 5-day / 25-day remote windows, and the equity-visible setting described as closing a gap the Territory
documents itself. The four windows belong in `constants.md`, never inline.

### Claim 3.4 — "There is audit / ombudsman evidence that remote repairs run late relative to town."

**Verdict: CONFIRMED for the NT (dated, qualitative); CONFIRMED with numbers for WA (current, analogue).**

- **Commonwealth Ombudsman, *Remote Housing Reforms in the Northern Territory*, published June 2012.** Section
  "Timeliness and responsiveness": "Although timeframes have been established under the SLAs for the completion of
  repairs and maintenance work, **these are not always met**." Case study 7: urgent repairs still not done **11 months**
  after complaint; the tenant was relocated before any work happened. Case study 8: a disability-access work order
  classified **"routine"** and completed **nearly nine months** later, with wet-season community access given as the
  reason quotes could not be obtained. Recommendation 13 asks for systems "to monitor progress ... and taking action
  where delay or quality issues are identified".
  *Caveat: 2012, SIHIP/shire era. It evidences the mechanism — misclassification, wet-season access, no monitoring —
  not current performance.*
- **WA Office of the Auditor General, *Management of Housing Maintenance Information*, tabled 6 August 2025** —
  quantified, current, and the closest measurable analogue: time to issue the **first work order averaged 21.9 days in
  remote areas vs 10.6 days in metropolitan areas** (an 84% increase since 2019). Priority 2 (urgent) targets met 74%
  of the time, P3 77%, P4 routine 72%; emergency 95% but averaging ~10 hours against an 8-hour target. Remote travel
  costs up to $8/km.
- Grealy et al. (2025), NT: across 5,498 houses over 20 months (Jul 2021 – Feb 2023) only **1,315 Condition Assessment
  Tool inspections** were completed — **23.9%** of stock against a contractual annual-inspection requirement. Annual
  maintenance spend stayed flat at ~**AUD 7,843 per dwelling**, i.e. Healthy Homes did not shift resources to
  preventive maintenance.
- **Lead, not fact:** ABC News, 22 Aug 2024 — class action against the WA Housing Authority covering ~3,000 remote
  Aboriginal community premises across eight regions, alleging its own annual reports showed KPIs for emergency,
  urgent and priority response times "consistently below the required benchmarks"; one home reported with no roof
  since March 2022.

**TBD — needs validation:** current NT-specific *actual* median days-to-complete, town vs remote. Nothing published
was found. Would be settled by a DHLGCD FOI, an NT Auditor-General housing-maintenance audit, or RoGS chapter-18 data
tables. **Do not invent this number.** Our synthetic skew is justified by the *policy* gap (3.3) plus the WA *measured*
gap (3.4), the latter labelled explicitly as an interstate analogue.

---

## Item 4 — Fault categories and urgency classes in Australian social housing

All rows below come from primary government sources, checked 2026-09-12.

| Jurisdiction (source, date) | Class | Window | Published example faults |
|---|---|---|---|
| **NT** — DHLGCD fact sheet FS17, 10/2025 | Immediate | 4 h | FS17 lists examples for the whole sheet, not per class: gas leaks, exposed electrical wires, dangerous electrical fault, flooding or serious flood damage |
| | Urgent | 2 business days town / **5 business days remote** | blocked toilets or drains, leaking sewerage, leaking water from taps or pipes, broken locks or door handles, smoke alarms not working, serious roof leak, serious storm/fire/impact damage |
| | Routine | 10 business days town / **25 business days remote** | dripping or tight taps, stove elements not working, fans not working properly, power points not working, broken doors |
| **QLD** — qld.gov.au public housing response times, updated 5 May 2026 | Immediate | 1 h | gas leak, fire, exposed live wires in accessible locations, burst pipes inside the building |
| | Urgent | 4 h | no lights or power, serious storm damage, serious water penetration, burst pipe outside building, fully blocked sewerage, smoke alarm malfunction, building unsecured after forced entry, major structural damage endangering occupants |
| | Priority | 24 h | minor blocked drains, cistern failure/overflow, broken external door locks, broken windows, multiple light outages, security light failure, full stove malfunction, **fan repair/replacement in remote communities**, **hot water system failure in remote communities** |
| | Non-urgent | case-by-case, escalatable | — |
| **WA** — Dept of Communities tenant guide SD111 (05/23); categories confirmed by OAG report 6 Aug 2025 | Emergency (P1) | 8 h | report of electric shock, earth wiring issues, faulty smoke alarm, no power to property, gas leak |
| | Urgent (P2) | 24 h | no hot water, blocked toilet, burst pipe or water leak, faulty gas stove |
| | Priority (P3) | 48 h | replace stove or hot water unit, water temperature, cracked toilet bowl, leaking tap, security lights not working |
| | Routine (P4) | 28 days | rehang door, replace washing line, rewire flyscreens |
| **NSW** — nsw.gov.au Homes NSW maintenance service, updated 13 Jan 2026 | Emergency | immediate (Maintenance Hub 1800 422 322) | flooding from a burst water pipe, raw sewage overflowing inside the home, gas leak, major water leak that can't be isolated, fire damage |
| | Non-urgent | not published on that page | — |

Two observations worth carrying into the report:

- **QLD is the only jurisdiction found that names remoteness inside the class definition itself** — fans and hot water
  systems in remote communities are escalated into the 24-hour Priority class. That is an existing precedent for
  "remoteness changes urgency", and it runs the *opposite* direction from NT's remote-extended windows.
- **There is no national standard taxonomy.** Class names (Immediate/Emergency/Urgent/Priority/Routine) and windows
  differ per jurisdiction for overlapping faults. Contradiction recorded, not resolved. We choose one and say which.

**TBD — needs validation:** the NSW statutory 24-hour urgent-repair duty is attributed in secondary sources to the
*Residential Tenancies Act 2010* (NSW); I did not read the Act. Settled by reading s.62/s.64 directly if we want to cite it.

### Proposed taxonomy for our synthetic generator

Adopt **NT FS17 as the spine** — it is the jurisdiction we model and it carries the town/remote split the project is
about — and borrow **QLD's per-class fault examples** to populate it, because NT publishes examples but does not map
them to classes.

Urgency classes: **Immediate (4 h) · Urgent (2 d town / 5 d remote) · Routine (10 d town / 25 d remote)**, plus a
**Non-urgent / planned** sink.

Fault categories to generate against: electrical hazard; gas; sewage / blocked toilet or drain; water supply, burst
pipe or no water; hot water system; stove and cooking; smoke alarm; security (locks, doors, windows, unsecured after
forced entry); structural / roof / storm damage; cooling (fans, aircon); lighting and power points; minor plumbing
(taps). Each generated report carries a ground-truth class from this table plus a free-text tenant phrasing, so
extraction accuracy is measurable rather than asserted.

**Household vulnerability and heat are not part of any published class definition** found (QLD's remote fan/hot-water
escalation is the nearest thing). Our "aircon dead, baby in the house" signal is therefore **our extension, not NT
policy** — this must be stated in the report, or a judge will read it as a claim about how NT actually triages.

---

## Where this belongs

- Claims 3.1–3.3 and the four NT response windows → **PRD data section**, and the four windows into `constants.md`
  (values that must not be retyped).
- Claim 3.4 (Ombudsman 2012, WA OAG 2025, Grealy et al. 2025, ABC lead) → **report references**, Discussion/ethics
  section: the town/remote gap is documented, not invented by us.
- The taxonomy table and the proposed generator taxonomy → **PRD data section**, as the ground-truth schema.
- The WA class action and the NSW *Residential Tenancies Act* detail → **report references** only; not load-bearing.

## Sources

- ANAO, Auditor-General Report No. 18 2021–22, *Remote Housing in the Northern Territory* — https://www.anao.gov.au/sites/default/files/Auditor-General_Report_2021-22_18.pdf
- NT DHLGCD fact sheet FS17, *Repairs and maintenance*, 10/2025 — https://dhlgcd.nt.gov.au/media/documents/fact-sheets/repairs-and-maintenance-fs17.pdf
- NT.GOV.AU, *Repairs and maintenance of your public housing home* (checked 2026-09-12) — https://nt.gov.au/property/social-housing/looking-after-your-home/repairs-and-maintenance-of-your-home
- NT DHLGCD, *Remote housing* and *Remote housing maintenance* (checked 2026-09-12) — https://dhlgcd.nt.gov.au/remote-housing/remote-housing
- NT DHLGCD, *Annual Report 2024-25* — https://dhlgcd.nt.gov.au/__data/assets/pdf_file/0007/1567987/dhlgcd-annual-report-2024-25.pdf
- Commonwealth Ombudsman, *Remote Housing Reforms in the Northern Territory*, June 2012 — https://www.ombudsman.gov.au/__data/assets/pdf_file/0026/29627/Remote-Housing-Reforms-in-the-Northern-Territory.pdf
- WA Office of the Auditor General, *Management of Housing Maintenance Information*, 6 Aug 2025 — https://audit.wa.gov.au/reports-and-publications/reports/management-of-housing-maintenance-information/
- Grealy, Su & Thomas (2025), *IJERPH* 22(6):836 — https://pmc.ncbi.nlm.nih.gov/articles/PMC12193293/
- Queensland Government, *Response times for maintenance*, updated 5 May 2026 — https://www.qld.gov.au/housing/public-community-housing/public-housing-tenants/looking-after-your-home/maintenance/property-maintenance/response-times
- WA Department of Communities, tenant maintenance guide SD111 (05/2023) — https://www.wa.gov.au/system/files/2023-06/sd111_maintenance_dl_web.pdf
- NSW Government, *Maintenance service* (Homes NSW), updated 13 Jan 2026 — https://www.nsw.gov.au/housing-and-construction/social-affordable/public-housing-tenants/maintenance-and-repairs/maintenance-service
- ABC News, 22 Aug 2024 (lead only) — https://www.abc.net.au/news/2024-08-22/wa-indigenous-public-housing-class-action-launched/104189272
