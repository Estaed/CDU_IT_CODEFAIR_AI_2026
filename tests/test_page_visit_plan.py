"""The visit plan (PRD 3.3, wireframes §6, pooled crews 2026-09-14): unsigned state points
back to the workspace; after a signature the rule sentence and the three road-km metrics
render, crew rows use short job numbers with the registration in a caption, air/barge work
stays manual and out of every crew container, an order edit needs a reason and is audited
against the batch version, and an accepted plan is marked superseded by a later signature."""

import re
import socket
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from fair_turn.app.components import ranking_table
from fair_turn.core import audit, constants
from fair_turn.data import artefacts

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "fair_turn" / "app" / "pages"
VISIT_PLAN = PAGES / "visit_plan.py"
TODAY = constants.WINDOW_START + timedelta(days=constants.WINDOW_DAYS)
TEXT_KINDS = ("title", "subheader", "markdown", "caption", "info", "error", "success")
RULE = "Distance chooses which crew goes, never which job is served. The jobs are the signed list."
KM_METRICS = (
    "Road km, this signed list",
    "Road km, efficiency-first list",
    "Extra road km for today's weighting",
)


def _refuse(*args, **kwargs):
    raise RuntimeError("network disabled")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(socket, "socket", _refuse)


@pytest.fixture(scope="module")
def art() -> artefacts.Artefacts:
    return artefacts.load_all()


def _road_pair(art: artefacts.Artefacts) -> tuple[str, str]:
    ids = [
        job.job_id
        for job in ranking_table.open_jobs(TODAY)
        if not job.needs_human
        and art.communities[job.community_id]["road_access"] != "barge_or_air"
        and not any(
            c["community_id"] == job.community_id
            and c["closed_from"] <= TODAY.isoformat() <= c["closed_to"]
            for c in art.closures
        )
    ]
    assert len(ids) >= 2, "fixture needs two open road jobs"
    return ids[0], ids[1]


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
    assert [i.value for i in at.info] == [
        'Nothing to plan yet. On the workspace page, press "Review and sign" to sign '
        "today's list. The run sheet appears here as soon as it is signed.",
    ]
    assert "Columns of the run sheet" in [caption.value for caption in at.caption]
    assert list(at.dataframe[0].value.columns) == [
        "stop",
        "crew",
        "job",
        "community",
        "distance km",
    ]
    assert at.dataframe[0].value.empty
    assert RULE not in _page_text(at)
    assert not at.metric
    assert (
        'st.page_link("pages/workspace.py", label="Go to the workspace")'
        in VISIT_PLAN.read_text(encoding="utf-8")
    )


def test_rule_sentence_and_road_km_metrics_render_after_a_signature(tmp_path, art) -> None:
    audit_path = tmp_path / "audit.jsonl"
    road_a, road_b = _road_pair(art)
    barge = _barge_job_id(art)
    _sign(audit_path, 1, [road_a, road_b, barge], "A. Coordinator")

    at = _open(tmp_path, audit_path)
    text = _page_text(at)
    assert f"Signed list {TODAY} v1 by A. Coordinator" in text
    assert RULE in text
    metrics = {m.label: m.value for m in at.main.metric}
    assert set(metrics) == set(KM_METRICS)
    assert all(value.endswith(" km") for value in metrics.values())
    plan = at.session_state["plan"]
    assert metrics[KM_METRICS[0]] == f"{plan.road_km:,.0f} km"


def test_reach_caption_counts_jobs_no_crew_within_reach_can_take(tmp_path, art) -> None:
    audit_path = tmp_path / "audit.jsonl"
    road_a, road_b = _road_pair(art)
    _sign(audit_path, 1, [road_a, road_b], "A. Coordinator")

    at = _open(tmp_path, audit_path)
    lines = [
        c.value for c in at.main.caption if c.value.startswith("Signed jobs not planned today")
    ]
    assert len(lines) == 1
    match = re.fullmatch(
        r"Signed jobs not planned today: this signed list (\d+), efficiency-first list (\d+)\.",
        lines[0],
    )
    assert match
    assert int(match.group(1)) == at.session_state["plan"].out_of_reach


def test_crew_rows_use_short_numbers_and_barge_work_stays_manual(tmp_path, art) -> None:
    audit_path = tmp_path / "audit.jsonl"
    road_a, road_b = _road_pair(art)
    barge = _barge_job_id(art)
    _sign(audit_path, 1, [road_a, road_b, barge], "A. Coordinator")

    at = _open(tmp_path, audit_path)
    markdowns = [m.value for m in at.main.markdown]
    captions = [c.value for c in at.main.caption]
    for rank, job_id in ((1, road_a), (2, road_b)):
        short = ranking_table.short_id(job_id)
        assert any(
            re.search(rf"^\d+\.\s+{re.escape(short)}\b", v) and f"signed rank {rank}" in v
            for v in markdowns
        )
        assert any(job_id in c for c in captions)
        assert not any(job_id in v for v in markdowns)

    text = _page_text(at)
    assert "Signed, air or barge access: arrange freight" in text
    assert "air/barge access, no road route" in text
    assert "Next action: book air/barge freight — owner: coordinator" in text
    barge_short = ranking_table.short_id(barge)
    assert not any(re.search(rf"^\d+\.\s+{re.escape(barge_short)}\b", v) for v in markdowns)
    assert {s.job_id for cp in at.session_state["plan"].crews for s in cp.stops} == {
        road_a,
        road_b,
    }


def test_order_edit_needs_a_reason_and_is_audited_with_the_batch_version(tmp_path, art) -> None:
    audit_path = tmp_path / "audit.jsonl"
    road_a, road_b = _road_pair(art)
    _sign(audit_path, 1, [road_a, road_b], "A. Coordinator")

    at = _open(tmp_path, audit_path)
    at = _run(at.button(key="visit_edit_apply").click())
    assert any("A reason is required." in e.value for e in at.error)
    assert not [r for r in audit.read(audit_path) if isinstance(r, audit.PlanDecision)]

    at.text_input(key="visit_edit_reason").set_value("Tenant asked for the afternoon.")
    at = _run(at.button(key="visit_edit_apply").click())
    decisions = [r for r in audit.read(audit_path) if isinstance(r, audit.PlanDecision)]
    assert [(d.action, d.batch_version, d.reason) for d in decisions] == [
        ("edit", 1, "Tenant asked for the afternoon.")
    ]
    assert at.session_state["plan"].changes[-1].reason == "Tenant asked for the afternoon."


def test_a_new_signature_supersedes_an_accepted_plan(tmp_path, art) -> None:
    audit_path = tmp_path / "audit.jsonl"
    road_a, road_b = _road_pair(art)
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


def test_efficiency_first_side_compares_only_the_jobs_still_open(tmp_path, art) -> None:
    audit_path = tmp_path / "audit.jsonl"
    road_a, road_b = _road_pair(art)
    _sign(audit_path, 1, [road_a, road_b, "JR-2025-99999"], "A. Coordinator")

    at = _open(tmp_path, audit_path)
    text = _page_text(at)
    assert "1 signed jobs are no longer open, so both sides compare the 2 jobs still open." in text
    plan = at.session_state["plan"]
    signed_road_stops = sum(len(cp.stops) for cp in plan.crews)
    assert signed_road_stops == 2


def test_what_to_do_here_list_renders(tmp_path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    at = _open(tmp_path, audit_path)
    text = _page_text(at)
    assert "**What to do here**" in text
    assert "Check each crew's stops and kilometres." in text
    assert (
        "A job under *Signed, not planned today* needs a phone call: "
        "the reason next to it says why." in text
    )
    assert "Accept the plan, or reject it with a reason." in text


def test_no_hours_appear_anywhere_on_the_page(tmp_path, art) -> None:
    audit_path = tmp_path / "audit.jsonl"
    road_a, road_b = _road_pair(art)
    barge = _barge_job_id(art)
    _sign(audit_path, 1, [road_a, road_b, barge], "A. Coordinator")

    at = _open(tmp_path, audit_path)
    text = _page_text(at)
    assert " h " not in text
    assert "hours" not in text.lower()
