"""The workspace sign-off (PRD 3.1, wireframes §5 and §9): metrics and outcomes stay hidden
until a signature, a frozen review goes stale on any change, a valid submit writes one
versioned ``SignOff``, a duplicate or failed write writes nothing, and a change after signing
is a revision shown in the header. Also the pure metrics and map checks that lived in the
retired board tests."""

import re
import socket
import statistics
from datetime import timedelta
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from fair_turn.app import state
from fair_turn.app.components import map as nt_map_component
from fair_turn.app.components import metrics, ranking_table, sign_off_form
from fair_turn.core import audit, capacity_sim, constants
from fair_turn.data import artefacts

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "fair_turn" / "app" / "pages"
WORKSPACE = PAGES / "workspace.py"
REGION = constants.REMOTE_REGIONS[0]
REVEAL = ("median wait", "travel cost")
LOCKED_OUTCOMES = (
    "Wait times and travel cost appear after you sign. We hide them until then so the numbers "
    "do not steer your ordering."
)
TEXT_KINDS = ("title", "subheader", "markdown", "caption", "info", "warning", "success", "error")


def _refuse(*args, **kwargs):
    raise RuntimeError("network disabled")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(socket, "socket", _refuse)


@pytest.fixture(scope="module")
def art() -> artefacts.Artefacts:
    return artefacts.load_all()


def _script(tmp_path: Path) -> Path:
    """The audit log in ``tmp_path``; the runtime file is isolated by ``tests/conftest.py``."""
    script = tmp_path / "workspace_with_temp_audit.py"
    body = [
        "from pathlib import Path",
        "from fair_turn.app import state",
        f'state.set_audit_path(Path(r"{tmp_path / "audit.jsonl"}"))',
        f'exec(compile(open(r"{WORKSPACE}", encoding="utf-8").read(), r"{WORKSPACE}", "exec"))',
    ]
    script.write_text("\n".join(body) + "\n", encoding="utf-8", newline="")
    return script


def _run(runnable) -> AppTest:
    """Run an ``AppTest`` or a widget changed on one; either returns the ``AppTest``."""
    at = runnable.run(timeout=60)
    assert not at.exception
    return at


def _open(tmp_path: Path) -> AppTest:
    return _run(AppTest.from_file(str(_script(tmp_path))))


def _main_text(at: AppTest) -> str:
    """Every text element outside the sidebar, plus metric labels and values, lower-cased.
    The sidebar's weighting control names travel cost as a setting, not as an outcome, and so
    does the selected job's "Ranked ..." why-sentence (a job is selected on first render since
    Task-38); both are excluded, so the words in REVEAL can only come from the outcome panel."""
    values = [
        e.value
        for kind in TEXT_KINDS
        for e in getattr(at.main, kind)
        if not str(e.value).startswith("Ranked ")
    ]
    values += [f"{m.label} {m.value}" for m in at.main.metric]
    return "\n".join(values).lower()


def _header(at: AppTest) -> str:
    return next(m.value for m in at.markdown if m.value.startswith("Day "))


def _keys(at: AppTest) -> set[str]:
    return {b.key for b in at.button}


def _review(at: AppTest, key: str = "workspace_review_and_sign") -> AppTest:
    return _run(at.button(key=key).click())


def _set_lam(at: AppTest, value: float) -> AppTest:
    return _run(at.sidebar.slider[0].set_value(value))


def _sign(at: AppTest, signer: str, reason: str, decision: str | None = None) -> AppTest:
    at.text_input(key="sign_off_signer").set_value(signer)
    at.text_area(key="sign_off_reason").set_value(reason)
    if decision is not None:
        at.selectbox(key="sign_off_decision").set_value(decision)
    return _run(at.button(key="sign_off_submit").click())


def _sign_offs(path: Path) -> list[audit.SignOff]:
    return [r for r in audit.read(path) if isinstance(r, audit.SignOff)]


# --- decide before reveal, stale review, signature, duplicate, revision ----------------------


def test_sign_off_flow_from_draft_to_changed_since_signature(tmp_path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    at = _open(tmp_path)
    assert _header(at).endswith("Status: Draft")
    text = _main_text(at)
    assert LOCKED_OUTCOMES.lower() in text
    assert len(at.metric) == 4
    assert not [
        word
        for word in REVEAL
        if any(word in f"{metric.label} {metric.value}".lower() for metric in at.metric)
    ]
    assert any("Outcomes appear after you sign" in m.value for m in at.markdown)
    assert "sign_off_submit" not in _keys(at)

    _review(at)
    assert _header(at).endswith("Status: Review open (batch v1)")
    assert "sign_off_submit" in _keys(at)
    assert "Open today's list" in [e.label for e in at.expander]

    _set_lam(at, 0.5)
    assert metrics_hidden(at)
    assert "The list changed since you opened this review; open it again." in [
        w.value for w in at.warning
    ]
    assert "sign_off_submit" not in _keys(at)
    assert not audit_path.exists()

    _review(at, "workspace_open_again")
    assert "sign_off_submit" in _keys(at)
    assert metrics_hidden(at)
    _sign(at, "A. Coordinator", "remote backlog is ageing")
    (record,) = _sign_offs(audit_path)
    assert len(audit.read(audit_path)) == 1
    assert record.batch_version == 1
    assert re.fullmatch(r"\d{8}-v1", record.audit_ref)
    assert (record.decision, record.signer, record.lam) == ("approve", "A. Coordinator", 0.5)
    cap = ranking_table.capacity(state.ALL_REGIONS)
    assert len(record.today_job_ids) == cap
    assert record.today_job_ids == record.ranked_job_ids[:cap]
    assert any(record.audit_ref in s.value for s in at.success)
    assert "median wait" in _main_text(at)
    assert len(at.metric) == 8
    assert [metric.label for metric in at.main.metric[4:]] == list(metrics.LABELS.values())
    assert any(
        info.value.startswith("Effect: ") and "Simulated over the 90-day set" in info.value
        for info in at.main.info
    )
    assert (
        "Baseline: efficiency-first (travel-cost weight 1.00). Simulated over the 90-day set. "
        "Days and AUD."
    ) in [c.value for c in at.caption]
    assert re.search(r"Status: Signed v1 \d{2}:\d{2} by A\. Coordinator$", _header(at))

    _run(at.button(key="sign_off_submit").click())
    assert any("already signed" in e.value for e in at.error)
    assert len(audit.read(audit_path)) == 1

    _set_lam(at, 0.0)
    records = audit.read(audit_path)
    assert [type(r) for r in records] == [audit.SignOff, audit.Revision]
    assert (records[1].old_lam, records[1].new_lam) == (0.5, 0.0)
    assert _header(at).endswith("Status: Changed since signature (signed v1 stays authoritative)")
    assert "median wait" in _main_text(at)  # the metrics stay live after a signature

    _review(at, "workspace_open_again")
    assert _header(at).endswith("Status: Review open (batch v2)")


def metrics_hidden(at: AppTest) -> bool:
    text = _main_text(at)
    return (
        len(at.metric) == 4
        and LOCKED_OUTCOMES.lower() in text
        and any("Outcomes appear after you sign" in m.value for m in at.markdown)
    )


def test_empty_fields_are_flagged_inline_and_defer_is_recorded(tmp_path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    at = _review(_open(tmp_path))
    _sign(at, "  ", "")
    shown = [m.value for m in at.markdown]
    assert f":red[{sign_off_form.SIGNER_REQUIRED}]" in shown
    assert f":red[{sign_off_form.REASON_REQUIRED}]" in shown
    assert not audit_path.exists()
    assert metrics_hidden(at)

    _sign(at, "A. Coordinator", "", "Defer")
    assert f":red[{sign_off_form.REASON_REQUIRED}]" in [m.value for m in at.markdown]
    assert f":red[{sign_off_form.SIGNER_REQUIRED}]" not in [m.value for m in at.markdown]
    assert not audit_path.exists()

    _sign(at, "A. Coordinator", "crews held for a storm", "Defer")
    (record,) = _sign_offs(audit_path)
    assert record.decision == "defer"


def test_failed_audit_write_writes_nothing_and_keeps_the_review_open(tmp_path, monkeypatch) -> None:
    audit_path = tmp_path / "audit.jsonl"
    at = _review(_open(tmp_path))

    def fail(path, record):
        raise OSError("disk full")

    monkeypatch.setattr(audit, "append", fail)
    _sign(at, "A. Coordinator", "remote backlog is ageing")
    assert "Could not write the audit log: disk full" in [e.value for e in at.error]
    assert not audit_path.exists()
    assert _header(at).endswith("Status: Review open (batch v1)")
    assert "sign_off_submit" in _keys(at)
    assert metrics_hidden(at)


def test_phase_one_pages_are_retired() -> None:
    names = {p.stem for p in PAGES.glob("*.py")}
    assert not names & {"board", "job_card", "sign_off"}
    assert {"workspace", "review_queue", "visit_plan", "tenant", "evidence_lab"} <= names


# --- pure metrics and map checks, moved from tests/test_board_map_metrics.py -----------------


def _map_keys(node) -> set[str]:
    if isinstance(node, dict):
        return set(node).union(*(_map_keys(v) for v in node.values()))
    if isinstance(node, list):
        return set().union(*(_map_keys(v) for v in node))
    return set()


def _marks(spec: dict) -> list[str]:
    layers = spec.get("layer", [spec])
    return [m if isinstance(m, str) else m["type"] for m in (layer["mark"] for layer in layers)]


def _simulate(art: artefacts.Artefacts, today, lam: float, jobs=None):
    inputs = metrics.sim_inputs(art)
    if jobs is not None:
        inputs["jobs"] = jobs
    return capacity_sim.simulate(
        lam=lam,
        start=constants.WINDOW_START,
        days=(today - constants.WINDOW_START).days + 1,
        **inputs,
    )


def test_map_spec_is_inline_with_outline_and_dots(art) -> None:
    counts = {cid: 2 for cid in list(art.communities)[:3]}
    spec = nt_map_component.nt_map(art.communities, counts, state.ALL_REGIONS).to_dict()
    assert "url" not in _map_keys(spec)
    assert _marks(spec) == ["geoshape", "circle"]
    points = spec["layer"][1]["data"]["values"]
    assert {p["community_id"] for p in points} == set(art.communities)
    assert {p["community_id"]: p["open"] for p in points if p["open"]} == counts
    outline = spec["layer"][0]["data"]["values"]
    assert [f["properties"]["iso_3166_2"] for f in outline] == ["AU-NT"]


def test_map_for_one_region_drops_outline_and_other_regions(art) -> None:
    spec = nt_map_component.nt_map(art.communities, {}, REGION).to_dict()
    assert "url" not in _map_keys(spec)
    assert _marks(spec) == ["circle"]
    ids = {p["community_id"] for p in spec["data"]["values"]}
    assert ids == {cid for cid, row in art.communities.items() if row["region"] == REGION}
    assert 0 < len(ids) < len(art.communities)


def test_region_panel_is_the_full_pooled_run_restricted_to_that_region(art) -> None:
    """Crews are one NT-wide pool (2026-09-14), so a region is not a separate simulation: its
    panel medians are the full run's waits over that region's jobs, open jobs censored at the
    day after the run, and travel cost stays whole NT."""
    today = constants.WINDOW_START + timedelta(days=45)
    jobs = artefacts.to_jobs(art)
    full = _simulate(art, today, 0.0)
    end = today + timedelta(days=1)
    for region in (REGION, constants.TOWN_REGION):
        own = [
            j
            for j in jobs
            if art.communities[j.community_id]["region"] == region
            and not j.needs_human
            and j.reported_on < end
        ]
        waits = {
            remote: sorted(
                full.wait_days[j.job_id]
                if full.wait_days[j.job_id] is not None
                else (end - j.reported_on).days
                for j in own
                if j.is_remote == remote
            )
            for remote in (True, False)
        }
        values = metrics.panel_values(full, jobs, art.communities, region)
        for remote, key in ((True, "median_wait_remote"), (False, "median_wait_town")):
            expected = float(statistics.median(waits[remote])) if waits[remote] else None
            assert values[key] == expected
        assert values["travel_cost"] == full.travel_cost
    town = metrics.panel_values(full, jobs, art.communities, constants.TOWN_REGION)
    assert town["median_wait_town"] is not None
    assert town["median_wait_remote"] is None and town["gap"] is None


def test_formatting_and_deltas() -> None:
    values = {
        "median_wait_remote": 12.5,
        "median_wait_town": None,
        "gap": 3.0,
        "travel_cost": 1234.4,
    }
    base = {"median_wait_remote": 10.0, "median_wait_town": 4.0, "gap": 3.5, "travel_cost": 1000.0}
    assert metrics.formatted(values) == {
        "median_wait_remote": "12.5 days",
        "median_wait_town": metrics.NOT_AVAILABLE,
        "gap": "3.0 days",
        "travel_cost": "1,234",
    }
    assert metrics.deltas(values, base) == {
        "median_wait_remote": "+2.5 days",
        "median_wait_town": None,
        "gap": "-0.5 days",
        "travel_cost": "+234",
    }
