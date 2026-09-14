# Task-48: Provider switch and example reports for intake, from the UI

Status: TODO

> **Execution:** agent `claude` · effort `medium` · plan mode **no**
> *Why:* Tarik (2026-09-14) wants to switch the extractor and submit a test report without touching the environment. Part 2 seam amended the same day: the environment variable stays the default, the UI may override it for the session.

**Lane**
- OWNS: `fair_turn/app/intake.py`, `fair_turn/llm/intake.py` (only: `configured(override: str | None = None)`), `tests/test_intake.py`, `tests/test_page_workspace.py` (only the intake-disabled assertions if they change)
- MUST NOT TOUCH: `fair_turn/app/pages/`, `fair_turn/app/components/`, `fair_turn/app/state.py`, `fair_turn/llm/claude_cli.py`, `fair_turn/llm/ollama.py`, `fair_turn/core/`
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: none

## Objective

Inside the intake container the coordinator picks the provider (none, claude, ollama) and can
load one of three example reports with one click, then presses Extract. The environment
variable remains the default; the choice lives in session state and never in a file.

## Execution Guide

- `llm/intake.py`: `configured(override: str | None = None) -> Provider | None` — when
  `override` is given (non-empty), validate it like the env value and return it; when it is
  the literal "none", return `None`; otherwise fall back to the environment as today. Keep the
  error for unknown values.
- `app/intake.py` (the only app module that may import `fair_turn.llm`): at the top of the
  intake container, `st.selectbox("Extractor", ["none", "claude", "ollama"], index=<from env
  default>, help="claude = Claude Sonnet through the logged-in claude CLI; ollama = the local
  model named in FAIR_TURN_OLLAMA_MODEL; none = intake disabled. The environment variable
  FAIR_TURN_PROVIDER sets the default.")`, stored in `st.session_state` under one key
  (`intake_provider`) — this module already owns the intake state; keep reads/writes inside
  this module. Pass the choice to `configured(override=...)`. The disabled reason text for
  "none" stays as it is.
- Example reports: `st.pills("Load an example", ["Cooling, Alice Springs", "Hot water,
  remote", "Electrical, urgent"], selection_mode="single")`; each maps to one synthetic
  report chosen at build time from `data/build/reports.json` by job id (pick three ids whose
  labels in `labels.json` are: fault cooling in a town community; fault hot_water in a remote
  community; fault electrical with safety immediate or urgent; hard-code the three ids as
  module constants with a comment saying how they were chosen). Loading an example fills the
  draft's text, community id and reported date (today) and clears any previous result; the
  text stays editable.
- The Extract button and the verification path are unchanged; the provider name shown in the
  status line and saved in the runtime record is the chosen one.
- Tests (`tests/test_intake.py`, fake provider as the existing tests do): `configured("ollama")`
  returns ollama regardless of the env; `configured("none")` returns None; an unknown override
  raises; the intake container renders the selectbox and three example pills; loading an
  example fills the text with the report's text and the community id from labels; switching
  the provider to "none" disables Extract with the reason.

## Acceptance Criteria (DoD)

- [ ] Provider selectbox overrides the environment for the session; "none" disables intake with the reason (tests).
- [ ] Three example reports load with one click and stay editable (test).
- [ ] The runtime record carries the chosen provider (test through the fake).
- [ ] Layer rule unchanged: only `app/intake.py` imports `fair_turn.llm` (existing test).
- [ ] Gate green.
