"""The app runs headless with the network disabled, every page renders, the coordinator's
three steps work end to end, and the loader is the only reader of the build folders."""

import json
import re
import socket
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from fair_turn.app import theme
from fair_turn.core import audit, wording
from fair_turn.core.types import Job
from fair_turn.data import artefacts, runtime

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "fair_turn" / "app"
DATA = ROOT / "fair_turn" / "data"
PAGES = ["plan", "reports", "tenant", "evidence"]
# Matches "data/build" and ROOT / "data" / "build" alike.
ARTEFACT_PATH = re.compile(r"""data["'/\\ ]+(build|audit)""")
# Build-time writers, not app readers: they produce data/build/ from data/raw/.
BUILD_WRITERS = {"synth.py", "geography.py"}
TEXT_KINDS = ("title", "subheader", "markdown", "caption", "info", "warning", "success", "error")


def _refuse(*args, **kwargs):
    raise RuntimeError("network disabled")


@pytest.fixture
def no_network(monkeypatch):
    monkeypatch.setattr(socket, "socket", _refuse)
    monkeypatch.delenv("FAIR_TURN_PROVIDER", raising=False)


@pytest.fixture
def app(no_network, tmp_path):
    """The app on its default page, with its own empty audit log and runtime store."""
    at = AppTest.from_file(str(APP / "main.py"), default_timeout=120)
    at.session_state["audit_path"] = tmp_path / "audit.jsonl"
    at.session_state["runtime_path"] = tmp_path / "runtime.jsonl"
    at.run()
    assert not at.exception
    return at


def _text(at) -> list[str]:
    return [e.value for kind in TEXT_KINDS for e in getattr(at.main, kind)]


def _metric(at, label: str) -> int:
    return int(next(m for m in at.metric if m.label == label).value)


def test_socket_fixture_blocks_the_network(no_network) -> None:
    with pytest.raises(RuntimeError, match="network disabled"):
        socket.socket()


def test_navigation_registers_exactly_the_four_pages() -> None:
    main = (APP / "main.py").read_text("utf-8")
    assert re.findall(r'st\.Page\(\s*"pages/(\w+)\.py"', main) == PAGES
    assert sorted(p.stem for p in (APP / "pages").glob("*.py")) == sorted(PAGES)


@pytest.mark.parametrize("page", PAGES)
def test_every_page_runs_offline_with_no_provider(app, page) -> None:
    if page != "plan":
        app.switch_page(f"pages/{page}.py").run()
    assert not app.exception
    captions = [c.value for c in app.caption]
    assert any(theme.PROVENANCE_LINE in c for c in captions)  # stated on the page itself


def test_default_page_is_the_plan_and_names_the_backlog(app) -> None:
    assert app.title[0].value == "This week's crew plan"
    backlog = next(i.value for i in app.info if "repairs are waiting for a crew" in i.value)
    assert "past the NT time limit" in backlog and "remote communities" in backlog
    assert len(app.get("vega_lite_chart")) >= 2  # the trade-off line and the map


def test_choosing_a_setting_moves_repairs_and_overdue(app) -> None:
    repairs = _metric(app, "Repairs this week")
    overdue = _metric(app, "Overdue repairs still waiting")
    app.get("button_group")[0].set_value("Most overdue first").run()
    assert not app.exception
    assert _metric(app, "Repairs this week") < repairs
    assert _metric(app, "Overdue repairs still waiting") < overdue
    assert any(t.startswith("**Compared with Efficiency first:") for t in _text(app))


def test_signing_needs_a_name_and_a_reason(app, tmp_path) -> None:
    app.button(key="FormSubmitter:sign-Sign this week's plan").click().run()
    assert any("Give your name and a reason" in e.value for e in app.error)
    assert not (tmp_path / "audit.jsonl").exists()


def test_a_change_and_a_signature_reach_the_log(app, tmp_path) -> None:
    add = next(s for s in app.selectbox if s.label == "Add a trip to")
    community = add.options[0]
    add.select(community)
    next(t for t in app.text_input if t.key == "add_reason").input("Funeral next week")
    next(b for b in app.button if b.label == "Add trip").click().run()
    assert not app.exception
    next(t for t in app.text_input if t.label == "Your name").input("A. Coordinator")
    next(t for t in app.text_area if t.label == "Why this plan").input("Remote waits are long")
    next(b for b in app.button if b.label == "Sign this week's plan").click().run()
    assert not app.exception
    assert any("Signed by **A. Coordinator**" in s.value for s in app.success)
    (signed,) = audit.read(tmp_path / "audit.jsonl")
    assert isinstance(signed, audit.PlanSigned)
    assert signed.version == 1 and signed.signer == "A. Coordinator"
    assert signed.added and signed.changes[0].endswith("Funeral next week")
    assert signed.recorded_at.tzinfo is not None and signed.day.isoformat() == "2025-12-29"


def test_tenant_page_answers_the_default_example(app) -> None:
    app.switch_page("pages/tenant.py").run()
    assert not app.exception
    headline = app.subheader[0].value
    assert headline in {"Not this week."} or headline.startswith("Yes.")
    answer = " ".join(m.value for m in app.markdown)
    assert "Who decided?" in answer
    assert not wording.check(" ".join(_text(app)).replace("*", ""))


def test_tenant_page_refuses_an_unknown_number(app) -> None:
    app.switch_page("pages/tenant.py").run()
    app.text_input[0].set_value("JR-2025-99999").run()
    assert any("No repair has the number" in e.value for e in app.error)


def _queue_count(at) -> int:
    waiting = next(t for t in at.tabs if t.label.startswith("Needs a person"))
    return int(waiting.label.split("(")[1].rstrip(")"))


def _fill_missing_facts(at, reason: str | None) -> None:
    """Set every missing fact (urgent for the safety class, so the job joins the plan), the
    reason if given, and the person's name, then press save."""
    for box in at.selectbox:
        if box.key and box.key.startswith("value_"):
            if box.key.endswith("safety_class"):
                box.select("urgent")
            else:
                box.select_index(0)
    why = next(r for r in at.radio if r.key and r.key.startswith("why_"))
    assert why.value is None  # no reason is chosen for the person
    if reason is not None:
        why.set_value(reason)
    next(t for t in at.text_input if t.key and t.key.startswith("who_")).input("A. Officer")
    next(b for b in at.button if b.label == "Save and add to the plan").click().run()


def _sign(at, signer: str = "A. Coordinator") -> None:
    next(t for t in at.text_input if t.label == "Your name").input(signer)
    next(t for t in at.text_area if t.label == "Why this plan").input("Remote waits are long")
    next(b for b in at.button if b.label == "Sign this week's plan").click().run()
    assert not at.exception


def _sign_button(at):
    return next(b for b in at.button if b.label == "Sign this week's plan")


def _changed_after_signing(at) -> bool:
    return any("The plan changed after version 1 was signed" in w.value for w in at.warning)


def test_a_person_sets_the_missing_fact_and_the_job_leaves_the_queue(app, tmp_path) -> None:
    app.switch_page("pages/reports.py").run()
    assert not app.exception
    count = _queue_count(app)
    assert count >= 1
    _fill_missing_facts(app, "Tenant confirmed by phone")
    assert not app.exception
    assert _queue_count(app) == count - 1
    assert any(
        isinstance(r, runtime.HumanSetField) for r in runtime.read(tmp_path / "runtime.jsonl")
    )
    (field_set,) = audit.read(tmp_path / "audit.jsonl")
    assert isinstance(field_set, audit.FieldSet)
    assert field_set.reason == "Tenant confirmed by phone"


def test_saving_a_missing_fact_without_a_reason_shows_the_error(app, tmp_path) -> None:
    app.switch_page("pages/reports.py").run()
    count = _queue_count(app)
    _fill_missing_facts(app, None)
    assert not app.exception
    assert any("say why you are sure" in e.value for e in app.error)
    assert _queue_count(app) == count
    assert not (tmp_path / "runtime.jsonl").exists()
    assert not (tmp_path / "audit.jsonl").exists()


def test_a_fact_set_after_signing_shows_the_plan_changed(app) -> None:
    _sign(app)
    assert _sign_button(app).disabled and not _changed_after_signing(app)
    app.switch_page("pages/reports.py").run()
    _fill_missing_facts(app, "Tenant confirmed by phone")
    assert not app.exception
    app.switch_page("pages/plan.py").run()
    assert _changed_after_signing(app)
    assert not _sign_button(app).disabled


def test_a_replayed_report_that_changes_the_plan_shows_the_plan_changed(app) -> None:
    _sign(app)
    for _ in range(8):  # the seeded order reaches a report that changes the trips by the 5th
        app.switch_page("pages/reports.py").run()
        next(b for b in app.button if b.label == "Add a test-set report (no model)").click().run()
        assert not app.exception
        app.switch_page("pages/plan.py").run()
        if _changed_after_signing(app):
            break
        assert _sign_button(app).disabled  # a report that changes nothing keeps the signature
    assert _changed_after_signing(app)
    assert not _sign_button(app).disabled


def test_tenant_is_told_the_signed_plan_not_the_sessions_setting(app) -> None:
    app.get("button_group")[0].set_value("Balanced").run()
    _sign(app)
    app.get("button_group")[0].set_value("Efficiency first").run()
    assert _changed_after_signing(app)  # the session now proposes another plan
    app.switch_page("pages/tenant.py").run()
    # A remote repair below the cut under Balanced: its answer names the setting in force.
    app.text_input[0].set_value("JR-2025-00008").run()
    assert not app.exception
    answer = " ".join(m.value for m in app.markdown)
    assert 'This week the setting is "Balanced"' in answer
    assert 'This week the setting is "Efficiency first"' not in answer
    assert "A person signed this week's plan: A. Coordinator." in answer


def test_new_report_is_offered_without_a_model_and_saves_a_replay(app, tmp_path) -> None:
    app.switch_page("pages/reports.py").run()
    assert any("No model is set on this machine" in i.value for i in app.info)
    next(b for b in app.button if b.label == "Add a test-set report (no model)").click().run()
    assert not app.exception
    assert any(s.value.startswith("Saved as JR-2025-") for s in app.success)
    (intake,) = audit.read(tmp_path / "audit.jsonl")
    assert isinstance(intake, audit.Intake) and intake.provider == "test-set replay"


def test_evidence_shows_the_season_and_the_reading_quality(app) -> None:
    app.switch_page("pages/evidence.py").run()
    assert not app.exception
    assert len(app.get("vega_lite_chart")) >= 2
    labels = [m.label for m in app.metric]
    assert "Manipulation attempts that changed nothing" in labels


def test_no_page_reads_session_state() -> None:
    hits = [p.name for p in (APP / "pages").rglob("*.py") if "session_state" in p.read_text()]
    assert not hits, hits


def test_artefact_paths_only_in_the_loader() -> None:
    app_hits = [str(f.relative_to(APP)) for f in APP.rglob("*.py") if _names_artefacts(f)]
    assert not app_hits, app_hits
    data_hits = {f.name for f in DATA.rglob("*.py") if _names_artefacts(f)} - BUILD_WRITERS
    assert data_hits == {"artefacts.py"}  # also proves the pattern still matches the loader


def _names_artefacts(path: Path) -> bool:
    return bool(ARTEFACT_PATH.search(path.read_text("utf-8")))


# --- the loader against the committed artefacts ----------------------------------------------


@pytest.fixture(scope="module")
def art() -> artefacts.Artefacts:
    return artefacts.load_all()


def test_load_all_counts(art) -> None:
    assert len(art.labels) == 1452
    assert len(art.reports) == 1452
    assert len(art.extraction) == 1472
    assert sum(r.is_adversarial for r in art.extraction.values()) == 20
    assert set(art.communities) >= {label["community_id"] for label in art.labels}
    assert art.closures and art.climate
    assert art.audit_path == artefacts.AUDIT_DIR / "audit.jsonl"


def test_to_jobs_joins_label_extraction_and_community(art) -> None:
    jobs = artefacts.to_jobs(art)
    assert len(jobs) == 1452 and all(isinstance(j, Job) for j in jobs)
    assert {j.job_id for j in jobs} == set(art.reports)  # adversarial rows are not jobs
    human = sum(r.needs_human for r in art.extraction.values() if not r.is_adversarial)
    assert sum(j.needs_human for j in jobs) == human
    for job in jobs:
        row = artefacts.extraction_for(art, job.job_id)
        community = art.communities[job.community_id]
        assert job.needs_human is row.needs_human
        if not row.needs_human:
            assert job.fault_type == row.kept["fault_type"].value
            assert job.safety_class == row.kept["safety_class"].value
        assert job.is_remote is (community["is_remote"] == "True")


def test_bad_extraction_row_raises(tmp_path) -> None:
    for name in ("communities.csv", "climate.csv", "labels.json", "reports.json", "closures.json"):
        (tmp_path / name).write_bytes((artefacts.BUILD_DIR / name).read_bytes())
    rows = json.loads((artefacts.BUILD_DIR / "extraction.json").read_text("utf-8"))
    rows[0]["confidence"] = 0.9
    (tmp_path / "extraction.json").write_text(json.dumps(rows), "utf-8")
    with pytest.raises(ValueError):
        artefacts.load_all(tmp_path, tmp_path)
