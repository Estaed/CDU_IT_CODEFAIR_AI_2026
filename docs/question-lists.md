# Question lists

A person approves every question list before it is used. The AI does not write or approve
the questions, choose an outcome, or turn missing evidence into a failed requirement.

Each list lives in `readmark/checklist/lists/<id>/`. Adding a folder needs no code change.
Use a lowercase id with hyphens. The default is `nt-priority-housing`.

- `list.yaml` holds `id`, `title` and a `policies` array. Optional `decisions` maps `approve`,
  `decline` and `request_information` to the labels the officer sees. Optional `labels` sets the
  screen's `service` name, `case_noun` (what a case is called) and `officer` (who decides). Housing
  keeps the default wording for both.
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
