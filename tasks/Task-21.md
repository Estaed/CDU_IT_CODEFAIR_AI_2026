# Task-21: The easy example: a student's assessment extension under the real CDU rule
> **Execution:** agent `main-loop` · effort `high`
> *Why:* Tarık, who does not know housing law, needs an example he understands at once to follow
> the whole system. It is also an internal test against a real rule (2026-10-03: "kolay örneği sen
> yap hallet"). The orchestrator builds it. Codex writes the case file, a different model family
> from the reader (Blueprint).

**Lane**
- OWNS: `data/cases/S-01/**`, `data/policies/cdu-extension/**`, `readmark/checklist/lists/cdu-extension/**` (or wherever Task-18 puts lists), `runs/S-01/**`, `reports/2026-10-0x-easy-example.md`
- MUST NOT TOUCH: `web/**`, `readmark/serve.py`, `readmark/record/**` (Task-19); all other code; `runs/A-0142/**`, `runs/E-*/**`, `runs/H-01/**`, `runs/eval/**`; `design/**`, `docs/contracts.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: Task-18

## Contract (main loop, 2026-10-03)

**The rule.** CDU, "Higher Education Assessment (Coursework) Policy and Procedure"
(<https://policies.cdu.edu.au/view-current.php?id=177>), read on the day it is fetched. It is the
real source of the questions.
- **Before use:**
  - confirm the page is public;
  - read its copyright and AI-use terms;
  - record the version and date.
- **Same handling as the NT policies:**
  - the PDF is downloaded by hand and git-ignored;
  - a lock file pins its SHA-256;
  - only short quotes are shown on screen.

**The question list `cdu-extension`.** Five or six questions, each with its verbatim policy
sentence, for example:
- were the grounds for an extension among those the procedure lists;
- was the request made before the due date (after it, the request becomes special consideration);
- is the extension asked for within the days the procedure allows;
- is there supporting evidence;
- for special consideration, was the request made within the working days the procedure allows.

The exact wording comes from the fetched document, not from this list. Tarık approves the list at
the eye check.

**The case S-01.** A synthetic student file of 6–8 pages, written by Codex from a facts table the
orchestrator writes first. No real person's details. Its documents:
- the extension request, modelled on CDU's real form;
- a medical certificate;
- email exchanges with the lecturer;
- a unit outline extract with the due date;
- a submission receipt.

About half the questions come out clean. The flagged ones are everyday ones:
- the certificate covers fewer days than the extension asked for;
- the date on the form and the date in the email disagree.

There is a `gold.json` like E-01's.

**The run.**
- One live pipeline run: the Claude writer and Jev. Measure the Claude quota first.
- After that, the case replays offline from `runs/S-01/`, with no key.

## Goal
S-01 opens on the screen with its own list. Tarık can follow every question without knowing any
law. It replays offline.

## Why
It lets Tarık understand the system, and gives an internal test on a real rule that no Claude stage
has seen.

## Acceptance
- [ ] `uv run python scripts/gate.py` exits 0, and `git status` shows no change after it runs.
- [ ] `python -m readmark run --case S-01 --replay` succeeds with no key and no `claude` on PATH,
  and `view.json` validates against the schema.
- [ ] The A-0142, E-* and H-01 replays and `runs/eval/` are byte-identical.
- [ ] `reports/2026-10-0x-easy-example.md` records the policy source, its date and terms, the
  facts table, and how the checks did against `gold.json` (with n).
- [ ] (eye) Tarık opens S-01 and understands what each question asks and why each flag is there.

## Out of scope
- Counting S-01 in the frozen evaluation numbers (7 Oct). It is reported separately.
