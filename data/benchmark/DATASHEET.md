# Readmark synthetic cases — datasheet

**Creation and composition.** Codex GPT-6 wrote `facts.csv` first, then each `case.md`, then `gold.json` and the mutations, using the five local NT public-housing PDFs and the fixed scenario. The case pages were rewritten as dated forms, letters, ledgers, records and declarations on 3 October 2026. Applicants and case-specific organisations are invented; Darwin and Palmerston are real places. A-0142 is the demo; E-01 tests a breach termination, E-02 missing urgent-need documentation, and E-03 a possible discretion referral. The set contains cases n=4, pages n=96 and facts n=47. Word counts per page, including document headers: A-0142 mean 221.1, minimum 161; E-01 mean 213.8, minimum 182; E-02 mean 214.8, minimum 183; E-03 mean 210.1, minimum 178.

**Why these document types appear.** All types are permitted by `docs/contracts.md`; these policy sentences explain the evidence each carries:

| Type | Policy basis |
|---|---|
| `form` | Priority §3: “New applicants may apply for priority housing when they first complete their application for social housing.” |
| `letter` | Priority §3.1: “Applicants must prove their urgent need for priority housing and are required to provide documentation that supports their claim for priority.” DFV §3.5 lists a support-service letter. |
| `medical` | Identification and Documentation §2: “Applicants who require special consideration or priority housing due to medical or social needs must also provide evidence of those needs.” |
| `statutory-declaration` | Eligibility §3.2: “Applicants must be an Australian citizen or have permanent residency status.” Declarations of residence and property are checked with other records. |
| `ledger` | Eligibility §3.4: “The CEO (Housing) will seek to recover outstanding debts in line with the Debt Management policy.” |
| `tenancy-record` | Eligibility §3.5: “An application will not be accepted until the 2-year period has expired.” The record establishes the termination ground and date. |
| `other` | Identification and Documentation §3.1: “In establishing identity, documents must be provided which verify the client’s full name and date of birth.” Appendix 1 lists utility accounts; §3.2 requires income and asset evidence. |

**Labels.** A-0142 has stale value n=1, contradiction n=1, omission n=3 and policy misread n=1. E-01 has two-year exclusion n=2 and policy misread n=1. E-02 has missing documentation n=4. E-03 has discretion n=4, stale value n=1 and contradiction n=1. Each E-file has correct claims n=8 plus labelled mutations n=7: one each for number swap, date swap, negation, stale value, entity swap, omission and policy misread. Total correct claims n=24; total mutations n=21. Trap tags describe constructed risks, not errors observed from a live model.

**Licence, use and limits.** The original synthetic cases and labels are CC BY 4.0. The five NT Government policy PDFs are NTG copyright, are not bundled, and contribute only short attributed quotes in gold rationales. These files support Readmark development, replay and claim-checking evaluation. They contain no real client data and are not evidence of real-world accuracy or a representative sample of NT applicants. Income limits and discretionary authority require the normal policy process; a delegated officer makes any actual decision.
