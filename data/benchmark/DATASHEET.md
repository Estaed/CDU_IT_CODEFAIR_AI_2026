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

**Mini-benchmark release (Task-10).** `facts.csv` preserves each source fact, with a `case_id`
column. `gold.csv` has one row per clause outcome, its rationale, the file's correct decision
and a semicolon-separated list of required pages. `mutations.csv` preserves every evaluation
sentence, its source fact, mutation type and gold label. The source files remain unchanged.
The release includes A-0142, E-01, E-02, E-03 and the separately constructed held-out H-01
(cases n=5); the mutation CSV contains E-01..E-03 only (claims n=45, supported controls n=24,
labelled errors n=21). See `runs/eval/benchmark.json` for released row counts and their n.

**Generation and held-out discipline.** The original cases were built facts-first by Codex,
then expanded into synthetic documents and labelled against the fixed clause checklist.
H-01 was constructed separately and sealed before evaluation. The evaluator freezes hashes
of the implementation, schemas, clause checklist and lockfile before H-01's single live run.
The scorer reads its seal, facts and gold only after the completed run; none of those labels
are supplied to the writer, audit locator or checker. Its run marker records the last code
change, freeze, start and completion times. A second live run is refused. All live responses
are cached, and replay requires no model key. Releasing H-01's labels makes this file public:
it must not be called an unseen test for future versions.

**Trap taxonomy.** Fact tags describe risks planted in the file: `stale_value` (an old amount
presented as current), `contradiction` (records disagree or supersede each other), `omission`
(decisive evidence overlooked), `policy_misread` (a policy consequence stated incorrectly),
`exclusion_2yr` (a tenancy breach within the exclusion period), `missing_doc` (a required
document absent), and `discretion` (an extreme situation requiring an authorised decision).
`none` marks an ordinary fact. Mutation types are `number_swap`, `date_swap`, `negation`,
`stale_value`, `entity_swap`, `omission`, and `policy_misread`; `none` marks supported controls.
The omission mutations are explicit false claims about absent evidence, not a measure of
all facts a free-text summary leaves unstated. The supported/contradicted/unsupported labels
are synthetic builder labels, not independently adjudicated officer decisions.

**Scoring and limits.** A mutation is caught when the audit claim path returns any status
other than supported. False alarms are measured only on supported controls. A trap is touched
when a flag under its clause names a passage containing the exact fact quote; facts with no
page use the clause's explicit missing-evidence flag. Required and suggested touches remain
separate. A touched trap is a review lead, not a verified summary error. The held-out summary
has no independent error labels: its flag counts cannot establish real-error precision.
The cumulative ablation accepts proposed claims for its unvalidated Claude-alone baseline;
it does not perform an additional Claude-as-checker experiment. The scan adds reading leads,
not mutation verdicts. These small constructed files test particular failure classes, and
the forced cap is a product constraint, not evidence that eight passages always suffice.

**Reuse and attribution.** The released synthetic CSVs use the same CC BY 4.0 licence as
the original cases: attribute the Readmark team, AI Challenge 2026, CDU IT Code Fair 2026.
Real NT policy material remains NT Government copyright; download the pinned PDFs separately
using the README. The external SummEdits checker sample has its own provenance and licence
notes in `summedits/README.md`; it is separate from these synthetic CSVs.
