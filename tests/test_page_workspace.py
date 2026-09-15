"""The workspace splits today's list at capacity, keeps review-queue jobs out of every frame,
states composition only before a signature, and writes one audit record per explained hand
move (PRD 3.1, wireframes §3 and §9)."""

import json
import re
import socket
from collections import Counter
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from fair_turn.app.components import (
    cluster_map,
    details_pane,
    job_rows,
    keyboard,
    ranking_table,
    run_sheet,
)
from fair_turn.core import audit, constants, decisions, scoring
from fair_turn.core.batch import HandMove
from fair_turn.core.types import SafetyClass
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
    # Immediate jobs go to the make-safe lane, never into the crew ranking (PRD 3.1, 2026-09-15).
    jobs = [j for j in ranking_table.open_jobs(LAST_DAY) if not decisions.is_make_safe(j)]
    return scoring.rank(jobs, LAST_DAY, 1.0)


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


def _heading(job) -> str:
    """The pane heading: short id and the community label as the pane renders it."""
    label = ranking_table.community_label(job.community_id)
    return f"Job {ranking_table.short_id(job.job_id)} · {label}"


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
    today, backlog = _today_ids(at), _frame(at, 3)
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
    assert _heading(top) in [s.value for s in at.subheader]
    assert details_pane.NOTHING_SELECTED not in [i.value for i in at.info]


def test_todays_list_is_rows_not_a_table_and_the_backlog_keeps_the_table(tmp_path) -> None:
    at = _run(_script(tmp_path))
    cap = ranking_table.capacity("All")
    assert at.tabs[0].dataframe.len == 0
    assert at.tabs[3].dataframe.len == 1
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
    assert _heading(second) in [s.value for s in at.subheader]
    values = [markdown.value for markdown in at.tabs[0].markdown]
    position = values.index("**2**")  # the rank cell opens the second row
    # The Selected badge sits under the Open button, after the rank in the same row.
    assert values.count(f":orange-badge[{job_rows.SELECTED}]") == 1
    assert f":orange-badge[{job_rows.SELECTED}]" in values[position : position + 8]


def test_backlog_search_narrows_the_frame_only(tmp_path) -> None:
    at = _run(_script(tmp_path))
    full = _frame(at, 3)
    community = str(full.iloc[0]["community id"])
    at.text_input(key="workspace_backlog_search").set_value(community).run(timeout=60)
    assert not at.exception
    narrowed = _frame(at, 3)
    assert 0 < len(narrowed) < len(full)
    assert set(narrowed["community id"]) == {community}
    assert list(narrowed["rank"]) == [
        row["rank"] for _, row in full.iterrows() if row["community id"] == community
    ]
    assert _today_ids(at) == [s.job.job_id for s in _ranked()[: ranking_table.capacity("All")]]


def test_backlog_table_has_display_config_and_bounded_height(tmp_path) -> None:
    at = _run(_script(tmp_path))
    proto = at.tabs[3].dataframe[0].proto
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
        "max_value": float(_frame(at, 3)["score_bar"].max()),
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
    nodes = _map_nodes(at)
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
    data = json.loads(_map_nodes(at)[0].proto.json)
    assert data["selected"] == job.community_id


def _map_nodes(at: AppTest) -> list:
    """The map's component nodes; the keyboard listener is a component node too."""
    return [
        node
        for node in at.get("bidi_component")
        if node.proto.component_name.endswith(cluster_map.COMPONENT_NAME)
    ]


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
    assert not _map_nodes(at)
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
    backlog = _frame(at, 3)
    assert list(backlog["job_id"]) == [
        s.job.job_id for s in ranked[cap:] if _in_region(art, region, s.job)
    ]
    assert {point["region"] for point in _map_features(at)} == {region}
    assert at.tabs[0].label == f"To decide {len(in_today)}"
    assert _effect(at) == "Effect: No job changes between today's list and the backlog."


# --- needs a human in the daily view ----------------------------------------------------------


def _human_ids(at: AppTest) -> list[str]:
    by_short = {
        ranking_table.short_id(j.job_id): j.job_id for j in ranking_table.open_jobs(LAST_DAY)
    }
    return [
        by_short[m.value[len("**Job ") : -2]]
        for m in at.tabs[2].markdown
        if m.value.startswith("**Job #")
    ]


def test_tabs_are_today_needs_a_human_and_backlog(tmp_path, art) -> None:
    at = _run(_script(tmp_path))
    queue = [j for j in ranking_table.open_jobs(LAST_DAY) if j.needs_human]
    labels = [tab.label for tab in at.tabs]
    assert labels[2] == f"Needs a human {len(queue)}"
    assert labels[0].startswith("To decide ") and labels[1] == "Accepted 0"
    assert labels[3].startswith("Backlog ")
    ids = _human_ids(at)
    assert sorted(ids) == sorted(j.job_id for j in queue)
    buttons = [b for b in at.tabs[2].button if b.label == "Review"]
    assert len(buttons) == len(queue)
    texts = [t.value for t in at.tabs[2].text]
    for job in queue:
        if job.fault_type is None:
            assert "Fault type not found in the report" in texts
        if job.safety_class is None:
            assert "Safety class not found in the report" in texts
    # A value the model proposed and verification rejected never renders in these rows.
    shown = "\n".join(texts + [m.value for m in at.tabs[2].markdown])
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
        t.value for t in at.tabs[2].text
    ]


def test_empty_needs_a_human_tab_says_so(tmp_path, monkeypatch) -> None:
    real = ranking_table.open_jobs
    monkeypatch.setattr(
        ranking_table, "open_jobs", lambda today: [j for j in real(today) if not j.needs_human]
    )
    at = _run(_script(tmp_path))
    assert at.tabs[2].label == "Needs a human 0"
    assert NO_HUMAN_JOBS in [i.value for i in at.tabs[2].info]


# --- weighting and the effect sentence -------------------------------------------------------


def test_filter_pills_clear_to_the_full_list(tmp_path) -> None:
    at = _run(_script(tmp_path))
    assert len(at.sidebar.pills) == 2
    fault = at.sidebar.pills[0]
    fault.select("cooling").run(timeout=60)
    assert not at.exception
    filtered_count = len(_today_ids(at)) + len(_frame(at, 3))
    at.sidebar.button(key="workspace_clear_filters").click().run(timeout=60)
    assert not at.exception
    full_count = len(_today_ids(at)) + len(_frame(at, 3))
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


def test_a_not_today_rejection_shows_in_the_effect_the_reach_line_and_the_tile(
    tmp_path, art
) -> None:
    """The effect sentence, the reach caption and the tile read To decide + Accepted; the
    efficiency-first side stays the first capacity-many jobs of the λ = 1.0 ranking."""
    cap = ranking_table.capacity("All")
    ranked = _ranked()
    out, into = ranked[0].job, ranked[cap].job
    audit.append(
        tmp_path / "audit.jsonl",
        audit.JobDecision(LAST_DAY, out.job_id, "not_today", "coordinator", "tenant away"),
    )
    at = _run(_script(tmp_path))
    remote_in = int(art.communities[into.community_id]["is_remote"] == "True")
    remote_out = int(art.communities[out.community_id]["is_remote"] == "True")
    assert _effect(at) == (
        f"Effect: Efficiency first moves 1 job into today's list ({remote_in} remote, "
        f"{1 - remote_in} town) and 1 job to the backlog ({remote_out} remote, "
        f"{1 - remote_out} town)."
    )
    decided = [s.job.job_id for s in ranked[1 : cap + 1]]
    jobs_by_id = {j.job_id: j for j in ranking_table.open_jobs(LAST_DAY)}
    reach = [c.value for c in at.main.caption if c.value.startswith("Crew reach: ")]
    assert reach == [run_sheet.reach_line(decided, jobs_by_id, LAST_DAY)]
    assert at.main.metric[0].value == f"{cap} of {cap}"


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
    assert _heading(job) in [s.value for s in at.subheader]
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
    assert promoted in list(_frame(at, 3)["job_id"])

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
    shown = set(_today_ids(at)) | set(_frame(at, 3)["job_id"])
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


def _add_report(at: AppTest, kind: str) -> AppTest:
    at.selectbox(key="workspace_dev_kind").set_value(kind)
    at.button(key="workspace_dev_add").click().run(timeout=60)
    assert not at.exception
    return at


@pytest.mark.parametrize("kind", ["Immediate", "Urgent", "Routine", "Needs a person"])
def test_dev_add_report_lands_where_its_message_says(art, tmp_path, kind) -> None:
    at = _run(_script(tmp_path))
    assert not _intake_rows()
    _add_report(at, kind)
    (row,) = _intake_rows()
    assert row["job_id"] == _next_ids(art, 1)[0]
    assert row["provider"] == "dev-replay"
    assert row["model"] == "synthetic replay (no model call)"
    assert row["reported_on"] == LAST_DAY.isoformat()
    assert at.session_state["selected_job_id"] == row["job_id"]
    audit_rows = [
        json.loads(line) for line in (tmp_path / "audit.jsonl").read_text("utf-8").splitlines()
    ]
    assert [r["job_id"] for r in audit_rows if r.get("provider") == "dev-replay"] == [row["job_id"]]
    # Matched on what the page shows: the new id is unknown to this process's cached open jobs.
    short = ranking_table.short_id(row["job_id"])
    today_captions = [c.value for c in at.tabs[0].caption if re.match(r"Job #\d+ · ", c.value)]
    today_at = [i for i, c in enumerate(today_captions) if c.startswith(f"Job {short} · ")]
    backlog = _frame(at, 3)
    in_backlog = backlog[backlog["job_id"] == row["job_id"]]
    in_human = f"**Job {short}**" in [m.value for m in at.tabs[2].markdown]
    (message,) = [s.value for s in at.success if s.value.startswith(f"Report {short} added")]
    if kind == "Immediate":  # the make-safe lane, not the crew ranking (PRD 3.1, 2026-09-15)
        assert row["status"] == "extracted" and row["extraction"]["safety_class"] == "immediate"
        assert "is in Make safe now" in message, message
        assert at.button(key=f"{MAKE_SAFE_OPEN}{row['job_id']}")
        assert not in_human and not today_at and in_backlog.empty
        assert short not in "\n".join(c.value for c in at.tabs[1].caption)
        return
    if kind == "Needs a person":
        assert row["status"] == "needs_review"
        assert message == f"Report {short} added. It needs a person: open the Needs a human tab."
        assert in_human and not today_at and in_backlog.empty
        return
    assert row["status"] == "extracted" and row["extraction"]["safety_class"] == kind.lower()
    match = re.fullmatch(
        rf"Report {short} added \({kind.lower()}\)\. It ranks (\d+)(?:st|nd|rd|th): "
        r"(it is in To decide|it waits in the Backlog, because (.+))\.",
        message,
    )
    assert match, message
    assert not in_human
    rank = int(match.group(1))
    if match.group(2) == "it is in To decide":
        assert in_backlog.empty and len(today_at) == 1
        assert today_at[0] + 1 == rank  # nothing is accepted, so rows are ranks 1..capacity
    else:
        assert not today_at and int(in_backlog["rank"].iloc[0]) == rank
        if kind == "Routine":
            assert match.group(3) == "a new routine repair has most of its NT window left"


def test_dev_message_stays_until_the_next_action(tmp_path) -> None:
    at = _add_report(_run(_script(tmp_path)), "Urgent")
    new_id = at.session_state["selected_job_id"]
    at.run(timeout=60)
    assert [s for s in at.success if s.value.startswith("Report ")]
    other = next(
        b
        for b in at.tabs[0].button
        if (b.key or "").startswith(f"{TODAY_ROWS_KEY}_open_") and not b.key.endswith(new_id)
    )
    other.click().run(timeout=60)
    assert not at.exception
    assert not [s for s in at.success if s.value.startswith("Report ")]


def test_dev_pressing_twice_gives_two_distinct_ids(art, tmp_path) -> None:
    at = _run(_script(tmp_path))
    at.button(key="workspace_dev_add").click().run(timeout=60)
    at.button(key="workspace_dev_add").click().run(timeout=60)
    assert not at.exception
    rows = _intake_rows()
    assert [row["job_id"] for row in rows] == _next_ids(art, 2)
    assert len({row["text"] for row in rows}) == 2


# --- today's steps and the field check (PRD 3.1) ----------------------------------------------

STEP_TITLES = (
    "Jobs that need a person",
    "Decide today's jobs",
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
    assert any(m.value.endswith("then Accept or Reject.") for m in at.markdown)


def test_no_accept_all_control_on_the_workspace(tmp_path) -> None:
    at = _run(_script(tmp_path))
    labels = [b.label for b in at.button]
    assert labels
    assert not [label for label in labels if re.search(r"\ball\b", label, re.IGNORECASE)]


# --- accept or reject each job (PRD 3.1) ------------------------------------------------------


def _labels(at: AppTest) -> list[str]:
    return [tab.label for tab in at.tabs]


def _fake_keys(monkeypatch) -> list[str]:
    """Replace the keyboard listener: each run pops one queued key, like one real keydown."""
    queue: list[str] = []

    def fake(data, key):
        return SimpleNamespace(pressed={"key": queue.pop(0), "nonce": 1} if queue else None)

    monkeypatch.setattr(keyboard, "_mount", fake)
    return queue


def _press(at: AppTest, queue: list[str], key: str) -> AppTest:
    queue.append(key)
    at.run(timeout=60)
    assert not at.exception
    assert not queue
    return at


def test_keyboard_hint_sits_above_the_tabs(tmp_path) -> None:
    at = _run(_script(tmp_path))
    assert keyboard.HINT in [c.value for c in at.main.caption]


def test_j_and_k_walk_to_decide_and_wrap(tmp_path, monkeypatch) -> None:
    queue = _fake_keys(monkeypatch)
    cap = ranking_table.capacity("All")
    ids = [s.job.job_id for s in _ranked()[:cap]]
    at = _run(_script(tmp_path))
    assert at.session_state["selected_job_id"] == ids[0]
    _press(at, queue, "j")
    assert at.session_state["selected_job_id"] == ids[1]
    assert any(s.value.startswith(f"Job {ranking_table.short_id(ids[1])} · ") for s in at.subheader)
    _press(at, queue, "k")
    assert at.session_state["selected_job_id"] == ids[0]
    _press(at, queue, "k")
    assert at.session_state["selected_job_id"] == ids[-1]
    _press(at, queue, "j")
    assert at.session_state["selected_job_id"] == ids[0]


def test_j_selects_the_first_job_when_the_selection_is_not_in_to_decide(
    tmp_path, monkeypatch
) -> None:
    queue = _fake_keys(monkeypatch)
    ranked = _ranked()
    cap = ranking_table.capacity("All")
    # Seeded once through session state: a script line would reset the selection every rerun.
    at = AppTest.from_file(str(_script(tmp_path)))
    at.session_state["selected_job_id"] = ranked[cap].job.job_id
    at.run(timeout=60)
    assert not at.exception
    _press(at, queue, "j")
    assert at.session_state["selected_job_id"] == ranked[0].job.job_id


def test_a_refuses_without_the_read_tick_then_accepts_once_ticked(tmp_path, monkeypatch) -> None:
    queue = _fake_keys(monkeypatch)
    cap = ranking_table.capacity("All")
    at = _run(_script(tmp_path))
    job_id = at.session_state["selected_job_id"]
    _press(at, queue, "a")
    assert "Tick 'I have read the report' first." in [t.value for t in at.toast]
    assert not _decisions(tmp_path)
    at.checkbox(key=f"read_{job_id}").check().run(timeout=60)
    _press(at, queue, "a")
    (record,) = _decisions(tmp_path)
    assert (record.job_id, record.decision, record.actor) == (job_id, "accepted", "coordinator")
    assert _labels(at)[:2] == [f"To decide {cap - 1}", "Accepted 1"]


def test_a_refuses_a_job_that_is_not_in_to_decide(tmp_path, monkeypatch) -> None:
    queue = _fake_keys(monkeypatch)
    backlog_id = _ranked()[ranking_table.capacity("All")].job.job_id
    at = _run(_script(tmp_path, _select(backlog_id)))
    at.checkbox(key=f"read_{backlog_id}").check().run(timeout=60)
    _press(at, queue, "a")
    assert "This job is not in To decide." in [t.value for t in at.toast]
    assert not _decisions(tmp_path)


def test_a_refuses_once_todays_list_is_signed(tmp_path, monkeypatch) -> None:
    queue = _fake_keys(monkeypatch)
    cap = ranking_table.capacity("All")
    for s in _ranked()[:cap]:
        audit.append(
            tmp_path / "audit.jsonl", audit.JobDecision(LAST_DAY, s.job.job_id, "accepted", "A")
        )
    at = _run(_script(tmp_path))
    at.button(key="workspace_review_and_sign").click().run(timeout=60)
    at.text_input(key="sign_off_signer").set_value("A. Coordinator")
    at.text_area(key="sign_off_reason").set_value("Every job was read and decided today.")
    at.button(key="sign_off_submit").click().run(timeout=60)
    assert not at.exception
    assert at.session_state["signed_today"]
    before = len(_decisions(tmp_path))
    _press(at, queue, "a")
    assert "Today's list is signed." in [t.value for t in at.toast]
    assert len(_decisions(tmp_path)) == before


def test_x_opens_the_reject_form_for_the_selected_job(tmp_path, monkeypatch) -> None:
    queue = _fake_keys(monkeypatch)
    at = _run(_script(tmp_path))
    job_id = at.session_state["selected_job_id"]
    _press(at, queue, "x")
    assert at.session_state["reject_job"] == job_id
    assert at.radio(key=f"reject_kind_{job_id}").value == "Not today: move it to the backlog"
    assert not _decisions(tmp_path)


def _accepted_ids(at: AppTest) -> list[str]:
    by_short = {ranking_table.short_id(s.job.job_id): s.job.job_id for s in _ranked()}
    return [
        by_short[match.group(1)]
        for caption in at.tabs[1].caption
        if (match := re.match(r"Job (#\d+) · ", caption.value))
    ]


def _decisions(tmp_path: Path) -> list[audit.JobDecision]:
    return [r for r in audit.read(tmp_path / "audit.jsonl") if isinstance(r, audit.JobDecision)]


def test_accept_needs_the_read_tick_and_moves_the_job_to_accepted(tmp_path) -> None:
    cap = ranking_table.capacity("All")
    at = _run(_script(tmp_path))
    job_id = at.session_state["selected_job_id"]
    assert job_id == _ranked()[0].job.job_id
    assert _labels(at)[:2] == [f"To decide {cap}", "Accepted 0"]
    accept = at.button(key=f"decide_accept_{job_id}")
    assert accept.label == details_pane.ACCEPT and accept.proto.icon == ":material/check:"
    assert accept.proto.disabled
    reject = at.button(key=f"decide_reject_{job_id}")
    assert reject.label == details_pane.REJECT and reject.proto.icon == ":material/close:"
    assert at.checkbox(key=f"read_{job_id}").label == details_pane.READ_BOX

    at.checkbox(key=f"read_{job_id}").check().run(timeout=60)
    assert not at.button(key=f"decide_accept_{job_id}").proto.disabled
    at.button(key=f"decide_accept_{job_id}").click().run(timeout=60)
    assert not at.exception
    assert _labels(at)[:2] == [f"To decide {cap - 1}", "Accepted 1"]
    assert job_id not in _today_ids(at)
    assert _accepted_ids(at) == [job_id]
    assert any(":material/check: Accepted" in m.value for m in at.tabs[1].markdown)
    assert sum("Not decided" in m.value for m in at.tabs[0].markdown) == cap - 1
    (record,) = _decisions(tmp_path)
    assert (record.job_id, record.decision, record.day) == (job_id, "accepted", LAST_DAY)
    assert any(
        m.value.startswith(":material/check: Accepted by coordinator at ") for m in at.markdown
    )
    assert any(
        m.value == f"{cap - 1} left: open each job, read it to the bottom, then Accept or Reject."
        for m in at.markdown
    )

    at.button(key=f"decide_undo_{job_id}").click().run(timeout=60)
    assert not at.exception
    assert _labels(at)[:2] == [f"To decide {cap}", "Accepted 0"]
    assert _today_ids(at)[0] == job_id
    assert [r.decision for r in _decisions(tmp_path)] == ["accepted", "undone"]


def test_reject_not_today_keeps_to_decide_full_and_moves_the_job_to_the_backlog(tmp_path) -> None:
    cap = ranking_table.capacity("All")
    ranked = _ranked()
    job_id, next_in = ranked[0].job.job_id, ranked[cap].job.job_id
    at = _run(_script(tmp_path, _select(job_id)))
    at.button(key=f"decide_reject_{job_id}").click().run(timeout=60)
    assert not at.exception
    assert at.radio(key=f"reject_kind_{job_id}").value == "Not today: move it to the backlog"
    at.button(key=f"reject_save_{job_id}").click().run(timeout=60)
    assert details_pane.REASON_REQUIRED in [e.value for e in at.error]
    assert not _decisions(tmp_path)

    at.text_input(key=f"reject_reason_{job_id}").set_value("tenant away this week")
    at.button(key=f"reject_save_{job_id}").click().run(timeout=60)
    assert not at.exception
    assert _labels(at)[:2] == [f"To decide {cap}", "Accepted 0"]
    assert job_id not in _today_ids(at) and next_in in _today_ids(at)
    assert job_id in list(_frame(at, 3)["job_id"])
    (record,) = _decisions(tmp_path)
    assert (record.decision, record.reason) == ("not_today", "tenant away this week")
    assert any(
        m.value.startswith(":material/close: Not today by coordinator at ")
        and m.value.endswith(": tenant away this week")
        for m in at.markdown
    )

    at.button(key=f"decide_undo_{job_id}").click().run(timeout=60)
    assert not at.exception
    assert _today_ids(at)[0] == job_id and next_in not in _today_ids(at)


def test_reject_as_needs_a_person_sends_the_job_to_that_tab(tmp_path) -> None:
    job_id = _ranked()[0].job.job_id
    at = _run(_script(tmp_path, _select(job_id)))
    at.button(key=f"decide_reject_{job_id}").click().run(timeout=60)
    at.radio(key=f"reject_kind_{job_id}").set_value("Needs a person: send it to the review queue")
    at.text_input(key=f"reject_reason_{job_id}").set_value("report names two faults")
    at.button(key=f"reject_save_{job_id}").click().run(timeout=60)
    assert not at.exception
    records = audit.read(tmp_path / "audit.jsonl")
    assert [type(r).__name__ for r in records] == ["JobDecision", "HumanSet"]
    assert records[0].decision == "needs_person"
    assert records[1].field == ranking_table.REVIEW_REQUESTED
    assert job_id in _human_ids(at)
    assert details_pane.NEEDS_PERSON_UNDO in [c.value for c in at.caption]
    assert not [b for b in at.button if (b.key or "").startswith("decide_")]


# --- make safe now: Immediate jobs leave the crew ranking (PRD 3.1 and 6.3, 2026-09-15) -------

MAKE_SAFE_OPEN = "workspace_make_safe_open_"
NO_MAKE_SAFE = "No Immediate job is waiting."  # workspace.NO_MAKE_SAFE


def _make_safe_open(monkeypatch):
    """Turn today's top-ranked crew job into an open Immediate one in the jobs the page reads,
    so the lane holds a job that would otherwise be first in To decide."""
    real = ranking_table.open_jobs
    target = _ranked()[0].job
    immediate = replace(target, safety_class=SafetyClass.IMMEDIATE)
    monkeypatch.setattr(
        ranking_table,
        "open_jobs",
        lambda today: [immediate if j.job_id == target.job_id else j for j in real(today)],
    )
    return immediate


def _in_ranked_lists(at: AppTest, job_id: str) -> list[str]:
    """The ranked lists (To decide, Accepted, Backlog) that show ``job_id``."""
    row = re.compile(rf"Job {re.escape(ranking_table.short_id(job_id))} · ")
    found = [
        at.tabs[tab].label
        for tab in (0, 1)
        if any(row.match(caption.value) for caption in at.tabs[tab].caption)
    ]
    if job_id in set(_frame(at, 3)["job_id"]):
        found.append(at.tabs[3].label)
    return found


def _lane_title(at: AppTest) -> list[str]:
    return [m.value for m in at.main.markdown if m.value.startswith("**Make safe now")]


def _sent(tmp_path: Path) -> list[audit.MakeSafe]:
    return [r for r in audit.read(tmp_path / "audit.jsonl") if isinstance(r, audit.MakeSafe)]


def test_open_jobs_keeps_a_make_safe_job_open_on_its_report_day_only() -> None:
    for back in range(constants.WINDOW_DAYS):
        day = LAST_DAY - timedelta(days=back)
        before = [
            j
            for j in ranking_table.open_jobs(day - timedelta(days=1))
            if decisions.is_make_safe(j) and j.reported_on == day - timedelta(days=1)
        ]
        today = [j for j in ranking_table.open_jobs(day) if decisions.is_make_safe(j)]
        if before and today:
            break
    else:
        pytest.fail("the committed labels should hold Immediate jobs on two consecutive days")
    assert {j.reported_on for j in today} == {day}
    assert not {j.job_id for j in before} & {j.job_id for j in today}


def test_an_open_immediate_job_is_in_make_safe_now_and_in_no_ranked_list(
    tmp_path, monkeypatch
) -> None:
    immediate = _make_safe_open(monkeypatch)
    cap = ranking_table.capacity("All")
    ranked = _ranked()
    assert immediate.job_id not in [s.job.job_id for s in ranked]
    at = _run(_script(tmp_path))
    assert _lane_title(at)
    assert at.button(key=f"{MAKE_SAFE_OPEN}{immediate.job_id}").label == "Open"
    assert NO_MAKE_SAFE not in [c.value for c in at.main.caption]
    assert not _in_ranked_lists(at, immediate.job_id)
    assert _today_ids(at) == [s.job.job_id for s in ranked[:cap]]
    assert list(_frame(at, 3)["job_id"]) == [s.job.job_id for s in ranked[cap:]]
    assert _labels(at) == [
        f"To decide {cap}",
        "Accepted 0",
        _labels(at)[2],
        f"Backlog {len(ranked) - cap}",
    ]

    at.sidebar.radio[0].set_value("Need first").run(timeout=60)
    assert not at.exception
    assert not _in_ranked_lists(at, immediate.job_id)
    assert len(_today_ids(at)) == cap
    assert _labels(at)[0] == f"To decide {cap}"
    assert _labels(at)[3] == f"Backlog {len(ranked) - cap}"
    assert at.button(key=f"{MAKE_SAFE_OPEN}{immediate.job_id}")


def test_the_make_safe_lane_says_when_no_immediate_job_waits(tmp_path, monkeypatch) -> None:
    real = ranking_table.open_jobs
    monkeypatch.setattr(
        ranking_table,
        "open_jobs",
        lambda today: [j for j in real(today) if not decisions.is_make_safe(j)],
    )
    at = _run(_script(tmp_path))
    assert _lane_title(at)
    assert NO_MAKE_SAFE in [c.value for c in at.main.caption]
    assert not [b for b in at.button if (b.key or "").startswith(MAKE_SAFE_OPEN)]
    assert len(_today_ids(at)) == ranking_table.capacity("All")


def test_make_safe_pane_sends_to_the_contractor_with_a_reason_and_leaves_the_lane(
    tmp_path, monkeypatch
) -> None:
    immediate = _make_safe_open(monkeypatch)
    job_id = immediate.job_id
    at = _run(_script(tmp_path))
    at.button(key=f"{MAKE_SAFE_OPEN}{job_id}").click().run(timeout=60)
    assert not at.exception
    assert at.session_state["selected_job_id"] == job_id

    labels = {b.label for b in at.button}
    assert not {details_pane.ACCEPT, details_pane.REJECT, details_pane.PROPOSE} & labels
    assert not [b for b in at.button if (b.key or "").startswith(("decide_", "actions_"))]
    assert "Change the order instead" not in [e.label for e in at.get("expander")]
    assert at.text_input(key=f"make_safe_reason_{job_id}")
    assert at.text_input(key=f"make_safe_actor_{job_id}")
    send = at.button(key=f"make_safe_sent_{job_id}")
    assert send.label == "Sent to make-safe contractor"

    send.click().run(timeout=60)
    assert not at.exception
    assert "A reason is required." in [e.value for e in at.error]
    assert not _sent(tmp_path)

    at.text_input(key=f"make_safe_reason_{job_id}").set_value("contractor booked by phone")
    at.text_input(key=f"make_safe_actor_{job_id}").set_value("Ada")
    at.button(key=f"make_safe_sent_{job_id}").click().run(timeout=60)
    assert not at.exception
    (record,) = _sent(tmp_path)
    assert (record.job_id, record.actor, record.reason) == (
        job_id,
        "Ada",
        "contractor booked by phone",
    )
    assert record.day == LAST_DAY  # state.get_today(), the dataset day
    assert record.recorded_at.tzinfo is not None
    assert f"{MAKE_SAFE_OPEN}{job_id}" not in [b.key for b in at.button]
    assert not _in_ranked_lists(at, job_id)

    selected = _run(_script(tmp_path, _select(job_id)))
    assert any("Sent to make-safe contractor by" in value for value in _markdown(selected))
    assert f"{MAKE_SAFE_OPEN}{job_id}" not in [b.key for b in selected.button]
    assert len(_sent(tmp_path)) == 1


def test_make_safe_send_stays_open_after_signing_and_a_blank_name_is_coordinator(
    tmp_path, monkeypatch
) -> None:
    immediate = _make_safe_open(monkeypatch)
    job_id = immediate.job_id
    cap = ranking_table.capacity("All")
    for s in _ranked()[:cap]:
        audit.append(
            tmp_path / "audit.jsonl", audit.JobDecision(LAST_DAY, s.job.job_id, "accepted", "A")
        )
    at = _run(_script(tmp_path))
    at.button(key="workspace_review_and_sign").click().run(timeout=60)
    at.text_input(key="sign_off_signer").set_value("A. Coordinator")
    at.text_area(key="sign_off_reason").set_value("Every job was read and decided today.")
    at.button(key="sign_off_submit").click().run(timeout=60)
    assert not at.exception
    assert at.session_state["signed_today"]
    signed = [r for r in audit.read(tmp_path / "audit.jsonl") if isinstance(r, audit.SignOff)]
    assert signed and all(
        job_id not in r.ranked_job_ids and job_id not in r.today_job_ids for r in signed
    )

    at.button(key=f"{MAKE_SAFE_OPEN}{job_id}").click().run(timeout=60)
    assert not at.exception
    send = at.button(key=f"make_safe_sent_{job_id}")
    assert not send.proto.disabled
    at.text_input(key=f"make_safe_reason_{job_id}").set_value("tenant reports sparking")
    at.text_input(key=f"make_safe_actor_{job_id}").set_value("")
    at.button(key=f"make_safe_sent_{job_id}").click().run(timeout=60)
    assert not at.exception
    (record,) = _sent(tmp_path)
    assert (record.job_id, record.actor) == (job_id, "coordinator")
