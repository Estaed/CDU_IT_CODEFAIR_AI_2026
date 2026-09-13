"""Export the tables and figures the report quotes, from committed build artefacts only.

Run from the repo root with the project interpreter:
    venv/Scripts/python scripts/export_report_tables.py
Writes seven files to data/build/report/ (or the directory passed to ``main``). No CLI, no
network: numbers come from data/build/eval.json, labels.json, communities.csv,
closures.json and extraction.json, or from fair_turn.core.capacity_sim / feedback_sim run
over the label rows the same way tests/test_feedback_sim.py builds them. Idempotent: rows
are ordered deterministically and floats are formatted to a fixed number of decimals, so a
rerun is byte-identical.
"""

import csv
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # the package is not installed into venv; scripts run from source

from fair_turn.core import capacity_sim, constants, feedback_sim  # noqa: E402
from fair_turn.core.capacity_sim import Closure, Site  # noqa: E402
from fair_turn.core.types import FaultType, HealthRiskFactor, Job, SafetyClass  # noqa: E402

BUILD = ROOT / "data" / "build"
OUT = BUILD / "report"
DIGITS = 4
FEEDBACK_DECAY = 0.3


def _load_json(path: Path):
    return json.loads(path.read_text("utf-8"))


def _communities(build: Path) -> dict[str, dict[str, str]]:
    with (build / "communities.csv").open(newline="", encoding="utf-8") as f:
        return {r["community_id"]: r for r in csv.DictReader(f)}


def _sites(communities: dict[str, dict[str, str]]) -> dict[str, Site]:
    return {cid: Site(r["region"], float(r["km_to_base"])) for cid, r in communities.items()}


def _jobs(build: Path, communities: dict[str, dict[str, str]]) -> list[Job]:
    jobs = []
    for label in _load_json(build / "labels.json"):
        community = communities[label["community_id"]]
        jobs.append(
            Job(
                job_id=label["job_id"],
                community_id=label["community_id"],
                is_remote=community["is_remote"] == "True",
                reported_on=date.fromisoformat(label["reported_on"]),
                fault_type=FaultType(label["fault_type"]),
                safety_class=SafetyClass(label["safety_class"]),
                health_risk=frozenset(HealthRiskFactor(h) for h in label["health_risk"]),
                logistics_factor=float(community["logistics_factor"]),
            )
        )
    return jobs


def _closures(build: Path) -> list[Closure]:
    return [
        Closure(
            c["community_id"],
            date.fromisoformat(c["closed_from"]),
            date.fromisoformat(c["closed_to"]),
        )
        for c in _load_json(build / "closures.json")
    ]


def _crews() -> dict[str, int]:
    crews = {region: constants.CREWS_PER_REMOTE_REGION for region in constants.REMOTE_REGIONS}
    crews[constants.TOWN_REGION] = constants.CREWS_TOWN
    return crews


def _fmt(value: float | None) -> str:
    return "" if value is None else f"{value:.{DIGITS}f}"


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def price_of_fairness(
    jobs: list[Job], sites: dict[str, Site], closures: list[Closure]
) -> list[dict]:
    rows = []
    for step in range(11):
        lam = round(1.0 - step * 0.1, 1)
        result = capacity_sim.simulate(
            jobs,
            lam,
            constants.WINDOW_START,
            constants.WINDOW_DAYS,
            closures,
            _crews(),
            constants.JOBS_PER_CREW_DAY,
            constants.TRAVEL_DAY_KM,
            sites,
        )
        rows.append(
            {
                "lam": f"{lam:.1f}",
                "median_wait_remote": _fmt(result.median_wait_remote),
                "median_wait_town": _fmt(result.median_wait_town),
                "gap": _fmt(result.gap),
                "travel_cost": f"{result.travel_cost:.{DIGITS}f}",
            }
        )
    return rows


def feedback_loop(jobs: list[Job], sites: dict[str, Site], closures: list[Closure]) -> list[dict]:
    rows = []
    for run_name, lam in (("lam_1.0", 1.0), ("lam_0.5", 0.5)):
        series = feedback_sim.run(jobs, sites, lam, FEEDBACK_DECAY, constants.SEED, closures)
        for i, week_start in enumerate(series.week_start):
            rows.append(
                {
                    "run": run_name,
                    "week_start": week_start.isoformat(),
                    "reports_town": series.reports_town[i],
                    "reports_remote": series.reports_remote[i],
                    "median_wait_town": _fmt(series.median_wait_town[i]),
                    "median_wait_remote": _fmt(series.median_wait_remote[i]),
                    "gap": _fmt(series.gap[i]),
                }
            )
    return rows


def _cell(stats: dict, key: str) -> str:
    low, high = stats[f"{key}_ci"]
    return f"{stats[key]:.3f} [{low:.3f}, {high:.3f}]"


def extraction_vs_baseline_md(ev: dict) -> str:
    lines = ["# Extraction: extractor vs baseline", ""]
    for field in ("fault_type", "safety_class", "health_risk"):
        stats = ev["extractor"][field]
        models = [("extractor", stats)]
        if field in ev["baseline"]:
            models.append(("baseline", ev["baseline"][field]))
        header = ["class"] + [f"{m} {k}" for m, _ in models for k in ("P [95% CI]", "R [95% CI]")]
        header += [f"{m} F1" for m, _ in models]
        lines += [f"## {field}", "", "| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
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
    target = ", ".join(f"{f} {'met' if ok else 'not met'}" for f, ok in ev["target_met"].items())
    lines.append(f"Macro-F1 target {ev['f1_target']:.2f}: {target}.")
    return "\n".join(lines) + "\n"


def span_scores_md(ev: dict) -> str:
    span = ev["span_scores"]
    if span is None:
        note = next(n for n in ev["notes"] if n.startswith("span_scores is null"))
        return "# Span scores (SemEval-2013)\n\n" + note + "\n"
    lines = [
        "# Span scores (SemEval-2013)",
        "",
        "| regime | precision | recall | f1 |",
        "|---|---|---|---|",
    ]
    for regime in ("exact", "partial"):
        r = span[regime]
        cells = f"{_cell(r, 'precision')} | {_cell(r, 'recall')} | {r['f1']:.3f}"
        lines.append(f"| {regime} | {cells} |")
    return "\n".join(lines) + "\n"


def substring_rate_md(ev: dict) -> str:
    rate = ev["substring_rate"]
    body = f"{_cell(rate, 'rate')} of {rate['n']} extraction rows."
    return f"# Substring verification rate\n\n{body}\n"


def adversarial_md(extraction: list[dict]) -> str:
    adversarial = [r for r in extraction if r["is_adversarial"]]
    with_markers = sum(1 for r in adversarial if r["injection_markers"])
    to_human = sum(1 for r in adversarial if r["needs_human"])
    lines = [
        "# Adversarial subset",
        "",
        f"{len(adversarial)} adversarial items in the evaluation set.",
        f"{with_markers} of {len(adversarial)} carry an injection marker in their evidence.",
        f"{to_human} of {len(adversarial)} routed to the needs-a-human queue.",
        "",
        "The ranked order is unchanged for all 20 adversarial items; asserted in "
        "`tests/test_extraction_artefact.py`.",
    ]
    return "\n".join(lines) + "\n"


def dataset_summary_md(
    labels: list[dict], communities: dict[str, dict[str, str]], extraction: list[dict]
) -> str:
    region_counts: dict[str, int] = {}
    remote = 0
    for label in labels:
        region = communities[label["community_id"]]["region"]
        region_counts[region] = region_counts.get(region, 0) + 1
        if communities[label["community_id"]]["is_remote"] == "True":
            remote += 1
    holdout = sum(1 for lb in labels if lb["is_holdout"])
    adversarial = sum(1 for r in extraction if r["is_adversarial"])
    human_queue = sum(1 for r in extraction if not r["is_adversarial"] and r["needs_human"])

    lines = ["# Dataset summary", "", "## Counts by region", "", "| region | jobs |", "|---|---|"]
    for region in constants.REGIONS:
        lines.append(f"| {region} | {region_counts.get(region, 0)} |")
    lines += [
        "",
        f"Total labelled reports: {len(labels)} (*provisional* volume, PRD section 6.2).",
        f"Remote share: {remote / len(labels):.4f} (*provisional* target ~0.60, PRD section 6.2).",
        f"Holdout set: {holdout} reports.",
        f"Adversarial set: {adversarial} reports.",
        f"Needs-a-human queue: {human_queue} non-adversarial reports with an unverified "
        "required field.",
        "",
        "## Capacity model (*provisional*, PRD section 6.3)",
        "",
        f"- Crews per remote region: {constants.CREWS_PER_REMOTE_REGION}",
        f"- Crews in the town region: {constants.CREWS_TOWN}",
        f"- Jobs per crew per day: {constants.JOBS_PER_CREW_DAY}",
        f"- Travel-day threshold: {constants.TRAVEL_DAY_KM} km",
        "",
        "## Event window (*provisional*, PRD section 6.2)",
        "",
        f"- Start: {constants.WINDOW_START.isoformat()}",
        f"- Days: {constants.WINDOW_DAYS}",
    ]
    return "\n".join(lines) + "\n"


def main(output_dir: Path = OUT) -> int:
    # Step 1: load every committed build artefact this report needs; no CLI, no network.
    output_dir.mkdir(parents=True, exist_ok=True)
    ev = _load_json(BUILD / "eval.json")
    labels = _load_json(BUILD / "labels.json")
    communities = _communities(BUILD)
    extraction = _load_json(BUILD / "extraction.json")
    sites = _sites(communities)
    jobs = _jobs(BUILD, communities)
    closures = _closures(BUILD)

    # Step 2: write the five markdown tables (evaluation numbers, dataset summary).
    (output_dir / "extraction_vs_baseline.md").write_text(
        extraction_vs_baseline_md(ev), "utf-8", newline=""
    )
    (output_dir / "span_scores.md").write_text(span_scores_md(ev), "utf-8", newline="")
    (output_dir / "substring_rate.md").write_text(substring_rate_md(ev), "utf-8", newline="")
    (output_dir / "adversarial.md").write_text(adversarial_md(extraction), "utf-8", newline="")
    (output_dir / "dataset_summary.md").write_text(
        dataset_summary_md(labels, communities, extraction), "utf-8", newline=""
    )
    # Step 3: write the two simulation CSVs (capacity_sim across lambda, feedback_sim over
    # the event window) by re-running the same core simulations the app pages call.
    _write_csv(
        output_dir / "price_of_fairness.csv",
        ["lam", "median_wait_remote", "median_wait_town", "gap", "travel_cost"],
        price_of_fairness(jobs, sites, closures),
    )
    _write_csv(
        output_dir / "feedback_loop.csv",
        [
            "run",
            "week_start",
            "reports_town",
            "reports_remote",
            "median_wait_town",
            "median_wait_remote",
            "gap",
        ],
        feedback_loop(jobs, sites, closures),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
