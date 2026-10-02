# Task-28: Intake: provider seam and the in-page new-report action

Status: DONE

> **Execution:** agent `codex` · effort `high`
> *Why:* The provider contract, the states and the persistence rules are written; tests run against a fake provider so no subscription is spent.

**Lane**
- OWNS: `fair_turn/llm/intake.py`, `fair_turn/llm/prompts.py` (append `INTAKE_PROMPT_VERSION` and the intake prompt only), `fair_turn/app/intake.py`, `tests/test_intake.py`, `tests/fakes/provider.py`
- MUST NOT TOUCH: `fair_turn/llm/claude_cli.py`, `fair_turn/llm/ollama.py` (Task-27, Task-36), `fair_turn/app/pages/` (Task-29, Task-31), `fair_turn/data/runtime.py` (Task-23)
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-23, Task-24

## Objective

Let a coordinator submit a synthetic report and have it extracted, verified and stored
through the same schema as the build, with every failure visible and no duplicate job.

## Execution Guide

- `llm/intake.py`: `Provider = Literal["claude", "ollama"]`; `configured() -> Provider | None` from `FAIR_TURN_PROVIDER` (unset or empty → `None`; `ollama` → raise `NotAcceptedYet("Ollama extraction is benchmarked in Task-36")` until then); `extract(text: str, provider: Provider, timeout: float = 120, call: Callable | None = None) -> IntakeResult` where `call` defaults to `claude_cli.generate(prompt, schema.json_schema(), model="sonnet", timeout=timeout)` and `IntakeResult(extraction: dict | None, verified: VerifiedExtraction | None, status, provider, model, prompt_version, latency_s, validation: str, error: str | None)`. Validation with `schema.Extraction`, then `core.verify_spans.verify`; status `extracted` when both required fields verified, `needs_review` when the schema passed but a required field failed verification, `not_extracted` on `CliError`, timeout or schema failure (reason in `validation`/`error`). The rejected value is not part of `IntakeResult.verified`; it stays in `extraction` for the audit record only.
- `app/intake.py`: `render(container) -> None` inside a bordered container toggled by `state` (`get/set_intake_draft`): `st.text_area` (draft kept in state), `st.selectbox` community id (from artefacts), `st.date_input` defaulting to `state.get_today()` with the caption "dataset day", "Extract" button. Validation: empty or whitespace-only, or over 4,000 characters → red text under the field, text preserved. Provider states: `configured() is None` → button disabled and `st.info` naming `FAIR_TURN_PROVIDER`; `NotAcceptedYet` → the same with its message. On click: `st.status` with provider, model and elapsed seconds; then the fields table (field, value, phrase, badge); "Add to ranked queue" (status `extracted`) shows the resulting rank from `scoring.rank` over current jobs plus the new one and whether it is inside `capacity`; "Send to review queue" otherwise. Both write one `runtime.IntakeReport` with a `draft_token` generated when the draft was created (so a double click or retry is a no-op) and one `audit.Intake` record. The new job's id comes from `runtime.next_job_id`. Never a model call outside the button's handler; never a `subprocess` import here (the layer test enforces it).
- `tests/fakes/provider.py`: fake `call` returning a fixed valid object, an object with a wrong phrase, an invalid object, and one that raises `CliError`/`TimeoutError`.
- Tests: the four outcomes map to the three statuses with the right `validation` string; a repeated `draft_token` writes nothing; `FAIR_TURN_PROVIDER` unset disables the button (AppTest, `monkeypatch.delenv`); with the fake provider (injected through a `state` hook for tests), submitting writes exactly one runtime record and one audit record; whitespace text shows the error and keeps the text.

## Acceptance Criteria (DoD)

- [ ] All four provider outcomes tested; the rejected value never appears in `verified`.
- [ ] Double submission proven idempotent at the runtime store and the audit log.
- [ ] Provider-unset and not-accepted states render with their reasons (AppTest, sockets refused).
- [ ] `app/intake.py` is the only app module importing `fair_turn.llm` (layer test).
- [ ] Gate green.
