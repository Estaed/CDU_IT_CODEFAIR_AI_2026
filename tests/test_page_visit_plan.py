"""The visit plan (PRD 3.3, wireframes §6): unsigned state points back to the workspace,
crew stops render in signed order, air/barge work stays manual and out of every crew
container, a suggestion applies only with a reason, and an accepted plan is marked
superseded once a later signature lands."""

import re
import socket
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from fair_turn.app.components import ranking_table
from fair_turn.core import audit, constants
from fair_turn.core import visit_plan as visit_plan_module
from fair_turn.data import artefacts

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "fair_turn" / "app" / "pages"
VISIT_PLAN = PAGES / "visit_plan.py"
TODAY = constants.WINDOW_START + timedelta(days=constants.WINDOW_DAYS)
TEXT_KINDS = ("title", "subheader", "markdown", "caption", "info", "error", "success")


def _refuse(*args, **kwargs):
    raise RuntimeError("network disabled")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(socket, "socket", _refuse)


@pytest.fixture(scope="module")
def art() -> artefacts.Artefacts:
    return artefacts.load_all()


def _same_region_road_pair(art: artefacts.Artefacts) -> tuple[str, str]:
    by_region: dict[str, list[str]] = {}
    for job in ranking_table.open_jobs(TODAY):
        if job.needs_human:
            continue
        row = art.communities[job.community_id]
        if row["road_access"] == "barge_or_air":
            continue
        by_region.setdefault(row["region"], []).append(job.job_id)
    for ids in by_region.values():
        if len(ids) >= 2:
            return ids[0], ids[1]
    raise AssertionError("fixture needs two open road jobs in the same region")


def _barge_job_id(art: artefacts.Artefacts) -> str:
    for job in ranking_table.open_jobs(TODAY):
        if (
            not job.needs_human
            and art.communities[job.community_id]["road_access"] == "barge_or_air"
        ):
            return job.job_id
    raise AssertionError("fixture needs one open barge/air job")


def _script(tmp_path: Path, audit_path: Path) -> Path:
    script = tmp_path / "visit_plan_with_temp_audit.py"
    body = [
        "from pathlib import Path",
        "from fair_turn.app import state",
        f'state.set_audit_path(Path(r"{audit_path}"))',
        f'exec(compile(open(r"{VISIT_PLAN}", encoding="utf-8").read(), r"{VISIT_PLAN}", "exec"))',
    ]
    script.write_text("\n".join(body) + "\n", encoding="utf-8", newline="")
    return script


def _run(runnable) -> AppTest:
    at = runnable.run(timeout=60)
    assert not at.exception
    return at


def _open(tmp_path: Path, audit_path: Path) -> AppTest:
    return _run(AppTest.from_file(str(_script(tmp_path, audit_path))))


def _sign(audit_path: Path, version: int, job_ids: list[str], signer: str) -> None:
    audit.append(
        audit_path,
        audit.SignOff(
            day=TODAY,
            lam=1.0,
            reason="daily sign-off",
            signer=signer,
            signed_at=datetime.now(),
            ranked_job_ids=tuple(job_ids),
            batch_version=version,
            today_job_ids=tuple(job_ids),
        ),
    )


def _page_text(at: AppTest) -> str:
    return "\n".join(e.value for kind in TEXT_KINDS for e in getattr(at.main, kind))


def test_unsigned_state_points_back_to_the_workspace(tmp_path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    at = _open(tmp_path, audit_path)
    assert "Sign today's list first" in [i.value for i in at.info]
    assert "visit_go_to_workspace" in {b.key for b in at.button}


def test_crew_stops_are_in_signed_order_and_barge_job_stays_manual(tmp_path, art) -> None:
    audit_path = tmp_path / "audit.jsonl"
    road_a, road_b = _same_region_road_pair(art)
    barge = _barge_job_id(art)
    _sign(audit_path, 1, [road_a, road_b, barge], "A. Coordinator")

    at = _open(tmp_path, audit_path)
    text = _page_text(at)
    assert f"Signed list {TODAY} v1 by A. Coordinator" in text
    assert "Signed work needing manual coordination" in text
    assert barge in text
    assert "air/barge access, no road route" in text

    markdowns = [m.value for m in at.main.markdown]
    index_a = next(i for i, v in enumerate(markdowns) if road_a in v and "signed rank 1" in v)
    index_b = next(i for i, v in enumerate(markdowns) if road_b in v and "signed rank 2" in v)
    assert index_a < index_b

    assert not any(re.search(rf"\d+\.\s+{re.escape(barge)}\b", v) for v in markdowns)


def test_suggestion_requires_a_reason_and_swaps_the_two_stops_once_accepted(
    tmp_path, art, monkeypatch
) -> None:
    audit_path = tmp_path / "audit.jsonl"
    road_a, road_b = _same_region_road_pair(art)
    _sign(audit_path, 1, [road_a, road_b], "A. Coordinator")

    probe = _open(tmp_path, audit_path)
    plan = probe.session_state["plan"]
    crew_plan = next(cp for cp in plan.crews if {road_a, road_b} <= {s.job_id for s in cp.stops})
    old_order = tuple(s.job_id for s in crew_plan.stops)
    new_order = tuple(reversed(old_order))
    suggestion = visit_plan_module.Suggestion(
        crew_base=crew_plan.crew.base,
        job_a=old_order[0],
        job_b=old_order[1],
        old_order=old_order,
        new_order=new_order,
        saving_km=99.0,
    )
    monkeypatch.setattr(visit_plan_module, "suggestions", lambda current, factor: [suggestion])

    at = _open(tmp_path, audit_path)
    at = _run(at.button(key="visit_suggestion_accept_0").click())
    assert any("A reason is required." in e.value for e in at.error)
    assert not [r for r in audit.read(audit_path) if isinstance(r, audit.PlanDecision)]

    at.text_input(key="visit_suggestion_reason_0").set_value("Avoid a repeat drive.")
    at = _run(at.button(key="visit_suggestion_accept_0").click())

    decisions = [r for r in audit.read(audit_path) if isinstance(r, audit.PlanDecision)]
    assert len(decisions) == 1
    assert decisions[0].action == "suggestion_accept"
    assert decisions[0].reason == "Avoid a repeat drive."

    new_plan = at.session_state["plan"]
    new_crew_plan = next(cp for cp in new_plan.crews if cp.crew.base == crew_plan.crew.base)
    assert tuple(s.job_id for s in new_crew_plan.stops) == new_order


def test_a_new_signature_supersedes_an_accepted_plan(tmp_path, art) -> None:
    audit_path = tmp_path / "audit.jsonl"
    road_a, road_b = _same_region_road_pair(art)
    _sign(audit_path, 1, [road_a, road_b], "A. Coordinator")

    at = _open(tmp_path, audit_path)
    at.text_input(key="visit_accept_reason").set_value("Approved for today's crews.")
    at = _run(at.button(key="visit_accept_plan").click())
    assert "Plan status: Accepted" in _page_text(at)

    _sign(audit_path, 2, [road_a, road_b], "B. Coordinator")
    at = _run(at)

    text = _page_text(at)
    assert "Plan status: Superseded" in text
    assert "Built on v1; sign-off v2 supersedes it — rebuild" in text


def test_no_hours_appear_anywhere_on_the_page(tmp_path, art) -> None:
    audit_path = tmp_path / "audit.jsonl"
    road_a, road_b = _same_region_road_pair(art)
    barge = _barge_job_id(art)
    _sign(audit_path, 1, [road_a, road_b, barge], "A. Coordinator")

    at = _open(tmp_path, audit_path)
    text = _page_text(at)
    assert " h " not in text
    assert "hours" not in text.lower()
