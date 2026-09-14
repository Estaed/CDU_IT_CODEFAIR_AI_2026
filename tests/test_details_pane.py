"""The workspace details pane presents job evidence as a scannable summary (PRD 3.1)."""

import re
import socket
from datetime import timedelta
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from fair_turn.app.components import details_pane, highlight, ranking_table
from fair_turn.core import constants, scoring
from fair_turn.data import artefacts, policy

ROOT = Path(__file__).resolve().parent.parent


def _refuse(*args, **kwargs):
    raise RuntimeError("network disabled")


@pytest.fixture(autouse=True)
def no_network(monkeypatch) -> None:
    monkeypatch.setattr(socket, "socket", _refuse)


@pytest.fixture(scope="module")
def art() -> artefacts.Artefacts:
    return artefacts.load_all()


def _open_jobs():
    today = constants.WINDOW_START + timedelta(days=constants.WINDOW_DAYS)
    return today, ranking_table.open_jobs(today)


def _script(tmp_path: Path, job_id: str) -> Path:
    """Create an offline Streamlit app that renders only the selected-job pane."""
    script = tmp_path / "details_pane_app.py"
    script.write_text(
        "from pathlib import Path\n"
        "from fair_turn.app import state\n"
        "from fair_turn.app.components import details_pane, ranking_table\n"
        "from fair_turn.core import constants, scoring\n"
        "from fair_turn.data import artefacts\n"
        "from datetime import timedelta\n"
        f'state.set_runtime_path(Path(r"{tmp_path / "runtime.jsonl"}"))\n'
        f'state.set_audit_path(Path(r"{tmp_path / "audit.jsonl"}"))\n'
        f'state.set_selected_job_id("{job_id}")\n'
        "art = artefacts.load_all()\n"
        "today = constants.WINDOW_START + timedelta(days=constants.WINDOW_DAYS)\n"
        "jobs = ranking_table.open_jobs(today)\n"
        "current = scoring.rank(jobs, today, 1.0)\n"
        "details_pane.render(\n"
        '    art, jobs, current, ranking_table.capacity("All"), set(), today, 1.0\n'
        ")\n",
        encoding="utf-8",
        newline="",
    )
    return script


def _run(tmp_path: Path, job_id: str) -> AppTest:
    at = AppTest.from_file(str(_script(tmp_path, job_id))).run(timeout=60)
    assert not at.exception
    return at


def _markdown(at: AppTest) -> list[str]:
    return [element.value for element in at.markdown]


def _page_text(at: AppTest) -> str:
    values = _markdown(at)
    values += [element.value for element in at.warning]
    values += [element.value for element in at.caption]
    return "\n".join(values)


def test_ranked_and_review_jobs_show_their_status_badges(art, tmp_path) -> None:
    today, jobs = _open_jobs()
    ranked = scoring.rank(jobs, today, 1.0)[0].job
    ranked_text = _page_text(_run(tmp_path, ranked.job_id))
    assert ranked.safety_class is not None
    assert ranked.safety_class.value.capitalize() in ranked_text
    assert ("Remote" if ranked.is_remote else "Town") in ranked_text

    review = next(job for job in jobs if job.needs_human)
    review_text = _page_text(_run(tmp_path, review.job_id))
    assert "Needs a human" in review_text


def test_summary_list_has_score_then_all_four_factors(art, tmp_path) -> None:
    today, jobs = _open_jobs()
    ranked = scoring.rank(jobs, today, 1.0)[0].job
    values = _markdown(_run(tmp_path, ranked.job_id))
    labels = ["Score", "urgency", "safety", "household health risk", "logistics"]
    positions = [
        next(i for i, value in enumerate(values) if value.startswith(f"**{label}**"))
        for label in labels
    ]
    assert positions == sorted(positions)
    assert "urgency + safety + household health risk - logistics" in values
    assert any("from NT window:" in value for value in values)
    assert any("from geography:" in value for value in values)
    assert any(value.startswith("Ranked ") for value in values)


def test_empty_health_evidence_and_rejected_value_do_not_render(art, tmp_path) -> None:
    _today, jobs = _open_jobs()
    without_health_evidence = next(
        job
        for job in jobs
        if not job.needs_human
        and not any(field.startswith("health") for field in art.extraction[job.job_id].kept)
    )
    assert "No source phrase found" in _page_text(_run(tmp_path, without_health_evidence.job_id))

    review = next(
        job
        for job in jobs
        if any(
            field in art.extraction[job.job_id].dropped for field in ("fault_type", "safety_class")
        )
    )
    dropped = next(iter(art.extraction[review.job_id].dropped.values()))
    assert dropped not in _page_text(_run(tmp_path, review.job_id))


def _buttons(at: AppTest) -> list[str]:
    return [button.label for button in at.button]


def _rendered_report(art, job_id: str) -> str:
    """The report text exactly as the pane renders it: verbatim, phrases highlighted."""
    text = art.reports[job_id]
    evidence = {field: ev.evidence for field, ev in art.extraction[job_id].kept.items()}
    return highlight.render(text, highlight.spans(text, evidence))


def test_header_reads_as_a_short_id_with_the_registration_in_the_caption(art, tmp_path) -> None:
    today, jobs = _open_jobs()
    ranked = scoring.rank(jobs, today, 1.0)[0].job
    at = _run(tmp_path, ranked.job_id)
    heading = at.subheader[0].value
    assert heading.startswith(f"Job {ranking_table.short_id(ranked.job_id)} ")
    assert ranked.job_id not in heading
    assert heading.endswith(
        " ".join(word.title() if word.isalpha() else word for word in ranked.community_id.split())
    )
    captions = [element.value for element in at.caption]
    assert any(caption.startswith(f"Registration {ranked.job_id} ") for caption in captions)


def test_report_text_is_rendered_above_the_explanation(art, tmp_path) -> None:
    today, jobs = _open_jobs()
    ranked = scoring.rank(jobs, today, 1.0)[0].job
    at = _run(tmp_path, ranked.job_id)
    values = _markdown(at)
    report = values.index(_rendered_report(art, ranked.job_id))
    assert report < values.index("**Why it sits here.**")
    assert details_pane.REPORT_CAPTION in [element.value for element in at.caption]


def test_fields_and_policy_sit_in_their_own_expanders(art, tmp_path) -> None:
    today, jobs = _open_jobs()
    ranked = scoring.rank(jobs, today, 1.0)[0].job
    labels = [block.label for block in _run(tmp_path, ranked.job_id).get("expander")]
    assert "Fields read from the report" in labels
    assert "Policy reference" in labels


def test_a_long_policy_passage_is_cut_with_the_full_text_one_click_away(art, tmp_path) -> None:
    index = policy.load()
    today, jobs = _open_jobs()
    job, passage = next(
        (job, passage)
        for job in jobs
        if job.safety_class is not None
        for passage in policy.lookup(
            index,
            job.safety_class.value,
            art.communities[job.community_id]["is_remote"] == "True",
            job.fault_type,
        )
        if len(passage.text) > details_pane.PASSAGE_PREVIEW_CHARS
    )
    at = _run(tmp_path, job.job_id)
    values = _markdown(at)
    cut = passage.text[: details_pane.PASSAGE_PREVIEW_CHARS].rsplit(" ", 1)[0]
    preview = highlight.render(f"{cut}…", [])
    assert preview in values
    assert highlight.render(passage.text, []) in values
    assert at.get("popover")


def test_action_buttons_say_what_they_do(art, tmp_path) -> None:
    today, jobs = _open_jobs()
    ranked = scoring.rank(jobs, today, 1.0)
    cap = ranking_table.capacity("All")
    at = _run(tmp_path, ranked[1].job.job_id)
    assert "Move up one place" in _buttons(at)
    assert "Move down one place" in _buttons(at)
    assert "Send to review queue" in _buttons(at)
    assert any("every change needs a reason and is logged" in value for value in _markdown(at))

    backlog = _run(tmp_path, ranked[cap].job.job_id)
    assert "Promote into today's list" in _buttons(backlog)
    assert any(
        caption.startswith("This job is in the backlog.")
        for caption in [element.value for element in backlog.caption]
    )


def test_badges_use_named_colours_without_hex_literals() -> None:
    source = (ROOT / "fair_turn" / "app" / "components" / "details_pane.py").read_text("utf-8")
    assert '"immediate": "red"' in source
    assert '"urgent": "orange"' in source
    assert 'color="yellow"' in source
    assert 'color="gray"' in source
    assert not re.search(r"#[0-9A-Fa-f]{3,8}\\b", source)
