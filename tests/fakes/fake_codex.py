"""Stand-in for ``codex exec`` in wrapper tests. Behaviour comes from ``FAKE_MODE``:
``ok``, ``bad_then_ok`` (garbage in the output file on the first call, counted in
``FAKE_COUNTER``), ``fail`` (exit 2 with stderr)."""

import json
import os
import sys
from pathlib import Path


def main() -> int:
    mode = os.environ.get("FAKE_MODE", "ok")
    argv = sys.argv[1:]
    stdin = sys.stdin.read()  # the wrapper must close stdin, so this is empty
    schema = json.loads(Path(argv[argv.index("--output-schema") + 1]).read_text("utf-8"))
    out_path = Path(argv[argv.index("-o") + 1])
    prompt = argv[-1]
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
    out_path.write_text(
        json.dumps(
            {
                "echo": prompt,
                "schema_title": schema.get("title"),
                "stdin_was_empty": stdin == "",
                "flags": argv[:-1],
            }
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
