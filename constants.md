# Constants — values that must not be retyped

One definition each, in `fair_turn/core/constants.py`. Every other module reads from there;
Blueprint Key Constraints forbid literal copies. Secrets never go here (none exist: model access
is two logged-in CLIs).

| Name | Value | What it is for | Source |
|---|---|---|---|
| `CREW_BASE_COORDS` | Darwin, Katherine, Tennant Creek, Alice Springs and Nhulunbuy latitude/longitude pairs | Crew-base locations: where every crew starts and returns in the weekly plan | BushTel town records, `data/raw/bushtel_community_detail_2026-09-12.json` (`Point.Latitude`, `Point.Longitude`) |
| `TEAM_NUMBER` | AIC014 | Submission file name, report cover, slide footer | CDU registration; confirmed by Tarik 2026-09-12. The sibling Data Innovation Challenge entry is DIC005, never this one. |
| `SEED` | 20260912 | Only randomness source for synthesis and simulation | Project decision, the date Blueprint was written |
| `WINDOW_START` | 2025-10-01 | First day of the synthetic event window | PRD §6.2 |
| `WINDOW_DAYS` | 90 | Length of the window (to 29 Dec 2025) | PRD §6.2 |
| `SAFETY_CLASSES` | immediate, urgent, routine | NT's three repair classes | DHLGCD FS17 "Repairs and maintenance", 10/2025 |
| `MAKE_SAFE_HOURS` | 4 | Immediate class make-safe window, town and remote | FS17, 10/2025 |
| `RESPONSE_BUSINESS_DAYS` | urgent 2 / 5, routine 10 / 25 (town / remote) | NT response windows by class and locality | FS17, 10/2025 |
| `DIPL_APPROVAL_AUD` | 500 | Approval gate for non-urgent work; documented, unused in v1 | FS17, 10/2025; PRD §8 |
| `CREW_BASES` | Darwin, Katherine, Tennant Creek, Alice Springs, Nhulunbuy | Crew home bases for distance | Provisional; the five NT regional centres |
| `CREWS_AT_BASE` | Darwin 3, Katherine 2, Tennant Creek 1, Alice Springs 2, Nhulunbuy 2 | Licensed trade crews per regional town in the weekly plan | Provisional, our assumption (2026-10-02 rebuild, `docs/PRODUCT.md`); NT does not publish crew numbers. Sized so the crews roughly match the synthetic report volume (about 100 crew jobs a week) and remote trips compete with town work. Sensitivity: `data/build/report/one_more_crew.csv` |
| `CREW_DAYS_PER_WEEK` | 5 | Working days per crew per week | Provisional; a Monday-to-Friday week, public holidays not modelled |
| `JOBS_PER_CREW_DAY` | 3 | Repairs a crew fixes in one working day at one place | Provisional, our assumption; unchanged from the first version |
| `DRIVE_KM_PER_DAY` | 400 | Road km a crew covers in a day of driving; a trip's driving days are its round trip at this rate, in half days | Provisional, our assumption; road km are haversine times the road factor below |
| `MAX_JOBS_PER_TRIP` | 9 | Repairs one trip carries: three working days at one community | Provisional, our assumption |
| `PLAN_DAY` | 2025-12-29 | The planning Monday the app shows: the Monday after the last synthetic report | Project decision, 2026-10-02 |
| `SETTINGS` | Most repairs 0.0, Balanced 0.5, Most overdue first 1.0 | The three named settings of what decides where crews go | Project decision, 2026-10-02; the formula is in `fair_turn/core/weekly.py` and `docs/PRODUCT.md` |
| `REMOTE_REGIONS` | CENTRAL AUSTRALIA, BIG RIVERS, BARKLY, TOP END, EAST ARNHEM | Region names, BushTel spelling | `NTRegionName` in `data/raw/bushtel_community_detail_2026-09-12.json` |
| `TOWN_REGION` | DARWIN, PALMERSTON, LITCHFIELD | The town region, BushTel spelling | Same field |
| `HEAT_SEASON_MONTHS` | Oct–Mar | Extreme-heat exposure factor | NT Health heat-health advice (reports/2026-09-12-research-data-and-stack.md) |
| `WET_SEASON_MONTHS` | Oct–Apr | Road-logistics season | BoM NT seasonal summaries (same report) |
| `ROAD_FACTORS` (in `fair_turn/data/geography.py`) | sealed 1.0, unsealed 1.4, barge_or_air 2.5 | Multiplier on haversine km giving `logistics_factor` | Provisional project assumption (Task-01); no NT source |
| `REPORT_TARGET`, `REMOTE_REPORT_SHARE` (in `fair_turn/data/synth.py`) | 1500, 0.6 | Expected report count and remote share of the synthetic window | Provisional, PRD §6.2; NT work-order volumes are unpublished |
| `REMOTE_REPORT_RATE_RATIO` (`synth.py`) | 0.8 | A remote fault becomes a report with this probability, town 1.0: mechanism 3, static part | Provisional, PRD §6.2 |
| `HOLDOUT_COUNT` (`synth.py`) | 150 | Labels flagged for the evaluation set | PRD §6.4 |
| `F1_TARGET` (`eval/metrics.py`) | 0.85 | Macro-F1 pass mark for fault_type and safety_class; provisional, reported either way | PRD §7 |
| `POPULATION_BAND_MIDPOINTS` (`synth.py`) | 50 / 175 / 375 / 750 / 1500; not recorded 100 | Weight of a remote community in the fault draw | Provisional, PRD §6.2 |
| `TOWN_REPORT_WEIGHTS` (`synth.py`) | Darwin .55, Alice Springs .20, Katherine .12, Nhulunbuy .07, Tennant Creek .06 | Split of town reports across the five base towns (no population band in the table) | Provisional, PRD §6.2 |
| `FAULT_MIX`, `HEAT_RAMP` (`synth.py`) | plumbing .20, electrical .14, doors .12, cooling .10, sewer .10, roof .08, hot water .07, stove .07, pests .06, other .06; cooling ×1.0/1.3/1.6 and hot water ×1.0/1.1/1.2 Oct/Nov/Dec | Fault-type mix and its within-window heat ramp | Provisional, PRD §6.2; categories from FS17 and reports/2026-09-12-research-housing.md item 4 |
| `SAFETY_MIX_BY_FAULT` (`synth.py`) | per fault type, P(immediate, urgent, routine); overall about 8 / 45 / 47 % | Safety class conditional on fault type | Provisional, PRD §6.2; FS17 gives example faults per class, not proportions |
| `NO_WATER_PROBABILITY` (`synth.py`) | 0.6 | Chance an immediate/urgent water or sewer fault leaves the household without water or sanitation | Provisional, PRD §6.2 |
| `CLOSURES_PER_MONTH`, `CLOSURE_DAYS` (`synth.py`) | Poisson mean 0.15 / 0.4 / 0.9 per closable community Oct/Nov/Dec; 2–10 days each | Synthetic wet-season access closures: mechanism 2 | Provisional, PRD §6.2; no NT closure history exists |
| `MONTHLY_MEAN_MAX` (`synth.py`) | five BoM stations, Oct/Nov/Dec mean maximum | Base of the daily climate table | BoM climate statistics pages, station ids in `synth.py`; UNVERIFIED, see `data/raw/PROVENANCE.md` |
| `TEMP_AR_PHI`, `TEMP_ANOMALY_SD`, `HEAT_WARNING_EXCESS_C`, `HEAT_WARNING_DAYS` (`synth.py`) | 0.6, 2.5 °C, 2.0 °C, 3 days | Daily anomaly persistence and the relative heat-warning rule | Provisional, PRD §6.2; EHF-style relative framing from reports/2026-09-12-research-data-and-stack.md §3, thresholds ours |
