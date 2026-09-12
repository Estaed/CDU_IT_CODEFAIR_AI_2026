# Task-00: Package layout, constants, theme tokens, wording lint

> **Execution:** agent `claude` (main loop) · effort `medium` · plan mode **no**
> *Why:* every constant needs a provenance row and a judgement about its source; the rest is mechanical but small.

**Lane**
- OWNS: `fair_turn/core/__init__.py`, `fair_turn/core/constants.py`, `fair_turn/core/wording.py`, `fair_turn/data/__init__.py`, `fair_turn/llm/__init__.py`, `fair_turn/eval/__init__.py`, `fair_turn/app/__init__.py`, `fair_turn/app/theme.py`, `.streamlit/config.toml`, `constants.md`, `tests/test_constants.py`, `tests/test_wording.py`, `tests/test_theme.py`
- MUST NOT TOUCH: `pyproject.toml` (append-only, Task-00 owner for the `textstat` dep already present), `CLAUDE.md`
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: none

## Objective

Create the five package layers Part 2 names, the single source of every policy number,
the theme tokens, and the two repo-wide lints (deficit language, hex literals) so that
every later task is written against them instead of retyping values.

## Execution Guide

- `fair_turn/core/constants.py`: `SEED = 20260912`; date window `WINDOW_START = date(2025, 10, 1)`, `WINDOW_DAYS = 90`; NT windows from FS17 as a dict keyed by safety class and `is_remote`: immediate 4 h (both), urgent 2 / 5 business days, routine 10 / 25; `DIPL_APPROVAL_AUD = 500` (documented, unused by v1 code); `CREW_BASES` (Darwin, Katherine, Tennant Creek, Alice Springs, Nhulunbuy); `CREWS_PER_REMOTE_REGION = 2`, `CREWS_TOWN = 3`, `JOBS_PER_CREW_DAY = 4`, `TRAVEL_DAY_KM = 200`; `REMOTE_REGIONS` exactly as BushTel spells them (`CENTRAL AUSTRALIA`, `BIG RIVERS`, `BARKLY`, `TOP END`, `EAST ARNHEM`), `TOWN_REGION = "DARWIN, PALMERSTON, LITCHFIELD"`; heat season months Oct–Mar; wet season Oct–Apr. Plain Python only.
- `constants.md`: delete the template instructions; one row per constant above with source (FS17 10/2025, PRD §6.3 provisional, BushTel field, BoM season definition).
- `fair_turn/core/wording.py`: `DEFICIT_TERMS` tuple (`vulnerable`, `vulnerability`, `at-risk`, `non-compliant`, `dysfunctional`); `check(text) -> list[str]` returns offending terms plus `"reading_level"` when `textstat.flesch_kincaid_grade(text) > 7`.
- `.streamlit/config.toml` `[theme]`: primaryColor, backgroundColor, secondaryBackgroundColor, textColor. Font is already done (2026-09-12): `font = "IBM Plex Sans, sans-serif"` with three `[[theme.fontFaces]]` tables pointing at `fair_turn/app/static/fonts/*.woff2` (OFL, licence file alongside) served by `server.enableStaticServing`; the `static/` folder must sit next to `main.py`, not at the repo root (verified: root placement 404s). No Google Fonts URL anywhere. Colour values come from the design file under `design/` once it exists; until then the IBM tokens in `design/DESIGN_IBM.md`. `fair_turn/app/theme.py`: named colours for the five remote regions + town, `TOWN`/`REMOTE` pair, factor colours (urgency, safety, health_risk, logistics), `HUMAN_QUEUE`, `PROVENANCE_LINE = "Geography real (BushTel/ABS); events synthetic"`. Follow the `dataviz` skill's palette rules.
- Tests: `test_wording.py` runs `wording.check` over every `.py` under `fair_turn/`, `docs/PRD.md` and every `.json`/`.csv` under `data/build/` (skip if absent) and asserts no deficit term (the `DEFICIT_TERMS` definition line itself is exempt); `test_theme.py` greps `fair_turn/app/**/*.py` except `theme.py` for `#[0-9a-fA-F]{6}` and asserts none; `test_constants.py` asserts the five region strings match `NTRegionName` values present in `data/raw/bushtel_community_detail_2026-09-12.json`.

## Acceptance Criteria (DoD)

- [ ] The five layer folders exist with `__init__.py`; `tests/test_layers.py` still passes.
- [ ] `constants.py` defines every value listed above; `constants.md` has a provenance row for each and no template text.
- [ ] `test_constants.py`, `test_wording.py`, `test_theme.py` pass.
- [ ] `wording.check("The vulnerable tenant")` returns `["vulnerable"]`; a 30-word plain sentence returns `[]`.
- [ ] Gate green.
