"""Freeze the public NT sources Fair Turn seeds its synthetic data from.

Run once; commits the snapshots under data/raw/. The app never calls these at runtime.
Usage: PYTHONUTF8=1 python scripts/fetch_raw_sources.py
"""

import json
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
TODAY = date.today().isoformat()
UA = {"User-Agent": "FairTurn-research/0.1 (CDU IT Code Fair 2026; one-off snapshot)"}


def get(url: str, retries: int = 3) -> bytes:
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except Exception as exc:  # noqa: BLE001 - one-off fetch script, report and retry
            print(f"  retry {attempt + 1}: {url} -> {exc}", file=sys.stderr)
            time.sleep(2)
    raise SystemExit(f"failed: {url}")


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)

    # 1. BushTel community list (all 797 records), then detail for Major/Minor communities.
    communities = json.loads(get("https://bushtel.nt.gov.au/api/Community?community=&boundary=0"))
    (RAW / f"bushtel_communities_{TODAY}.json").write_bytes(
        json.dumps(communities, indent=1).encode()
    )
    print(f"bushtel list: {len(communities)} records")
    # Types seen 2026-09-12: Family Outstation 635, Major 59, Town Camp 45, Minor 37,
    # Village 13, Town 6, City 2. Detail is pulled for the populated settlement types.
    wanted = [
        c
        for c in communities
        if c["CommunityTypeName"] in ("Major", "Minor", "Town Camp", "Village", "Town", "City")
    ]
    print(f"fetching detail for {len(wanted)} communities")
    details = []
    for c in wanted:
        details.append(json.loads(get(f"https://bushtel.nt.gov.au/api/Community/{int(c['Id'])}")))
        time.sleep(0.3)
    (RAW / f"bushtel_community_detail_{TODAY}.json").write_bytes(
        json.dumps(details, indent=1).encode()
    )
    print(f"bushtel detail: {len(details)} records")

    # 2. NT road report obstruction snapshot (current only; no history exists).
    roads = get("https://roadreport.nt.gov.au/api/Obstruction/GetAll")
    (RAW / f"roadreport_obstructions_{TODAY}.json").write_bytes(roads)
    print(f"roadreport: {len(json.loads(roads))} records")


if __name__ == "__main__":
    main()
