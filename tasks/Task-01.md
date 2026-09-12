# Task-01: Geography layer with pseudonymous community ids

> **Execution:** agent `claude` (main loop) · effort `high` · plan mode **no**
> *Why:* decides how real places become ids and what a "road access class" is from BushTel prose; data judgement, not mechanics. PRD open question 1 (licence) does not block.

**Lane**
- OWNS: `fair_turn/data/geography.py`, `scripts/fetch_raw_sources.py` (append the outline fetch), `data/geo/`, `data/build/communities.csv`, `tests/test_geography.py`, `tests/_real_names.py`
- MUST NOT TOUCH: `fair_turn/core/` (Task-00, Task-02), `data/raw/` (frozen)
- GATE: `venv/Scripts/python scripts/gate.py` (repo root)
- DEPENDS ON: Task-00

## Objective

Turn the frozen BushTel, coverage and road snapshots into one committed table of
communities the whole project reads, with region-coded pseudonymous ids, real
coordinates, distance and road-access factors, and the NT outline the map draws.

## Execution Guide

- `geography.py`: `load_communities() -> pandas.DataFrame` from `data/build/communities.csv`; `build_communities(raw_dir) -> DataFrame` from the raw files. Rows: the 96 Major/Minor BushTel records plus the five crew-base towns (from the Town/City records). Columns: `community_id` (`"BIG RIVERS R-07"` style, numbered by descending population within region; towns keep their real names), `region`, `is_remote`, `lat`, `lon`, `population_band` (bands, never the exact count), `road_access` (parse BushTel prose: `sealed` / `unsealed` / `barge_or_air`; keep the raw phrase in a `road_note` column only in a non-committed debug frame), `crew_base`, `km_to_base` (haversine), `logistics_factor` (`km_to_base * ROAD_FACTORS[road_access]` with `ROAD_FACTORS = {sealed: 1.0, unsealed: 1.4, barge_or_air: 2.5}` defined in `geography.py`, since `constants.py` belongs to Task-00; add a provenance row to `constants.md` marked provisional), `wet_season_closable` (True for unsealed and barge_or_air).
- Cross-check coordinates with the CC-BY coverage XLSX; log mismatches over 5 km to stdout, do not fail.
- Extend `fetch_raw_sources.py` with a `--outline` step: Natural Earth 1:10m admin-1 (public domain), keep the NT feature only, write `data/geo/nt_outline.geojson` (simplify if over 500 KB). Run it once, commit the file.
- `tests/_real_names.py`: helper that yields every `Name` from the BushTel detail JSON for the Major/Minor records; `test_geography.py` asserts none appears in `communities.csv`, in `fair_turn/app/`, or in `docs/PRD.md`; asserts 101 rows, unique ids, every remote row `km_to_base > 0`, every region in `constants.REMOTE_REGIONS + [TOWN_REGION]`, and `data/geo/nt_outline.geojson` parses with one feature.

## Acceptance Criteria (DoD)

- [ ] `data/build/communities.csv` committed, 101 rows, columns as listed, no real community name.
- [ ] `data/geo/nt_outline.geojson` committed, one NT feature, under 500 KB, source and licence noted in `data/raw/PROVENANCE.md`.
- [ ] `build_communities` is deterministic: running it twice yields byte-identical CSV.
- [ ] `test_geography.py` passes; the real-name helper is reused by later tests.
- [ ] Gate green.
