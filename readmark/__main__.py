"""``python -m readmark run|serve|eval``."""

import argparse
import sys
from pathlib import Path

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
    action = lists.add_mutually_exclusive_group(required=True)
    action.add_argument("--coverage", metavar="LIST_ID")
    action.add_argument("--generate", type=Path, metavar="RULES_FOLDER")
    lists.add_argument("--id")
    lists.add_argument("--name")
    lists.add_argument("--scope", help="one-sentence subject; defaults to the list name")
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
        if args.generate:
            if not args.id or not args.name:
                parser.error("--generate needs --id and --name")
            from readmark.checklist.generate import generate_from_folder

            result = generate_from_folder(args.generate, args.id, args.name,
                                          args.scope or args.name, replay=args.replay)
            print(f"{args.id}: {len(result['suggestions'])} suggestions; none approved. "
                  f"Open /?list={args.id} to review them.")
            return 0
        from readmark.checklist.coverage import run_coverage
        from readmark.checklist.lists import generated_lists_dir

        options = ({"lists_dir": generated_lists_dir()}
                   if (generated_lists_dir() / args.coverage).is_dir() else {})
        result = run_coverage(args.coverage, replay=args.replay, **options)
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
