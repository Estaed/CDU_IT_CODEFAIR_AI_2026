"""The app shell runs headless with the network disabled, every page renders, the loader is
the only reader of the build and audit folders, and no page touches session state."""

import json
import re
import socket
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from fair_turn.app import theme
from fair_turn.core.types import Job
from fair_turn.data import artefacts

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "fair_turn" / "app"
DATA = ROOT / "fair_turn" / "data"
PAGES = ["workspace", "review_queue", "visit_plan", "tenant", "evidence_lab"]
PAGE_FILES = sorted(p.stem for p in (APP / "pages").glob("*.py"))
# Matches "data/build" and ROOT / "data" / "build" alike.
ARTEFACT_PATH = re.compile(r"""data["'/\\ ]+(build|audit)""")
# Build-time writers, not app readers: they produce data/build/ from data/raw/.
BUILD_WRITERS = {"synth.py", "geography.py"}


def _refuse(*args, **kwargs):
    raise RuntimeError("network disabled")


@pytest.fixture
def no_network(monkeypatch):
    monkeypatch.setattr(socket, "socket", _refuse)


def test_socket_fixture_blocks_the_network(no_network) -> None:
    with pytest.raises(RuntimeError, match="network disabled"):
        socket.socket()


def test_main_runs_offline(no_network) -> None:
    at = AppTest.from_file(str(APP / "main.py")).run(timeout=60)
    assert not at.exception
    assert at.title[0].value == "Workspace"  # the default page ran
    assert theme.PROVENANCE_LINE in [c.value for c in at.sidebar.caption]


@pytest.mark.parametrize("page", PAGE_FILES)
def test_page_runs_offline(page, no_network) -> None:
    at = AppTest.from_file(str(APP / "pages" / f"{page}.py")).run(timeout=60)
    assert not at.exception
    assert theme.PROVENANCE_LINE in [c.value for c in at.caption]


def test_navigation_registers_exactly_the_five_pages() -> None:
    main = (APP / "main.py").read_text("utf-8")
    assert re.findall(r'st\.Page\("pages/(\w+)\.py"', main) == PAGES
    assert set(p.stem for p in (APP / "pages").glob("*.py")) >= set(PAGES)


def test_no_page_reads_session_state() -> None:
    pages = (APP / "pages").rglob("*.py")
    hits = [p.name for p in pages if "session_state" in p.read_text("utf-8")]
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
        assert {str(f) for f in job.health_risk} == {
            k.split(":", 1)[1] for k in row.kept if k.startswith("health_risk:")
        }
        assert job.is_remote is (community["is_remote"] == "True")
        assert job.logistics_factor == float(community["logistics_factor"])
    assert any(j.is_remote for j in jobs) and any(not j.is_remote for j in jobs)
    assert any(j.health_risk for j in jobs)
    job = jobs[0]
    assert artefacts.report_text(art, job.job_id) == art.reports[job.job_id]


def test_bad_extraction_row_raises(tmp_path) -> None:
    for name in ("communities.csv", "climate.csv", "labels.json", "reports.json", "closures.json"):
        (tmp_path / name).write_bytes((artefacts.BUILD_DIR / name).read_bytes())
    rows = json.loads((artefacts.BUILD_DIR / "extraction.json").read_text("utf-8"))
    rows[0]["confidence"] = 0.9
    (tmp_path / "extraction.json").write_text(json.dumps(rows), "utf-8")
    with pytest.raises(ValueError):
        artefacts.load_all(tmp_path, tmp_path)
