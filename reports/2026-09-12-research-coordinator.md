# Research — How NT remote housing maintenance triage actually works today

Reconstructing the Fair Turn persona's real job from public sources. Live-web check: **2026-09-12**.
Method as in the housing report: falsifiable claim → verdict → dated sources → what it changes for us.
Primary sources only; anything not found is marked **TBD — needs validation** rather than filled in.

---

## Q1 — Who receives a fault report, and what logs it

### Claim 1.1 — "There is a single NT-wide phone line for remote housing repairs."
**Verdict: CONFIRMED.** **1800 104 076** — "to request a visit from your local maintenance team or
follow-up on some maintenance repair jobs"; out of hours the call "is diverted to a call centre".
Sources: NT.GOV.AU *Repairs and maintenance of your public housing home* and DHLGCD *Remote housing
maintenance* (both checked 2026-09-12); DHLGCD *Useful contacts* FS04 (same, checked 2026-09-12).

### Claim 1.2 — "The tenant's report is received by the contractor, not by a government queue."
**Verdict: CONFIRMED, and this is the single most important correction to our persona.**
Three routes exist in parallel: the 1800 line; the **Remote Housing Maintenance Officer (HMO)** in
community (non-trade repairs); and the **Community Housing Officer (CHO)**, the tenancy-side worker.
The CHO does *not* own a queue — "The CHO should notify the **Housing Maintenance Contractor
directly** of all maintenance requests received, and in return should receive a **job registration
number**" (NT TFHC, *Tenancy Management Support Services Handbook*, v1.3 June 2021, §3.2.1). The
contract obliges the contractor to "**Register all repairs and work requests and provide a
registration reference number to the person making the request**" and to "Provide a **first response**
for any repairs and maintenance … and a presence in the community" (RFT Description of Works §9.5,
reproduced in Menzies, *Healthy Homes Monitoring and Evaluation Project — Final Report*, Sep 2023,
App. 13). The department's role is the **Housing Maintenance Contract Officer**, who "monitors the
task" — the handbook's own split is Contractor column = record/act, Department column = inform and
monitor.

### Claim 1.3 — "A named departmental work-order system exists."
**Verdict: CONFIRMED — four named systems, none of them a triage queue.**
**TMS** (Tenancy Management System — tenancies, crowding, stock, inspections), **ASNEX** (Asset
Systems Nexus — contract and maintenance expenditure), **AIS** (Asset Information System), **CBIS**
(Corporate Business Intelligence System — the reporting layer over TMS). Source: Menzies Final Report
Sep 2023, §3.2 and §7.6; confirmed at the abstract level by Grealy, Su & Thomas, *IJERPH* 22(6):836,
26 May 2025. The contractor's own "**tasking system**" is where the job actually lives (Handbook §3.2.1).

**What it changes for us:** Fair Turn's user is the **contractor-side triage/coordination role** (or
the departmental Contract Officer looking at the same list), not a government dispatcher with an
NT-wide queue. The demo must say so. The job-registration-number concept is real and should appear
in the tenant view as the lookup key.

---

## Q2 — Who prioritises and dispatches

### Claim 2.1 — "Prioritisation is contractual, and a dollar threshold gates it."
**Verdict: CONFIRMED.** Non-urgent works over **AUD 500** require approval from the **NT Government
contract superintendent** — a **DIPL** (Infrastructure, Planning and Logistics) role, not Housing.
Providers reported this caused "additional administration and delays"; Menzies recommends raising the
threshold. Two carve-outs: §7.20 of the RFT exempts work "urgently required to make safe, secure,
protect, isolate, cut, cap or join"; §9.9.2.3 "**Works Exempt from Pre-Approval**" lists faults
repairable "**at the time of triage**" (blocked drains, blocked toilets, toilet leaking onto floor,
fast dripping taps, broken shower rose, water leaking into electricals). Sources: Menzies Final
Report Sep 2023 §7.5/§7.20; Grealy et al. 2025.

### Claim 2.2 — "Regional offices run their own queues."
**Verdict: CONFIRMED at the region level.** Remote public housing is administered through five remote
regions — **Top End, Arnhem, Big Rivers, Barkly, Central Australia** — each with its own office and
number, alongside urban offices (Greater Darwin, Palmerston, Katherine, Tennant Creek, Alice Springs,
Nhulunbuy). Menzies describes work being coordinated by "**regional TFHC and DIPL staff**" per region.
Sources: DHLGCD *Contacts* / FS04 (checked 2026-09-12); Menzies Final Report Sep 2023 §6.
*Not confirmed:* that each region holds a single ranked daily list. **TBD — needs validation.**

### Claim 2.3 — "Trades are contracted, clustered by community, and mostly Aboriginal enterprises."
**Verdict: CONFIRMED (two sources).** Under Healthy Homes (from 2021) one contract typically covers
**one to three communities**; by May 2023, **31 contracts to 22 companies, 25 of them to 17 Aboriginal
Business Enterprises, covering 49 remote communities**; terms of only **15–22 months**. The predecessor
model was two-tier: HMOs for non-trade work plus a regional **Trade Panel** of 92 contractors, in
clusters "based on geographical location and cultural alignments". Sources: Grealy et al. 2025;
Menzies Final Report Sep 2023 §2, §7.

### Claim 2.4 — "Travel mode and wet season shape dispatch."
**Verdict: PARTLY CONFIRMED — qualitative only.** Menzies: pricing varies because some communities are
near Darwin/Alice while others "require **plane, ferry, and barge travel**"; where providers sit in
regional towns "significant travel costs are involved". Commonwealth Ombudsman (June 2012) records
wet-season community access as the stated reason quotes could not be obtained on a repair that then
took nearly nine months. **No published schedule, charter roster or wet-season closure rule for
maintenance visits was found. TBD — needs validation.**

**What it changes for us:** the logistics factor is defensible (plane/ferry/barge, town-based crews),
but our 90-day road-closure series stays labelled synthetic. The AUD 500 / make-safe-exempt split is a
*real* published rule — worth surfacing in the UI as a flag ("repairable at triage, no approval needed"),
which is a cheap, highly credible detail.

---

## Q3 — What the coordinator knows, and does not

### Claim 3.1 — "The system cannot currently tell anyone how long a tenant waited."
**Verdict: CONFIRMED, emphatically.** Menzies Final Report §7.6.2: "it is **not possible to determine
whether there has been an improvement in the timeliness of completion of work orders following tenant
reporting**. Existing datasets are a more accurate representation of contracted service providers'
reporting processes (i.e. when they bulk upload invoices) than the actual delivery of jobs, and as
such they are a **poor source of information about the lengths of time between tenant reporting and
maintenance works**." Also: preventive vs responsive work cannot be distinguished; trade vs
handyperson cannot be distinguished; CAT condition data is on **paper** and not in CBIS.

### Claim 3.2 — "Household composition and dwelling condition are available at decision time."
**Verdict: CONTRADICTED for condition; PARTLY for household.** TMS/CBIS hold crowding rates *by
community* and dwelling size/standard — not per-household health need. CBIS0093 Dwelling Details "does
not provide detailed information about the condition of health hardware". Only **1,315 CAT inspections
across 5,498 houses** in 20 months (23.9%). Source: Menzies Sep 2023 §4/§7.6.2; Grealy et al. 2025.

### Claim 3.3 — Published pain points in the process itself.
**Verdict: CONFIRMED.** (a) $500 approval bottleneck and superintendent workload (Menzies 2023);
(b) "double handling where housing maintenance officers and contract superintendents are each involved
in determining work orders" (Menzies 2023 §10); (c) misclassification — a disability-access job
classified "routine" and done nearly nine months later (Ombudsman, June 2012, case study 8); SLA
timeframes "are **not always met**" (ibid.), with Recommendation 13 asking for systems to monitor
delay; (d) Joint Steering Committee Aboriginal members' concern at "lack of clear reporting from the
department and a reluctance to share data" (ABC News, 26 Apr 2025 — **lead, not fact**).

**What it changes for us:** Fair Turn's strongest honest claim is **not** "we rank better than the
coordinator". It is "**we make the wait visible and the reason recordable**", in a system whose own
evaluator says wait time cannot currently be measured. Put that quote in the report.

---

## Q4 — Published volumes

**Verdict: NOT PUBLISHED. TBD — needs validation. Do not invent.**
No count of work orders per year, per community, or urgent-vs-routine share was found. What exists:
contractual **KPI targets** — "100% immediate; 95% urgent and 90% of routine service requests are
responded to within required timeframe" (RFT KPI table, Menzies Sep 2023 App. 13); expenditure —
**AUD 43.12m across 5,498 dwellings in 2022 (AUD 7,843/dwelling)**, of which ~51.5% was coded
"miscellaneous/other" (Grealy et al. 2025); **AUD 92m** for property and tenancy management in
2024–25 with **AUD 10m/yr** ring-fenced for cyclical/preventive works (DHLGCD, 2025). Per-community
dwelling counts from Housing for Health project tables give a usable scale: 15–51 houses per small
community (Menzies Sep 2023 §6). Actuals against the KPI targets are **not published**.

---

## Q5 — Community voice in prioritisation

### Claim 5.1 — "Housing Reference Groups exist and have a defined advisory role."
**Verdict: CONFIRMED — but for allocation and contracting, not for repair triage.**
HRGs are "made up of selected local residents who represent different interest groups" and "advise …
on decisions like **who will get a house** and any community issues which may affect housing"
(NT.GOV.AU *Remote public housing reference groups*, checked 2026-09-12). The PTM framework commits to
"select service providers consistent with traditional Aboriginal owners and community aspirations,
where identified under **Local Decision Making agreements and/or Housing Reference Groups**" (Menzies
Sep 2023 App. 13). Menzies records HRGs selecting next tenants, and HRG + community meetings being the
forum where Housing for Health proposals were put and faults named (meetings 5 Apr 2022, 27 Apr 2022).
**No published mechanism was found by which an HRG influences the order of repair jobs. TBD.**

**What it changes for us:** our "community in the loop" answer must be honest — HRGs are a *real,
named, existing* NT structure with a *real* advisory remit, and extending them to repair prioritisation
is **our proposal, not current practice**. Framed that way it is a strength (we plug into an existing
Aboriginal-governance structure rather than inventing one); framed loosely a judge will read it as a
false claim about how NT works.

---

## A day in the coordinator's work, as far as public sources support it

At 7am the list is not in a government system. It is in the **contractor's tasking system** — the
company holding the Healthy Homes contract for this cluster of one to three communities, probably an
Aboriginal Business Enterprise, on a contract with 15–22 months to run [Menzies 2023; Grealy 2025].
Overnight faults arrived three ways: the **1800 104 076** line, diverted after hours to a call centre;
the **Community Housing Officer**, who phoned them straight to the contractor and wrote down the **job
registration number**; and the **Housing Maintenance Officer** in community, who can fix what needs no
licence [NT.GOV.AU; Handbook §3.2.1, June 2021].

Each job carries a class: **immediate** (make safe, 4 hours), **urgent** (5 working days), **routine**
(25 working days) — the remote windows, 2.5× the town ones [FS17, 10/2025; Handbook §3.2.1]. The first
sort is not by need but by **authority**: blocked toilets, blocked drains, fast dripping taps, water
leaking into electricals can be fixed **at the time of triage** with no approval; anything else
non-urgent over **AUD 500** waits on a **DIPL contract superintendent** who is servicing many
contractors at once [Menzies 2023 §7.5, §9.9.2.3]. *Assumption:* that approval wait is the largest
single source of variance in remote wait times — Menzies names it as a delay source but does not
quantify it.

The second sort is the truck. Some communities are a drive; others need **plane, ferry or barge**
[Menzies 2023 §7.5.1]. A wet-season road can stop the visit outright — the Ombudsman's 2012 case where
access made quoting impossible and the job ran nine months is the documented instance [Ombudsman, June
2012]. *Assumption:* crews are batched per community visit rather than dispatched per job; the
contract's per-community work plans imply it but no source states it.

What the coordinator does **not** have is the thing they most need. Household health need is nowhere in
the data — crowding is held by community, not household, and dwelling condition sits on **paper CAT
forms**, of which only 23.9% were ever completed [Menzies 2023; Grealy 2025]. And the wait itself is
invisible: the department's own evaluator states the data reflects when invoices were bulk-uploaded,
not when the job was done, so "it is not possible to determine whether there has been an improvement in
the timeliness of completion of work orders following tenant reporting" [Menzies 2023 §7.6.2]. The
department side of the loop is a **Housing Maintenance Contract Officer** monitoring tasks, and a KPI
of 95% urgent / 90% routine whose actuals are not published [Handbook; Menzies 2023 App. 13].

Community voice reaches housing through the **Housing Reference Group** — which advises on who gets a
house and which provider is chosen, and met in these communities to name faults — but **not** on the
order of today's jobs [NT.GOV.AU, checked 2026-09-12; Menzies 2023]. *That last gap is the one Fair
Turn proposes to fill, and it is a proposal, not a description.*

---

## Where this belongs

- **PRD persona** — Claims 1.2, 1.3, 2.1, 2.2 and the day-in-the-life narrative: the user is the
  contractor-side triage/coordination role in one cluster, working a contractor tasking system, with a
  DIPL approval gate at AUD 500 and a departmental Contract Officer monitoring. Job registration number
  = the tenant view's lookup key. The five remote regions → geography layer's region field.
- **Report, Discussion/ethics** — Claims 3.1 and 3.3: NT's own evaluator says wait time between tenant
  report and completion cannot be measured today. This is Fair Turn's honest value proposition and
  should be quoted verbatim.
- **Report, community section + slide** — Claim 5.1, with the "our proposal, not current practice"
  caveat stated on the slide, not just in the paper.
- **BACKLOG.md** — the four TBDs: per-region queue structure, wet-season maintenance rules, work-order
  volumes, HRG role in repair order. All would need FOI or direct contact; none blocks v1.

## Sources

- NT TFHC, *Tenancy Management Support Services Handbook*, v1.3 June 2021 — https://dhlgcd.nt.gov.au/media/documents/housing2/housing/living-strong-program/tenancy-support-services-handbook.pdf
- Menzies School of Health Research (Grealy, Su & Thomas), *Healthy Homes Monitoring and Evaluation Project — Final Report*, September 2023 — https://www.menzies.edu.au/content/Document/Healthy%20Homes%20Monitoring%20and%20Evaluation%20Project%20-%20Final%20Report.pdf
- Grealy, Su & Thomas (2025), *IJERPH* 22(6):836, 26 May 2025 — https://pmc.ncbi.nlm.nih.gov/articles/PMC12193293/
- DHLGCD, *Remote housing maintenance* (checked 2026-09-12) — https://dhlgcd.nt.gov.au/housing-projects-and-programs/housing-initiatives-and-strategies/remote-housing-maintenance-contracts
- NT.GOV.AU, *Remote public housing reference groups* (checked 2026-09-12) — https://nt.gov.au/property/social-housing/housing-in-remote-communities/remote-housing-reference-group
- NT.GOV.AU, *Repairs and maintenance of your public housing home* (checked 2026-09-12) — https://nt.gov.au/property/social-housing/looking-after-your-home/repairs-and-maintenance-of-your-home
- DHLGCD, *Contacts* and *Useful contacts* FS04 (checked 2026-09-12) — https://dhlgcd.nt.gov.au/contacts
- DHLGCD fact sheet FS17, *Repairs and maintenance*, 10/2025 — https://dhlgcd.nt.gov.au/media/documents/fact-sheets/repairs-and-maintenance-fs17.pdf
- Commonwealth Ombudsman, *Remote Housing Reforms in the Northern Territory*, June 2012 — https://www.ombudsman.gov.au/__data/assets/pdf_file/0026/29627/Remote-Housing-Reforms-in-the-Northern-Territory.pdf
- ABC News, 26 Apr 2025 (lead only) — https://www.abc.net.au/news/2025-04-26/nt-communities-waiting-for-federal-labor-housing-promise/105151102

**Note on access:** `nt.gov.au` and `dhlgcd.nt.gov.au` sit behind Cloudflare and refused direct fetches
on 2026-09-12; those pages were read through the search index rather than opened. The Menzies Final
Report and the Handbook were downloaded and read in full text. Exact regional phone numbers were not
verified character-by-character and are not load-bearing.
