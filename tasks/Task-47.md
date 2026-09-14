# Task-47: Review queue with less typing: reason chips, remembered name, drafted clarification

Status: DONE

> **Execution:** agent `claude` · effort `high` · plan mode **no**
> *Why:* Tarik (2026-09-14) asked for the human's work here to shrink. The model may not pre-fill the field (PRD 3.2, Part 2 Key Constraints: the rejected model value never renders, so a "just accept" button would anchor the reviewer), so the saving comes from fewer keystrokes: preset reasons, a remembered name, and a templated clarification message.

**Lane**
- OWNS: `fair_turn/app/pages/review_queue.py`, `fair_turn/app/state.py` (only `get_actor` / `set_actor`), `tests/test_page_review_queue.py`
- MUST NOT TOUCH: `fair_turn/app/components/`, `fair_turn/app/intake.py`, `fair_turn/core/`, `fair_turn/data/`, `fair_turn/llm/`
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: 39

## Objective

Reviewing a job takes three clicks and no typing in the common case: pick the value, pick a
reason chip, press "Mark rankable". The name is typed once per session. "Request
clarification" drafts the message to the tenant from a template so the coordinator edits
rather than writes. The page says in one line why the system does not propose the value.

## Execution Guide

- `state.py`: `get_actor() -> str` (default "coordinator") and `set_actor(value: str)`,
  following the existing getter/setter style.
- Reason: replace the free `st.text_input("Reason")` with `st.pills("Reason", REASON_PRESETS,
  selection_mode="single", key=...)` plus a smaller `st.text_input("Other reason (optional)")`.
  `REASON_PRESETS` (module constant, plain English, no deficit words): "Report names the
  appliance", "Report describes the fault", "Tenant confirmed by phone", "Housing officer
  confirmed on site", "Photo attached to the report". The stored reason is the chip text, or
  the free text when given (free text wins); an empty pair still blocks with the existing
  "A reason is required." error. Every action that needs a reason (mark rankable, request
  clarification, leave in queue) reads the same pair.
- Name: `st.text_input("Your name", value=state.get_actor())`; on any submit call
  `state.set_actor(name)` so the next job pre-fills it.
- Clarification: when "Request clarification" is pressed, show `st.text_area("Message to the
  tenant", value=draft, height=...)` built by a template `clarification_draft(missing_fields:
  tuple[str, ...], job_id: str) -> str` (module function, no model call): "Hello, this is about
  repair {job_id}. Your report did not say {what}. Could you tell us {question}? Reply to this
  message or call your Community Housing Officer." where `what`/`question` come from a small
  dict per field (fault type: "what has broken" / "which part of the house or appliance is
  faulty"; safety class: "how urgent it is" / "whether anyone is without power, water,
  cooling or a safe way in"). A "Send clarification" button records the existing
  clarification action with the message as the reason; the draft passes `core.wording.check`
  (test).
- One caption under the membership rule: "The system does not suggest a value here. Showing
  its rejected guess would steer you, so you set the field from the report."
- Tests: chips exist with the five presets; selecting a chip and pressing "Mark rankable"
  with no free text records that chip text as the reason (read the runtime record); free
  text overrides the chip; the name persists across Next; the clarification draft names the
  missing field and passes the wording check; the anchoring caption is present.

## Acceptance Criteria (DoD)

- [ ] Reason chips plus optional free text; chip text is stored when free text is empty (test).
- [ ] Name remembered across jobs in the session (test).
- [ ] Clarification draft from a template, wording check green, sent as the recorded reason (test).
- [ ] Anchoring caption present; the model's rejected value still never renders (existing test).
- [ ] Gate green.
