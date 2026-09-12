"""Write the synthetic ground truth to data/build/: labels, personas, closures, climate.

Run from the repo root with the project interpreter; idempotent for the same seed:
    venv/Scripts/python scripts/build_labels.py
Second step of the build pipeline (after fetch_raw_sources.py); needs no model and no network.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # the package is not installed into venv; scripts run from source

from fair_turn.data.synth import write_all  # noqa: E402  (needs the sys.path line above)


def main() -> int:
    for path in write_all():
        print(f"wrote {path.relative_to(ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
