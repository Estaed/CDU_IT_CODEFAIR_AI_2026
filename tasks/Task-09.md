# Task-09: CLI wrappers for the two subscription models

> **Execution:** agent `claude` (main loop) · effort `high` · plan mode **no**
> *Why:* touches Tarik's logged-in CLIs and their quirks (stdin handling, quota windows); tests use fake executables, the one real call is a manual smoke check.

**Lane**
- OWNS: `fair_turn/llm/claude_cli.py`, `fair_turn/llm/codex_cli.py`, `tests/test_cli_wrappers.py`, `tests/fakes/`
- MUST NOT TOUCH: `fair_turn/llm/schema.py` (Task-08), `scripts/` build scripts (Task-10, Task-11)
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-08

## Objective

Two thin, tested subprocess wrappers so the build scripts never touch CLI flags directly.

## Execution Guide

- `claude_cli.py`: `generate(prompt, schema: dict, model="opus", timeout=300) -> dict`: runs `[claude, "-p", "--model", model, "--output-format", "json", "--json-schema", json.dumps(schema)]` with `input=prompt` on stdin, `stdin` never left open; parses stdout JSON, returns `structured_output`; raises `CliError` with stderr on non-zero exit or `is_error`.
- `codex_cli.py`: `extract(prompt, schema: dict, timeout=300) -> dict`: writes the schema to a temp file, runs `[codex, "exec", "--sandbox", "read-only", "--skip-git-repo-check", "--output-schema", schema_path, "-o", out_path, prompt]` with `stdin=subprocess.DEVNULL`, reads `out_path`; no `-m`.
- Both: executable name resolved with `shutil.which`, overridable by parameter for tests; retries once on invalid JSON; log the call count and wall time to stdout.
- `tests/fakes/`: `fake_claude.py` and `fake_codex.py` scripts that emit canned output; tests invoke the wrappers with `executable=[sys.executable, fake_path]`; cover success, invalid JSON then success, non-zero exit.

## Acceptance Criteria (DoD)

- [x] Wrapper tests pass with the fake executables; no test invokes a real CLI.
- [x] Neither wrapper ever calls `subprocess.run` without a `timeout` and with stdin unresolved.
- [ ] One manual real call per wrapper on Tarik's machine is recorded in the task file's notes with the date (not gated).
- [x] Gate green.

## Notes

- 2026-09-12 real call, Claude wrapper: `generate("Reply with the single word pong.",
  <one-enum schema>, model="haiku", timeout=120)` returned `{"answer": "pong"}` in 16.6 s
  (`claude` 2.1.269, logged in on Tarik's machine).
- 2026-09-12 real call, Codex wrapper: pending. Codex is held back until the Claude window
  renews (operator decision); one smoke call is owed before this task is DONE.
- Trap found while gating: `%TEMP%\pytest-of-TARIK` (created 2026-09-10) was unreadable
  and made every `tmp_path` fixture error with WinError 5. Renamed to
  `pytest-of-TARIK.broken-2026-09-12`; pytest recreated a healthy one.
