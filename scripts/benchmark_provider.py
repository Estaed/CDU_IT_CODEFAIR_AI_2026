"""Benchmark one intake provider on the build extractor's tables (PRD sections 5 and 7).

Runs the 150 holdout reports and the 20 adversarial items through ``llm.intake.extract`` with
the named provider and model, scores fault_type, safety_class and health_risk with
``fair_turn.eval.metrics`` the way ``run_eval.py`` does, and decides the intake default:
``ollama`` only if its macro-F1 is not below the build extractor's in eval.json for both
required fields and every adversarial item leaves the rank unchanged (Part 2, the provider
seam). From the repo root, after ``ollama pull qwen3:8b``:
    venv/Scripts/python scripts/benchmark_provider.py --provider ollama --model qwen3:8b
Writes data/build/eval_<provider>.json, prints the decision line and exits 0 either way: the
table is the pass mark, not the exit code. ``--fake`` answers every item with its gold label
and the report's first three words as evidence, so the pipeline runs with no model.
"""

import argparse
import json
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # the package is not installed into venv; scripts run from source

from fair_turn.core.types import FaultType, HealthRiskFactor, SafetyClass  # noqa: E402
from fair_turn.core.verify_spans import REQUIRED_FIELDS  # noqa: E402
from fair_turn.eval import metrics  # noqa: E402
from fair_turn.llm import claude_cli, intake, ollama  # noqa: E402

BUILD = ROOT / "data" / "build"
FIELDS = {"fault_type": [str(v) for v in FaultType], "safety_class": [str(v) for v in SafetyClass]}
DIGITS = 4

Call = Callable[[str, dict], dict]


def fake_call_for(label: dict, text: str) -> Call:
    """The gold label, every evidence phrase the report's first three words."""
    phrase = " ".join(text.split()[:3])

    def call(prompt: str, json_schema: dict) -> dict:
        return {
            "fault_type": label["fault_type"],
            "fault_type_evidence": phrase,
            "safety_class": label["safety_class"],
            "safety_class_evidence": phrase,
            "health_risk": list(label["health_risk"]),
            "health_risk_evidence": [phrase] * len(label["health_risk"]),
            "location_mentioned": False,
            "location_evidence": "",
            "crew_or_access_note": "",
        }

    return call


def provider_call(provider: str, model: str, timeout: float) -> Call:
    if provider == "ollama":

        def call(prompt: str, json_schema: dict) -> dict:
            return ollama.chat(prompt, json_schema, model=model, timeout=timeout)

    else:

        def call(prompt: str, json_schema: dict) -> dict:
            return claude_cli.generate(prompt, json_schema, model=model, timeout=timeout)

    return call


def _predicted(result: intake.IntakeResult, field: str) -> str:
    verified = result.verified
    if verified is None or verified.needs_human:
        return metrics.EMPTY
    return str(getattr(verified, field))


def _factors(result: intake.IntakeResult) -> set[str]:
    verified = result.verified
    return set() if verified is None or verified.needs_human else set(verified.health_risk)


def _ranked_fields(result: intake.IntakeResult) -> tuple | None:
    """What the ranking reads from one extraction; None when the job goes to the human queue."""
    verified = result.verified
    if verified is None or verified.needs_human:
        return None
    return (verified.fault_type, verified.safety_class, tuple(sorted(verified.health_risk)))


def rank_unchanged(original: intake.IntakeResult, substitute: intake.IntakeResult) -> bool:
    """The injected copy leaves the rank unchanged if the ranking reads the same fields from it
    as from its original, or if it goes to the human queue and so moves no ranked job (the
    same rule as ``order_unchanged`` in tests/test_extraction_artefact.py)."""
    fields = _ranked_fields(substitute)
    return fields is None or fields == _ranked_fields(original)


def decide(
    ours: dict[str, float], build: dict[str, float], adversarial_ok: int, adversarial_n: int
) -> tuple[str, str]:
    """``ollama`` only if not below the build extractor on both required fields and every
    adversarial item left the rank unchanged; otherwise ``claude``, with the numbers."""
    numbers = "; ".join(
        f"{field} macro-F1 {ours[field]:.4f} vs build {build[field]:.4f}"
        for field in REQUIRED_FIELDS
    )
    adversarial = f"adversarial {adversarial_ok}/{adversarial_n} rank unchanged"
    lower = [field for field in REQUIRED_FIELDS if ours[field] < build[field]]
    all_held = adversarial_n > 0 and adversarial_ok == adversarial_n
    if not lower and all_held:
        held = "not below the build extractor on both required fields"
        return "ollama", f"{held}; {numbers}; {adversarial}"
    failed = [f"below the build extractor on {', '.join(lower)}"] if lower else []
    if not all_held:
        failed.append("not every adversarial item left the rank unchanged")
    return "claude", f"{'; '.join(failed)}; {numbers}; {adversarial}"


def _latency(values: list[float]) -> dict:
    if not values:
        return {"p50": None, "p90": None, "max": None, "n": 0}
    array = np.array(values)
    return {
        "p50": float(np.percentile(array, 50)),
        "p90": float(np.percentile(array, 90)),
        "max": float(array.max()),
        "n": len(values),
    }


def _rounded(node):
    if isinstance(node, float):
        return round(node, DIGITS)
    if isinstance(node, dict):
        return {k: _rounded(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_rounded(v) for v in node]
    return node


def benchmark(
    provider: str,
    model: str,
    call_for: Callable[[dict, str], Call],
    build: Path = BUILD,
    limit: int | None = None,
    timeout: float = 300,
) -> dict:
    # Step 1: the holdout set and the adversarial items, selected as run_eval.py and
    # extract.py select them; --limit trims both for a smoke run.
    labels = json.loads((build / "labels.json").read_text("utf-8"))
    texts = {
        r["job_id"]: r["text"] for r in json.loads((build / "reports.json").read_text("utf-8"))
    }
    adversarial = json.loads((build / "adversarial.json").read_text("utf-8"))
    by_id = {label["job_id"]: label for label in labels}
    holdout = [lb for lb in labels if lb["is_holdout"] and not lb["is_adversarial"]]
    holdout, adversarial = holdout[:limit], adversarial[:limit]

    latencies: list[float] = []
    results: dict[str, intake.IntakeResult] = {}

    def run(job_id: str, label: dict, text: str) -> intake.IntakeResult:
        result = intake.extract(text, provider, timeout=timeout, call=call_for(label, text))
        latencies.append(result.latency_s)
        print(f"{job_id}: {result.status} in {result.latency_s:.1f} s", flush=True)
        return result

    # Step 2: one extraction per holdout report, scored per field like run_eval.py.
    for label in holdout:
        results[label["job_id"]] = run(label["job_id"], label, texts[label["job_id"]])
    scored = [results[lb["job_id"]] for lb in holdout]
    fields = {}
    for field, classes in FIELDS.items():
        gold = [lb[field] for lb in holdout]
        fields[field] = metrics.prf(gold, [_predicted(r, field) for r in scored], classes)
    gold_sets = [set(lb["health_risk"]) for lb in holdout]
    factors = [str(f) for f in HealthRiskFactor if any(str(f) in g for g in gold_sets)]
    fields["health_risk"] = metrics.multilabel_prf(
        gold_sets, [_factors(r) for r in scored], factors
    )

    # Step 3: each adversarial item against its original (extracted here if --limit left the
    # original out of the scored set).
    moved = []
    for item in adversarial:
        original_id = item["original_job_id"]
        label = by_id[original_id]
        if original_id not in results:
            results[original_id] = run(original_id, label, texts[original_id])
        substitute = run(item["job_id"], label, item["text"])
        if not rank_unchanged(results[original_id], substitute):
            moved.append(item["job_id"])

    # Step 4: the decision against the build extractor's numbers in eval.json.
    evaluation = json.loads((build / "eval.json").read_text("utf-8"))
    build_numbers = {f: evaluation["extractor"][f]["macro_f1"] for f in evaluation["extractor"]}
    ours = {f: round(fields[f]["macro_f1"], DIGITS) for f in REQUIRED_FIELDS}
    unchanged = len(adversarial) - len(moved)
    default, reason = decide(ours, build_numbers, unchanged, len(adversarial))
    statuses = [r.status for r in scored]
    return _rounded(
        {
            "provider": provider,
            "model": model,
            "n_items": len(holdout),
            "n_adversarial": len(adversarial),
            "fields": fields,
            "statuses": {s: statuses.count(s) for s in sorted(set(statuses))},
            "adversarial": {"unchanged": unchanged, "n": len(adversarial), "moved": moved},
            "latency_s": _latency(latencies),
            "decision": {"default": default, "reason": reason},
            "build_extractor": build_numbers,
            "run_at": datetime.now(UTC).isoformat(timespec="seconds"),
        }
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["claude", "ollama"], required=True)
    parser.add_argument("--model", required=True, help="e.g. qwen3:8b or sonnet")
    parser.add_argument("--limit", type=int, help="first N holdout and adversarial items only")
    parser.add_argument("--out", type=Path, help="default data/build/eval_<provider>.json")
    parser.add_argument("--fake", action="store_true", help="answer with the gold labels")
    parser.add_argument("--timeout", type=float, default=300, help="seconds per call")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    real = None if args.fake else provider_call(args.provider, args.model, args.timeout)

    def call_for(label: dict, text: str) -> Call:
        return fake_call_for(label, text) if real is None else real

    result = benchmark(args.provider, args.model, call_for, limit=args.limit, timeout=args.timeout)
    out = args.out or BUILD / f"eval_{args.provider}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1) + "\n", "utf-8", newline="")
    print(f"wrote {out}")
    print(f"decision: default = {result['decision']['default']} ({result['decision']['reason']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
