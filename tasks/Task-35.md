# Task-35: Integration: five-surface smoke, offline proof, README, submission package, docstring citations

Status: DONE

> **Execution:** agent `codex` · effort `medium` · plan mode **no**
> *Why:* Cross-cutting checks and documentation with a command for every item; the "Runs in the room" bar in PRD §7 is the criterion.

**Lane**
- OWNS: `tests/test_app_smoke.py`, `README.md`, `scripts/package_submission.py`, `tests/test_package.py`, `fair_turn/app/pages/workspace.py` (override-rate caption in the header only), docstring first lines citing "PRD 3.x" across `fair_turn/` (citation text only), `design/phase-2-wireframes.md` (§4: "dialog" → in-page container, one sentence)
- MUST NOT TOUCH: any `fair_turn/core/` logic, `docs/PRD.md`, `CLAUDE.md`
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-31, Task-32, Task-33, Task-34

## Objective

Prove the Phase 2 app renders every surface offline with no provider, document how a judge
runs it and how to enable intake, and ship the new artefacts in the zip.

## Execution Guide

- Smoke test: with sockets refused and `FAIR_TURN_PROVIDER` deleted, open every page in `pages/`; assert no exception, the provenance caption on each, the intake button disabled with its reason on the workspace, the visit plan's unsigned message, no "median wait" text before a signature, at least one Vega-Lite chart on the evidence lab. Add the header caption "Override rate: N %" from `audit.override_rate` linking to the evidence lab.
- README: run command unchanged; new section "Live intake (optional)": `FAIR_TURN_PROVIDER=claude` with a logged-in `claude`, what is stored under `data/runtime/`, that nothing is required to run; new section "Policy index": `build_policy_index.py` needs Ollama with `bge-m3`, the artefact is committed; the licence status of FS17 (PRD open question 6). PowerShell and Git Bash forms of every command.
- `package_submission.py`: include `data/build/policy_passages.json`, the FS17 PDF and PROVENANCE row, exclude `data/runtime/`; `test_package.py` asserts both.
- Docstrings: update "PRD 3.x" citations in the files that survive to the Phase 2 numbering (3.1 workspace, 3.2 review queue, 3.3 visit plan, 3.4 tenant, 3.5 evidence lab); a test greps `fair_turn/` for `PRD 3.6` and fails if any remains.

## Acceptance Criteria (DoD)

- [ ] Offline smoke test over all five surfaces passes with sockets refused and no provider.
- [ ] Zip contents asserted (policy artefact in, runtime out).
- [ ] README documents intake and the policy index in both shells; no `PRD 3.6` citation remains.
- [ ] Gate green.
