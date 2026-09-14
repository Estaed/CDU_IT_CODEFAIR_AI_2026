# Models — which model does what in this project

## Decisions

| Lane / surface | Model | Effort | Why chosen | Measured on | Evidence |
|---|---|---|---|---|---|
| Intake extractor | claude / sonnet | provider default | Retained: qwen3:8b F1 was 0.6882 fault type, 0.5605 safety class and 0.5809 health risk against Claude's required-field 0.9187 and 0.5641; 6/20 adversarial ranks unchanged; latency p50 4.6260 s, p90 5.3214 s, max 10.0973 s | 2026-09-14: 150 holdout + 20 adversarial items | `data/build/eval_ollama.json` |
| Intake extractor comparison | ollama / qwen3.5:9b | temperature 0, thinking disabled | Not selected: F1 was 0.6142 fault type, 0.5352 safety class and 0.5804 health risk; 14/20 adversarial ranks unchanged; latency p50 5.1593 s, p90 6.0732 s, max 11.5759 s | 2026-09-14: 150 holdout + 20 adversarial items | `data/build/eval_ollama_qwen35.json` |
<!-- | Codex gate lane | Codex | high | Held a 40-file spec over a 3h unattended run without drifting; the Opus sub-agent tried on the same task lost the thread after ~90min. | 2026-01-01 | otopilot report daily/2026-01-01.md, run log reports/2026-01-01-gate-lane.md | -->

## Notes

- Record here when a tier was changed and what triggered it (a limit, a bad
  output, a cost, a measured run). "We moved X to Codex on <date> because Y,
  see <evidence>" is the useful form — no evidence, no row.
- Do not pin a Codex model with `-m` unless the account is known to have it —
  it fails with `401 No eligible Codex account supports this model`. Omitting
  it uses the default from `~/.codex/config.toml`.
