"""Chart palette and fixed UI strings. The only file under ``fair_turn/app`` that may hold a
colour literal; values are copied from ``design/design-system/chart-palette.json``."""

from fair_turn.core.constants import REMOTE_REGIONS, TOWN_REGION

REGION_COLOURS = dict(
    zip(
        (*REMOTE_REGIONS, TOWN_REGION),
        ("#8a6400", "#007d79", "#9f1853", "#198038", "#2d5bbf", "#4d5358"),
        strict=True,
    )
)
TOWN = "#262626"
REMOTE = "#8a3ffc"
LOCALITY_STROKE = {"town": "solid", "remote": "dashed"}
FACTOR_COLOURS = {
    "urgency": "#da1e28",
    "safety": "#b35c00",
    "health_risk": "#6929c4",
    "logistics": "#0072c3",
}
HUMAN_QUEUE = "#684e00"
HUMAN_QUEUE_BACKGROUND = "#fcf4d6"
GRIDLINE = "#e0e0e0"
AXIS_LABEL = "#525252"
STROKE_WIDTH = 2
PROVENANCE_LINE = "Geography real (BushTel/ABS); events synthetic"
