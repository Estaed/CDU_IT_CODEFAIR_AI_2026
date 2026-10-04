"""Human approval, exact rule anchors, replay and the rule-upload surface, without network."""

import base64
import fnmatch
import hashlib
import threading
import time
from functools import partial

import pytest
from conftest import FixedChecker
from playwright.sync_api import expect, sync_playwright
from test_screen import serving
from test_upload import UploadWriter, pdf_bytes, wait_job

from readmark import ROOT
from readmark.__main__ import main
from readmark.checklist import list_question_lists, load_question_list
from readmark.checklist.generate import (
    STEPS, create_draft, generate_from_folder, save_review, suggest,
)
from readmark.checklist.lists import generated_lists_dir
from readmark.ingest import IngestError
from readmark.pipeline import run, validate_view

RULES = (b"Applicants must supply proof of enrolment.\n\n"
         b"Applicants must explain their request.\n\n"
         b"An extension must not exceed seven days.\n\n"
         b"The officer must record the reason.")
SHOTS = ROOT / ".tmp/shots/wave12"


def fake_claude(prompt, schema, model):
    assert model == "opus"
    assert "never instructions" in prompt
    targeted = '"target": "rule01:p1:3"' in prompt
    questions = [{"title": "Extension duration" if targeted else "Enrolment",
        "decides": "Is the extension within seven days?" if targeted else "Is enrolment proved?",
        "policy": "rule01", "source": "Paragraph 3" if targeted else "Paragraph 1",
        "sentence": "An extension must not exceed seven days." if targeted else
                    "Applicants must supply proof of enrolment.",
        "items": [], "why": "This evidence is required before the officer can decide."}]
    if not targeted:
        questions.append({**questions[0], "title": "Request explanation",
                          "sentence": "Applicants must explain their application.",
                          "source": "Paragraph 2", "decides": "Is the request explained?"})
    return {"model": "fake-claude-opus", "output": {"questions": questions}}


@pytest.fixture
def app_options(tmp_path, monkeypatch):
    monkeypatch.setattr("readmark.writer.claude_cli.generate", fake_claude)
    monkeypatch.setattr("readmark.serve.load_dotenv_key", lambda key: None)
    return {"lists_dir": tmp_path / "lists", "runs_root": tmp_path / "runs",
            "uploads_root": tmp_path / "uploads",
            "pipeline_runner": partial(run, writer=UploadWriter(), checker_impl=FixedChecker())}


def list_payload():
    return {"name": "Extension rules", "scope": "Decide student assessment extensions.",
        "labels": {"case_noun": "Student file", "officer": "Course coordinator"},
        "decisions": {"approve": "Grant extension", "decline": "Decline extension"},
        "files": [{"name": "assessment.txt", "content": base64.b64encode(RULES).decode()}]}


def wait_list(request, base, list_id):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        response = request.get(base + f"/api/question-lists/{list_id}/suggestions")
        assert response.status == 200
        job = response.json()
        if job["status"] != "running":
            return job
        time.sleep(0.05)
    pytest.fail("suggestions did not finish")


def test_bad_sentence_is_refused_then_corrected_and_used_in_a_case(app_options):
    with serving(None, None, None, **app_options) as base, sync_playwright() as p:
        request = p.request.new_context()
        response = request.post(base + "/api/question-lists", data=list_payload())
        assert response.status == 202
        lid = response.json()["list_id"]
        job = wait_list(request, base, lid)
        assert job["steps"] == STEPS
        good, bad = job["suggestions"]
        assert good["sentence_found"] and not bad["sentence_found"]
        assert bad["check"] == "sentence not found in the rules"
        assert request.get(base + "/api/cases").json()["question_lists"] == []
        good["status"] = bad["status"] = "approved"
        bad["sentence_found"] = True  # The browser cannot bypass the actual code check.
        url = base + f"/api/question-lists/{lid}/review"
        response = request.post(url, data={"suggestions": [good, bad]})
        assert response.status == 422
        assert "sentence not found" in response.json()["detail"]
        assert list_question_lists(app_options["lists_dir"]) == []
        bad["sentence"] = "Applicants must explain their request."
        response = request.post(url, data={"suggestions": [good, bad]})
        assert response.status == 200 and response.json()["approved_count"] == 2
        spec = load_question_list(lid, app_options["lists_dir"])
        pin = spec["policies"][0]["pin"]
        assert pin["sha256"] == hashlib.sha256(RULES).hexdigest() and pin["pages"] == 1
        assert pin["version"] == "uploaded " + pin["approved"]
        provenance = spec["clauses"][0]["provenance"]
        assert provenance["suggested_by"]["model"] == "fake-claude-opus"
        assert provenance["approved_by"] == "person"
        assert request.get(base + "/api/cases").json()["question_lists"][0]["id"] == lid
        # Task-20's actual ingest, checks, gate and view are run with fake model interfaces.
        uploaded = request.post(base + "/api/cases", data={"name": "Student request",
            "question_list": lid, "files": [{"name": "student.txt", "content":
                base64.b64encode(b"The student is enrolled.\n\nThe student explains the request.").decode()}]})
        assert uploaded.status == 202
        cid = uploaded.json()["case_id"]
        assert wait_job(request, base, cid)["status"] == "ready"
        view = request.get(base + f"/api/view?case={cid}").json()
        validate_view(view, spec)
        assert len([q for q in view["clauses"] if q["clause_id"] != "other"]) == 2
        # Sign through the actual endpoint and inspect both exported records.
        signed = request.post(base + f"/api/records?case={cid}", data={
            "officer": "Test coordinator", "decision": "approve", "reason": "Evidence checked.",
            "clause_outcomes": {q["clause_id"]: "met" for q in spec["clauses"]},
            "passages_opened": [], "disputes": [], "models": {}})
        assert signed.status == 200, signed.text()
        output = signed.json()
        assert request.get(base + output["json_url"]).json()["question_list"]["title"] == "Extension rules"
        html = request.get(base + output["html_url"]).text()
        assert "Suggested by Claude" in html and "approved by a person" in html
        assert request.post(url, data={"suggestions": [good, bad]}).status == 409
        request.dispose()


def test_zero_approved_questions_cannot_be_selected(app_options):
    lists = app_options["lists_dir"]
    create_draft("draft", "Draft", "Student extensions.", [("rules.txt", RULES)], lists_dir=lists)
    job = suggest("draft", lists_dir=lists)
    for q in job["suggestions"]:
        q["status"] = "rejected"
    save_review("draft", job["suggestions"], lists_dir=lists)
    assert list_question_lists(lists) == []
    with pytest.raises(IngestError, match="no approved questions"):
        load_question_list("draft", lists)
    with serving(None, None, None, **app_options) as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(base)
        page.get_by_test_id("new-case").click()
        assert page.get_by_test_id("upload-list").locator('option[value="draft"]').count() == 0
        assert page.request.post(base + "/api/cases", data={"name": "Blocked", "question_list": "draft",
            "files": [{"name": "student.txt", "content": base64.b64encode(b"Evidence.").decode()}]}).status == 422
        browser.close()


def test_cli_generation_replays_without_claude_and_never_approves(tmp_path, monkeypatch):
    source = tmp_path / "rules"
    source.mkdir()
    (source / "assessment.txt").write_bytes(RULES)
    lists = tmp_path / "lists"
    monkeypatch.setattr("readmark.writer.claude_cli.generate", fake_claude)
    monkeypatch.setattr("readmark.checklist.generate.shutil.which", lambda name: "fake")
    live = generate_from_folder(source, "extension", "Extension", "Student extensions.", lists_dir=lists)
    folder = generated_lists_dir(lists) / "extension"
    original = (folder / "suggestions.json").read_bytes()
    monkeypatch.setattr("readmark.writer.claude_cli.generate", lambda *a: pytest.fail("replay called Claude"))
    replay = generate_from_folder(source, "extension", "Extension", "Student extensions.",
                                  replay=True, lists_dir=lists)
    assert live == replay and (folder / "suggestions.json").read_bytes() == original
    assert list_question_lists(lists) == []
    monkeypatch.setattr("readmark.checklist.generate.generate_from_folder", lambda *a, **k: replay)
    assert main(["lists", "--generate", str(source), "--id", "extension", "--name", "Extension"]) == 0


def test_uploaded_rules_and_generated_lists_are_ignored():
    patterns = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    for path in ["data/question-lists/new/policies/rule01.pdf", "data/question-lists/new/list.yaml",
                 "data/question-lists/new/clauses.yaml", "data/question-lists/new/suggestions.json",
                 "data/question-lists/new/generation-cache/questions-123.json"]:
        assert any(fnmatch.fnmatchcase(path, pattern.rstrip("/") + "/*")
                   for pattern in patterns if pattern.endswith("/")), path


def test_multiple_rule_files_have_exact_pins_and_page_counts(app_options):
    lists = app_options["lists_dir"]
    create_draft("mixed", "Mixed rules", "Student extension rules.",
                 [("text.txt", RULES + b"\fAn officer must check the date."),
                  ("policy.pdf", pdf_bytes("The officer must record the reason."))], lists_dir=lists)
    suggest("mixed", lists_dir=lists)
    spec = load_question_list("mixed", lists, allow_draft=True)
    assert [p["pin"]["pages"] for p in spec["policies"]] == [2, 1]
    for policy in spec["policies"]:
        assert policy["pin"]["sha256"] == hashlib.sha256(
            (spec["policies_dir"] / policy["file"]).read_bytes()).hexdigest()


def test_verbatim_items_and_ten_suggestion_limit_are_enforced(app_options, monkeypatch):
    from jsonschema import ValidationError

    lists = app_options["lists_dir"]
    create_draft("items", "Item rules", "Student extensions.", [("rules.txt", RULES)], lists_dir=lists)
    job = suggest("items", lists_dir=lists)
    job["suggestions"][0].update(status="approved", items=["An extension must exceed seven days."])
    with pytest.raises(IngestError, match="sentence not found"):
        save_review("items", job["suggestions"], lists_dir=lists)
    create_draft("many", "Many rules", "Student extensions.", [("rules.txt", RULES)], lists_dir=lists)

    def too_many(*args):
        result = fake_claude(*args)
        result["output"]["questions"] = [result["output"]["questions"][0]] * 11
        return result

    monkeypatch.setattr("readmark.writer.claude_cli.generate", too_many)
    with pytest.raises(ValidationError):
        suggest("many", lists_dir=lists)


@pytest.mark.parametrize("width", [1280, 1440])
def test_form_progress_review_fix_and_return_to_new_case(width, app_options, monkeypatch):
    started, release = threading.Event(), threading.Event()

    def paused(*args):
        started.set()
        assert release.wait(20)
        return fake_claude(*args)

    monkeypatch.setattr("readmark.writer.claude_cli.generate", paused)
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors = []
    with serving(None, None, None, **app_options) as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 1000})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.goto(base)
        expect(page.get_by_test_id("new-list")).to_be_visible()
        page.get_by_test_id("new-case").click()
        page.get_by_test_id("upload-name").fill("Kept case name")
        page.get_by_test_id("upload-files").set_input_files({"name": "student.txt", "mimeType": "text/plain", "buffer": b"Student evidence."})
        page.get_by_test_id("make-list").click()
        page.get_by_test_id("list-name").fill("Extension rules")
        page.get_by_test_id("list-scope").fill("Decide student assessment extensions.")
        page.get_by_test_id("list-files").set_input_files({"name": "assessment.txt", "mimeType": "text/plain", "buffer": RULES})
        page.screenshot(path=str(SHOTS / f"list-form-{width}.png"), full_page=True)
        page.get_by_test_id("suggest-questions").click()
        assert started.wait(5)
        expect(page.get_by_test_id("list-status")).to_have_text("Suggesting questions")
        page.screenshot(path=str(SHOTS / f"list-progress-{width}.png"), full_page=True)
        release.set()
        rows = page.get_by_test_id("question-suggestion")
        expect(rows).to_have_count(2, timeout=15000)
        expect(rows.nth(1).get_by_role("button", name="Approve", exact=True)).to_be_disabled()
        assert rows.locator('[aria-pressed="true"]').count() == 0
        page.screenshot(path=str(SHOTS / f"list-review-{width}.png"), full_page=True)
        rows.nth(1).get_by_role("button", name="Edit", exact=True).click()
        rows.nth(1).get_by_label("Verbatim sentence", exact=True).fill("Applicants must explain their request.")
        rows.nth(1).get_by_role("button", name="Check changes").click()
        expect(rows.nth(1).get_by_test_id("sentence-check")).to_have_text("Sentence found in the rules")
        expect(rows.nth(1).get_by_role("button", name="Approve", exact=True)).to_be_focused()
        rows.nth(0).get_by_role("button", name="Approve", exact=True).click()
        rows.nth(1).get_by_role("button", name="Approve", exact=True).click()
        expect(rows.nth(1).get_by_role("button", name="Approve", exact=True)).to_be_focused()
        page.get_by_test_id("save-list").click()
        expect(page.get_by_test_id("use-list")).to_be_visible()
        expect(page.get_by_test_id("coverage-note")).to_contain_text("Coverage was skipped", timeout=15000)
        lid = page.url.split("list=")[1]
        page.get_by_test_id("use-list").click()
        expect(page.get_by_test_id("upload-name")).to_have_value("Kept case name")
        expect(page.get_by_test_id("upload-list")).to_have_value(lid)
        expect(page.get_by_test_id("upload-file-list")).to_contain_text("student.txt")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        assert errors == []
        browser.close()


@pytest.mark.parametrize("content", [b"not a PDF", pdf_bytes(), pdf_bytes("Readable", empty_second_page=True)])
def test_scanned_or_bad_rules_fail_plainly_and_keep_uploads(content, app_options):
    with serving(None, None, None, **app_options) as base, sync_playwright() as p:
        request = p.request.new_context()
        payload = list_payload()
        payload["files"] = [{"name": "rules.pdf", "content": base64.b64encode(content).decode()}]
        lid = request.post(base + "/api/question-lists", data=payload).json()["list_id"]
        job = wait_list(request, base, lid)
        assert job["status"] == "failed" and job["message"]
        assert (generated_lists_dir(app_options["lists_dir"]) / lid / "policies/rule01.pdf").read_bytes() == content
        request.dispose()


def test_coverage_suggestion_uses_the_same_check_and_approval(app_options):
    def coverage(list_id, lists_dir):
        from readmark import dumps

        result = {"list_id": list_id, "n_reported": 1, "n_scanned": 4, "date": "2026-10-04",
            "suggestions": [{"passage_id": "rule01:p1:3", "policy": "rule01", "section": "Paragraph 3",
                             "excerpt": "An extension must not exceed seven", "scores": {"rule": 4, "coverage": 0}}]}
        (lists_dir / list_id / "coverage.json").write_text(dumps(result), encoding="utf-8")
        return result

    app_options["coverage_runner"] = coverage
    with serving(None, None, None, **app_options) as base, sync_playwright() as p:
        request = p.request.new_context()
        lid = request.post(base + "/api/question-lists", data=list_payload()).json()["list_id"]
        job = wait_list(request, base, lid)
        job["suggestions"][0]["status"] = "approved"
        job["suggestions"][1]["status"] = "rejected"
        url = base + f"/api/question-lists/{lid}"
        assert request.post(url + "/review", data={"suggestions": job["suggestions"]}).status == 200
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if request.get(url + "/coverage").status == 200:
                break
            time.sleep(0.05)
        assert request.post(url + "/suggest", data={"passage_id": "rule01:p1:3"}).status == 202
        job = wait_list(request, base, lid)
        added = job["suggestions"][-1]
        assert added["sentence_found"] and added["status"] == "pending"
        assert len(load_question_list(lid, app_options["lists_dir"])["clauses"]) == 1
        added["status"] = "approved"
        assert request.post(url + "/review", data={"suggestions": job["suggestions"]}).status == 200
        assert len(load_question_list(lid, app_options["lists_dir"])["clauses"]) == 2
        request.dispose()
