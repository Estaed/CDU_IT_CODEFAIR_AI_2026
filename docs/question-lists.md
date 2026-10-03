# Question lists

A person approves every question list before it is used. The AI does not write or approve
the questions, choose an outcome, or turn missing evidence into a failed requirement.

Each list lives in `readmark/checklist/lists/<id>/`. Adding a folder needs no code change.
Use a lowercase id with hyphens. The default is `nt-priority-housing`.

- `list.yaml` holds `id`, `title` and a `policies` array. Optional `decisions` maps `approve`,
  `decline` and `request_information` to the labels the officer sees. Optional `labels` sets the
  screen's `service` name, `case_noun` (what a case is called) and `officer` (who decides). Housing
  keeps the default wording for both.
- Optional `scope` is a non-empty sentence describing the list's subject. It filters advisory
  policy-coverage suggestions only; a list without it retains the unfiltered behaviour.
- Each policy has `key`, `file`, `title` and `pin`.
- The pin has `sha256`, `version`, `approved`, `pages` and `url`, matching the existing lock format.
- `clauses.yaml` holds the approved questions: `clause_id`, `policy` (the policy key), `source`,
  `title`, `sentence` (verbatim), `decides` and optional verbatim `items`.
- Policy files are in `policies/` inside the list folder. Optional `policy_directory` in
  `list.yaml` points elsewhere, relative to that folder. Housing points to `data/policies/`.

For example, a policy entry can be:

```yaml
key: assessment
file: assessment.txt
title: Assessment rules
pin:
  sha256: <64 lowercase hex characters>
  version: "1"
  approved: "2026-10-03"
  pages: 1
  url: https://example.org/assessment.txt
```

Download policy PDFs by hand and keep restricted policy text out of git. UTF-8 `.txt` policies
are also supported: blank lines separate paragraphs; form feed separates pages. Hash the exact
file bytes, for example with `Get-FileHash -Algorithm SHA256 <file>`. Ingest checks every pin
before reading text and stops on a missing or changed file. Re-pin only after a person approves
the new version and checks every question against it. Each question sentence must be found
word for word in its named policy.

In a case folder, `question-list.json` contains `{"question_list": "<id>"}`. An absent file
uses housing; an invalid file or unknown id fails. Set the list before running the case.
Changing it after a run requires rebuilding the run and starting a new officer record.

The public API is in `readmark.checklist`:

```python
list_question_lists()                  # [{"id": ..., "title": ...}], sorted by id
load_question_list("nt-priority-housing")  # id, title, policies, policies_dir, clauses
case_question_list("A-0142")           # selected id, or the default
set_case_question_list("new-case", "assessment")  # validate and save the selection
```

All four accept `lists_dir=Path(...)`. The case functions accept `case_dir=Path(...)` for an
existing case folder. `run(..., case_file=Path(...), lists_dir=Path(...))` supports imported
cases and temporary lists. Ingest accepts `policy_passages(question_list=loaded_list)`.
`validate_view(view, loaded_list)` binds validation to that list's question ids and policy count;
the version-2 output fields stay the same. Housing keeps its frozen writer and audit contracts.
Other lists use the same writer interface with their own ids and a general officer context.

## Advisory policy coverage

Run `python -m readmark lists --coverage <list-id>` once live with `TYPESAFE_API_KEY`.
`--replay` reads only that list's `coverage-cache/`, through the existing `Cache` class;
it never reads a key or calls the network. The pinned policy downloads are still needed
locally to reconstruct the request hashes. Repeating the scan reproduces `coverage.json`
byte for byte, including the original UTC date saved with the rule-and-coverage responses.

Jev receives the approved questions (title, decision, policy sentence and items) and all
policy paragraphs in file order, in batches of 20. It gives each paragraph two scores on
a 0–4 scale: an operative rule score (0 background, 2 uncertain, 3 clear rule, 4 explicit
binding rule), and how fully at least one question asks the person to decide that specific
rule (0 none, 1 merely related topic, 2 partial, 3 substantial, 4 explicit). Policy and
question text are data, never instructions. Sharing words or mentioning another process
in passing does not cover that process's own rules.

Report a paragraph when **rule ≥ 3 and question coverage ≤ 1**. This asks for a clear
rule and a clear gap; uncertain rules and partly covered rules are left out. These are
advisory thresholds, not calibrated accuracy or a proof of completeness. No questions
are generated, approved or changed, and no case flags, outcomes or records are affected.

For a list with `scope`, score only those candidate paragraphs with the existing Jev relevance
scan, in batches of 20, against one clause-like topic: `title` is the list title, `source` is
`scope`, and both `decides` and `sentence` are the scope sentence. Paragraphs are rendered as
policy documents with the list title and date label `current`, matching the scope probe.
Keep only suggestions with **scope ≥ 2.0** on the same 0–4 scale. Store that score with each
suggestion, plus the scope sentence, threshold, scope model and `n_scope_scanned`. Scope calls
use the same list-local replay cache, storing responses rather than policy text. The home
screen count is the number left after this filter.

The orchestrator's 4 Oct scope probe kept **7 of 52** candidates for `cdu-extension`
(264 paragraphs scanned), and **13 of 56** for `nt-priority-housing` (368 scanned).
The delivered live run with the same topic and threshold kept **6 of 52** and **12 of 56**,
respectively; live model scores can vary. Its recorded responses are frozen in each list's
cache and reproduce byte for byte with `--replay`. CDU procedures **(74)** (special
consideration) and **(78)** (late penalty), and the seven-day late-submission cutoff, remain
suggestions. These counts describe suggestions, not measured accuracy.

`coverage.json` records the scanned/reported counts, thresholds, model, recorded UTC date,
policy SHA-256 pins, and each suggestion's paragraph id, section, page, scores and a verified
verbatim excerpt of at most 25 words. Even a short paragraph is never copied whole.
For text policies a leading numbered procedure supplies the section label. Responses in
`coverage-cache/` retain rule-and-coverage scores, model and date; relevance responses also
retain score distributions and model metadata. Requests and policy text are not stored.
The home screen's **Question lists** section opens these suggestions. Full paragraphs are
read on demand from the pinned local policy file in a separate policy dialog, with no
case opening time or browser draft changes. A missing local policy shows a plain error.
