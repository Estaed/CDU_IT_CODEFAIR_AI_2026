"""The tenant view: a real answer for a known rankable job, a plain message for an unknown
id, and a plain message with no rank for a job stuck in the human queue."""

import socket
from datetime import timedelta
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from fair_turn.app.components import ranking_table
from fair_turn.core import constants, scoring, wording
from fair_turn.data import artefacts

ROOT = Path(__file__).resolve().parent.parent
TENANT = ROOT / "fair_turn" / "app" / "pages" / "tenant.py"
TODAY = constants.WINDOW_START + timedelta(days=constants.WINDOW_DAYS)


def _refuse(*args, **kwargs):
    raise RuntimeError("network disabled")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(socket, "socket", _refuse)


@pytest.fixture(scope="module")
def art() -> artefacts.Artefacts:
    return artefacts.load_all()


def _rankable_ids(art: artefacts.Artefacts) -> list[str]:
    jobs = ranking_table.open_jobs(TODAY)
    ranked = scoring.rank(jobs, TODAY, 1.0)
    return sorted(s.job.job_id for s in ranked)


def _human_queue_open_id(art: artefacts.Artefacts) -> str:
    for job in ranking_table.open_jobs(TODAY):
        if job.needs_human:
            return job.job_id
    raise AssertionError("no committed open job needs a human")


def _page_text(at: AppTest) -> str:
    parts = [h.value for h in at.subheader] + [c.value for c in at.caption]
    parts += [m.value for m in at.markdown] + [w.value for w in at.text]
    parts += [i.value for i in at.info]
    return "\n".join(parts)


def test_known_rankable_id_shows_id_and_independent_lambda0_rank(art) -> None:
    job_id = _rankable_ids(art)[0]
    jobs = ranking_table.open_jobs(TODAY)
    expected_rank0 = next(s.rank for s in scoring.rank(jobs, TODAY, 0.0) if s.job.job_id == job_id)

    at = AppTest.from_file(str(TENANT)).run(timeout=60)
    at.text_input[0].set_value(job_id).run(timeout=60)

    assert not at.exception
    text = _page_text(at)
    assert job_id in text
    assert str(expected_rank0) in text


def test_page_text_passes_wording_check_for_five_sampled_jobs(art) -> None:
    sample = _rankable_ids(art)[:5]
    assert len(sample) == 5

    for job_id in sample:
        at = AppTest.from_file(str(TENANT)).run(timeout=60)
        at.text_input[0].set_value(job_id).run(timeout=60)
        assert not at.exception
        markdown_text = "\n".join(m.value for m in at.markdown)
        assert wording.check(markdown_text) == []


def test_unknown_id_shows_plain_message_and_no_exception() -> None:
    at = AppTest.from_file(str(TENANT)).run(timeout=60)
    at.text_input[0].set_value("NOT-A-REAL-JOB-ID").run(timeout=60)

    assert not at.exception
    assert at.info
    assert "could not find" in at.info[0].value


def test_human_queue_id_shows_person_checking_and_no_rank(art) -> None:
    job_id = _human_queue_open_id(art)

    at = AppTest.from_file(str(TENANT)).run(timeout=60)
    at.text_input[0].set_value(job_id).run(timeout=60)

    assert not at.exception
    text = _page_text(at)
    assert "person is checking" in text
    assert "NT policy window" not in text
    assert "coordinator's reason" not in text
