"""The case queue and saved officer state, using only temporary records and replay views."""

import hashlib
import json
import shutil

import pytest
from playwright.sync_api import expect, sync_playwright
from test_screen import (
    A0142, DOMAIN_SHOTS, FAST_OPEN, LABELLED_CASES, TIER_SHOTS, question_tiers, serving,
    wait_until_opened,
)

from readmark import ROOT
from readmark import record as rec
from readmark.__main__ import main
from readmark.checklist import case_question_list, load_question_list

SHOTS = ROOT / ".tmp/shots/wave8"


@pytest.fixture
def home_runs(tmp_path):
    runs = tmp_path / "runs"
    # Discover views, so the same suite works when Task-21 adds S-01.
    for source in (ROOT / "runs").glob("*/view.json"):
        # Uploaded cases (U-*) are local, git-ignored data with user-given names; the suite
        # tests the committed cases, so a local upload never turns the gate red.
        if source.parent.name.startswith("U-"):
            continue
        target = runs / source.parent.name
        target.mkdir(parents=True)
        shutil.copyfile(source, target / "view.json")
    return runs


@pytest.mark.parametrize("include_examples", [False, True])
def test_home_discovers_cases_with_or_without_optional_examples(include_examples, home_runs,
                                                               tmp_path):
    subset = tmp_path / "subset"
    subset.mkdir()
    for source in home_runs.glob("*/view.json"):
        spec = load_question_list(case_question_list(source.parent.name))
        if not include_examples and spec.get("labels"):
            continue
        target = subset / source.parent.name
        target.mkdir()
        shutil.copyfile(source, target / "view.json")
    expected = {p.parent.name for p in subset.glob("*/view.json")} - {"stub", "eval"}
    with serving(None, None, None, runs_root=subset) as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(base)
        expect(page.get_by_role("heading", name="All cases", exact=True)).to_be_visible()
        assert set(page.get_by_test_id("home-case").evaluate_all(
            "rows => rows.map(row => row.dataset.case)")) == expected
        browser.close()


@pytest.mark.parametrize("width", [1280, 1440])
def test_home_counts_both_tiers_from_each_replay(width, home_runs):
    with serving(None, None, None, runs_root=home_runs) as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 1000})
        page.goto(base)
        expect(page.get_by_test_id("home-case").first).to_be_visible()
        cases = page.request.get(base + "/api/cases").json()["cases"]
        for case in cases:
            cid = case["case_id"]
            view = json.loads((home_runs / cid / "view.json").read_text(encoding="utf-8"))
            tiers = question_tiers(view)
            needs = [c["title"] for c in view["clauses"] if tiers.get(c["clause_id"]) == "needs"]
            worth = [c["title"] for c in view["clauses"] if tiers.get(c["clause_id"]) == "worth"]
            assert case["flags"] == needs
            assert case["worth_a_look"] == worth
            assert case["required_count"] == len(view["required_reading"])
            page.locator(f'[data-testid="home-case"][data-case="{cid}"]').click()
            expect(page.get_by_test_id("home-tiers")).to_have_text(
                f"{len(needs)} need a look · {len(worth)} worth a look")
            summary = page.get_by_test_id("case-summary")
            expect(summary).to_contain_text(f"{len(view['required_reading'])} required passages")
            flags = summary.locator(".home-flags")
            expect(flags.locator(".task-icon.flag")).to_have_count(len(needs))
            expect(flags.locator(".task-icon.worth")).to_have_count(len(worth))
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            if cid in {"A-0142", "S-01"}:
                TIER_SHOTS.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(TIER_SHOTS / f"{cid}-home-{width}.png"), full_page=True)
        browser.close()


@pytest.mark.parametrize("case_id", LABELLED_CASES)
@pytest.mark.parametrize("width", [1280, 1440])
def test_home_selected_case_and_completed_decision_use_list_words(case_id, width, home_runs):
    spec = load_question_list(case_question_list(case_id))
    words = rec.wording(spec)
    labels, decisions = words["labels"], words["decisions"]
    name = f"{labels['case_noun']} {case_id}"
    with serving(None, None, None, runs_root=home_runs) as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 1000})
        page.goto(base)
        row = page.locator(f'[data-testid="home-case"][data-case="{case_id}"]')
        row.click()
        expect(row).to_contain_text(name)
        expect(page.get_by_test_id("case-summary")).to_contain_text(name)
        expect(page.locator("#serviceDescription")).to_have_text(labels["service"])
        expect(page.locator("#officerLabel")).to_have_text(labels["officer"])
        for surface in (row, page.get_by_test_id("case-summary"), page.get_by_test_id("service-band")):
            assert not any(word.lower() in surface.inner_text().lower() for word in (
                "Applicant file", "Priority housing", "Delegated officer", "Darwin urban"))
        DOMAIN_SHOTS.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(DOMAIN_SHOTS / f"{case_id}-home-{width}.png"), full_page=True)
        page.get_by_test_id("open-case").click()
        expect(page.locator("h1")).to_have_text(name)
        expect(page.get_by_test_id("wait-context")).to_be_hidden()
        # Exercise each saved decision, using only temporary records and the real record builder.
        view = json.loads((home_runs / case_id / "view.json").read_text(encoding="utf-8"))
        for decision, label in decisions.items():
            payload = {
                "decision": decision, "reason": "Review completed against the selected questions.",
                "clause_outcomes": {c["clause_id"]: "cannot_decide" for c in view["clauses"]
                                   if c["clause_id"] != "other"},
                "passages_opened": [{"passage_id": r["passage_id"],
                                     "opened_at": "2026-10-03T04:30:00Z", "seconds_in_view": 3}
                                    for r in view["required_reading"]],
            }
            record = rec.build(payload, view)
            directory = home_runs / case_id / "records"
            for path in directory.glob("*"):
                path.unlink()
            rec.save(record, directory)
            page.goto(base + "/?home=1")
            row = page.get_by_role("region", name="Completed").locator(
                f'[data-case="{case_id}"]')
            expect(row).to_contain_text(name)
            expect(row).to_contain_text(label)
            row.click()
            expect(page.get_by_test_id("case-summary")).to_contain_text(label)
            page.get_by_test_id("open-case").click()
            expect(page.locator("body")).to_contain_text(label)
            expect(page.locator("body")).to_contain_text(name)
        browser.close()


def test_cli_home_default_and_direct_case(monkeypatch):
    apps = []
    monkeypatch.setattr("readmark.serve.uvicorn.run", lambda app, **kwargs: apps.append(app))
    monkeypatch.setattr("sys.argv", ["readmark", "serve"])
    assert main(["serve"]) == 0
    settings = next(r.endpoint for r in apps[-1].routes if r.path == "/api/settings")
    from starlette.requests import Request

    assert settings(Request({"type": "http", "query_string": b""}))["default_case"] is None
    assert main(["serve", "--case", "A-0142"]) == 0
    settings = next(r.endpoint for r in apps[-1].routes if r.path == "/api/settings")
    assert settings(Request({"type": "http", "query_string": b""}))["default_case"] == "A-0142"
    monkeypatch.setattr("sys.argv", ["readmark", "serve", "--case", "stub"])
    assert main(["serve", "--case", "stub"]) == 0
    settings = next(r.endpoint for r in apps[-1].routes if r.path == "/api/settings")
    assert settings(Request({"type": "http", "query_string": b""}))["default_case"] == "stub"


@pytest.mark.parametrize("width", [1280, 1440])
def test_home_lists_groups_titles_pages_and_signed_record(width, home_runs):
    initial = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in home_runs.glob("*/view.json")}
    with serving(None, None, None, runs_root=home_runs) as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 1000})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        page.goto(base)
        expect(page.get_by_role("heading", name="All cases", exact=True)).to_be_visible()
        expect(page.get_by_test_id("new-case")).to_be_enabled()
        expected_ids = {path.parent.name for path in home_runs.glob("*/view.json")}
        expected_ids -= {"stub", "eval"}
        assert set(page.get_by_test_id("home-case").evaluate_all(
            "rows => rows.map(row => row.dataset.case)")) == expected_ids
        for cid in sorted(expected_ids):
            view = json.loads((home_runs / cid / "view.json").read_text(encoding="utf-8"))
            spec = load_question_list(case_question_list(cid))
            row = page.locator(f'[data-testid="home-case"][data-case="{cid}"]')
            expect(row).to_contain_text(spec["title"])
            expect(row).to_contain_text(f"{view['case']['pages']} pages")
            if cid in {"E-01", "E-02", "E-03", "H-01"}:
                expect(page.get_by_role("region", name="Evaluation files").locator(
                    f'[data-case="{cid}"]')).to_have_count(1)
        expect(page.get_by_role("region", name="In progress").locator(
            '[data-case="A-0142"]')).to_contain_text("0 of 8 decided")
        expect(page.get_by_test_id("case-summary")).to_contain_text("Documents (60)")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        SHOTS.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(SHOTS / f"home-in-progress-{width}.png"), full_page=True)
        # Follow the real UI through signing with the short opening clock.
        page.get_by_test_id("open-case").click()
        page.get_by_test_id("intro-dismiss").click()
        for item in A0142["required_reading"]:
            pid = item["passage_id"]
            page.evaluate("cid => selectClause(cid)", item["clause_ids"][0])
            page.evaluate("pid => openPassage(pid)", pid)
            wait_until_opened(page)
        for clause in A0142["clauses"]:
            if clause["clause_id"] == "other":
                continue
            page.evaluate("cid => selectClause(cid)", clause["clause_id"])
            page.get_by_test_id(f"outcome-{clause['clause_id']}-cannot_decide").check()
        page.get_by_test_id("sign-btn").click()
        page.get_by_test_id("decision-request_information").check()
        page.get_by_test_id("reason").fill("Current income evidence is needed.")
        page.get_by_test_id("continue-btn").click()
        page.get_by_test_id("confirm-sign").click()
        expect(page.get_by_test_id("record")).to_be_visible()
        signed = page.evaluate("S.signed.record")
        assert all(o["seconds_in_view"] >= FAST_OPEN for o in signed["passages_opened"])
        page.reload()
        expect(page.get_by_test_id("record")).to_be_visible()
        page.get_by_test_id("home-link").click()
        completed = page.get_by_role("region", name="Completed").locator('[data-case="A-0142"]')
        expect(completed).to_contain_text("Request more information")
        expect(page.get_by_role("region", name="In progress").locator(
            '[data-case="A-0142"]')).to_have_count(0)
        completed.click()
        expect(page.get_by_test_id("open-case")).to_have_text("View record")
        expect(completed).to_contain_text(page.evaluate(
            "stamp => fmtDate(stamp.slice(0, 10))", signed["signed_at"]))
        page.screenshot(path=str(SHOTS / f"home-completed-{width}.png"), full_page=True)
        # Completed state comes from disk, even in a browser with no saved draft.
        fresh = browser.new_page()
        fresh.goto(base + "/?home=1")
        fresh.get_by_role("region", name="Completed").locator('[data-case="A-0142"]').click()
        fresh.get_by_test_id("open-case").click()
        expect(fresh.locator("body")).to_contain_text("Current income evidence is needed.")
        denied = page.request.get(base + f"/api/records/{signed['record_id']}.json?case=E-02")
        assert denied.status == 404
        repeat = page.request.post(base + "/api/records?case=A-0142", data={})
        assert repeat.status == 409
        browser.close()
    assert errors == []
    assert initial == {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in home_runs.glob("*/view.json")}


def test_case_progress_openings_and_disputes_survive_reload_without_leaking(home_runs):
    with serving(None, None, None, runs_root=home_runs) as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 1000})
        page.goto(base + "/?case=A-0142")
        page.get_by_test_id("intro-dismiss").click()
        decisive = [c for c in A0142["clauses"] if c["clause_id"] != "other"]
        for clause in decisive[:2]:
            page.evaluate("cid => selectClause(cid)", clause["clause_id"])
            page.get_by_test_id(f"outcome-{clause['clause_id']}-cannot_decide").check()
        pid = A0142["required_reading"][0]["passage_id"]
        page.evaluate("cid => selectClause(cid)", A0142["required_reading"][0]["clause_ids"][0])
        page.evaluate("pid => openPassage(pid)", pid)
        wait_until_opened(page)
        page.evaluate("S.claimOpen = true; render()")
        page.get_by_role("button", name="This note is wrong").first.click()
        page.get_by_test_id("dispute-reason").fill("This file needs a further check.")
        page.get_by_test_id("dispute-save").click()
        page.get_by_test_id("home-link").click()
        expect(page.locator('[data-case="A-0142"]')).to_contain_text("2 of 8 decided")
        page.locator('[data-case="E-02"]').click()
        page.get_by_test_id("open-case").click()
        expect(page.get_by_test_id("clause-row").first).to_be_visible()
        assert page.evaluate("Object.keys(S.outcomes).length") == 0
        assert page.evaluate("Object.keys(S.disputes).length") == 0
        assert page.evaluate("Object.values(S.opened).filter(o => o.opened_at).length") == 0
        assert page.locator('input[data-outcome]:checked').count() == 0
        page.get_by_test_id("home-link").click()
        page.locator('[data-case="A-0142"]').click()
        page.get_by_test_id("open-case").click()
        expect(page.get_by_test_id("clause-row").first).to_be_visible()
        assert page.evaluate("Object.keys(S.outcomes).length") == 2
        assert page.evaluate("Object.keys(S.disputes).length") == 1
        assert page.evaluate("pid => hasOpened(pid)", pid)
        page.reload()
        expect(page.get_by_test_id("clause-row").first).to_be_visible()
        assert page.evaluate("Object.keys(S.outcomes).length") == 2
        assert page.evaluate("Object.values(S.disputes)[0].reason") == "This file needs a further check."
        assert page.evaluate("pid => hasOpened(pid)", pid)
        invalid = page.request.get(base + "/api/view?case=..%2F..%2F.env")
        assert invalid.status == 404
        browser.close()


def test_policy_dialog_and_passage_cache_follow_each_cases_question_list(
        home_runs, tmp_path, monkeypatch):
    import readmark.serve as server

    text = "A student may request an extension before the assessment is due."
    policy_file = tmp_path / "assessment.txt"
    policy_file.write_text(text, encoding="utf-8", newline="\n")
    alternate = {
        "id": "extension-test", "title": "Assessment extensions", "policies_dir": tmp_path,
        "clauses": [], "policies": [{
            "key": "assessment", "file": "assessment.txt", "title": "Assessment policy",
            "pin": {"sha256": hashlib.sha256(policy_file.read_bytes()).hexdigest(),
                    "version": "1", "approved": "2026-10-03", "pages": 1,
                    "url": "https://example.org/assessment"},
        }],
    }
    original_load = server.load_question_list
    original_selection = server.case_question_list
    monkeypatch.setattr(server, "load_question_list",
                        lambda lid: alternate if lid == alternate["id"] else original_load(lid))
    monkeypatch.setattr(server, "case_question_list",
                        lambda cid: alternate["id"] if cid == "A-0142" else original_selection(cid))
    view_path = home_runs / "A-0142" / "view.json"
    view = json.loads(view_path.read_text(encoding="utf-8"))
    housing_pid = next(pid for pid, source in view["sources"].items()
                       if source["kind"] == "policy" and source["exists"])
    policy_pid = "assessment:p1:1"
    view["sources"][policy_pid] = dict(view["sources"][housing_pid], passage_id=policy_pid,
                                       page=1, doc_title="Assessment policy")
    view_path.write_text(json.dumps(view), encoding="utf-8", newline="\n")
    server._policy_text.cache_clear()
    try:
        with serving(None, None, None, runs_root=home_runs) as base, sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(base + "/?case=A-0142")
            page.get_by_test_id("intro-dismiss").click()
            # A non-housing list without optional wording still uses the original labels.
            expect(page.locator("#caseNoun")).to_have_text(rec.LABELS["case_noun"])
            expect(page.locator("#serviceDescription")).to_have_text(rec.LABELS["service"])
            expect(page.locator("#officerLabel")).to_have_text(rec.LABELS["officer"])
            expect(page.get_by_test_id("wait-context")).to_be_hidden()
            page.get_by_test_id("about-btn").click()
            policies = page.get_by_test_id("about").locator(".pol")
            expect(policies).to_have_text("Assessment policy, version 1, approved 3 Oct 2026")
            expect(page.get_by_test_id("about")).to_contain_text("Assessment extensions")
            page.get_by_test_id("about").get_by_role("button", name="Close", exact=True).click()
            page.evaluate("pid => openPassage(pid)", policy_pid)
            expect(page.get_by_role("dialog", name="Policy passage")).to_contain_text(text)
            assert page.request.get(
                base + f"/api/passages/{housing_pid}?case=A-0142").status == 404
            other = page.request.get(base + "/api/view?case=E-02").json()
            other_pid = next(pid for pid, source in other["sources"].items()
                             if source["kind"] == "policy" and source["exists"])
            assert page.request.get(base + f"/api/passages/{other_pid}?case=E-02").status == 200
            lists = page.request.get(base + "/api/cases").json()["cases"]
            assert next(c for c in lists if c["case_id"] == "A-0142")["question_list"] == {
                "id": "extension-test", "title": "Assessment extensions"}
            page.evaluate("""() => {
                S.view.required_reading = [];
                S.outcomes = Object.fromEntries(decisive().map(c => [c.clause_id, 'met']));
                S.sel = 'signoff'; render();
            }""")
            expect(page.get_by_test_id("form-helper")).to_have_text(
                "Write it so the applicant could read and challenge it.")
            for key, label in rec.DECISIONS.items():
                expect(page.locator("label").filter(has=page.get_by_test_id(
                    f"decision-{key}"))).to_have_text(label)
            browser.close()
    finally:
        server._policy_text.cache_clear()


@pytest.mark.parametrize("width", [1280, 1440])
def test_home_question_list_coverage_opens_policies_without_changing_case_state(width, home_runs):
    from readmark.checklist.coverage import read_coverage

    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in home_runs.rglob("*") if p.is_file()}
    with serving(None, None, None, runs_root=home_runs) as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 1000})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(base)
        section = page.get_by_test_id("question-lists")
        expect(section).to_be_visible()
        expect(section).to_contain_text("Jev suggests these may need a question. A person decides.")
        storage_before = page.evaluate("JSON.stringify(localStorage)")
        shots = ROOT / ".tmp/shots/wave11"
        shots.mkdir(parents=True, exist_ok=True)
        section.scroll_into_view_if_needed()
        page.screenshot(path=str(shots / f"question-lists-{width}.png"), full_page=True)
        for list_id in ("cdu-extension", "nt-priority-housing"):
            coverage = read_coverage(list_id)
            link = section.locator(f'[data-coverage="{list_id}"]')
            expect(link).to_have_text(f"{coverage['n_reported']} policy rules no question covers")
            link.click()
            dialog = page.get_by_test_id("list-coverage")
            expect(dialog).to_be_visible()
            expect(dialog.get_by_test_id("coverage-suggestion")).to_have_count(coverage["n_reported"])
            expect(dialog).to_contain_text(f"{coverage['n_scanned']} paragraphs scanned")
            if list_id == "cdu-extension":
                for number in (74, 78):
                    expect(dialog.get_by_role("heading", name=f"Procedure ({number})", exact=True)).to_have_count(1)
                page.screenshot(path=str(shots / f"cdu-suggestions-{width}.png"))
                for number in (74, 78):
                    rule = dialog.get_by_test_id("coverage-suggestion").filter(
                        has=page.get_by_role("heading", name=f"Procedure ({number})", exact=True))
                    rule.scroll_into_view_if_needed()
                    page.screenshot(path=str(shots / f"cdu-procedure-{number}-{width}.png"))
            suggestion = coverage["suggestions"][0]
            dialog.locator(f'[data-list-policy="{suggestion["passage_id"]}"]').click()
            policy = page.get_by_test_id("coverage-policy")
            expect(policy).to_be_visible()
            spec = load_question_list(list_id)
            if all((spec["policies_dir"] / item["file"]).exists() for item in spec["policies"]):
                expect(policy).to_contain_text(suggestion["excerpt"])
            else:
                expect(policy).to_contain_text("The pinned policy file could not be read")
            policy.get_by_role("button", name="Back to suggestions").click()
            expect(dialog).to_be_visible()
            dialog.get_by_role("button", name="Close", exact=True).click()
            expect(dialog).to_be_hidden()
        assert page.evaluate("JSON.stringify(localStorage)") == storage_before
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        assert page.request.get(base + "/api/question-lists/cdu-extension/passages/priority:p1:1").status == 404
        assert page.request.get(base + "/api/question-lists/unknown/coverage").status == 404
        assert page.request.get(base + "/api/question-lists/cdu-extension/passages/assessment:p999:1").status == 404
        assert errors == []
        browser.close()
    assert before == {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in home_runs.rglob("*") if path.is_file()}
