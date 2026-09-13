"""Stand-in for ``codex exec`` in wrapper tests. Behaviour comes from ``FAKE_MODE``:
``ok``, ``bad_then_ok`` (garbage in the output file on the first call, counted in
``FAKE_COUNTER``), ``fail`` (exit 2 with stderr), ``extract`` (one canned extraction per
report in the prompt's fenced JSON block: fault evidence is the report's first three words,
so it verifies; every second report's safety evidence is not in the report, so it drops)."""

import json
import os
import re
import sys
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
    on_stdin = argv[-1] == "-"
    prompt = sys.stdin.read() if on_stdin else argv[-1]  # the wrapper passes "-" and stdin
    schema = json.loads(Path(argv[argv.index("--output-schema") + 1]).read_text("utf-8"))
    out_path = Path(argv[argv.index("-o") + 1])
    if mode == "fail":
        print("fake codex: simulated failure", file=sys.stderr)
        return 2
    if mode == "bad_then_ok":
        counter = Path(os.environ["FAKE_COUNTER"])
        calls = int(counter.read_text()) + 1 if counter.exists() else 1
        counter.write_text(str(calls))
        if calls == 1:
            out_path.write_text("this is not json {", encoding="utf-8")
            return 0
    if mode == "extract":
        out_path.write_text(json.dumps({"items": canned_items(prompt)}), encoding="utf-8")
        return 0
    out_path.write_text(
        json.dumps(
            {
                "echo": prompt,
                "schema_title": schema.get("title"),
                "prompt_on_stdin": on_stdin,
                "flags": argv[:-1],
            }
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
