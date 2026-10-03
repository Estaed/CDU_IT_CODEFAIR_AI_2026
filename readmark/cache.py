"""Replay cache: every live model response is stored under ``runs/<case>/cache/`` keyed by a
hash of its request (contract, Run outputs).

Only the response is written, never the request: the request carries policy text, and the cache
must hold none beyond the quotes the screen shows. ``--replay`` reads these files and never
touches the network or a key.
"""

import hashlib
import json
from collections.abc import Callable
from pathlib import Path


class ReplayMiss(RuntimeError):
    """A replay asked for a response that was never recorded."""


def request_key(request: dict) -> str:
    canonical = json.dumps(request, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class Cache:
    def __init__(self, directory: Path, replay: bool):
        self.directory = directory
        self.replay = replay

    def call(self, kind: str, request: dict, live: Callable[[], dict]) -> dict:
        """Return the cached response for ``request``; on a miss, call ``live`` and store it,
        unless this is a replay, which fails instead."""
        key = request_key(request)
        path = self.directory / f"{kind}-{key[:24]}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))["response"]
        if self.replay:
            raise ReplayMiss(
                f"--replay: no cached {kind} response for request {key[:24]} in {self.directory}. "
                "Run once live (without --replay) to record it."
            )
        response = live()
        self.directory.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"kind": kind, "key": key, "response": response}, indent=1,
                       ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return response
