# Easy example S-01: a student's assessment extension under the real CDU rule (2026-10-03)

The easy example from Task-21. Tarık asked for it so he can follow the system without housing law.
It is also an internal test: a real rule, and a file that no Claude stage saw before its run.

## The rule
- **Source:** CDU, "Higher Education Coursework Assessment Policy and Procedure",
  <https://policies.cdu.edu.au/view-current.php?id=177>. Read on 2026-10-03.
- **Status:** current. Effective 1 March 2026; approved by the Academic Board on 29 October 2025;
  review date 1 March 2029 (from the policy's "Status and Details" page).
- **Terms:**
  - CDU's copyright notice allows downloading, displaying, printing and reproducing the material
    "for private use or use within your organisation, for non-commercial purposes only". It grants
    no licence to publish.
  - So the policy text is not in the repo. `scripts/fetch_cdu_policy.py` rebuilds it locally into
    `data/policies/cdu-extension/` (git-ignored).
  - `list.yaml` pins it by SHA-256. Two fetches gave the same hash, `1562db50…`.
  - The screen shows only the five question sentences and short quotes.
- **The question list `cdu-extension`:** five questions, each resting on one verbatim sentence.

| Question | Procedure |
|---|---|
| Asked before the due date | (64) |
| A listed reason | (66), with its 8 listed grounds |
| Request form complete | (68), with its 5 required items |
| Evidence for more than 72 hours | (65) |
| Seven days at most | (71) |

## The file S-01
- **Facts first:** the orchestrator wrote `facts.csv` (12 facts) and `gold.json` before any model
  ran.
- **The text:** Codex (`gpt-6.1-sol`) wrote `case.md` from the facts. It has 7 pages and 1,172
  words: the Learnline request form, a GP certificate, the student's email, the unit outline, the
  draft upload receipt, the extension register and the lecturer's acknowledgement. Codex's own check
  found all 12 quotes verbatim and none of the forbidden words.
- **The intended answers:** three questions are clean (deadline, reason, length). Two need the
  officer:
  - the form asks for 17 September, but the email says 16;
  - the certificate covers 9 to 12 September only, but the request runs to 17 September.

## The run
- **One live run:** 3 Oct, 22:31. One Claude call (`opus`, 56 s), and Jev as the checker.
- **Output:** 19 notes; 8 required passages, with 6 more suggested.
- **Quota:** the Claude weekly window read 91% both before and after; the run cost less than one
  point.
- **Offline replay:** `python -m readmark run --case S-01 --replay`, with no key and `claude` off
  PATH, reproduces `runs/S-01/` byte-identical. It needs the local policy text, as A-0142 needs the
  NT PDFs.
- **Isolation:** the A-0142, E-01..03 and H-01 replays and every number in `runs/eval/` are
  unchanged. `cases.json` and `summary.json` changed only in H-01's `changed_result_files` list.

## How the checks did (n = 1 file, 5 questions, 19 notes)

| What | Result |
|---|---|
| The AI's notes name both problems | **2 of 2.** "The student's email says the form asks for Wednesday 16 September, but the form itself proposes Thursday 17 September 2026." "The certificate period ends several days before the proposed new due date, so it does not cover the whole extension asked for." |
| Notes whose quote was verified | 19 of 19 supported; 0 quote not found |
| The date disagreement as a "two pages disagree" flag | **found:** p.1 against p.3 (17 against 16 September). It sits under "Seven days at most", not under "Request form complete" |
| The certificate gap as a flag | **not flagged.** The note stating it is correct, so nothing is wrong to flag. The officer sees it only by reading the notes or the page |
| Questions with a flag | 5 of 5, where the intent was 2 of 5. Four carry only "possibly missed" |
| Required reading against the intended pages (p.1, p.2, p.3) | p.1 and p.3 are required. **p.2, the certificate, is not** |
| "Possibly missed" passages | 6, all on pages 3 and 5 (the email and the upload receipt). Those on page 3 bear on the case; those on page 5 are noise |

## What this tells us
- **On a short, clean file, Claude's notes did the real work.** They named both everyday problems
  in plain words, and every one of them was verified in the file.
- **The "possibly missed" scan over-flags short files.** Almost every paragraph of a 7-page request
  is relevant to some question, so the screen flagged 5 of 5 questions where the intent was 2. That
  is the opposite of the calm "half clean" page Tarık asked for.
- **A correct note that states a problem raises no flag,** because the checks flag only notes that
  fail. The certificate gap therefore does not reach required reading.
- These are findings, not fixes. Changing the scan or the gate now would change the frozen numbers
  due on 7 Oct. The orchestrator brings both to Tarık to decide.
