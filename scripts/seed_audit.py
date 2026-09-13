"""Write data/audit/sample.jsonl: three signed days, one revision and two overrides, so the
audit log has history for the demo with no runtime interaction.

Run from the repo root with the project interpreter; deterministic and idempotent (fixed
datetimes, no ``now()``), so a rerun is byte-identical:
    venv/Scripts/python scripts/seed_audit.py
"""

import csv
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # the package is not installed into venv; scripts run from source

from fair_turn.core import audit, capacity_sim, constants, scoring  # noqa: E402
from fair_turn.core.capacity_sim import Closure, Site  # noqa: E402
from fair_turn.core.types import FaultType, HealthRiskFactor, Job, SafetyClass  # noqa: E402

BUILD = ROOT / "data" / "build"
AUDIT = ROOT / "data" / "audit"
SIGNER = "R. Coordinator"


def _load_json(path: Path):
    return json.loads(path.read_text("utf-8"))


def _communities() -> dict[str, dict[str, str]]:
    with (BUILD / "communities.csv").open(newline="", encoding="utf-8") as f:
        return {r["community_id"]: r for r in csv.DictReader(f)}


def _jobs(communities: dict[str, dict[str, str]]) -> list[Job]:
    jobs = []
    for label in _load_json(BUILD / "labels.json"):
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


def _closures() -> list[Closure]:
    return [
        Closure(
            c["community_id"],
            date.fromisoformat(c["closed_from"]),
            date.fromisoformat(c["closed_to"]),
        )
        for c in _load_json(BUILD / "closures.json")
    ]


def _crews() -> dict[str, int]:
    crews = {region: constants.CREWS_PER_REMOTE_REGION for region in constants.REMOTE_REGIONS}
    crews[constants.TOWN_REGION] = constants.CREWS_TOWN
    return crews


def _open_jobs(jobs: list[Job], sites: dict[str, Site], closures: list[Closure], today: date):
    result = capacity_sim.simulate(
        jobs,
        lam=1.0,
        start=constants.WINDOW_START,
        days=(today - constants.WINDOW_START).days + 1,
        closures=closures,
        crews_per_region=_crews(),
        jobs_per_crew_day=constants.JOBS_PER_CREW_DAY,
        travel_day_km=constants.TRAVEL_DAY_KM,
        sites=sites,
    )
    return [j for j in jobs if j.reported_on <= today and result.completed_on[j.job_id] is None]


def main() -> int:
    # Step 1: load the community/job/closure rows the capacity simulation needs.
    communities = _communities()
    sites = {cid: Site(r["region"], float(r["km_to_base"])) for cid, r in communities.items()}
    jobs = _jobs(communities)
    closures = _closures()

    # Step 2: pick three fixed sign-off days near the end of the event window, each with its
    # own lambda and reason, so the seeded log has a believable history for the demo.
    days = [constants.WINDOW_START + timedelta(days=constants.WINDOW_DAYS - n) for n in (3, 2, 1)]
    lams = (1.0, 0.7, 0.5)
    reasons = (
        "weekly sign-off, no changes since last week",
        "logistics weighted higher after a fuel-price rise",
        "logistics weighted lower to clear the remote backlog",
    )

    path = AUDIT / "sample.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()

    # Step 3: rank the open jobs for each day and append a signed-off entry per day.
    for day, lam, reason in zip(days, lams, reasons, strict=True):
        ranked = scoring.rank(_open_jobs(jobs, sites, closures, day), day, lam)
        ranked_ids = tuple(s.job.job_id for s in ranked[:10])
        audit.append(
            path,
            audit.SignOff(
                day=day,
                lam=lam,
                reason=reason,
                signer=SIGNER,
                signed_at=datetime.combine(day, datetime.min.time()),
                ranked_job_ids=ranked_ids,
            ),
        )

    # Step 4: on the middle day, append one lambda revision and two rank overrides, so the
    # log shows both kinds of after-the-fact change an auditor would look for.
    middle_day = days[1]
    audit.append(
        path,
        audit.Revision(
            day=middle_day,
            old_lam=lams[0],
            new_lam=lams[1],
            reason="logistics weighted higher after a fuel-price rise",
            at=datetime.combine(middle_day, datetime.min.time()) + timedelta(minutes=5),
        ),
    )

    ranked_middle = scoring.rank(_open_jobs(jobs, sites, closures, middle_day), middle_day, lams[1])
    overrides = (
        (ranked_middle[2], 1, "crew already on site"),
        (ranked_middle[4], 2, "tenant escalated to the coordinator directly"),
    )
    for i, (scored, to_rank, reason) in enumerate(overrides):
        audit.append(
            path,
            audit.Override(
                day=middle_day,
                job_id=scored.job.job_id,
                from_rank=scored.rank,
                to_rank=to_rank,
                reason=reason,
                at=datetime.combine(middle_day, datetime.min.time()) + timedelta(minutes=10 + i),
            ),
        )

    print(f"wrote {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
