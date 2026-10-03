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

    lists = sub.add_parser("lists", help="scan an approved question list for uncovered policy rules")
    lists.add_argument("--coverage", required=True, metavar="LIST_ID")
    lists.add_argument("--replay", action="store_true",
                       help="use the list's coverage-cache only; no keys, no network")

    ev = sub.add_parser("eval", help="evaluation parts -> runs/eval/<part>.json and summary.json")
    ev.add_argument("--case")
    ev.add_argument("--part", choices=["checker", "cases", "mutations", "ablation", "benchmark"],
                    help="checker: SummEdits; cases: end-to-end files; mutations: audit claims; "
                         "ablation: cumulative layers; benchmark: release synthetic CSVs; "
                         "without --part, only summary.json is rebuilt from the parts present")
    ev.add_argument("--replay", action="store_true",
                    help="read model responses from the part's replay cache; no keys, no network")
    ev.add_argument("--checker", choices=["jev", "claude"], default="jev")

    args = parser.parse_args(argv)
    if args.verb == "lists":
        from readmark.checklist.coverage import run_coverage

        result = run_coverage(args.coverage, replay=args.replay)
        print(f"{args.coverage}: {result['n_reported']} policy rules no question covers "
              f"(n={result['n_scanned']} scanned; {result['model']}; {result['date']})")
        return 0
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
    from readmark.eval import assemble_summary, eval_dir

    if args.case and args.part not in ("cases", "mutations"):
        parser.error("--case applies to --part cases or --part mutations")
    if args.part in ("cases", "mutations") and args.checker != "jev":
        parser.error("case evaluation freezes the existing Jev checker; use --checker jev")
    if args.part == "checker":
        from readmark.eval.checker import evaluate

        result = evaluate(replay=args.replay)
        for name in ("jev", "claude"):
            o = result["checkers"][name]["overall"]
            print(f"{name}: balanced accuracy {o['balanced_accuracy']} (n={o['n']})")
        print(f"-> {eval_dir() / 'checker.json'}")
    elif args.part:
        from readmark.eval.cases import (
            evaluate_ablation,
            evaluate_cases,
            evaluate_mutations,
            release_benchmark,
        )

        if args.part == "cases":
            result = evaluate_cases(args.replay, args.case)
            for cid, score in result["cases"].items():
                reading, gold = score["required_reading"], score["gold_page_coverage"]
                print(f"{cid}: required passages {reading['count']} (cap n={reading['n']}), "
                      f"gold pages covered {gold['count']} (n={gold['n']})")
        elif args.part == "mutations":
            result = evaluate_mutations(args.replay, args.case)
            for name in ("catch_rate", "false_alarm_rate"):
                metric = result["overall"][name]
                print(f"{name}: {metric['rate']} (n={metric['n']})")
        elif args.part == "ablation":
            evaluate_ablation()
        elif args.part == "benchmark":
            release_benchmark()
        print(f"-> {eval_dir() / (args.part + '.json')}")
    print(f"-> {assemble_summary()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
