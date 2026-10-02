"""Export the tables and figures the report quotes, from committed build artefacts only.

Run from the repo root with the project interpreter:
    venv/Scripts/python scripts/export_report_tables.py
Writes eight files to data/build/report/ (or the directory passed to ``main``). No CLI, no
network: numbers come from data/build/eval.json, labels.json, communities.csv,
closures.json and extraction.json, or from the weekly planner (fair_turn.core.weekly and
weeks) run over the same jobs the app plans. Idempotent: rows are ordered deterministically
and floats are formatted to a fixed number of decimals, so a rerun is byte-identical.
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # the package is not installed into venv; scripts run from source

from fair_turn.core import constants, weekly, weeks  # noqa: E402
from fair_turn.core.types import Job  # noqa: E402
from fair_turn.data import artefacts, geography  # noqa: E402

BUILD = ROOT / "data" / "build"
OUT = BUILD / "report"
DIGITS = 4


def _load_json(path: Path):
    return json.loads(path.read_text("utf-8"))


def _communities(build: Path) -> dict[str, dict[str, str]]:
    with (build / "communities.csv").open(newline="", encoding="utf-8") as f:
        return {r["community_id"]: r for r in csv.DictReader(f)}


def _jobs(build: Path, communities: dict[str, dict[str, str]]) -> list[Job]:
    """The jobs the app ranks: verified extracted fields, not the gold labels, so every
    simulation figure in the report is the one the workspace computes. A job whose required
    field failed verification sits in the human queue and outside the medians, as in the
    app. (``communities`` is accepted for the old signature; the loader reads its own.)"""
    return artefacts.to_jobs(artefacts.load_all(build))


def _fmt(value: float | None) -> str:
    return "" if value is None else f"{value:.{DIGITS}f}"


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


SETTING_STEPS = 11  # 0.0, 0.1, ... 1.0
FIRST_MONDAY = weeks.FIRST_MONDAY
SEASON_WEEKS = weeks.SEASON_WEEKS
HISTORY_WEEKS = weeks.HISTORY_WEEKS
WEEK_COLUMNS = [
    "setting",
    "name",
    "repairs",
    "repairs_remote",
    "overdue_left",
    "overdue_left_remote",
    "driving_days",
    "remote_trips",
]
BAND_KEYS = {name: name.replace(" ", "_").replace("-", "_to_") for name, _ in weeks.BANDS}
SEASON_COLUMNS = [
    "setting",
    "name",
    "repairs",
    "driving_days",
    "on_time_town",
    "on_time_remote",
    *(f"{key}_{m}" for key in BAND_KEYS.values() for m in ("median_wait", "still_open")),
]
CREW_COLUMNS = ["extra_crew_at", "setting", "name", "repairs", "on_time_remote", "far_still_open"]


def _settings() -> list[float]:
    return [step / (SETTING_STEPS - 1) for step in range(SETTING_STEPS)]


def this_week(jobs: list[Job], places, closures) -> list[dict]:
    """The planning-day trade-off line the plan page draws: one plan per setting."""
    history = weeks.simulate(jobs, places, 0.0, FIRST_MONDAY, HISTORY_WEEKS, closures)
    open_jobs = history.open_on(jobs, constants.PLAN_DAY)
    closed = weeks.closed_for_week(closures, constants.PLAN_DAY)
    rows = []
    for setting in _settings():
        plan = weekly.plan(open_jobs, places, constants.PLAN_DAY, setting, closed=closed)
        s = weekly.summarise(plan, open_jobs)
        rows.append(
            {
                "setting": f"{setting:.1f}",
                "name": weekly.setting_name(setting),
                "repairs": s.repairs,
                "repairs_remote": s.repairs_remote,
                "overdue_left": s.overdue_left,
                "overdue_left_remote": s.overdue_left_remote,
                "driving_days": f"{s.driving_days:g}",
                "remote_trips": s.remote_trips,
            }
        )
    return rows


def season(jobs: list[Job], places, closures) -> list[dict]:
    """Every Monday of the window planned under each setting: who waits, by distance."""
    rows = []
    for setting in _settings():
        run = weeks.simulate(jobs, places, setting, FIRST_MONDAY, SEASON_WEEKS, closures)
        r = weeks.measure(run, jobs, places, setting)
        row = {
            "setting": f"{setting:.1f}",
            "name": weekly.setting_name(setting),
            "repairs": r.repairs,
            "driving_days": f"{r.driving_days:g}",
            "on_time_town": _fmt(r.on_time_town),
            "on_time_remote": _fmt(r.on_time_remote),
        }
        for band in r.bands:
            key = BAND_KEYS[band.band]
            row[f"{key}_median_wait"] = f"{band.median_wait:g}"
            row[f"{key}_still_open"] = band.still_open
        rows.append(row)
    return rows


def one_more_crew(jobs: list[Job], places, closures) -> list[dict]:
    """One extra crew at each base in turn, at Efficiency first and Balanced."""
    rows = []
    for base in constants.CREW_BASES:
        crews = dict(constants.CREWS_AT_BASE)
        crews[base] += 1
        for name in ("Efficiency first", "Balanced"):
            setting = constants.SETTINGS[name]
            run = weeks.simulate(jobs, places, setting, FIRST_MONDAY, SEASON_WEEKS, closures, crews)
            r = weeks.measure(run, jobs, places, setting)
            rows.append(
                {
                    "extra_crew_at": base,
                    "setting": f"{setting:.1f}",
                    "name": name,
                    "repairs": r.repairs,
                    "on_time_remote": _fmt(r.on_time_remote),
                    "far_still_open": r.bands[-1].still_open,
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
    # What the model itself did, before the marker rule: did the injected text change the
    # required fields it returned for the same report?
    by_id = {r["job_id"]: r for r in extraction}
    swayed = []
    for row in adversarial:
        original = by_id[row["original_job_id"]]["kept"]
        changed = [
            field
            for field in ("fault_type", "safety_class")
            if row["kept"].get(field, {}).get("value") != original.get(field, {}).get("value")
        ]
        if changed:
            swayed.append(f"{row['job_id']} ({', '.join(changed)})")
    lines = [
        "# Adversarial subset",
        "",
        f"{len(adversarial)} adversarial items in the evaluation set.",
        f"{with_markers} of {len(adversarial)} carry an injection marker in their evidence.",
        f"{to_human} of {len(adversarial)} routed to the needs-a-human queue.",
        "",
        "The ranked order is unchanged for all 20 adversarial items; asserted in "
        "`tests/test_extraction_artefact.py`.",
        "",
        "Before that rule, the extractor's own output for the injected copy differed from the "
        f"clean original on {len(swayed)} of {len(adversarial)} items"
        + (f": {'; '.join(swayed)}." if swayed else "."),
        "The marker list was written with the injection phrases in view, so the rule is shown "
        "to work on known phrasings only; a new phrasing relies on the extractor alone.",
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
        "## Crew model (*provisional*, constants.md)",
        "",
        "- Crews per base: " + ", ".join(f"{b} {n}" for b, n in constants.CREWS_AT_BASE.items()),
        f"- Crew-days per week: {constants.CREW_DAYS_PER_WEEK}",
        f"- Repairs per crew-day: {constants.JOBS_PER_CREW_DAY}",
        f"- Road km driven per day: {constants.DRIVE_KM_PER_DAY}",
        f"- Repairs per remote trip, at most: {constants.MAX_JOBS_PER_TRIP}",
        f"- Planning day: {constants.PLAN_DAY.isoformat()}",
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
    places = geography.places(communities)
    jobs = _jobs(BUILD, communities)
    closures = _load_json(BUILD / "closures.json")

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
    # Step 3: the three plan tables, by re-running the same core planner the app calls.
    tables = (
        ("this_week_by_setting.csv", WEEK_COLUMNS, this_week),
        ("season_by_setting.csv", SEASON_COLUMNS, season),
        ("one_more_crew.csv", CREW_COLUMNS, one_more_crew),
    )
    for name, columns, build in tables:
        _write_csv(output_dir / name, columns, build(jobs, places, closures))
    return 0


if __name__ == "__main__":
    sys.exit(main())
