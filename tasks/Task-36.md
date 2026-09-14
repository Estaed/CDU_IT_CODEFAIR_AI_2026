# Task-36: Ollama extractor benchmark (last step): qwen3:8b against the build extractor, default decided by the table

Status: DONE

> **Execution:** agent `codex` · effort `high` · plan mode **no**
> *Why:* The code (chat wrapper, benchmark script, eval table) is specified and tested with fakes; the pull and the real run are the main loop's on Tarik's machine, and the decision rule is written in Part 2. Tarik's call 2026-09-14: this is the last Phase 2 step; nothing before it pulls or calls an Ollama chat model.

**Lane**
- OWNS: `fair_turn/llm/ollama.py` (`chat` function), `fair_turn/llm/intake.py` (remove `NotAcceptedYet`, route `ollama`), `scripts/benchmark_provider.py`, `tests/test_ollama.py`, `data/build/eval_ollama.json`, `MODELS.md`, plus (added by the orchestrator 2026-09-14, attempt 2) the `ollama` case in `tests/test_intake.py`, the `NotAcceptedYet` reference in `fair_turn/app/intake.py`, and the README sentence that says Ollama is not accepted yet
- MUST NOT TOUCH: `fair_turn/eval/` (reuse as is), `scripts/run_eval.py`, `fair_turn/app/`
- GATE: `venv/Scripts/python scripts/gate.py` (repo root) (the real benchmark run is the main loop's; its exit code is quoted in the report, not gated)
- DEPENDS ON: Task-28, Task-35

## Objective

Measure a local extractor on the same tables as the build extractor and let the numbers,
not the fact that it runs, decide whether Ollama becomes the intake default.

## Execution Guide

- `ollama.py`: `chat(prompt: str, schema: dict, model: str, base_url=..., timeout: float = 300) -> dict` over `/api/chat` with `format=schema`, `stream=False`, `options={"temperature": 0}`; parse `message.content` as JSON; raise `OllamaUnavailable` or `OllamaInvalidOutput` with the raw text truncated.
- `intake.py`: `ollama` provider calls `chat(prompt, schema, model=OLLAMA_EXTRACT_MODEL)`; `OLLAMA_EXTRACT_MODEL = "qwen3:8b"` defined here with the fallback `"gemma3:4b"` selectable by `FAIR_TURN_OLLAMA_MODEL`.
- `scripts/benchmark_provider.py --provider ollama --model qwen3:8b`: runs the 150-item set and the 20 adversarial items through `intake.extract` with the provider's call, reuses `fair_turn/eval` to produce the same table as `run_eval.py`, writes `data/build/eval_ollama.json` with model, latency percentiles and the decision line: `default = "ollama"` only if macro-F1 for both required fields is not below the build extractor's in `eval.json` and 20/20 adversarial leave the rank unchanged; otherwise `default = "claude"` with the numbers. Prints the decision and exits 0 either way (the exit code is not a pass mark; the table is).
- `MODELS.md`: the first measured lane on this project: provider, model, F1 per field, latency, decision, date.
- Tests with fakes: `chat` parses a valid object and raises on invalid JSON and on a connection error; the benchmark script with a fake call writes the artefact and prints a decision; the decision rule is unit-tested on hand-built numbers (equal → ollama, one field lower → claude, adversarial 19/20 → claude).

## Acceptance Criteria (DoD)

- [x] `chat` failure modes and the decision rule tested with fakes.
- [x] Main loop: `ollama pull qwen3:8b`, then `venv/Scripts/python scripts/benchmark_provider.py --provider ollama --model qwen3:8b` from the repo root; `eval_ollama.json` and `MODELS.md` committed with the numbers; if the decision is `ollama`, the README default and Part 2's seam line are updated in the same commit (Part 2 edit raised to Tarik first, rule 8).
- [x] Gate green.
