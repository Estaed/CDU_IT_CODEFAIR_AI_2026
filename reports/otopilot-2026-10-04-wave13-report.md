# otopilot report, 4 October 2026: wave 13 (Task-28)

Plan: `reports/otopilot-2026-10-04-wave13-plan.md`. One Codex bee (`gpt-6.1-sol`/`high`, network
on) built the task. The orchestrator (Claude `opus`, this session, at 96% of its weekly pool)
gated, looked at the screens and integrated. No Claude or Jev call was made.

## Outcome

| Task | Outcome | Attempts | Bee time | Lane gate | Main SHA | Main gate |
|---|---|---|---|---|---|---|
| Task-28 | green, eye check pending: 1 | 1 | 44 min (16:28–17:12) | exit 0, 254 passed, 8 skipped | `34a36d3` | exit 0, 254 passed, 8 skipped; `git status` clean |

Baseline at BASE_SHA `a074899`: gate exit 0, 257 passed, 0 skipped.

## What changed (checked by the orchestrator)
- **Home screen:** A-0142 alone (W-01 has no run until Task-29). E-01..03, H-01 and `stub` are off the
  home screen; `eval` still runs them, and its replay test passes.
- **Deleted:** the CDU list, S-01 (case and run), `scripts/fetch_cdu_policy.py`, and their tests.
  The orchestrator also removed the git-ignored local cases `runs/U-*` and `data/uploads/U-*` (2 each)
  and `data/policies/cdu-extension/` from the main checkout.
- **W-01:** 24 PDFs, facts.csv, gold.json and its intake note in `data/cases/W-01/`.
  `scripts/fetch_wwcc_rules.py`, run on main, downloaded both rule PDFs and each matched its pin
  (`data/policies/nt-wwcc/policies.lock.json`). `git ls-files data/policies` holds only the two lock files.
- **Intake note:** both texts are word for word the task's.
- **Evaluation:** `runs/eval/` is byte-identical; even H-01's `changed_result_files` did not change.
- **Accessibility:** axe-core 4.10.3 on 6 surfaces × 2 widths: 0 violations, 0 serious or critical.
  16 keyboard actions were checked by hand. Details in `reports/2026-10-04-accessibility.md`.

## Deviations and findings
- **A spec contradiction in the task, resolved by the bee:** goal 3 says the note text "comes from
  a field in the case folder", but `data/cases/A-0142/**` is MUST NOT TOUCH. A-0142's note sits in
  `web/case-notes/A-0142/intake-note.json`; W-01's sits in its case folder. The screen reads either.
- **8 skipped tests (0 before):** `test_home.py:92` (2) and `test_screen.py:182` (6) iterate over
  cases whose list has its own words (Task-24). S-01 was the only one, so the set is now empty.
  They run again once W-01 has a run (Task-29).
- **Header subtitle:** the home screen still says "Priority housing review · Darwin urban". With
  W-01 on the home screen that line would be wrong. Left for Task-29 / the eye check.
- The bee could not write the git index (sandbox); the orchestrator made the one commit in the lane.

## Awaiting eye check
- Task-28 (eye): open A-0142 (`uv run python -m readmark serve`, then "Open case"). The intake note
  should say what the file is in under ten seconds and hint at no outcome; the mark, icons and boxes
  should look sober next to `reports/screens/ui-references/mock-6-gov-filepanel.png`. Screenshots:
  `reports/screens/2026-10-05-wave13/` (home, case with intake note, question; 1280 and 1440).

## Quota
- Codex: 5-hour 0% → 25%; weekly 57% → 61%.
- Claude: weekly 96% → 97% (at its wall); resets 21:30.

Run closed: tasks consumed
