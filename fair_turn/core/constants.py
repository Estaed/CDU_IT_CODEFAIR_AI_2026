"""Every policy number, capacity figure, region name and the seed, defined once.

Provenance for each value is a row in ``constants.md`` at the repo root. Nothing here is
retyped anywhere else in ``fair_turn``.
"""

from datetime import date

SEED = 20260912

# Synthetic event window: heat season and wet-season onset (PRD section 6.2).
WINDOW_START = date(2025, 10, 1)
WINDOW_DAYS = 90

# NT response windows, DHLGCD fact sheet FS17 "Repairs and maintenance", 10/2025.
SAFETY_CLASSES = ("immediate", "urgent", "routine")
MAKE_SAFE_HOURS = 4  # immediate class, town and remote alike
# Keyed by (safety class, is_remote); immediate is hours, not business days, see above.
RESPONSE_BUSINESS_DAYS = {
    ("urgent", False): 2,
    ("urgent", True): 5,
    ("routine", False): 10,
    ("routine", True): 25,
}
DIPL_APPROVAL_AUD = 500  # documented gate for non-urgent work; unused by v1 code (PRD 8)

# Weekly crew model (docs/PRODUCT.md, "The model"), all provisional: no NT source publishes
# crew numbers or productivity, so these are our assumptions and the report says so.
CREW_BASES = ("Darwin", "Katherine", "Tennant Creek", "Alice Springs", "Nhulunbuy")
CREWS_AT_BASE = {
    "Darwin": 3,
    "Katherine": 2,
    "Tennant Creek": 1,
    "Alice Springs": 2,
    "Nhulunbuy": 2,
}
CREW_DAYS_PER_WEEK = 5
JOBS_PER_CREW_DAY = 3
DRIVE_KM_PER_DAY = 400  # road km a crew covers in one day of driving
MAX_JOBS_PER_TRIP = 9  # three working days at one community
# NT public holidays inside the window and the planning week (Public Holidays Act 1981):
# not business days. A crew's week is still five days; see docs/PRODUCT.md.
PUBLIC_HOLIDAYS = (date(2025, 12, 25), date(2025, 12, 26), date(2026, 1, 1))
# The planning week the app shows: a full working week before Christmas, so no public
# holiday falls inside it.
PLAN_DAY = date(2025, 12, 15)
# The three named settings of "what decides where crews go" (0 = efficiency first).
SETTINGS = {"Efficiency first": 0.0, "Balanced": 0.5, "Most overdue first": 1.0}
CREW_BASE_COORDS = {
    "Darwin": (-12.461534, 130.842442),
    "Katherine": (-14.46676, 132.266768),
    "Tennant Creek": (-19.6478, 134.1902),
    "Alice Springs": (-23.6994, 133.8807),
    "Nhulunbuy": (-12.187, 136.7763),
}

# Regions exactly as BushTel spells ``NTRegionName``.
REMOTE_REGIONS = ("CENTRAL AUSTRALIA", "BIG RIVERS", "BARKLY", "TOP END", "EAST ARNHEM")
TOWN_REGION = "DARWIN, PALMERSTON, LITCHFIELD"
REGIONS = (*REMOTE_REGIONS, TOWN_REGION)

# Seasons by calendar month: NT Health extreme-heat season, BoM NT wet season.
HEAT_SEASON_MONTHS = (10, 11, 12, 1, 2, 3)
WET_SEASON_MONTHS = (10, 11, 12, 1, 2, 3, 4)
