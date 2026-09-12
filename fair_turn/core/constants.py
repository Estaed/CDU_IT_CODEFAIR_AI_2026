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

# Capacity model, PRD section 6.3, all provisional.
CREW_BASES = ("Darwin", "Katherine", "Tennant Creek", "Alice Springs", "Nhulunbuy")
CREWS_PER_REMOTE_REGION = 1
CREWS_TOWN = 2
JOBS_PER_CREW_DAY = 2
TRAVEL_DAY_KM = 200

# Regions exactly as BushTel spells ``NTRegionName``.
REMOTE_REGIONS = ("CENTRAL AUSTRALIA", "BIG RIVERS", "BARKLY", "TOP END", "EAST ARNHEM")
TOWN_REGION = "DARWIN, PALMERSTON, LITCHFIELD"
REGIONS = (*REMOTE_REGIONS, TOWN_REGION)

# Seasons by calendar month: NT Health extreme-heat season, BoM NT wet season.
HEAT_SEASON_MONTHS = (10, 11, 12, 1, 2, 3)
WET_SEASON_MONTHS = (10, 11, 12, 1, 2, 3, 4)
