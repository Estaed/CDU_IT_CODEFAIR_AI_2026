"""The workspace splits today's list at capacity, keeps review-queue jobs out of every frame,
states composition only before a signature, and writes one audit record per explained hand
move (PRD 3.1, wireframes §3 and §9)."""

import json
import socket
from datetime import date, timedelta
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from fair_turn.app.components import details_pane, ranking_table
from fair_turn.core import audit, constants, scoring
from fair_turn.core.batch import HandMove
from fair_turn.data import artefacts, policy

ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = ROOT / "fair_turn" / "app" / "pages" / "workspace.py"
LAST_DAY = constants.WINDOW_START + timedelta(days=constants.WINDOW_DAYS)
COLUMNS = [
    "rank",
    "rank change",
    "job_id",
    "community id",
    "fault type",
    "safety class",
    "window",
    "score",
    "score_bar",
]
OUTCOME_WORDS = ("wait", "travel", "median", "cost")


def _refuse(*args, **kwargs):
    raise RuntimeError("network disabled")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(socket, "socket", _refuse)


@pytest.fixture(scope="module")
def art() -> artefacts.Artefacts:
    return artefacts.load_all()


def _ranked():
    return scoring.rank(ranking_table.open_jobs(LAST_DAY), LAST_DAY, 1.0)


def _script(tmp_path: Path, *lines: str) -> Path:
    """Point the audit log at ``tmp_path`` (and run any fixture lines) before the page body;
    the runtime file is already isolated by ``tests/conftest.py``."""
    script = tmp_path / "workspace_with_temp_audit.py"
    body = [
        "from pathlib import Path",
        "from fair_turn.app import state",
        f'state.set_audit_path(Path(r"{tmp_path / "audit.jsonl"}"))',
        *lines,
        f'exec(compile(open(r"{WORKSPACE}", encoding="utf-8").read(), r"{WORKSPACE}", "exec"))',
    ]
    script.write_text("\n".join(body) + "\n", encoding="utf-8", newline="")
    return script


def _run(script: Path) -> AppTest:
    at = AppTest.from_file(str(script)).run(timeout=60)
    assert not at.exception
    return at


def _frame(at: AppTest, tab: int):
    return at.tabs[tab].dataframe[0].value


def _markdown(at: AppTest) -> list[str]:
    return [m.value for m in at.markdown]


def _select(job_id: str) -> str:
    return f'state.set_selected_job_id("{job_id}")'


def _open_needs_human(art, missing) -> str:
    open_ids = {j.job_id for j in ranking_table.open_jobs(LAST_DAY)}
    candidates = [
        label
        for label in art.labels
        if label["job_id"] in open_ids
        and art.extraction[label["job_id"]].needs_human
        and missing(art.extraction[label["job_id"]].kept)
    ]
    assert candidates, "the committed artefacts should hold such an open job"
    return max(candidates, key=lambda label: date.fromisoformat(label["reported_on"]))["job_id"]


# --- capacity split, review exclusion, compare view ------------------------------------------


def test_todays_list_is_capacity_and_first_render_selects_the_top_job(tmp_path) -> None:
    at = _run(_script(tmp_path))
    today, backlog = _frame(at, 0), _frame(at, 1)
    cap = ranking_table.capacity("All")
    crews = len(constants.REMOTE_REGIONS) * constants.CREWS_PER_REMOTE_REGION
    assert cap == (crews + constants.CREWS_TOWN) * constants.JOBS_PER_CREW_DAY
    ranked = _ranked()
    assert len(today) == cap
    assert list(today["job_id"]) == [s.job.job_id for s in ranked[:cap]]
    assert list(backlog["job_id"]) == [s.job.job_id for s in ranked[cap:]]
    assert list(today.columns) == COLUMNS == list(backlog.columns)
    queue = {j.job_id for j in ranking_table.open_jobs(LAST_DAY) if j.needs_human}
    assert queue
    assert not queue & (set(today["job_id"]) | set(backlog["job_id"]))
    top = _ranked()[0].job
    assert f"{top.job_id} · {top.community_id}" in [s.value for s in at.subheader]
    assert details_pane.NOTHING_SELECTED not in [i.value for i in at.info]


def test_todays_list_has_display_config_and_bounded_height(tmp_path) -> None:
    at = _run(_script(tmp_path))
    proto = at.tabs[0].dataframe[0].proto
    config = json.loads(proto.columns)
    assert set(COLUMNS) <= set(config)
    assert {
        name: config[name]["label"]
        for name in (
            "rank",
            "rank change",
            "job_id",
            "community id",
            "fault type",
            "safety class",
            "window",
            "score",
            "score_bar",
        )
    } == {
        "rank": "#",
        "rank change": "Delta",
        "job_id": "Job",
        "community id": "Community",
        "fault type": "Fault",
        "safety class": "Class",
        "window": "Window",
        "score": "Score",
        "score_bar": "Factors",
    }
    assert config["score_bar"]["type_config"] == {
        "type": "progress",
        "format": "%.1f",
        "min_value": 0.0,
        "max_value": float(_frame(at, 0)["score_bar"].max()),
    }
    assert ranking_table.table_height(ranking_table.capacity("All")) == 528
    assert ranking_table.table_height(21) == ranking_table.table_height(20)


def test_compare_renders_two_frames_with_identical_columns(tmp_path) -> None:
    at = _run(_script(tmp_path))
    assert len(at.tabs[0].dataframe) == 1
    at.checkbox[0].check().run(timeout=60)
    assert not at.exception
    frames = [frame.value for frame in at.tabs[0].dataframe]
    assert len(frames) == 2
    assert list(frames[0].columns) == list(frames[1].columns) == COLUMNS
    assert len(frames[0]) == len(frames[1]) == ranking_table.capacity("All")


# --- weighting and the effect sentence -------------------------------------------------------


def test_filter_pills_clear_to_the_full_list(tmp_path) -> None:
    at = _run(_script(tmp_path))
    assert len(at.sidebar.pills) == 2
    fault = at.sidebar.pills[0]
    fault.select("cooling").run(timeout=60)
    assert not at.exception
    filtered_count = len(_frame(at, 0)) + len(_frame(at, 1))
    at.sidebar.button(key="workspace_clear_filters").click().run(timeout=60)
    assert not at.exception
    full_count = len(_frame(at, 0)) + len(_frame(at, 1))
    assert filtered_count < full_count


def _effect(at: AppTest) -> str:
    return next(m.value for m in at.sidebar.markdown if m.value.startswith("Effect: "))


def test_effect_sentence_states_composition_only(tmp_path) -> None:
    at = _run(_script(tmp_path))
    sentences = [_effect(at)]
    assert sentences[0] == "Effect: No job changes between today's list and the backlog."
    at.sidebar.radio[0].set_value("Need first").run(timeout=60)
    assert not at.exception
    sentences.append(_effect(at))
    assert sentences[1].startswith("Effect: Need first moves ")
    captions = [c.value for c in at.sidebar.caption]
    assert "Travel-cost weight 0.00. 0 ignores travel cost, 1 applies the full penalty." in captions
    for sentence in sentences:
        assert not [word for word in OUTCOME_WORDS if word in sentence.lower()]


# --- the details pane ------------------------------------------------------------------------


def test_selected_id_in_state_shows_in_pane_header(tmp_path) -> None:
    job = _ranked()[0].job
    at = _run(_script(tmp_path, _select(job.job_id)))
    assert f"{job.job_id} · {job.community_id}" in [s.value for s in at.subheader]
    assert details_pane.NOTHING_SELECTED not in [i.value for i in at.info]


def test_human_set_field_shows_the_coordinator_badge(art, tmp_path) -> None:
    job_id = _open_needs_human(
        art, lambda kept: "fault_type" not in kept and "safety_class" in kept
    )
    set_field = f'state.set_human_set("{job_id}", "fault_type", "plumbing_water", reason="called")'
    at = _run(_script(tmp_path, set_field, _select(job_id)))
    assert any(details_pane.SET_BY_COORDINATOR in value for value in _markdown(at))
    unset = _run(_script(tmp_path, _select(_ranked()[0].job.job_id)))
    assert not any(details_pane.SET_BY_COORDINATOR in value for value in _markdown(unset))


def _factor_line(at: AppTest, name: str) -> str:
    return next(value for value in _markdown(at) if value.startswith(f"**{name}**"))


def test_no_source_phrase_only_on_extracted_factors(art, tmp_path) -> None:
    job_id = _open_needs_human(art, lambda kept: "safety_class" not in kept)
    at = _run(_script(tmp_path, _select(job_id)))
    assert _factor_line(at, "safety") == f"**safety** {details_pane.NO_PHRASE}"
    assert details_pane.IN_REVIEW in [w.value for w in at.warning]
    ranked = _run(_script(tmp_path, _select(_ranked()[0].job.job_id)))
    for run in (at, ranked):
        for name in ("urgency", "logistics"):
            assert "No source phrase found" not in _factor_line(run, name)
    assert _factor_line(ranked, "urgency").startswith("**urgency** ")
    assert "from NT window: " in _factor_line(ranked, "urgency")
    assert "from geography: " in _factor_line(at, "logistics")


def test_policy_unavailable_message(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(policy, "BUILD_DIR", tmp_path / "missing")
    at = _run(_script(tmp_path, _select(_ranked()[0].job.job_id)))
    assert details_pane.INDEX_UNAVAILABLE in [i.value for i in at.info]


def test_policy_passages_render_with_title_section_and_date(tmp_path, monkeypatch) -> None:
    job = _ranked()[0].job
    index_dir = tmp_path / "index"
    index_dir.mkdir()
    index = {
        "source": {"title": "Test fact sheet", "effective_date": "2025-10"},
        "threshold": 0.5,
        "embed_model": "test",
        "keys": {
            policy.key_for(job.safety_class.value, job.is_remote, job.fault_type): [
                {"section": "Urgent repairs", "text": "Call the hotline.", "score": 0.9}
            ]
        },
    }
    (index_dir / "policy_passages.json").write_text(json.dumps(index), "utf-8", newline="")
    monkeypatch.setattr(policy, "BUILD_DIR", index_dir)
    at = _run(_script(tmp_path, _select(job.job_id)))
    values = _markdown(at)
    assert "**Test fact sheet — Urgent repairs (effective 2025-10)**" in values
    assert "Call the hotline." in values
    assert details_pane.INDEX_UNAVAILABLE not in [i.value for i in at.info]
    assert details_pane.NO_PASSAGE not in [c.value for c in at.caption]


# --- hand moves: one audit record each, none without a reason --------------------------------


def _submit(at: AppTest, form: str, reason: str | None) -> AppTest:
    if reason is not None:
        at.text_input(key=f"{form}_reason").set_value(reason)
    at.button(key=f"{form}_submit").click().run(timeout=60)
    assert not at.exception
    return at


def test_promote_backlog_job_writes_one_promotion(tmp_path) -> None:
    ranked = _ranked()
    cap = ranking_table.capacity("All")
    promoted, displaced = ranked[cap].job.job_id, ranked[cap - 1].job.job_id
    audit_path = tmp_path / "audit.jsonl"
    at = _run(_script(tmp_path, _select(promoted)))
    assert promoted in list(_frame(at, 1)["job_id"])

    _submit(at, f"promote_{promoted}", None)
    assert details_pane.REASON_REQUIRED in [e.value for e in at.error]
    assert audit.read(audit_path) == []

    _submit(at, f"promote_{promoted}", "crew already in the community")
    records = audit.read(audit_path)
    assert len(records) == 1 and isinstance(records[0], audit.Promotion)
    assert (records[0].job_id, records[0].displaced_job_id) == (promoted, displaced)
    assert records[0].reason == "crew already in the community"
    today = list(_frame(at, 0)["job_id"])
    assert len(today) == cap and today[-1] == promoted and displaced not in today


def test_move_undo_and_send_to_review(tmp_path) -> None:
    ranked = _ranked()
    first, second = ranked[0].job.job_id, ranked[1].job.job_id
    audit_path = tmp_path / "audit.jsonl"
    at = _run(_script(tmp_path, _select(first)))

    _submit(at, f"move_down_{first}", "tenant away until the afternoon")
    records = audit.read(audit_path)
    assert len(records) == 1 and isinstance(records[0], audit.Override)
    assert (records[0].job_id, records[0].from_rank, records[0].to_rank) == (first, 1, 2)
    assert list(_frame(at, 0)["job_id"])[:2] == [second, first]

    at.button(key=f"undo_{first}").click().run(timeout=60)
    assert not at.exception
    assert list(_frame(at, 0)["job_id"])[:2] == [first, second]
    assert len(audit.read(audit_path)) == 1

    _submit(at, f"review_{first}", "tenant describes a different fault")
    records = audit.read(audit_path)
    assert len(records) == 2 and isinstance(records[1], audit.HumanSet)
    assert (records[1].field, records[1].value) == (
        "review_requested",
        "tenant describes a different fault",
    )
    shown = set(_frame(at, 0)["job_id"]) | set(_frame(at, 1)["job_id"])
    assert first not in shown
    assert details_pane.IN_REVIEW in [w.value for w in at.warning]


def test_apply_hand_moves_renumbers_and_ignores_unknown_ids() -> None:
    ranked = _ranked()[:4]
    ids = [s.job.job_id for s in ranked]
    moved = ranking_table.apply_hand_moves(
        ranked, [HandMove(ids[3], 4, 1, "r"), HandMove("JR-unknown", 9, 1, "r")]
    )
    assert [s.job.job_id for s in moved] == [ids[3], ids[0], ids[1], ids[2]]
    assert [s.rank for s in moved] == [1, 2, 3, 4]
