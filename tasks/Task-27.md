# Task-27: Policy index: FS17 passages as a build artefact keyed by typed fields

Status: DONE

> **Execution:** agent `codex` · effort `high`
> *Why:* Code is fully specified and tested with a fake embedder; the one real build run needs Ollama on Tarik's machine, so the main loop runs the script once after the bee's gate is green. PRD open question 6 (fact-sheet licence) is external, owner Tarik: meanwhile the script fetches the public PDF, quotes passages with attribution, and the report states the licence status.

**Lane**
- OWNS: `scripts/build_policy_index.py`, `fair_turn/llm/ollama.py` (embed function only; chat is Task-36), `fair_turn/data/policy.py`, `tests/test_policy.py`, `data/raw/PROVENANCE.md` (append one row), `data/raw/nt_fs17_repairs_and_maintenance_2025-10.pdf`, `data/build/policy_passages.json`
- MUST NOT TOUCH: `fair_turn/llm/claude_cli.py`, `fair_turn/llm/intake.py` (Task-28), `fair_turn/app/`
- GATE: `venv/Scripts/python scripts/gate.py` (repo root) (the real index build is run by the main loop; the test suite uses a fake embedder)
- DEPENDS ON: none

## Objective

Give the selected-job pane and the tenant answer cited policy passages without a model
call at run time: embed FS17 once, answer a finite set of typed queries once, commit the
result.

## Execution Guide

- `llm/ollama.py`: `embed(texts: list[str], model: str = "bge-m3", base_url: str = "http://localhost:11434", timeout: float = 120) -> list[list[float]]` over `urllib.request` POST to `/api/embed`; raise `OllamaUnavailable` on `URLError`/non-200 with the URL in the message. No other function yet.
- `scripts/build_policy_index.py`: fetch the FS17 PDF from the URL in `reports/2026-09-12-research-housing.md` into `data/raw/` if absent (append the PROVENANCE row: title, URL, fetched date, © NT Government, licence open question 6); extract text with `pypdf`; chunk by paragraph, 60–120 words, keep `(section_heading, text)`; embed chunks; build the query set from `constants`: every `(safety_class, "town" | "remote", fault_type)` plus `(safety_class, town_or_remote, None)` with a template sentence per key ("Response time and what counts as an urgent repair for a {fault} fault in a remote community"); cosine top-3 above threshold 0.55 (provisional; write it in the artefact header); write `policy_passages.json`: `{"source": {"title", "url", "effective_date": "2025-10", "fetched"}, "threshold", "embed_model", "keys": {key: [{"section", "text", "score"}]}}`. Idempotent; `--fake` flag uses a deterministic hash embedder for tests and CI.
- `data/policy.py`: `load(path=BUILD_DIR / "policy_passages.json") -> PolicyIndex`; `lookup(index, safety_class, is_remote, fault_type) -> list[Passage]` falling back to the fault-less key, then empty; `Passage(section, text, score, title, effective_date)`; `verify(index, document_text) -> bool` (every passage text a literal substring of the extracted document).
- Tests: build with `--fake` into `tmp_path` and assert the key set is complete, every passage is a substring of the chunked text, scores are sorted and above threshold; `lookup` fallback order; a missing file gives an index whose `lookup` returns `[]` and whose `available` is False.

## Acceptance Criteria (DoD)

- [ ] `--fake` build produces a complete key set; `verify` holds on it (unit tests).
- [ ] `lookup` fallback and unavailable-index behaviour tested.
- [ ] Real run by the main loop: `venv/Scripts/python scripts/build_policy_index.py` from the repo root with Ollama up writes the artefact; `verify` against the real PDF text holds (assert in `tests/test_policy.py` when the artefact exists); artefact and PDF committed with the PROVENANCE row.
- [ ] Gate green.
