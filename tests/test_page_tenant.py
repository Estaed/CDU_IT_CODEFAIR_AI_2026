"""The tenant view (PRD 3.4, wireframes §7): four bordered question blocks for a known job,
the registration-number format on an empty page and for an unknown id, the review copy with
no rank for a job in the human queue, and the signed and superseded copy read from the audit
log. Audit and runtime files point at a temporary folder so no local run leaks in."""

import re
import socket
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from fair_turn.app.components import ranking_table
from fair_turn.core import audit, constants, explain, scoring, wording
from fair_turn.data import artefacts

ROOT = Path(__file__).resolve().parent.parent
TENANT = ROOT / "fair_turn" / "app" / "pages" / "tenant.py"
TODAY = constants.WINDOW_START + timedelta(days=constants.WINDOW_DAYS)
REASON = "Crews are busy this week. We keep remote jobs moving."


def _refuse(*args, **kwargs):
    raise RuntimeError("network disabled")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(socket, "socket", _refuse)


@pytest.fixture(scope="module")
def art() -> artefacts.Artefacts:
    return artefacts.load_all()


def _road_rankable_ids(art: artefacts.Artefacts) -> list[str]:
    jobs = ranking_table.open_jobs(TODAY)
    ranked = scoring.rank(jobs, TODAY, 1.0)
    return sorted(
        s.job.job_id
        for s in ranked
        if art.communities[s.job.community_id]["road_access"] != "barge_or_air"
    )


def _human_queue_open_id() -> str:
    for job in ranking_table.open_jobs(TODAY):
        if job.needs_human:
            return job.job_id
    raise AssertionError("no committed open job needs a human")


def _open(tmp_path: Path, job_id: str | None) -> AppTest:
    at = AppTest.from_file(str(TENANT))
    at.session_state["audit_path"] = tmp_path / "audit.jsonl"
    at.session_state["runtime_path"] = tmp_path / "runtime.jsonl"
    at.run(timeout=60)
    if job_id is not None:
        at.text_input[0].set_value(job_id).run(timeout=60)
    assert not at.exception
    return at


def _bordered_blocks(node) -> list:
    found = []
    for child in getattr(node, "children", {}).values():
        proto = getattr(child, "proto", None)
        container = getattr(proto, "flex_container", None) if proto is not None else None
        if container is not None and container.border:
            found.append(child)
        found += _bordered_blocks(child)
    return found


def _answer_text(at: AppTest) -> str:
    parts = [h.value for h in at.subheader] + [m.value for m in at.markdown]
    parts += [i.value for i in at.info]
    return "\n".join(parts)


def _sign(tmp_path: Path, today_ids: tuple[str, ...], ranked_ids: tuple[str, ...], version=1):
    audit.append(
        tmp_path / "audit.jsonl",
        audit.SignOff(
            day=TODAY,
            lam=1.0,
            reason=REASON,
            signer="coordinator",
            signed_at=datetime.now(),
            ranked_job_ids=ranked_ids,
            batch_version=version,
            today_job_ids=today_ids,
        ),
    )


def test_empty_input_explains_the_number_format(tmp_path) -> None:
    at = _open(tmp_path, None)
    assert [title.value for title in at.title] == ["Tenant answer"]
    assert at.info
    assert explain.JOB_ID_PREFIX in at.info[0].value
    assert "receipt" in at.info[0].value
    assert not at.subheader


def test_example_selectbox_offers_open_jobs_from_each_queue_state(tmp_path) -> None:
    at = _open(tmp_path, None)
    examples = at.selectbox[0]

    assert examples.label == "Or try an example"
    assert examples.options and len(examples.options) == 3
    example_ids = [label.split(" - ", 1)[0] for label in examples.options]
    assert all(
        job_id in {j.job_id for j in ranking_table.open_jobs(TODAY)} for job_id in example_ids
    )
    assert "ranked today" in examples.options[0]
    assert "backlog" in examples.options[1]
    assert "review queue" in examples.options[2]

    chosen = example_ids[0]
    at = examples.select_index(0).run(timeout=60)
    assert not at.exception
    assert f"Job {chosen}" in [caption.value for caption in at.caption]


def test_known_id_renders_four_bordered_question_blocks(tmp_path, art) -> None:
    job_id = _road_rankable_ids(art)[0]
    at = _open(tmp_path, job_id)

    blocks = _bordered_blocks(at.main)
    assert len(blocks) == 4
    headings = [block.subheader[0].value for block in blocks]
    assert tuple(headings) == explain.QUESTIONS
    assert all(block.markdown for block in blocks)
    text = _answer_text(at)
    assert "has not signed it" in text  # no sign-off in the temporary audit log
    assert not re.search(r"will arrive|at \d", text)


def test_unsigned_draft_rank_matches_the_ranking(tmp_path, art) -> None:
    job_id = _road_rankable_ids(art)[0]
    jobs = [j for j in ranking_table.open_jobs(TODAY) if not j.needs_human]
    draft = next(s.rank for s in scoring.rank(jobs, TODAY, 1.0) if s.job.job_id == job_id)
    rank0 = next(s.rank for s in scoring.rank(jobs, TODAY, 0.0) if s.job.job_id == job_id)

    text = _answer_text(_open(tmp_path, job_id))
    assert f"On the draft, your repair is number {draft}." in text
    assert f"If distance did not count, your repair would be number {rank0}." in text


def test_bad_id_renders_unknown_copy(tmp_path) -> None:
    at = _open(tmp_path, "NOT-A-REAL-JOB-ID")
    text = _answer_text(at)
    assert "We could not find that job number." in text
    assert explain.JOB_ID_EXAMPLE in text
    assert len(_bordered_blocks(at.main)) == 4


def test_human_queue_id_renders_review_copy_and_no_rank(tmp_path) -> None:
    at = _open(tmp_path, _human_queue_open_id())
    text = _answer_text(at)
    assert "A person is checking your report before it is ranked." in text
    assert "We could not read" in text
    assert "is number" not in text
    assert "would be number" not in text


def test_signed_list_gives_signed_rank_and_backlog(tmp_path, art) -> None:
    first, second, third = _road_rankable_ids(art)[:3]
    _sign(tmp_path, (second, first), (second, first, third))

    signed = _answer_text(_open(tmp_path, first))
    assert "Your repair is number 2 on the signed list." in signed
    assert REASON in signed

    backlog = _answer_text(_open(tmp_path, third))
    assert "Your repair is number 3 in the queue, but it is not on today's list." in backlog


def test_superseded_names_the_signed_version_used(tmp_path, art) -> None:
    job_id = _road_rankable_ids(art)[0]
    _sign(tmp_path, (job_id,), (job_id,), version=1)
    audit.append(
        tmp_path / "audit.jsonl",
        audit.PlanDecision(TODAY, 1, "accept", "plan", "looks right"),
    )
    _sign(tmp_path, (job_id,), (job_id,), version=2)

    text = _answer_text(_open(tmp_path, job_id))
    assert "This answer uses the signed list version 2." in text


def test_page_text_passes_wording_check_for_five_sampled_jobs(tmp_path, art) -> None:
    sample = _road_rankable_ids(art)[:4] + [_human_queue_open_id()]
    assert len(sample) == 5
    for job_id in sample:
        at = _open(tmp_path, job_id)
        assert wording.check("\n".join(m.value for m in at.markdown)) == []
