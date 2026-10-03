"""``python -m readmark run|serve|eval``."""

import argparse
import sys

from readmark import case_run_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="readmark")
    sub = parser.add_subparsers(dest="verb", required=True)

    run = sub.add_parser("run", help="run every layer on one case and write runs/<case>/")
    run.add_argument("--case", required=True)
    run.add_argument("--replay", action="store_true",
                     help="read every model response from runs/<case>/cache/; no keys, no network")
    run.add_argument("--checker", choices=["jev", "claude"], default="jev")

    serve = sub.add_parser("serve", help="serve the review screen on localhost")
    serve.add_argument("--case", default="stub")
    serve.add_argument("--port", type=int, default=8765)

    ev = sub.add_parser("eval", help="evaluation (wave 2)")
    ev.add_argument("--case")

    args = parser.parse_args(argv)
    if args.verb == "run":
        from readmark.pipeline import run as run_case

        view = run_case(args.case, replay=args.replay, checker=args.checker)
        print(
            f"{args.case}: {len(view['claims'])} claims, "
            f"{len(view['required_reading'])} required passages "
            f"(+{len(view['suggested_reading'])} suggested) -> "
            f"{case_run_dir(args.case) / 'view.json'}"
        )
        return 0
    if args.verb == "serve":
        from readmark.serve import serve

        serve(args.case, args.port)
        return 0
    print("eval is not built yet: it arrives in wave 2 (mutation set, held-out file, checker "
          "evaluation).", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
