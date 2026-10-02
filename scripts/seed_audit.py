"""Write the committed sample decision log, ``data/audit/sample.jsonl``.

A short, believable morning on the planning day: a person sets a fact the AI could not
read, a test-set report is replayed with no model, the coordinator signs the Efficiency
first proposal, then changes the setting, adds a trip with a reason and signs again. The
wall clock is a demo morning (5 October 2026) and the planning day is in the data, so the
two clocks differ. Fixed times: the file is the same on every run. The Evidence page shows
it until a real plan is signed locally.

    venv/Scripts/python scripts/seed_audit.py
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fair_turn.core import audit, constants, weekly, weeks  # noqa: E402
from fair_turn.data import artefacts, geography  # noqa: E402

OUT = ROOT / "data" / "audit" / "sample.jsonl"
DARWIN = timezone(timedelta(hours=9, minutes=30))
SIGNER = "R. Coordinator"


def _signed(plan, jobs, version, reason, changes=(), added=()) -> audit.PlanSigned:
    summary = weekly.summarise(plan, jobs)
    return audit.PlanSigned(
        day=constants.PLAN_DAY,
        version=version,
        setting=plan.setting,
        setting_name=weekly.setting_name(plan.setting),
        signer=SIGNER,
        reason=reason,
        trips=weekly.trip_lines(plan),
        job_ids=tuple(sorted(plan.planned_job_ids())),
        changes=tuple(changes),
        repairs=summary.repairs,
        overdue_left=summary.overdue_left,
        added=tuple(added),
        recorded_at=datetime(2026, 10, 5, 9, 40, tzinfo=DARWIN)
        + timedelta(minutes=25 * (version - 1)),
    )


def main() -> None:
    art = artefacts.load_all()
    jobs = artefacts.to_jobs(art)
    places = geography.places(art.communities)
    history = weeks.simulate(
        jobs, places, 0.0, weeks.FIRST_MONDAY, weeks.HISTORY_WEEKS, art.closures
    )
    open_jobs = history.open_on(jobs, constants.PLAN_DAY)
    closed = weeks.closed_for_week(art.closures, constants.PLAN_DAY)
    person = next(j for j in open_jobs if j.needs_human)
    missing = "fault_type" if person.fault_type is None else "safety_class"
    value = "roof_structure" if missing == "fault_type" else "urgent"
    records: list[audit.Record] = [
        audit.FieldSet(
            constants.PLAN_DAY,
            person.job_id,
            missing,
            value,
            SIGNER,
            "Tenant confirmed by phone",
            recorded_at=datetime(2026, 10, 5, 9, 5, tzinfo=DARWIN),
        ),
        audit.Intake(
            constants.PLAN_DAY,
            "JR-2025-01453",
            "test-set replay",
            "copy of a test-set report, no model call",
            "test-set replay",
            0.0,
            "verified",
            "extracted",
            recorded_at=datetime(2026, 10, 5, 9, 20, tzinfo=DARWIN),
        ),
    ]
    first_plan = weekly.plan(open_jobs, places, constants.PLAN_DAY, 0.0, closed=closed)
    records.append(_signed(first_plan, open_jobs, 1, "Proposal as it stands, to get crews moving"))
    balanced = weekly.plan(open_jobs, places, constants.PLAN_DAY, 0.5, closed=closed)
    waiting = max(
        (
            w
            for w in balanced.waiting
            if w.reason == weekly.OUTRANKED and not places[w.community_id].is_town
        ),
        key=lambda w: len(w.job_ids),
    )
    reason = "Longest wait in the region; the community asked twice"
    second = weekly.plan(
        open_jobs, places, constants.PLAN_DAY, 0.5, closed=closed, add=[waiting.community_id]
    )
    records.append(
        _signed(
            second,
            open_jobs,
            2,
            "Remote households are weeks past the NT time limit; Balanced costs few repairs",
            changes=[f"added {waiting.community_id}: {reason}"],
            added=[waiting.community_id],
        )
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(b"")
    for record in records:
        audit.append(OUT, record)
    print(f"wrote {len(records)} records to {OUT.relative_to(ROOT)}", file=sys.stderr)


if __name__ == "__main__":
    main()
