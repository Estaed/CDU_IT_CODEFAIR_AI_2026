# Task-27 delivery — 2026-10-04

**Implemented; blocked on the required clean gate.** The remaining failure requires an
orchestrator change outside this task's OWNS. No out-of-lane source or frozen result was edited.

## Delivered implementation

- `readmark/checklist/generate.py`: rule uploads and code-generated pins; existing Claude CLI
  wrapper and response-only replay cache; ten initial suggestions; exact anchors; human review
  and provenance; one-question coverage follow-up; unapproved CLI generation.
- `readmark/checklist/lists.py`: discover uploaded lists alongside committed lists; exclude
  zero-approved drafts; use the same approved-clause format.
- `readmark/__main__.py`: `lists --generate <folder> --id <id> --name <name> [--scope ...] [--replay]`;
  existing committed-list coverage CLI retains its call contract.
- `readmark/serve.py`: bounded rule-upload API, progress, review/check/save, coverage and targeted
  generation; interrupt recovery; protect lists once a case selects them; list attribution in
  both HTML and JSON decision records.
- `web/lists.js`, `web/home.js`, `web/upload.js`, `web/app.js`, `web/index.html`,
  `web/theme.css`: home/new-case entry points, optional screen words, rule drop/upload,
  progress and per-suggestion Approve/Edit/Reject. Returning to New case retains its name
  and documents and selects the approved list.
- `tests/test_generate_list.py`: 12 tests using fake Claude, writer and checker; no network.
- `docs/question-lists.md`: the AI may suggest; a person approves every question; formats,
  replay, provenance, second pass and list immutability documented.
- `.gitignore`: `data/question-lists/`.
- Six PNGs: `list-{form,progress,review}-{1280,1440}.png`. Tests write to
  `.tmp/shots/wave12/`; the delivered set was copied once to this folder.

The **full text of all 13 implementation files**, including the added text and surrounding
existing code, is in [task27-source.txt](task27-source.txt). Modified code/document files
were checked as UTF-8 without BOM and LF without CRLF. `name:` and `description:` frontmatter
were not changed. No Git command or brain receipt was run.

## Acceptance

| Item | Result and evidence |
|---|---|
| Gate exits 0 and does not change Git status | **Blocked:** final gate exits 1 on the H-01 metadata mismatch below. Ruff and both replay smoke checks pass. No Git command was used; direct hashes of 2,585 tracked/delivered files and the Git index are identical before/after the final gate. Test outputs are in ignored `.tmp/`. |
| Every case replay, both committed lists and `runs/eval/` unchanged | No protected path was edited. The initial snapshot's 114 stage/eval/list files have zero changes. All 2,169 files under `runs/` and `readmark/checklist/lists/` are also identical before/after the final gate. |
| Fake Claude: verbatim sentence passes; changed word fails and cannot be approved; correction passes | **Pass:** `test_bad_sentence_is_refused_then_corrected_and_used_in_a_case` checks the actual server, including a forged browser “sentence_found” value. Invalid verbatim items are also refused. |
| Zero-approved list excluded; approved list runs a case end to end with fake writer | **Pass:** zero-approved selection is absent from the form and rejected by the API; approved list runs real ingest/checks/gate/view with fake model seams. Both signed exports carry the list and attribution. |
| Uploaded rules and generated lists git-ignored | **Pass:** `test_uploaded_rules_and_generated_lists_are_ignored` checks the ignore directory pattern against PDFs, YAML, suggestions and cache responses. No `git check-ignore` was run. |
| Live CDU policy as a new list: sentence matches against six hand-written questions and failed sentence count | **Deferred to orchestrator:** this environment declares restricted network access; no live Claude call was made. Claude executable was found, but live authentication/network access was not established. No count is claimed. |
| New-list page loads headlessly without console errors | **Pass:** Playwright checks both `pageerror` and error-level console messages at 1280 and 1440; both empty. It also checks edit/fix/approve/save and return to New case. |
| Form, progress and review screenshots at 1280 and 1440 | **Pass:** six delivered PNGs in this folder, copied once from the test output. Form, progress and review images were visually inspected against the project's light government form language. |
| Tarık's eye check against Task-15 look | **Pending:** human acceptance was not automated. Tarık must build a CDU list and judge sentence clarity and what Approve does. |

Additional fake tests check multi-file TXT/PDF pins and page counts, the ten-suggestion cap,
byte-identical replay without Claude, scanned/unreadable rules retaining their originals,
and a coverage suggestion staying pending until explicit approval.

## Scope contradiction and required integration

`readmark/eval/discipline.py` fingerprints every Python module. Its `NOT_RESULT_CODE`
already excludes Task-26 coverage helpers, but includes the new
`readmark/checklist/generate.py` as result-affecting code. Rebuilding evaluation in a
temporary runs folder therefore adds precisely that filename to
`/cases/H-01/heldout_discipline/changed_result_files`. The numeric evaluation fields are
unchanged, but `tests/test_eval_cases.py:189` requires the entire JSON to match the frozen
`runs/eval/cases.json` byte for byte.

Task-27 requires both the new module and a clean gate while forbidding changes to
`readmark/eval/**` and `runs/**`. The bee cannot resolve that contradiction within OWNS.
The orchestrator should decide whether this generation-only module belongs in the
guard's non-result exclusions, analogous to Task-26, then rerun the gate. This report
does not authorize or apply that change.

The first full gate produced **255 passed, 2 failed**. Its other failure was the coverage
CLI call shape, corrected within `readmark/__main__.py`; the 27 coverage tests then passed.
The final gate was repeated with pytest stopping at its first failure to confirm the
remaining blocker on the final code.

## Commands and actual output

Workspace-local cache/temp paths avoid this sandbox's denied default uv and pytest cache paths.

```powershell
$env:UV_CACHE_DIR = Join-Path $PWD '.tmp/uv-cache'
$env:PYTEST_ADDOPTS = '--basetemp=.tmp/pytest-task27-extra -o cache_dir=.tmp/pytest-cache'
uv run python -m pytest tests/test_generate_list.py -x --tb=short
```

That earlier ten-test run passed. After adding the final two checks:

```powershell
$env:UV_CACHE_DIR = Join-Path $PWD '.tmp/uv-cache'
$env:PYTEST_ADDOPTS = '--basetemp=.tmp/pytest-task27-final -o cache_dir=.tmp/pytest-cache'
uv run python -m pytest tests/test_generate_list.py -x --tb=short
```

```text
............                                                             [100%]
12 passed in 9.68s
```

```powershell
$env:UV_CACHE_DIR = Join-Path $PWD '.tmp/uv-cache'
$env:PYTEST_ADDOPTS = '--basetemp=.tmp/pytest-task27-coverage-fixed -o cache_dir=.tmp/pytest-cache'
uv run python -m pytest tests/test_coverage.py -x --tb=short
```

```text
...........................                                              [100%]
27 passed in 1.89s
```

The earlier combined feature/home/upload run:

```powershell
$env:UV_CACHE_DIR = Join-Path $PWD '.tmp/uv-cache'
$env:PYTEST_ADDOPTS = '--basetemp=.tmp/pytest-task27 -o cache_dir=.tmp/pytest-cache'
uv run python -m pytest tests/test_generate_list.py tests/test_home.py tests/test_upload.py -x --tb=short
```

```text
...............................................                          [100%]
47 passed in 61.48s (0:01:01)
```

Final gate command, exit **1**, with the tool's stdout preserved below:

```powershell
$env:UV_CACHE_DIR = Join-Path $PWD '.tmp/uv-cache'
$env:PYTEST_ADDOPTS = '--basetemp=.tmp/pytest-task27-gate-final -o cache_dir=.tmp/pytest-cache -x'
uv run python scripts/gate.py
```

```text
== ruff: D:\Charles Darwin University\6 - Year 2 - Semester 2\CODE IT FAIR 2026\AI Challenge 2026\.venv\Scripts\python.exe -m ruff check
All checks passed!
== ruff: ok
== pytest: D:\Charles Darwin University\6 - Year 2 - Semester 2\CODE IT FAIR 2026\AI Challenge 2026\.venv\Scripts\python.exe -m pytest
........................................................................ [ 28%]
........F
================================== FAILURES ===================================
___________ test_each_new_part_replays_twice_with_no_keys_or_claude ___________

tmp_path = WindowsPath('D:/Charles Darwin University/6 - Year 2 - Semester 2/CODE IT FAIR 2026/AI Challenge 2026/.tmp/pytest-task27-gate-final/test_each_new_part_replays_twi0')

    @needs_pdfs
    @pytest.mark.skipif(not complete_outputs(), reason="live evaluation has not completed yet")
    def test_each_new_part_replays_twice_with_no_keys_or_claude(tmp_path):
        runs = tmp_path / "runs"
        for cid in ALL_CASES:
            shutil.copytree(ROOT / "runs" / cid, runs / cid)
        shutil.copytree(EVAL, runs / "eval")
        env = {k: v for k, v in os.environ.items() if k not in ("TYPESAFE_API_KEY", "PATH")}
        env["PATH"] = str(Path(sys.executable).parent)
        env["READMARK_RUNS_DIR"] = str(runs)
        assert shutil.which("claude", path=env["PATH"]) is None
        # Benchmark release is checked below with an isolated destination, since the CLI writes
        # the project's committed CSVs. It has no live-model code path.
        for part in ("cases", "mutations", "ablation", None):
            name = part or 'audit_labels'  # summary assembly also rebuilds the labelled comparison
            expected = (EVAL / f"{name}.json").read_bytes()
            for _ in range(2):
                command = [sys.executable, '-m', 'readmark', 'eval', '--replay']
                if part:
                    command += ['--part', part]
                subprocess.run(command,
                               cwd=ROOT, env=env, capture_output=True, check=True, timeout=300)
>               assert (runs / "eval" / f"{name}.json").read_bytes() == expected
E               assert b'{\n "cases"...rately."\n}\n' == b'{\n "cases"...rately."\n}\n'
E                 
E                 At index 17716 diff: b'g' != b'l'
E                 Use -v to get more diff

tests\test_eval_cases.py:189: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_eval_cases.py::test_each_new_part_replays_twice_with_no_keys_or_claude
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!
1 failed, 80 passed in 33.89s
== pytest: FAILED (exit 1)
== replay smoke stub: D:\Charles Darwin University\6 - Year 2 - Semester 2\CODE IT FAIR 2026\AI Challenge 2026\.venv\Scripts\python.exe -m readmark run --case stub --replay
stub: 22 claims, 4 required passages (+0 suggested) -> C:\Users\TARIK\AppData\Local\Temp\tmpiyd53aie\stub\view.json
== replay smoke stub: ok
== replay smoke stub: view.json (schema version 2) matches readmark/schemas/view.schema.json
== replay smoke A-0142: D:\Charles Darwin University\6 - Year 2 - Semester 2\CODE IT FAIR 2026\AI Challenge 2026\.venv\Scripts\python.exe -m readmark run --case A-0142 --replay
A-0142: 34 claims, 8 required passages (+43 suggested) -> C:\Users\TARIK\AppData\Local\Temp\tmpvou05ids\A-0142\view.json
== replay smoke A-0142: ok
== replay smoke A-0142: view.json (schema version 2) matches readmark/schemas/view.schema.json
GATE FAILED
```

Direct before/after hash output (identical for the final gate):

```text
tracked_and_delivered_files 2585 8a4c5410da291e1b7e97267825beac9acdd770d14174ac5e54acbbdf9875f421
index 99a58e8baa3d5d4a443ac2d5150fe29cbd9cee0fc0a01de22377a97c558587ec
protected_files: 2169 8f4305e285ebe27f01cd7baab981fff465d1bd0460ed734781e37405c16aa3a9
```

