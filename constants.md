# Constants — values that must not be retyped

Delete these instructions once real values exist. If this project has no such
values, delete the file and say so in Part 2.

## Why

An address, an endpoint, a contract ID, an account number: typed once it is
data, typed twice it is a bug waiting for the two copies to disagree. Agents
are especially good at confidently reproducing a *nearly* correct constant.

One file, one definition each. Part 2's Key Constraints should forbid
hardcoding anything listed here.

## Rules

- Every entry: the name, the value, what it is for, and where it came from
  (the doc, the deploy, the person). A constant with no provenance cannot be
  verified later.
- Environment-specific values get one row per environment, never a single
  value that silently means "whatever I last used".
- **Secrets do not go here.** This file is committed. Keys, tokens and
  passwords belong in `.env` (already gitignored) and are referenced by name.
- When a value changes, change it here and let everything else read from here.

## Values

| Name | Value | What it is for | Source |
|---|---|---|---|
| | | | |
