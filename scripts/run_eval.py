"""Score the committed extraction against the synthetic labels and a no-model baseline.

Run from the repo root with the project interpreter; needs no model and no network:
    venv/Scripts/python scripts/run_eval.py
Writes data/build/eval.json and data/build/eval_tables.md. Exits 1 if macro-F1 for
fault_type or safety_class is below F1_TARGET, 0 otherwise; prints the numbers either way.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # the package is not installed into venv; scripts run from source

from fair_turn.core.types import FaultType, HealthRiskFactor, SafetyClass  # noqa: E402
from fair_turn.eval import baseline, metrics  # noqa: E402  (needs the sys.path line above)

BUILD = ROOT / "data" / "build"
FIELDS = {"fault_type": [str(v) for v in FaultType], "safety_class": [str(v) for v in SafetyClass]}
TARGET_FIELDS = ("fault_type", "safety_class")
DIGITS = 4


def _load(build: Path, name: str):
    return json.loads((build / name).read_text("utf-8"))


def _predicted(row: dict, field: str) -> str:
    if row["needs_human"] or field not in row["kept"]:
        return metrics.EMPTY
    return str(row["kept"][field]["value"])


def _factors(row: dict) -> set[str]:
    if row["needs_human"]:
        return set()
    return {k.split(":", 1)[1] for k in row["kept"] if k.startswith("health_risk:")}


def _pred_spans(rows: list[dict], texts: dict[str, str]) -> list[dict]:
    spans = []
    for row in rows:
        for field, kept in row["kept"].items():
            start = texts[row["job_id"]].find(kept["evidence"])
            if start >= 0:
                end = start + len(kept["evidence"])
                spans.append({"job_id": row["job_id"], "field": field, "start": start, "end": end})
    return spans


def _rounded(node):
    if isinstance(node, float):
        return round(node, DIGITS)
    if isinstance(node, dict):
        return {k: _rounded(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_rounded(v) for v in node]
    return node


def evaluate(build: Path = BUILD) -> dict:
    labels = _load(build, "labels.json")
    texts = {r["job_id"]: r["text"] for r in _load(build, "reports.json")}
    rows = {r["job_id"]: r for r in _load(build, "extraction.json") if not r["is_adversarial"]}
    holdout = [lb for lb in labels if lb["is_holdout"] and not lb["is_adversarial"]]
    train = [lb for lb in labels if not lb["is_holdout"] and not lb["is_adversarial"]]
    scored = [rows[lb["job_id"]] for lb in holdout]
    holdout_texts = [texts[lb["job_id"]] for lb in holdout]

    extractor, reference = {}, {}
    for field, classes in FIELDS.items():
        gold = [lb[field] for lb in holdout]
        extractor[field] = metrics.prf(gold, [_predicted(r, field) for r in scored], classes)
        predicted = baseline.fit_predict(
            [texts[lb["job_id"]] for lb in train], [lb[field] for lb in train], holdout_texts
        )
        reference[field] = metrics.prf(gold, predicted, classes)
    gold_sets = [set(lb["health_risk"]) for lb in holdout]
    factors = [str(f) for f in HealthRiskFactor if any(str(f) in g for g in gold_sets)]
    extractor["health_risk"] = metrics.multilabel_prf(
        gold_sets, [_factors(r) for r in scored], factors
    )

    notes = [
        "location_mentioned and crew_or_access_note have no gold label in labels.json, "
        "so they get no precision, recall or F1.",
        f"{sum(r['needs_human'] for r in scored)} of {len(scored)} holdout rows went to the "
        "human queue; their fields count as empty predictions (false negatives).",
        "Macro precision, recall and F1 are means over classes, not proportions, so they carry "
        "no Wilson interval; each per-class precision and recall, accuracy, exact-set match "
        "and the substring rate do.",
        "The baseline is scored for fault_type and safety_class only.",
        "The substring rate is over every extraction row, adversarial items included.",
    ]
    gold_spans_path = build / "gold_spans.json"
    if gold_spans_path.exists():
        gold_spans = _load(build, "gold_spans.json")
        span = metrics.span_scores(gold_spans, _pred_spans(scored, texts))
    else:
        span = None
        notes.append(
            "span_scores is null: no gold spans exist (labels were drawn first and the "
            "generator returned text only), and none were invented."
        )

    return _rounded(
        {
            "n_holdout": len(holdout),
            "extractor": extractor,
            "baseline": reference,
            "substring_rate": metrics.substring_rate(_load(build, "extraction.json")),
            "span_scores": span,
            "f1_target": metrics.F1_TARGET,
            "target_met": {f: extractor[f]["macro_f1"] >= metrics.F1_TARGET for f in TARGET_FIELDS},
            "notes": notes,
        }
    )


def _cell(stats: dict, key: str) -> str:
    low, high = stats[f"{key}_ci"]
    return f"{stats[key]:.3f} [{low:.3f}, {high:.3f}]"


def tables(result: dict) -> str:
    lines = [f"# Evaluation on {result['n_holdout']} holdout reports", ""]
    for field, stats in result["extractor"].items():
        models = [("extractor", stats)]
        if field in result["baseline"]:
            models.append(("baseline", result["baseline"][field]))
        header = ["class"] + [f"{m} {k}" for m, _ in models for k in ("P [95% CI]", "R [95% CI]")]
        header += [f"{m} F1" for m, _ in models]
        lines += [f"## {field}", "", "| " + " | ".join(header) + " |"]
        lines.append("|" + "---|" * len(header))
        for label in stats["per_class"]:
            per = [s["per_class"][label] for _, s in models]
            cells = [c for p in per for c in (_cell(p, "precision"), _cell(p, "recall"))]
            lines.append(
                "| " + " | ".join([label, *cells, *(f"{p['f1']:.3f}" for p in per)]) + " |"
            )
        macro = [f"{s[k]:.3f}" for _, s in models for k in ("macro_precision", "macro_recall")]
        macro += [f"**{s['macro_f1']:.3f}**" for _, s in models]
        lines.append("| " + " | ".join(["**macro**", *macro]) + " |")
        share = "exact_set_match" if "exact_set_match" in stats else "accuracy"
        summary = "; ".join(f"{m} {share.replace('_', ' ')} {_cell(s, share)}" for m, s in models)
        lines += ["", summary, ""]
    rate = result["substring_rate"]
    met = ", ".join(f"{f} {'met' if ok else 'not met'}" for f, ok in result["target_met"].items())
    lines.append(f"Substring verification: {_cell(rate, 'rate')} of {rate['n']} extraction rows.")
    lines.append(f"Macro-F1 target {result['f1_target']:.2f}: {met}.")
    lines += ["", "Notes:", "", *(f"- {n}" for n in result["notes"])]
    return "\n".join(lines) + "\n"


def main() -> int:
    result = evaluate()
    (BUILD / "eval.json").write_text(json.dumps(result, indent=1) + "\n", "utf-8", newline="")
    (BUILD / "eval_tables.md").write_text(tables(result), "utf-8", newline="")
    for field in TARGET_FIELDS:
        print(
            f"{field}: extractor macro-F1 {result['extractor'][field]['macro_f1']:.4f}, "
            f"baseline {result['baseline'][field]['macro_f1']:.4f}, "
            f"target {metrics.F1_TARGET} {'met' if result['target_met'][field] else 'NOT met'}"
        )
    print(f"health_risk: extractor macro-F1 {result['extractor']['health_risk']['macro_f1']:.4f}")
    print(f"substring rate {result['substring_rate']['rate']:.4f}")
    return 0 if all(result["target_met"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
