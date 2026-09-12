# Constants — values that must not be retyped

One definition each, in `fair_turn/core/constants.py`. Every other module reads from there;
Part 2 Key Constraints forbid literal copies. Secrets never go here (none exist: model access
is two logged-in CLIs).

| Name | Value | What it is for | Source |
|---|---|---|---|
| `SEED` | 20260912 | Only randomness source for synthesis and simulation | Project decision, the date Part 2 was written |
| `WINDOW_START` | 2025-10-01 | First day of the synthetic event window | PRD §6.2 |
| `WINDOW_DAYS` | 90 | Length of the window (to 29 Dec 2025) | PRD §6.2 |
| `SAFETY_CLASSES` | immediate, urgent, routine | NT's three repair classes | DHLGCD FS17 "Repairs and maintenance", 10/2025 |
| `MAKE_SAFE_HOURS` | 4 | Immediate class make-safe window, town and remote | FS17, 10/2025 |
| `RESPONSE_BUSINESS_DAYS` | urgent 2 / 5, routine 10 / 25 (town / remote) | NT response windows by class and locality | FS17, 10/2025 |
| `DIPL_APPROVAL_AUD` | 500 | Approval gate for non-urgent work; documented, unused in v1 | FS17, 10/2025; PRD §8 |
| `CREW_BASES` | Darwin, Katherine, Tennant Creek, Alice Springs, Nhulunbuy | Crew home bases for distance | PRD §6.1, provisional |
| `CREWS_PER_REMOTE_REGION` | 2 | Capacity model | PRD §6.3, provisional |
| `CREWS_TOWN` | 3 | Capacity model | PRD §6.3, provisional |
| `JOBS_PER_CREW_DAY` | 4 | Capacity model | PRD §6.3, provisional |
| `TRAVEL_DAY_KM` | 200 | Distance beyond which a visit costs a travel day | PRD §6.3, provisional |
| `REMOTE_REGIONS` | CENTRAL AUSTRALIA, BIG RIVERS, BARKLY, TOP END, EAST ARNHEM | Region names, BushTel spelling | `NTRegionName` in `data/raw/bushtel_community_detail_2026-09-12.json` |
| `TOWN_REGION` | DARWIN, PALMERSTON, LITCHFIELD | The town region, BushTel spelling | Same field |
| `HEAT_SEASON_MONTHS` | Oct–Mar | Extreme-heat exposure factor | NT Health heat-health advice (reports/2026-09-12-research-data-and-stack.md) |
| `WET_SEASON_MONTHS` | Oct–Apr | Road-logistics season | BoM NT seasonal summaries (same report) |
| `ROAD_FACTORS` (in `fair_turn/data/geography.py`) | sealed 1.0, unsealed 1.4, barge_or_air 2.5 | Multiplier on haversine km giving `logistics_factor` | Provisional project assumption (Task-01); no NT source |
