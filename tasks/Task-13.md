# Task-13: App shell, artefact loader, session state, offline smoke test

Status: DONE

> **Execution:** agent `claude` (main loop) · effort `high` · plan mode **no**
> *Why:* sets the Streamlit patterns every page task copies (navigation, cached loading, session state keys, socket-blocked smoke test); an architecture-shaped task.

**Lane**
- OWNS: `fair_turn/app/main.py`, `fair_turn/app/state.py`, `fair_turn/app/pages/` (stubs only), `fair_turn/data/artefacts.py`, `tests/test_app_smoke.py`
- MUST NOT TOUCH: `fair_turn/app/theme.py` (Task-00), page bodies beyond the stub (Task-14 to Task-19)
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-07, Task-11

## Objective

A running app with six navigable pages, one cached loader for every artefact, one
session-state module, and the headless smoke test that proves the app needs no network.

## Execution Guide

- `data/artefacts.py`: `load_all() -> Artefacts` (communities, labels, reports, extraction, closures, climate, audit path) from `data/build/` and `data/audit/`, validated through the pydantic schema for extraction rows; pure file reads.
- `app/main.py`: `st.set_page_config`, `st.navigation([st.Page(...)] * 6)` with titles Triage board, Job card, Sign-off, Tenant view, Feedback loop, Audit log; the provenance line from `theme.PROVENANCE_LINE` in the sidebar; `@st.cache_data` around `load_all`.
- `app/state.py`: typed accessors for session keys: `today`, `region`, `lam`, `signed_today: bool`, `selected_job_id`, `audit_path`. No page reads `st.session_state` directly.
- Pages: each stub renders its title and the provenance line; bodies come in later tasks.
- `tests/test_app_smoke.py`: a fixture that monkeypatches `socket.socket` to raise; runs `AppTest.from_file("fair_turn/app/main.py").run(timeout=60)` and then each page file individually, asserts `not at.exception`; parametrised over the six page files.

## Acceptance Criteria (DoD)

- [ ] `venv/Scripts/streamlit run fair_turn/app/main.py` starts (manual, not gated) and the smoke test passes for `main.py` and all six pages with sockets blocked.
- [ ] `load_all` is the only place `data/build/` paths appear in `fair_turn/app` or `fair_turn/data`.
- [ ] No page reads `st.session_state` directly (grep test inside the smoke test module).
- [ ] Gate green.
