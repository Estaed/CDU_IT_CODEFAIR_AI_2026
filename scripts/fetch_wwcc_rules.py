"""Download the two pinned NT Working with Children Clearance rule PDFs.

The source bytes and dates match the supplied synthetic W-01 test rules. Downloads are
git-ignored; only the lock is committed. A changed response never replaces a pinned file.
Run from any directory: ``python scripts/fetch_wwcc_rules.py``. No model is called.
"""

import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "policies" / "nt-wwcc"
LOCK = OUT / "policies.lock.json"
USER_AGENT = "Mozilla/5.0 (Readmark pinned rule download)"


def fetch_rules(destination: Path = OUT, lock: Path = LOCK) -> None:
    pins = json.loads(lock.read_text(encoding="utf-8"))
    downloads = []
    # Check both responses before publishing either: an error leaves local rules intact.
    for name, pin in pins.items():
        if Path(name).name != name or not name.endswith(".pdf"):
            raise ValueError(f"Invalid pinned PDF filename: {name}")
        request = urllib.request.Request(pin["url"], headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=60) as response:
            content = response.read()
        digest = hashlib.sha256(content).hexdigest()
        if not content.startswith(b"%PDF-") or digest != pin["sha256"]:
            raise ValueError(f"{name}: download differs from the pinned SHA-256; "
                             "existing rules were kept. Review the source before re-pinning.")
        downloads.append((name, content, digest))
    destination.mkdir(parents=True, exist_ok=True)
    for name, content, digest in downloads:
        path = destination / name
        path.write_bytes(content)
        print(f"{name}: SHA-256 {digest} (matches pin)")


def main() -> int:
    try:
        fetch_rules()
    except (OSError, ValueError, urllib.error.URLError) as exc:
        print(f"Rule download failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
