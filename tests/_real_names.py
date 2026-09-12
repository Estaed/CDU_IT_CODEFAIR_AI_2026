"""Every real name of a pseudonymised community, for tests that assert none leaked.

Not a test module (leading underscore); import it from tests that need the list.
"""

import json
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
DETAIL = RAW / "bushtel_community_detail_2026-09-12.json"
PSEUDONYMISED_TYPES = ("Major", "Minor")


def real_names() -> list[str]:
    """Upper-case names and aliases of every Major/Minor BushTel community."""
    names: set[str] = set()
    for r in json.loads(DETAIL.read_text("utf-8")):
        if r["CommunityTypeName"] not in PSEUDONYMISED_TYPES:
            continue
        names.add(r["Name"].upper())
        names.add(r["DefaultName"].upper())
        names.update(a.upper() for a in r.get("AliasNamesString", "").split(",") if a.strip())
    return sorted(names)
