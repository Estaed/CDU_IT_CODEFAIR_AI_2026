"""Stand-in for ``claude -p`` in wrapper tests. Behaviour comes from ``FAKE_MODE``:
``ok``, ``bad_then_ok`` (garbage on the first call, counted in ``FAKE_COUNTER``),
``is_error`` (JSON with ``is_error`` true), ``fail`` (exit 2 with stderr), ``extract``
(one canned extraction per report in the prompt's fenced JSON block: fault evidence is
the report's first three words, so it verifies; every second report's safety evidence is
not in the report, so it drops), ``fail_job`` (like ``fail`` when ``FAKE_FAIL_JOB``
appears in the prompt, else ``extract``), ``sleep`` (sleeps ``FAKE_SLEEP`` seconds,
default 30), ``sleep_job`` (like ``sleep`` when ``FAKE_SLEEP_JOB`` appears in the prompt,
else ``FAKE_MODE_FALLBACK``, default ``extract``)."""

import json
import os
import re
import sys
import time
from pathlib import Path


def canned_items(prompt: str) -> list[dict]:
    block = re.search(r"```json\n(.*?)\n```", prompt, re.S)
    reports = json.loads(block.group(1)) if block else []
    items = []
    for i, report in enumerate(reports):
        quote = " ".join(report["text"].split()[:3])
        items.append(
            {
                "job_id": report["job_id"],
                "fault_type": "other",
                "fault_type_evidence": quote,
                "safety_class": "routine",
                "safety_class_evidence": quote if i % 2 == 0 else "words that are not there",
                "health_risk": [],
                "health_risk_evidence": [],
                "location_mentioned": False,
                "location_evidence": "",
                "crew_or_access_note": "",
            }
        )
    return items


def main() -> int:
    mode = os.environ.get("FAKE_MODE", "ok")
    argv = sys.argv[1:]
    prompt = sys.stdin.read()  # the wrapper must pass the prompt on stdin
    schema = json.loads(argv[argv.index("--json-schema") + 1])
    if mode == "fail_job":
        mode = "fail" if os.environ["FAKE_FAIL_JOB"] in prompt else "extract"
    if mode == "sleep_job":
        fallback = os.environ.get("FAKE_MODE_FALLBACK", "extract")
        mode = "sleep" if os.environ["FAKE_SLEEP_JOB"] in prompt else fallback
    if mode == "sleep":
        time.sleep(float(os.environ.get("FAKE_SLEEP", "30")))
        return 0
    if mode == "fail":
        print("fake claude: simulated failure", file=sys.stderr)
        return 2
    if mode == "extract":
        print(json.dumps({"is_error": False, "structured_output": {"items": canned_items(prompt)}}))
        return 0
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
