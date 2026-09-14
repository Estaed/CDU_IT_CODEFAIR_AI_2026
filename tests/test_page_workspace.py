"""The workspace splits today's list at capacity, keeps review-queue jobs out of every frame,
states composition only before a signature, and writes one audit record per explained hand
move (PRD 3.1, wireframes §3 and §9)."""

import json
import re
import socket
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from fair_turn.app.components import cluster_map, details_pane, job_rows, ranking_table, run_sheet
from fair_turn.core import audit, constants, scoring
from fair_turn.core.batch import HandMove
from fair_turn.data import artefacts, policy, runtime

ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = ROOT / "fair_turn" / "app" / "pages" / "workspace.py"
LAST_DAY = constants.WINDOW_START + timedelta(days=constants.WINDOW_DAYS)
COLUMNS = [
    "rank",
    "rank change",
    "job_id",
    "safety class",
    "window",
    "score",
    "score_bar",
    "community id",
    "fault type",
]
OUTCOME_WORDS = ("wait", "travel", "median", "cost")
TODAY_ROWS_KEY = "workspace_today"  # workspace.TODAY_ROWS_KEY; importing the page would run it
MAP_CAPTION = (  # workspace.MAP_CAPTION
    "Circles group communities; zoom in or click a circle to split it. "
    "Click a dot to open its jobs."
)
NO_HUMAN_JOBS = "No jobs need a person today."  # workspace.NO_HUMAN_JOBS


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


def _today_ids(at: AppTest) -> list[str]:
    """Job ids of today's bordered rows, in rendered order: each row's caption reads
    ``Job #717 · <community>`` (``job_rows.render``), and the short number maps back to the
    registration id through the ranked jobs."""
    by_short = {ranking_table.short_id(s.job.job_id): s.job.job_id for s in _ranked()}
    ids = []
    for caption in at.tabs[0].caption:
        match = re.match(r"Job (#\d+) · ", caption.value)
        if match:
            ids.append(by_short[match.group(1)])
    return ids


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
    today, backlog = _today_ids(at), _frame(at, 2)
    cap = ranking_table.capacity("All")
    crews = len(constants.REMOTE_REGIONS) * constants.CREWS_PER_REMOTE_REGION
    assert cap == (crews + constants.CREWS_TOWN) * constants.JOBS_PER_CREW_DAY
    ranked = _ranked()
    assert len(today) == cap
    assert today == [s.job.job_id for s in ranked[:cap]]
    assert list(backlog["job_id"]) == [s.job.job_id for s in ranked[cap:]]
    assert list(backlog.columns) == COLUMNS
    queue = {j.job_id for j in ranking_table.open_jobs(LAST_DAY) if j.needs_human}
    assert queue
    assert not queue & (set(today) | set(backlog["job_id"]))
    top = _ranked()[0].job
    assert f"Job {ranking_table.short_id(top.job_id)} · {top.community_id}" in [
        s.value for s in at.subheader
    ]
    assert details_pane.NOTHING_SELECTED not in [i.value for i in at.info]


def test_todays_list_is_rows_not_a_table_and_the_backlog_keeps_the_table(tmp_path) -> None:
    at = _run(_script(tmp_path))
    cap = ranking_table.capacity("All")
    assert at.tabs[0].dataframe.len == 0
    assert at.tabs[2].dataframe.len == 1
    opens = [button for button in at.tabs[0].button if button.label == job_rows.OPEN]
    assert len(opens) == cap
    assert [button.proto.type for button in opens].count("primary") == 1
    values = [markdown.value for markdown in at.tabs[0].markdown]
    top = _ranked()[0]
    assert _today_ids(at)[0] == top.job.job_id
    assert f":orange-badge[{job_rows.SELECTED}]" in values
    assert ranking_table.window_text(top.job, LAST_DAY) in [c.value for c in at.tabs[0].caption]
    assert len([node for node in at.tabs[0] if getattr(node, "type", None) == "progress"]) == cap


def test_opening_a_row_selects_that_job(tmp_path) -> None:
    second = _ranked()[1].job
    at = _run(_script(tmp_path))
    at.button(key=f"{TODAY_ROWS_KEY}_open_{second.job_id}").click().run(timeout=60)
    assert not at.exception
    assert f"Job {ranking_table.short_id(second.job_id)} · {second.community_id}" in [
        s.value for s in at.subheader
    ]
    values = [markdown.value for markdown in at.tabs[0].markdown]
    position = values.index("**2**")  # the rank cell opens the second row
    # The Selected badge sits under the Open button, after the rank in the same row.
    assert values.count(f":orange-badge[{job_rows.SELECTED}]") == 1
    assert f":orange-badge[{job_rows.SELECTED}]" in values[position : position + 8]


def test_backlog_search_narrows_the_frame_only(tmp_path) -> None:
    at = _run(_script(tmp_path))
    full = _frame(at, 2)
    community = str(full.iloc[0]["community id"])
    at.text_input(key="workspace_backlog_search").set_value(community).run(timeout=60)
    assert not at.exception
    narrowed = _frame(at, 2)
    assert 0 < len(narrowed) < len(full)
    assert set(narrowed["community id"]) == {community}
    assert list(narrowed["rank"]) == [
        row["rank"] for _, row in full.iterrows() if row["community id"] == community
    ]
    assert _today_ids(at) == [s.job.job_id for s in _ranked()[: ranking_table.capacity("All")]]


def test_backlog_table_has_display_config_and_bounded_height(tmp_path) -> None:
    at = _run(_script(tmp_path))
    proto = at.tabs[2].dataframe[0].proto
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
        "rank change": "Δ",
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
        "max_value": float(_frame(at, 2)["score_bar"].max()),
    }
    assert ranking_table.table_height(ranking_table.capacity("All")) == 528
    assert ranking_table.table_height(21) == ranking_table.table_height(20)


def test_compare_renders_two_frames_with_identical_columns(tmp_path) -> None:
    at = _run(_script(tmp_path))
    assert at.tabs[0].dataframe.len == 0
    at.checkbox[0].check().run(timeout=60)
    assert not at.exception
    frames = [frame.value for frame in at.tabs[0].dataframe]
    assert len(frames) == 2
    assert list(frames[0].columns) == list(frames[1].columns) == COLUMNS
    assert len(frames[0]) == len(frames[1]) == ranking_table.capacity("All")


# --- the map: two sets, two levels ------------------------------------------------------------


def _map_features(at: AppTest) -> list[dict]:
    """The clustered map's features: the v2 component carries its ``data`` as JSON."""
    nodes = at.get("bidi_component")
    assert len(nodes) == 1
    return [f["properties"] for f in json.loads(nodes[0].proto.json)["features"]["features"]]


def _in_region(art, region: str, job) -> bool:
    return art.communities[job.community_id]["region"] == region


def test_map_mode_switches_between_todays_list_and_all_open_jobs(tmp_path) -> None:
    at = _run(_script(tmp_path))
    cap = ranking_table.capacity("All")
    today_communities = {s.job.community_id for s in _ranked()[:cap]}
    todays = _map_features(at)
    assert len(todays) == len(today_communities)
    assert sum(point["open_jobs"] for point in todays) == cap
    assert MAP_CAPTION in [c.value for c in at.caption]
    assert not [button for button in at.button if button.key == "workspace_all_regions"]
    at.radio(key="workspace_map_mode").set_value("All open jobs").run(timeout=60)
    assert not at.exception
    everything = _map_features(at)
    assert len(everything) >= len(todays)
    assert sum(point["open_jobs"] for point in everything) == len(ranking_table.open_jobs(LAST_DAY))


def test_map_ring_follows_the_selected_job(tmp_path) -> None:
    job = _ranked()[3].job
    at = _run(_script(tmp_path, _select(job.job_id)))
    data = json.loads(at.get("bidi_component")[0].proto.json)
    assert data["selected"] == job.community_id


def _fake_map(monkeypatch, picked=None, failed=None) -> None:
    def fake(data, key):
        return SimpleNamespace(picked=picked, failed=failed)

    monkeypatch.setattr(cluster_map, "_mount", fake)


def test_a_map_pick_opens_its_community_job(tmp_path, monkeypatch) -> None:
    cap = ranking_table.capacity("All")
    counts = Counter(s.job.community_id for s in _ranked()[:cap])
    single = next(s.job for s in _ranked()[1:cap] if counts[s.job.community_id] == 1)
    _fake_map(monkeypatch, picked=single.community_id)
    at = _run(_script(tmp_path))
    assert at.session_state["selected_job_id"] == single.job_id
    assert any(
        s.value.startswith(f"Job {ranking_table.short_id(single.job_id)} · ") for s in at.subheader
    )
    # Once its job is open the pick is spent, so opening a row later is not pulled back.
    assert at.session_state["map_pick"] is None


def test_a_failed_map_shows_the_outline(tmp_path, monkeypatch) -> None:
    _fake_map(monkeypatch, failed="style: network error")
    at = _run(_script(tmp_path))
    assert not at.get("bidi_component")
    assert len(at.get("vega_lite_chart")) >= 1
    assert cluster_map.UNAVAILABLE in [i.value for i in at.info]


# --- region is a view; capacity is NT-wide ----------------------------------------------------


def test_region_filter_narrows_rows_and_points_but_not_capacity(tmp_path, art) -> None:
    cap = ranking_table.capacity("All")
    ranked = _ranked()
    region = art.communities[ranked[0].job.community_id]["region"]
    at = _run(_script(tmp_path, f'state.set_region("{region}")'))
    in_today = [s.job.job_id for s in ranked[:cap] if _in_region(art, region, s.job)]
    assert _today_ids(at) == in_today
    assert at.main.metric[0].value == f"{len(in_today)} of {cap} in {region}"
    backlog = _frame(at, 2)
    assert list(backlog["job_id"]) == [
        s.job.job_id for s in ranked[cap:] if _in_region(art, region, s.job)
    ]
    assert {point["region"] for point in _map_features(at)} == {region}
    assert at.tabs[0].label == f"Today's list {len(in_today)}"
    assert _effect(at) == "Effect: No job changes between today's list and the backlog."


# --- needs a human in the daily view ----------------------------------------------------------


def _human_ids(at: AppTest) -> list[str]:
    by_short = {
        ranking_table.short_id(j.job_id): j.job_id for j in ranking_table.open_jobs(LAST_DAY)
    }
    return [
        by_short[m.value[len("**Job ") : -2]]
        for m in at.tabs[1].markdown
        if m.value.startswith("**Job #")
    ]


def test_tabs_are_today_needs_a_human_and_backlog(tmp_path, art) -> None:
    at = _run(_script(tmp_path))
    queue = [j for j in ranking_table.open_jobs(LAST_DAY) if j.needs_human]
    labels = [tab.label for tab in at.tabs]
    assert labels[1] == f"Needs a human {len(queue)}"
    assert labels[0].startswith("Today's list ") and labels[2].startswith("Backlog ")
    ids = _human_ids(at)
    assert sorted(ids) == sorted(j.job_id for j in queue)
    buttons = [b for b in at.tabs[1].button if b.label == "Review"]
    assert len(buttons) == len(queue)
    texts = [t.value for t in at.tabs[1].text]
    for job in queue:
        if job.fault_type is None:
            assert "Fault type not found in the report" in texts
        if job.safety_class is None:
            assert "Safety class not found in the report" in texts
    # A value the model proposed and verification rejected never renders in these rows.
    shown = "\n".join(texts + [m.value for m in at.tabs[1].markdown])
    for job in queue:
        for value in art.extraction[job.job_id].dropped.values():
            assert str(value) not in shown


def test_review_button_sets_the_focus(tmp_path) -> None:
    at = _run(_script(tmp_path))
    job_id = _human_ids(at)[0]
    at.button(key=f"workspace_review_{job_id}").click().run(timeout=60)
    assert not at.exception
    assert at.session_state["review_focus"] == job_id


def test_sent_to_review_job_names_the_reason(tmp_path) -> None:
    first = _ranked()[0].job.job_id
    at = _run(_script(tmp_path, _select(first)))
    at.text_input(key=f"actions_{first}_reason").set_value("tenant describes a different fault")
    at.button(key=f"actions_{first}_review").click().run(timeout=60)
    assert not at.exception
    assert first in _human_ids(at)
    assert "Sent to review: tenant describes a different fault" in [
        t.value for t in at.tabs[1].text
    ]


def test_empty_needs_a_human_tab_says_so(tmp_path, monkeypatch) -> None:
    real = ranking_table.open_jobs
    monkeypatch.setattr(
        ranking_table, "open_jobs", lambda today: [j for j in real(today) if not j.needs_human]
    )
    at = _run(_script(tmp_path))
    assert at.tabs[1].label == "Needs a human 0"
    assert NO_HUMAN_JOBS in [i.value for i in at.tabs[1].info]


# --- weighting and the effect sentence -------------------------------------------------------


def test_filter_pills_clear_to_the_full_list(tmp_path) -> None:
    at = _run(_script(tmp_path))
    assert len(at.sidebar.pills) == 2
    fault = at.sidebar.pills[0]
    fault.select("cooling").run(timeout=60)
    assert not at.exception
    filtered_count = len(_today_ids(at)) + len(_frame(at, 2))
    at.sidebar.button(key="workspace_clear_filters").click().run(timeout=60)
    assert not at.exception
    full_count = len(_today_ids(at)) + len(_frame(at, 2))
    assert filtered_count < full_count


def _effect(at: AppTest) -> str:
    return next(info.value for info in at.main.info if info.value.startswith("Effect: "))


def test_effect_sentence_states_composition_only(tmp_path) -> None:
    at = _run(_script(tmp_path))
    sentences = [_effect(at)]
    assert sentences[0] == "Effect: No job changes between today's list and the backlog."
    at.sidebar.radio[0].set_value("Need first").run(timeout=60)
    assert not at.exception
    sentences.append(_effect(at))
    assert sentences[1].startswith("Effect: Need first moves ")
    assert not [m for m in at.sidebar.markdown if m.value.startswith("Effect: ")]
    captions = [c.value for c in at.sidebar.caption]
    assert "Travel-cost weight 0.00. 0 ignores travel cost, 1 applies the full penalty." in captions
    for sentence in sentences:
        assert not [word for word in OUTCOME_WORDS if word in sentence.lower()]


def test_crew_reach_line_plans_todays_list_like_the_visit_plan(tmp_path) -> None:
    at = _run(_script(tmp_path))
    lines = [c.value for c in at.main.caption if c.value.startswith("Crew reach: ")]
    cap = ranking_table.capacity("All")
    today_ids = [s.job.job_id for s in _ranked()[:cap]]
    jobs_by_id = {j.job_id: j for j in ranking_table.open_jobs(LAST_DAY)}
    assert lines == [run_sheet.reach_line(today_ids, jobs_by_id, LAST_DAY)]
    assert re.fullmatch(
        r"Crew reach: (every job on today's list has a crew within reach\."
        rf"|\d+ of today's {cap} jobs (has|have) no crew within reach with a free slot\.)",
        lines[0],
    )


def test_kpi_row_has_the_day_values_and_help_text(tmp_path) -> None:
    at = _run(_script(tmp_path))
    labels = [metric.label for metric in at.main.metric]
    assert labels == [
        "Today's list",
        "Remote households today",
        "In review",
        "Override rate today",
    ]
    cap = ranking_table.capacity("All")
    assert at.main.metric[0].value == f"{cap} of {cap}"
    assert at.main.metric[2].value == "21"
    assert at.main.metric[3].value == "0%"
    assert at.main.metric[0].proto.help == (
        "Jobs proposed within today's capacity: crews x jobs per crew per day (Part 2 constants)."
    )
    assert at.main.metric[1].proto.help == "Change against the efficiency-first list."
    assert at.main.metric[2].proto.help == "Jobs waiting for a person to set a field."
    assert at.main.metric[3].proto.help == (
        "Share of today's signed jobs moved by hand. See Evidence lab -> Audit log."
    )


# --- the details pane ------------------------------------------------------------------------


def test_selected_id_in_state_shows_in_pane_header(tmp_path) -> None:
    job = _ranked()[0].job
    at = _run(_script(tmp_path, _select(job.job_id)))
    assert f"Job {ranking_table.short_id(job.job_id)} · {job.community_id}" in [
        s.value for s in at.subheader
    ]
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
    """The summary-list row for a factor, joined back into one line: the pane renders the
    label, the value and the source as three consecutive markdown cells (Task-42)."""
    values = _markdown(at)
    index = next(i for i, value in enumerate(values) if value == f"**{name}**")
    value, source = values[index + 1], values[index + 2]
    if source == details_pane.NO_PHRASE:
        return f"**{name}** {source}"
    return f"**{name}** {value} {source}"


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
    assert "**Test fact sheet**" in values
    assert "Urgent repairs · effective 2025-10" in [c.value for c in at.caption]
    assert "Call the hotline." in values
    assert details_pane.INDEX_UNAVAILABLE not in [i.value for i in at.info]
    assert details_pane.NO_PASSAGE not in [c.value for c in at.caption]


# --- hand moves: one audit record each, none without a reason --------------------------------


def _submit(at: AppTest, job_id: str, action: str, reason: str | None) -> AppTest:
    form = f"actions_{job_id}"
    if reason is not None:
        at.text_input(key=f"{form}_reason").set_value(reason)
    at.button(key=f"{form}_{action}").click().run(timeout=60)
    assert not at.exception
    return at


def test_promote_backlog_job_writes_one_promotion(tmp_path) -> None:
    ranked = _ranked()
    cap = ranking_table.capacity("All")
    promoted, displaced = ranked[cap].job.job_id, ranked[cap - 1].job.job_id
    audit_path = tmp_path / "audit.jsonl"
    at = _run(_script(tmp_path, _select(promoted)))
    assert promoted in list(_frame(at, 2)["job_id"])

    _submit(at, promoted, "promote", None)
    assert details_pane.REASON_REQUIRED in [e.value for e in at.error]
    assert audit.read(audit_path) == []

    _submit(at, promoted, "promote", "crew already in the community")
    records = audit.read(audit_path)
    assert len(records) == 1 and isinstance(records[0], audit.Promotion)
    assert (records[0].job_id, records[0].displaced_job_id) == (promoted, displaced)
    assert records[0].reason == "crew already in the community"
    today = _today_ids(at)
    assert len(today) == cap and today[-1] == promoted and displaced not in today


def test_move_undo_and_send_to_review(tmp_path) -> None:
    ranked = _ranked()
    first, second = ranked[0].job.job_id, ranked[1].job.job_id
    audit_path = tmp_path / "audit.jsonl"
    at = _run(_script(tmp_path, _select(first)))

    _submit(at, first, "down", "tenant away until the afternoon")
    records = audit.read(audit_path)
    assert len(records) == 1 and isinstance(records[0], audit.Override)
    assert (records[0].job_id, records[0].from_rank, records[0].to_rank) == (first, 1, 2)
    assert _today_ids(at)[:2] == [second, first]

    at.button(key=f"undo_{first}").click().run(timeout=60)
    assert not at.exception
    assert _today_ids(at)[:2] == [first, second]
    assert len(audit.read(audit_path)) == 1

    _submit(at, first, "review", "tenant describes a different fault")
    records = audit.read(audit_path)
    assert len(records) == 2 and isinstance(records[1], audit.HumanSet)
    assert (records[1].field, records[1].value) == (
        "review_requested",
        "tenant describes a different fault",
    )
    shown = set(_today_ids(at)) | set(_frame(at, 2)["job_id"])
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


# --- DEV OPTION: replay a synthetic report as a new intake -----------------------------------


def _intake_rows() -> list[dict]:
    """Runtime records in the file the page writes (isolated by ``tests/conftest.py``)."""
    path = runtime.RUNTIME_DIR / "runtime.jsonl"
    lines = path.read_text("utf-8").splitlines() if path.exists() else []
    return [json.loads(line) for line in lines]


def _next_ids(art, count: int) -> list[str]:
    ids = {label["job_id"] for label in art.labels}
    out = []
    for _ in range(count):
        out.append(runtime.next_job_id(ids | set(out)))
    return out


def _toasts(at: AppTest) -> list[str]:
    return [t.value for t in at.toast]


def test_dev_add_a_new_report_lands_in_the_ranking(art, tmp_path) -> None:
    at = _run(_script(tmp_path))
    assert not _intake_rows()
    at.button(key="workspace_dev_0").click().run(timeout=60)
    assert not at.exception
    (row,) = _intake_rows()
    assert row["job_id"] == _next_ids(art, 1)[0]
    assert row["provider"] == "dev-replay" and row["status"] == "extracted"
    assert row["model"] == "synthetic replay (no model call)"
    assert row["reported_on"] == LAST_DAY.isoformat()
    assert at.session_state["selected_job_id"] == row["job_id"]
    # Matched on what the page shows: the new id is unknown to this process's cached open jobs.
    short = ranking_table.short_id(row["job_id"])
    in_today = any(c.value.startswith(f"Job {short} · ") for c in at.tabs[0].caption)
    assert in_today or row["job_id"] in set(_frame(at, 2)["job_id"])
    assert f"**Job {short}**" not in [m.value for m in at.tabs[1].markdown]
    assert any(t.startswith(f"Report {short} added: it ranks ") for t in _toasts(at))
    audit_rows = [
        json.loads(line) for line in (tmp_path / "audit.jsonl").read_text("utf-8").splitlines()
    ]
    assert [r["job_id"] for r in audit_rows if r.get("provider") == "dev-replay"] == [row["job_id"]]


def test_dev_add_one_that_needs_a_human_lands_in_that_tab(art, tmp_path) -> None:
    at = _run(_script(tmp_path))
    at.button(key="workspace_dev_1").click().run(timeout=60)
    assert not at.exception
    (row,) = _intake_rows()
    assert row["job_id"] == _next_ids(art, 1)[0]
    assert row["status"] == "needs_review"
    short = ranking_table.short_id(row["job_id"])
    assert f"**Job {short}**" in [m.value for m in at.tabs[1].markdown]
    assert not any(c.value.startswith(f"Job {short} · ") for c in at.tabs[0].caption)
    assert row["job_id"] not in set(_frame(at, 2)["job_id"])
    assert any(t.startswith(f"Report {short} added: it needs a person (") for t in _toasts(at))


def test_dev_pressing_twice_gives_two_distinct_ids(art, tmp_path) -> None:
    at = _run(_script(tmp_path))
    at.button(key="workspace_dev_0").click().run(timeout=60)
    at.button(key="workspace_dev_0").click().run(timeout=60)
    assert not at.exception
    rows = _intake_rows()
    assert [row["job_id"] for row in rows] == _next_ids(art, 2)
    assert len({row["text"] for row in rows}) == 2


# --- today's steps and the field check (PRD 3.1) ----------------------------------------------

STEP_TITLES = (
    "Jobs that need a person",
    "Check today's jobs",
    "Choose the weighting and sign",
    "Open the visit plan",
)


def test_todays_steps_strip_sits_above_the_header_numbers(tmp_path) -> None:
    at = _run(_script(tmp_path))
    markdown = [m.value for m in at.main.markdown]
    positions = [markdown.index(f"**{n}. {title}**") for n, title in enumerate(STEP_TITLES, 1)]
    assert positions == sorted(positions)
    status = next(i for i, value in enumerate(markdown) if value.startswith("Day "))
    assert positions[-1] < status
    assert any("Next" in value for value in markdown)
    assert any(c.value.endswith("open a job, read the report, press ✓ or ✗.") for c in at.caption)


def test_no_accept_all_control_on_the_workspace(tmp_path) -> None:
    at = _run(_script(tmp_path))
    labels = [b.label for b in at.button]
    assert labels
    assert not [label for label in labels if re.search(r"\ball\b", label, re.IGNORECASE)]


def test_a_confirmed_check_shows_on_its_row_and_counts_in_the_steps(tmp_path) -> None:
    at = _run(_script(tmp_path))
    job_id = at.session_state["selected_job_id"]
    total = len(_today_ids(at))
    at.button(key=f"fieldcheck_ok_{job_id}").click().run(timeout=60)
    assert not at.exception
    row_badges = [m.value for m in at.tabs[0].markdown]
    assert sum("✓ Checked" in value for value in row_badges) == 1
    assert sum("Not checked" in value for value in row_badges) == total - 1
    assert any(c.value.startswith(f"1 of {total} checked") for c in at.caption)
