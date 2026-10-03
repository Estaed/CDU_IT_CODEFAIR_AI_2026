# otopilot report, 3–4 October 2026: waves 8–11 (v1.1, everything before submission)

Plan: `reports/otopilot-2026-10-03-wave7-plan.md`, extended by Tasks 24–26 on Tarık's word. Every
builder was a Codex bee (`gpt-6.1-sol`/`high`). The orchestrator (Claude `opus`, this session)
wrote the tasks, gated, reviewed the screens, ran the live checks and integrated. Tarık was asleep
from about 01:00; no question was asked after that.

## Outcomes

| Task | What | Outcome | Rounds | Main SHA | Main gate |
|---|---|---|---|---|---|
| Task-19 | Case home screen | green, eye check pending | 1 | `5012833` | 132 passed |
| Task-21 | Easy example S-01 (main loop) | green, eye check pending | — | `dcce8dc` | 127 passed |
| Task-24 | Case screen uses its list's words | green, eye check pending | 1 | `96cb9f2` | 145 passed |
| Task-25 | "Needs a look" against "worth a look" | green, eye check pending | 1 + 1 fix | `ed9dd9a` | 168 passed |
| Task-20 | New case: upload several documents | green, eye check pending | 1 | `d5c17d3` | 192 passed |
| Task-22 | Scanned pages read by Claude | green, eye check pending | 1 | `22529a5` | 206 passed |
| Task-23 | Search: words, and meaning through Jev | green, eye check pending | 1 | `14ae313` | 216 passed |
| Task-26 | Question-list coverage through Jev | green, eye check pending | 1 + 1 fix | `48bea6e` | **245 passed** |

## Live checks (orchestrator)
- **Task-20 upload:** two text PDFs from S-01 (form and certificate), list `cdu-extension`. Ready in
  50 s: one Claude call (42 s), 14 notes, highlights from both documents.
- **Task-22 scan:** an image-only PDF of two S-01 pages. Ready in 90 s: transcription took 21 s and
  19.5 s, then the writer 44 s. 14 notes, with quotes verified against the transcription.
- **Task-23 meaning search,** A-0142, "March statement":
  - word search finds only p.24, where the literal phrase appears (0.9 s);
  - meaning search puts **p.23, the March statement, first** (Jev score 3.85, 2.3 s).
- **Task-26 coverage (live Jev):**
  - `cdu-extension`: **6 of 264** paragraphs, including (74) special consideration (scope 3.34),
    (78) late penalty (scope 2.74) and the seven-day cut-off;
  - `nt-priority-housing`: **12 of 368**, including age 15+, proof of residency, the income and
    assets threshold, and non-residential property. None of these is among today's 8 questions.

## Review findings and fixes
- **Task-25:** "Open before you sign" listed "Page 5" twice. Fixed in one round: rows now add the
  paragraph when a page repeats.
- **Task-26: the first run reported 52 and 56 suggestions,** mostly rules about other matters.
  - The orchestrator first counted a scope filter on the stored suggestions (live Jev, 3 calls): 7/52
    and 13/56 kept.
  - The fix round added a per-list `scope` sentence and the filter. The live run kept 6/52 and 12/56.
- **Intro panel:** numbers fell onto their own lines. Fixed (`2a44a6c`).
- **The gate went red because of a local upload** (`U-*` folders under `runs/`). Tests now skip
  local uploads (`11a8ef6`).
- **One screen colour check was a one-shot read** that failed under load. It is now a retrying
  `to_have_css` (`684b542`).
- **H-01's `changed_result_files` grew with every checklist or ingest change.**
  - `runs/eval/cases.json` and `summary.json` were regenerated each time, and only path lines
    changed. **No evaluation number changed.**
  - `readmark/eval/discipline.py` now treats question-list coverage files as non-result code.

## Process notes
- **Pushed on red once** (`2a44a6c`): the push ran on its own line, not chained to the gate. The next
  commit fixed it, and from then on the push was chained (`gate && commit && push`). Logged in
  `gardener.py`.
- **One brief was patched after launch** (Task-26: a PATH line with a control character). The bee
  made no Claude calls.

## Quota at closeout (04:45)
- Claude weekly: 93%. It resets on 4 Oct at 21:30.
- Codex 5-hour: 96%, at its wall. It resets in about 30 min.

## Awaiting Tarık's eye
Tasks 15 (2 checks), 16, 17 (2 checks), 19, 20, 21, 22, 23, 24, 25 and 26, plus `clauses.yaml`.
Start with the home screen: `uv run python -m readmark serve`, then open http://localhost:8765/.

- Two local test cases from the live checks, "Live upload test" and "Live scan test", sit under In
  progress. They are git-ignored; to remove them, delete `runs/U-*` and `data/uploads/U-*`.
- A-0142 opens on its decision record, because of a record signed locally on 3 Oct at 20:07 (also
  git-ignored, in `runs/A-0142/records/`).

## Next
- **7 Oct:** freeze the numbers, with a one-page sheet for the teammate.
- **8 Oct:** the ZIP.
- **Visual nits for the eye check:** stacked highlight tags in one paragraph (Task-22); "1 pages".

Run closed: tasks consumed (v1.1)
