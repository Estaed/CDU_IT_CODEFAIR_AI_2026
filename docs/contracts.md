# Data contracts (Fixed for wave 1)

Every wave-1 task reads and writes these formats. Changing one is a Blueprint-level change, not a
task-level one.

## Policies
- **Files:** the five PDFs live in `data/policies/` (git-ignored). Tarık downloads them by hand from
  dhlgcd.nt.gov.au, because Cloudflare blocks scripts:
  - `priority-housing-policy.pdf`: <https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/accessing/priority-housing-policy.pdf>
  - `eligibility-for-social-housing-policy.pdf`: <https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/accessing/eligibility-for-social-housing-policy.pdf>
  - `identification-and-documentation-policy.pdf`: <https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/accessing/identification-and-documentation-policy.pdf>
  - `domestic-family-violence-policy.pdf`: <https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/living/domestic-family-violence-policy.pdf>
  - `discretionary-decision-making-policy.pdf`: <https://dhlgcd.nt.gov.au/media/documents/policies,-procedures-and-guidelines/foundations/discretionary-decision-making-policy.pdf>
- **Read-only fallback:** if a PDF is missing, its text can be read through `https://r.jina.ai/<url>`,
  which keeps the "Page x of y" markers. A text fallback is never pinned or committed.
- **`data/policies/policies.lock.json`** (committed): `{file: {url, version, approved, sha256, pages}}`.

## Decisive clauses (ids used everywhere)

| clause_id | Source | What the officer decides |
|---|---|---|
| `elig-residency` | Eligibility §3.2 | Australian citizen or permanent resident |
| `elig-property` | Eligibility §3.1.1 | Owns no residential property (DFV exemption with delegate approval) |
| `elig-income` | Eligibility §3 | Urban applicants must also meet the income criteria. The Income and Assets policy is not bundled, so v1 decides only whether income evidence is in the file |
| `elig-debts` | Eligibility §3.4 | Debt to the CEO (Housing) does not withhold housing |
| `elig-former-tenancy` | Eligibility §3.5 | Tenancy terminated for breach in the last 2 years means ineligible for 2 years |
| `prio-category` | Priority §3 | One of: young person transitioning from care; at risk of homelessness; serious medical or social problems; domestic or family violence |
| `prio-documentation` | Priority §3.1 | Urgent need proven with supporting documentation (see the Identification and documentation policy) |
| `prio-discretion` | Priority §3.1 + Discretionary decision making | "some discretion for extreme situations" |

## Case file: `data/cases/<case_id>/case.md` (held-out: `data/heldout/<case_id>/case.md`)
- UTF-8 markdown. Every page starts with a line `<!-- page N -->`, with N from 1 and consecutive.
- A document starts with a line `## Document: <type> | <title> | <date YYYY-MM-DD>` on its first page.
  `<type>` is one of the document types the Identification and documentation policy names, or
  `letter`, `ledger`, `tenancy-record`, `form`, `medical`, `statutory-declaration`, `other`.
- Paragraphs are separated by a blank line.
- A passage id is `<case_id>:p<N>:<k>`, where k is the 1-based paragraph index on page N. The ingest
  step computes it; the file never contains it.
- Every person and organisation is invented. Real NT place names are allowed. There are no real
  addresses, phone numbers or ID numbers.

## Facts table: `facts.csv` next to each `case.md`
Columns: `fact_id, clause_id, statement, value, page, quote, role, trap, decisive`
- `quote` is a verbatim substring of page `page`, after collapsing whitespace.
- `role` is one of `supports | against | contradicts | stale | missing`. For `missing`, `page` and
  `quote` are empty and `statement` says what is absent.
- `trap` is one of `none | stale_value | contradiction | omission | policy_misread | exclusion_2yr | missing_doc | discretion`.
- `decisive` is `yes` or `no`.

## Gold: `gold.json` next to each `case.md`
```json
{"case_id": "...", "outcomes": {"<clause_id>": "met|not_met|cannot_decide|not_applicable"},
 "correct_decision": "approve|decline|request_information",
 "required_reading": ["p8", "p23", "..."],
 "rationale": {"<clause_id>": "one sentence citing a verbatim policy quote and file pages"}}
```

## Mutation set: `mutations.jsonl` next to each `case.md` (evaluation files only)
One JSON object per line:
`{"summary_id", "claim", "mutation_type", "source_fact_id", "label"}`
- `mutation_type` is one of `none | number_swap | date_swap | negation | stale_value | entity_swap | omission | policy_misread`.
- `label` is one of `supported | contradicted | unsupported`.
- Each evaluation file has one correct summary of 6–10 claims and at least one mutation of each
  applicable type.

## Run outputs: `runs/<case_id>/<stage>.json`
Each stage writes one JSON file named after the stage (`passages`, `writer`, `checks`, `jev`, `gate`,
`view`, ...). Live model responses are cached under `runs/<case_id>/cache/` keyed by a hash of the
request. These files hold offsets and hashes, never policy text, apart from the short quotes the
screen shows. Task-00 documents `view.json` in `readmark/schemas/`.
