# Models — which model does what in this project

Delete these instructions once the table reflects reality. The routing policy
itself lives in the `chef` skills (`claude-chef` / `codex-chef`); this file
carries only the decisions actually **measured in this project** — never
general model-capability opinion. "Model X is generally good at Y" is a belief
that ages badly and is not a project decision; it does not belong here even as
justification. A row without a measured date and evidence is a guess wearing a
decision's clothes.

## Decisions

| Lane / surface | Model | Effort | Why chosen | Measured on | Evidence |
|---|---|---|---|---|---|
| Intake extractor benchmark (Task-36) | ollama / qwen3:8b against the build extractor (claude / sonnet) | temperature 0 | pending: F1 per field (fault_type, safety_class, health_risk), latency p50 / p90 / max and the decision (`default` = ollama only if not below the build extractor on both required fields and 20/20 adversarial leave the rank unchanged) come from the real run | 2026-09-14: code and fakes only, real run pending | pending: run `venv/Scripts/python scripts/benchmark_provider.py --provider ollama --model qwen3:8b` after `ollama pull qwen3:8b`; writes `data/build/eval_ollama.json` |
<!-- | Codex gate lane | Codex | high | Held a 40-file spec over a 3h unattended run without drifting; the Opus sub-agent tried on the same task lost the thread after ~90min. | 2026-01-01 | otopilot report daily/2026-01-01.md, run log reports/2026-01-01-gate-lane.md | -->

## Notes

- Record here when a tier was changed and what triggered it (a limit, a bad
  output, a cost, a measured run). "We moved X to Codex on <date> because Y,
  see <evidence>" is the useful form — no evidence, no row.
- Do not pin a Codex model with `-m` unless the account is known to have it —
  it fails with `401 No eligible Codex account supports this model`. Omitting
  it uses the default from `~/.codex/config.toml`.
