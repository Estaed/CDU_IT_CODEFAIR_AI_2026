# Task-14: Jev's "supports" score as a second signal for "checker disagrees"
**Status: DONE** — verified 2026-10-03
> **Execution:** agent `codex` · effort `high`
> *Why:* after Task-12, Jev's "not enough information" on true claims is the main remaining source
> of false alarms (A-0142: 15 "checker disagrees" of 19 flags, n=95). Task-08 found that Jev's
> separate "supports" score separates true from false summaries better than its verdict (AUC 0.899,
> balanced accuracy 0.857 at 0.3, n=300). Tarık agreed to try it (2026-10-03). Codex `gpt-6.1-sol`.

**Lane**
- OWNS: `readmark/checks/**`, `readmark/eval/**`, `readmark/pipeline.py`, `readmark/audit/claims.py`, `tests/test_checks_and_gate.py`, `tests/test_eval_cases.py`, `tests/test_eval_checker.py`, `tests/test_audit.py`, `tests/test_pipeline.py`, `runs/**`
- MUST NOT TOUCH: `web/**`, `readmark/serve.py`, `readmark/record/**`, `tests/test_screen.py`; `readmark/jev/**` (the checker seam stays as it is), `readmark/writer/**`, `readmark/audit/claude.py`, `readmark/audit/__init__.py`, `readmark/schemas/**`, `readmark/ingest/**`; `data/**`, `design/**`, `docs/contracts.md`, `AGENTS.md`, `notes.md`
- GATE: `uv run python scripts/gate.py` (from repo root)
- DEPENDS ON: none

## Goal
- **Choose the rule on outside data only.** On the committed SummEdits sample and its cached Jev
  verdicts (`runs/eval/cache/jev-run1`, n=300), compare two rules for "Jev backs the claim":
  - the verdict alone (today);
  - the verdict or the "supports" score at or above a threshold.

  Choose the threshold that maximises balanced accuracy on SummEdits. Record the rule, the
  threshold and both balanced accuracies, with n, in the checker part. No Readmark case (A-0142,
  E-files, H-01) may inform the choice.
- **Apply it.** A claim gets "checker disagrees" only when Jev does not back it under the chosen
  rule. Nothing else changes: the code checks, contradiction pairs, the scan and required reading
  keep their rules.
- **Re-measure from the cache**, with no Claude call and no Jev call. Report before and after, each
  with n, for:
  - the A-0142 and H-01 summary audits by status;
  - H-01's labelled flags by class (real error, file inconsistency, false alarm);
  - the mutation set's catch rate and false alarms;
  - the gold pages in required reading for every file.
- **Keep the record honest.**
  - H-01's first-run numbers stay frozen.
  - The new numbers are labelled "after changes, not held-out".
  - If a real error (a36 or a47 on A-0142, a52 on H-01) or a caught mutation stops being flagged,
    the report names it, with its Jev verdict and score.

## Why
"Checker disagrees" is the flag the officer sees most. If most of them are wrong, the officer learns
to ignore it, and the one that matters is skipped with the rest.

## Acceptance
- [x] `uv run python scripts/gate.py` exits 0.
- [x] A test: on a hand-made set, a claim with verdict "not_enough_information" and a "supports"
  score above the threshold is backed; one below it is not; a "contradicts" verdict is never backed
  by the score alone.
- [x] The checker part records the rule, the threshold and both balanced accuracies on SummEdits,
  with n. A test checks that the threshold is computed from SummEdits alone.
- [x] Every rebuilt run replays twice with `TYPESAFE_API_KEY` unset and `claude` off PATH, and gives
  byte-identical output.
- [x] `runs/eval/summary.json` carries before and after for each headline number, each with n, and
  H-01's first-run numbers unchanged.
- [x] The builder's report states plainly whether the change helps: false alarms removed, real
  errors kept, catches lost. If the rule loses a real error or a caught mutation, it is still
  reported, and the decision to keep it is left to Tarık.

## Out of scope
- Changing Jev's questions or the checker seam; Claude as a second vote; the screen.

Fixed: the parts seam; stage file names; CLI verbs and flags. Screen tests read `view.json` and must
pass unchanged.
