# Task-20: README, reproduction steps and submission zip

> **Execution:** agent `claude` (main loop) · effort `medium` · plan mode **no**
> *Why:* the README is judge-facing prose and the zip contents are a submission decision; the packaging script itself is mechanical and tested.

**Lane**
- OWNS: `README.md` (rewrite the "Scaffolding" section into run instructions; keep the competition sections), `scripts/package_submission.py`, `tests/test_package.py`
- MUST NOT TOUCH: `docs/` transcripts, `data/`
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-12, Task-19

## Objective

A judge with Python 3.13 and no accounts runs the app from the zip in three commands, and
the zip contains exactly what the submission rules ask for.

## Execution Guide

- README: three commands (`python -m venv venv`, `venv\Scripts\pip install -r requirements.txt`, `venv\Scripts\streamlit run fair_turn/app/main.py`) plus the POSIX variants; what each page shows in one line; how the build pipeline is rerun and that generation and extraction need a logged-in `claude` / `codex` (subscriptions), everything else runs offline; where the eval numbers are; the provenance and pseudonym statement; licence list from `PROVENANCE.md`.
- `package_submission.py`: builds `dist/AI-Challenge_Team-<N>_FairTurn.zip` from a fixed include list (`fair_turn/`, `scripts/`, `tests/`, `data/build/`, `data/geo/`, `data/raw/PROVENANCE.md`, `data/audit/sample.jsonl`, `docs/PRD.md`, `README.md`, `pyproject.toml`, `requirements.txt`, `uv.lock`, `.streamlit/config.toml`); excludes `venv/`, caches, the 20 MB BushTel detail JSON (README says how to refetch); refuses to run if the gate is red or the tree is dirty; team number from a CLI argument (PRD open question 3).
- Tests: build to a temp dir, assert the include list is present, the excluded paths absent, and the zip is under 15 MB.

## Acceptance Criteria (DoD)

- [ ] README commands verified by running them in a fresh `venv` (manual, dated note in this file).
- [ ] `test_package.py` passes; the script refuses on a dirty tree (tested with a temp file).
- [ ] Gate green.
