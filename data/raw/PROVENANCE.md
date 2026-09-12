# Raw sources — frozen snapshots, never fetched at runtime

Fetched 2026-09-12 by `scripts/fetch_raw_sources.py` (BushTel, road report) and by hand
(NT open data portal). Everything the synthetic dataset seeds from is here, so the app and
the report reproduce without network access. Research behind each source:
`reports/2026-09-12-research-geography.md`.

| File | Source | What it holds | Licence |
|---|---|---|---|
| `bushtel_communities_2026-09-12.json` | `https://bushtel.nt.gov.au/api/Community?community=&boundary=0` (undocumented public API) | 797 places: id, name, lat/lon, type (Major 59, Minor 37, Town Camp 45, Village 13, Town 6, City 2, Family Outstation 635) | TBD: footer says © NT Government, no licence stated. Confirm via nt.gov.au copyright page or opendata@nt.gov.au before publishing derived tables. |
| `bushtel_community_detail_2026-09-12.json` | `https://bushtel.nt.gov.au/api/Community/{id}` for the 162 non-outstation places | Population (ABS 2021 Census SA1; present for 139), NT region name, land council, SA1 code and geometry, prose description with distance to town and road notes, services, demographics | as above |
| `roadreport_obstructions_2026-09-12.json` | `https://roadreport.nt.gov.au/api/Obstruction/GetAll` | 80 current obstructions: road, type (flooding, road damage, roadworks), restriction, dates, geometry. Snapshot only; no history exists. | TBD |
| `ntgov_communities_mobile_coverage_2021.xlsx` | data.nt.gov.au "Remote Communities with 3G/4G Mobile Coverage 2021" | Community list with GPS coordinates and coverage tier; licence-clean cross-check for BushTel coordinates | Creative Commons Attribution (portal metadata, modified 2022-06-29) |
| `..._data-quality-statement.pdf` | same dataset | Data quality statement | as above |

Not fetched yet: ABS ILOC 2021 boundaries (CC BY 4.0, large GeoPackage) — only if the
region clustering needs official boundaries; BushTel `NTRegionName` may suffice.

Community names in these files are real. Fair Turn's synthetic dataset replaces them with
pseudonymous ids (see `notes.md`, "Community identity"); the id-to-name mapping is not
committed.
