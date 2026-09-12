"""Stand-in for ``claude -p`` in wrapper tests. Behaviour comes from ``FAKE_MODE``:
``ok``, ``bad_then_ok`` (garbage on the first call, counted in ``FAKE_COUNTER``),
``is_error`` (JSON with ``is_error`` true), ``fail`` (exit 2 with stderr)."""

import json
import os
import re
import sys
from pathlib import Path


def main() -> int:
    mode = os.environ.get("FAKE_MODE", "ok")
    argv = sys.argv[1:]
    prompt = sys.stdin.read()  # the wrapper must pass the prompt on stdin
    schema = json.loads(argv[argv.index("--json-schema") + 1])
    if mode == "fail":
        print("fake claude: simulated failure", file=sys.stderr)
        return 2
    if mode == "bad_then_ok":
        counter = Path(os.environ["FAKE_COUNTER"])
        calls = int(counter.read_text()) + 1 if counter.exists() else 1
        counter.write_text(str(calls))
        if calls == 1:
            print("this is not json {")
            return 0
    if mode == "is_error":
        print(json.dumps({"is_error": True, "result": "simulated model error"}))
        return 0
    if mode == "reports":  # one canned tenant report per job id found in the prompt
        ids = sorted(set(re.findall(r"JR-\d{4}-\d{5}", prompt)))
        reports = [
            {"job_id": i, "text": f"Report {i}: the tap leaks all day and night."} for i in ids
        ]
        print(json.dumps({"is_error": False, "structured_output": {"reports": reports}}))
        return 0
    print(
        json.dumps(
            {
                "is_error": False,
                "structured_output": {
                    "echo": prompt,
                    "schema_title": schema.get("title"),
                    "flags": argv,
                },
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
