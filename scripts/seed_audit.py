"""Write data/audit/sample.jsonl: three signed days, one revision and two overrides, so the
audit log has history for the demo with no runtime interaction.

Run from the repo root with the project interpreter; deterministic and idempotent. Wall-clock
timestamps are seed-derived rather than real, so a rerun is byte-identical:
    venv/Scripts/python scripts/seed_audit.py
"""

import csv
import json
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # the package is not installed into venv; scripts run from source

from fair_turn.core import audit, capacity_sim, constants, scoring  # noqa: E402
from fair_turn.core.capacity_sim import Closure, Site  # noqa: E402
from fair_turn.core.types import FaultType, HealthRiskFactor, Job, SafetyClass  # noqa: E402

BUILD = ROOT / "data" / "build"
AUDIT = ROOT / "data" / "audit"
SIGNER = "R. Coordinator"
DARWIN = ZoneInfo("Australia/Darwin")


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


def _human_queue_job_id() -> str:
    """A committed non-adversarial extraction that still needs coordinator review."""
    for row in _load_json(BUILD / "extraction.json"):
        if row.get("needs_human") and not row.get("is_adversarial"):
            return row["job_id"]
    raise RuntimeError("the committed extraction artefact has no human-queue job")


def _recorded_at(day: date, rng: random.Random) -> datetime:
    """A reproducible local wall-clock timestamp after 09:00 Darwin time."""
    start = datetime(day.year, day.month, day.day, 9, tzinfo=DARWIN)
    return start + timedelta(minutes=rng.randint(1, 420))


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
    rng = random.Random(constants.SEED)

    path = AUDIT / "sample.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()

    # Step 3: rank the open jobs for each day and append a signed-off entry per day.
    for day, lam, reason in zip(days, lams, reasons, strict=True):
        ranked = scoring.rank(_open_jobs(jobs, sites, closures, day), day, lam)
        ranked_ids = tuple(s.job.job_id for s in ranked)
        today_ids = ranked_ids[:10]
        recorded_at = _recorded_at(day, rng)
        audit.append(
            path,
            audit.SignOff(
                day=day,
                lam=lam,
                reason=reason,
                signer=SIGNER,
                signed_at=recorded_at,
                ranked_job_ids=ranked_ids,
                recorded_at=recorded_at,
                today_job_ids=today_ids,
            ),
        )

    # Step 4: on the middle day, append one lambda revision and two rank overrides, so the
    # log shows both kinds of after-the-fact change an auditor would look for.
    middle_day = days[1]
    revision_at = _recorded_at(middle_day, rng)
    audit.append(
        path,
        audit.Revision(
            day=middle_day,
            old_lam=lams[0],
            new_lam=lams[1],
            reason="logistics weighted higher after a fuel-price rise",
            at=revision_at,
            recorded_at=revision_at,
        ),
    )

    ranked_middle = scoring.rank(_open_jobs(jobs, sites, closures, middle_day), middle_day, lams[1])
    overrides = (
        (ranked_middle[2], 1, "crew already on site"),
        (ranked_middle[4], 2, "tenant escalated to the coordinator directly"),
    )
    for scored, to_rank, reason in overrides:
        recorded_at = _recorded_at(middle_day, rng)
        audit.append(
            path,
            audit.Override(
                day=middle_day,
                job_id=scored.job.job_id,
                from_rank=scored.rank,
                to_rank=to_rank,
                reason=reason,
                at=recorded_at,
                recorded_at=recorded_at,
            ),
        )

    # Step 5: add one event of each Phase 2 kind. The first event names a job still in the
    # human queue, so the audit sample also shows the required human intervention trail.
    human_job_id = _human_queue_job_id()
    audit.append(
        path,
        audit.HumanSet(
            day=middle_day,
            job_id=human_job_id,
            field="fault_type",
            value="plumbing_water",
            actor=SIGNER,
            reason="confirmed from the tenant report",
            recorded_at=_recorded_at(middle_day, rng),
        ),
    )
    audit.append(
        path,
        audit.Intake(
            day=days[2],
            job_id=human_job_id,
            provider="claude",
            model="sonnet",
            prompt_version="v1",
            latency_s=2.4,
            validation="missing fault type evidence",
            status="needs_review",
            recorded_at=_recorded_at(days[2], rng),
        ),
    )
    audit.append(
        path,
        audit.Promotion(
            day=days[2],
            job_id=ranked_middle[0].job.job_id,
            displaced_job_id=ranked_middle[-1].job.job_id,
            reason="coordinator confirmed immediate access",
            recorded_at=_recorded_at(days[2], rng),
        ),
    )
    audit.append(
        path,
        audit.PlanDecision(
            day=days[2],
            batch_version=1,
            action="accept",
            detail="signed order retained for crew allocation",
            reason="coordinator accepted the proposed visit plan",
            recorded_at=_recorded_at(days[2], rng),
        ),
    )

    print(f"wrote {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
