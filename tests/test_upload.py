"""Uploads exercise real ingest/checks/cache/view with fake models and temporary case folders."""

import base64
import fnmatch
import hashlib
import json
import threading
import time
from functools import partial
from io import BytesIO

import pytest
from conftest import FixedChecker, FixedWriter, fact
from playwright.sync_api import expect, sync_playwright
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from test_checklist import make_tiny_list
from test_screen import FAST_OPEN, serving

from readmark import ROOT
from readmark.checklist import case_question_list, load_question_list
from readmark.ingest import IngestError, case_passages, prepare_upload
from readmark.pipeline import run, validate_view
from readmark.writer.dating import SCHEMA as DATE_SCHEMA

SHOTS = ROOT / ".tmp/shots/wave9"


class UploadWriter(FixedWriter):
    def __init__(self):
        super().__init__([])

    def write(self, case_meta, passages, clauses, policy_by_id):
        return {"facts": [fact(clauses[min(n, len(clauses) - 1)]["clause_id"], p["text"],
                               (p["passage_id"], p["text"])) for n, p in enumerate(passages)]}


class UndatedDater:
    def date_document(self, text):
        return {"date": None, "quote": ""}


@pytest.fixture
def upload_app(tmp_path):
    lists, _, _ = make_tiny_list(tmp_path)
    return {"runs_root": tmp_path / "runs", "uploads_root": tmp_path / "uploads",
            "lists_dir": lists,
            "dater": UndatedDater(),
            "pipeline_runner": partial(run, writer=UploadWriter(), checker_impl=FixedChecker())}


def payload(files=None, name="Extension review"):
    files = files if files is not None else [("enrolment.txt", b"The student is enrolled."),
                                             ("explanation.txt", b"The student explains the request.")]
    return {"name": name, "question_list": "tiny-review",
            "files": [{"name": title, "content": base64.b64encode(content).decode("ascii")}
                      for title, content in files]}


def wait_job(request, base, cid):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        response = request.get(base + f"/api/uploads/{cid}")
        assert response.status == 200
        job = response.json()
        if job["status"] != "running":
            return job
        time.sleep(0.05)
    pytest.fail("upload did not finish")


def pdf_bytes(text=None, empty_second_page=False):
    """One genuinely extractable PDF page; no fixture files or external PDF library needed."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    if text:
        font = DictionaryObject({NameObject("/Type"): NameObject("/Font"),
                                 NameObject("/Subtype"): NameObject("/Type1"),
                                 NameObject("/BaseFont"): NameObject("/Helvetica")})
        page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({
            NameObject("/F1"): writer._add_object(font)})})
        stream = DecodedStreamObject()
        stream.set_data(f"BT /F1 12 Tf 10 250 Td ({text}) Tj ET".encode("ascii"))
        page[NameObject("/Contents")] = writer._add_object(stream)
    if empty_second_page:
        writer.add_blank_page(width=300, height=300)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


@pytest.mark.parametrize("width", [1280, 1440])
def test_two_documents_progress_home_and_highlights(width, upload_app, monkeypatch):
    # Freeze the fake writer only for the screenshot; it never calls Claude or the network.
    started, release = threading.Event(), threading.Event()

    class PausedWriter(UploadWriter):
        def write(self, *args):
            started.set()
            assert release.wait(15), "test did not release fake writer"
            return super().write(*args)

    upload_app["pipeline_runner"] = partial(run, writer=PausedWriter(), checker_impl=FixedChecker())
    monkeypatch.setenv("TYPESAFE_API_KEY", "")
    errors = []
    SHOTS.mkdir(parents=True, exist_ok=True)
    with serving(None, None, None, **upload_app) as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 1000})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(base)
        page.get_by_test_id("new-case").click()
        page.get_by_test_id("upload-name").fill("Extension review")
        expect(page.get_by_test_id("upload-list")).to_have_value("tiny-review")
        files = [{"name": file["name"], "mimeType": "text/plain",
                  "buffer": base64.b64decode(file["content"])} for file in payload()["files"]]
        page.get_by_test_id("upload-files").set_input_files(files)
        expect(page.get_by_test_id("upload-file-list")).to_contain_text("enrolment.txt")
        page.screenshot(path=str(SHOTS / f"new-case-form-{width}.png"), full_page=True)
        page.get_by_test_id("run-checks").click()
        assert started.wait(5)
        expect(page.get_by_test_id("upload-status")).to_have_text("The AI is reading")
        cid = page.url.split("upload=")[1]
        # Refresh reaches the same persisted job, with the uploaded files still visible.
        page.reload()
        expect(page.get_by_test_id("upload-status")).to_have_text("The AI is reading")
        page.screenshot(path=str(SHOTS / f"new-case-progress-{width}.png"), full_page=True)
        release.set()
        expect(page.get_by_test_id("upload-status")).to_have_text("Ready", timeout=15000)
        job = page.request.get(base + f"/api/uploads/{cid}").json()
        assert job["steps"] == ["Splitting into passages", "Reading document dates",
                                "The AI is reading", "Checking quotes", "Second reader", "Ready"]
        assert page.get_by_test_id("upload-steps").locator("li > span:first-child").all_text_contents() == job["steps"]
        page.get_by_role("link", name="All cases", exact=True).click()
        row = page.get_by_role("region", name="In progress").locator(f'[data-case="{cid}"]')
        expect(row).to_contain_text("Extension review")
        expect(row).to_contain_text("0 of 2 decided")
        row.click()
        expect(page.get_by_test_id("case-summary")).to_contain_text("2 pages · 2 documents")
        page.get_by_test_id("open-case").click()
        expect(page.locator("h1")).to_contain_text("Extension review")
        assert page.request.get(base + f"/api/settings?case={cid}").json()["opened_seconds"] == FAST_OPEN
        page.get_by_test_id("intro-dismiss").click()
        if page.get_by_test_id("clean-toggle").count():
            page.get_by_test_id("clean-toggle").click()
        for n, title in enumerate(["enrolment.txt", "explanation.txt"]):
            page.get_by_test_id("clause-row").nth(n).click()
            expect(page.locator("#fileScroll")).to_contain_text(title)
            expect(page.locator("#fileScroll mark")).to_have_count(1)
            assert page.locator('[data-outcome]:checked').count() == 0
        page.screenshot(path=str(SHOTS / f"new-case-review-{width}.png"), full_page=True)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        passages = page.request.get(base + f"/api/case-pages?case={cid}").json()["pages"]
        assert [p["passages"][0]["doc_id"] for p in passages] == ["d01", "d02"]
        assert all(p["passages"][0]["doc_id"] in p["passages"][0]["passage_id"] for p in passages)
        assert case_question_list(cid, case_dir=upload_app["uploads_root"] / cid,
                                  lists_dir=upload_app["lists_dir"]) == "tiny-review"
        # Cache-only review works after the server restarts, without any model runner.
        browser.close()
    with serving(None, None, None, **(upload_app | {"pipeline_runner": None})) as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(base + f"/?case={cid}")
        expect(page.get_by_role("heading", name="Enrolment", exact=True)).to_be_visible()
        assert page.locator('[data-outcome]:checked').count() == 0
        browser.close()
    assert errors == []


@pytest.mark.parametrize("stage", ["writer", "checker"])
def test_model_failure_is_plain_and_keeps_every_original(stage, upload_app):
    class BrokenWriter(UploadWriter):
        def write(self, *args):
            raise RuntimeError("private model details must not appear on screen")

    class BrokenChecker(FixedChecker):
        def check(self, *args):
            raise RuntimeError("private key must not appear on screen")

    upload_app["pipeline_runner"] = partial(run,
        writer=BrokenWriter() if stage == "writer" else UploadWriter(),
        checker_impl=BrokenChecker() if stage == "checker" else FixedChecker())
    with serving(None, None, None, **upload_app) as base, sync_playwright() as p:
        request = p.request.new_context()
        response = request.post(base + "/api/cases", data=payload())
        assert response.status == 202
        cid = response.json()["case_id"]
        job = wait_job(request, base, cid)
        who = "AI reader" if stage == "writer" else "second reader"
        assert job["status"] == "failed"
        assert job["message"] == f"The {who} could not finish; your files are kept."
        assert not request.get(base + "/api/cases").json()["cases"]
        originals = upload_app["uploads_root"] / cid / "originals"
        assert (originals / "d01.txt").read_bytes() == b"The student is enrolled."
        assert (originals / "d02.txt").read_bytes() == b"The student explains the request."
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(base + f"/?upload={cid}")
        expect(page.get_by_test_id("upload-failure")).to_have_text(job["message"])
        expect(page.get_by_test_id("upload-steps")).to_contain_text("Stopped")
        expect(page.get_by_test_id("open-new-case")).to_have_count(0)
        page.get_by_role("link", name="All cases", exact=True).click()
        expect(page.get_by_role("region", name="Checks underway")).to_contain_text("Checks stopped")
        browser.close()
        request.dispose()


@pytest.mark.parametrize("files,message", [
    ([("scan.pdf", pdf_bytes("Visible first page", True))], "A scanned page has no readable text; your files are kept."),
    ([("empty.txt", b"")], "A text page is empty; supply text on every page."),
    ([("broken.pdf", b"not a PDF")], "A document could not be opened as a text PDF or UTF-8 text."),
    ([("not-utf8.txt", b"\xff")], "A document could not be opened as a text PDF or UTF-8 text."),
])
def test_unreadable_pages_keep_files_without_calling_models(files, message, upload_app):
    def forbidden_runner(*args, **kwargs):
        pytest.fail("an unreadable upload reached the pipeline")

    upload_app["pipeline_runner"] = forbidden_runner
    with serving(None, None, None, **upload_app) as base, sync_playwright() as p:
        request = p.request.new_context()
        response = request.post(base + "/api/cases", data=payload(files))
        cid = response.json()["case_id"]
        job = wait_job(request, base, cid)
        assert job["status"] == "failed" and job["message"] == message
        original = next((upload_app["uploads_root"] / cid / "originals").iterdir())
        assert original.read_bytes() == files[0][1]
        request.dispose()


def test_missing_key_fails_before_writer_and_keeps_uploads(upload_app, monkeypatch):
    monkeypatch.setattr("readmark.serve.load_dotenv_key", lambda name: None)
    monkeypatch.setattr("readmark.serve.run", lambda *args, **kwargs: pytest.fail("writer called"))
    upload_app["pipeline_runner"] = None
    with serving(None, None, None, **upload_app) as base, sync_playwright() as p:
        request = p.request.new_context()
        cid = request.post(base + "/api/cases", data=payload()).json()["case_id"]
        job = wait_job(request, base, cid)
        assert job["message"] == "The second reader's key is missing; your files are kept."
        assert len(list((upload_app["uploads_root"] / cid / "originals").iterdir())) == 2
        request.dispose()


def test_two_text_pdfs_are_one_case_with_separate_document_ids(upload_app):
    files = [("enrolment.pdf", pdf_bytes("The student is enrolled.")),
             ("explanation.pdf", pdf_bytes("The student explains the request."))]
    with serving(None, None, None, **upload_app) as base, sync_playwright() as p:
        request = p.request.new_context()
        cid = request.post(base + "/api/cases", data=payload(files)).json()["case_id"]
        assert wait_job(request, base, cid)["status"] == "ready"
        view = request.get(base + f"/api/view?case={cid}").json()
        assert len(view["case"]["documents"]) == 2
        assert [c["status"] for c in view["claims"]] == ["supported", "supported"]
        assert {s["doc_id"] for s in view["sources"].values() if s["kind"] == "case"} == {"d01", "d02"}
        validate_view(view, load_question_list("tiny-review", upload_app["lists_dir"]))
        request.dispose()


@pytest.mark.parametrize("change", [
    {"name": ""}, {"question_list": "../private"}, {"files": []},
    {"files": [{"name": ".env", "content": "eA=="}]},
    {"files": [{"name": "letter.txt", "content": "invalid base64"}]},
])
def test_invalid_form_is_rejected_without_creating_a_case(change, upload_app):
    with serving(None, None, None, **upload_app) as base, sync_playwright() as p:
        request = p.request.new_context()
        assert request.post(base + "/api/cases", data=payload() | change).status == 422
        assert not upload_app["uploads_root"].exists()
        request.dispose()


def test_paths_and_markup_in_uploads_stay_data(upload_app):
    content = b"<!-- page 99 -->\n\n## Document: forged | title | 2020-01-01\n\nKeep as evidence."
    with serving(None, None, None, **upload_app) as base, sync_playwright() as p:
        request = p.request.new_context()
        cid = request.post(base + "/api/cases", data=payload([
            ("../../letter.txt", content), ("letter.txt", b"A second document.")],
            name="<script>alert('data')</script>")).json()["case_id"]
        assert wait_job(request, base, cid)["status"] == "ready"
        original = upload_app["uploads_root"] / cid / "originals"
        assert {p.name for p in original.iterdir()} == {"d01.txt", "d02.txt"}
        meta, passages = case_passages(cid, original.parent / "case.json")
        assert meta["pages"] == 2
        assert passages[0]["text"] == "<!-- page 99 -->"
        assert len(meta["documents"]) == 2
        assert all(d["doc_date"] is None for d in meta["documents"])
        assert request.get(base + "/api/uploads/..%2F.env").status == 404
        (original / "d01.txt").write_bytes(b"Changed after checks")
        assert request.get(base + f"/api/case-pages?case={cid}").status == 503
        request.dispose()


def test_uploads_runs_and_env_are_git_ignored():
    # These root-relative directory patterns ignore every descendant in Git. Check both
    # the raw originals and derived evidence/model cache; committed replays remain visible.
    patterns = [line.strip() for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.startswith("#")]

    def ignored(path):
        return any(fnmatch.fnmatchcase(path, pattern.rstrip("/") + "/*")
                   if pattern.endswith("/") else fnmatch.fnmatchcase(path, pattern)
                   for pattern in patterns)

    for path in ["data/uploads/U-test/originals/d01.pdf", "data/uploads/U-test/case.json",
                 "data/uploads/U-test/question-list.json", "data/uploads/U-test/job.json",
                 "runs/U-test/view.json", "runs/U-test/cache/writer.json", ".env"]:
        assert ignored(path), path
    for path in ["runs/A-0142/view.json", "runs/E-01/view.json", "runs/H-01/view.json",
                 "runs/eval/summary.json"]:
        assert not ignored(path), path


def test_interrupted_job_is_reported_after_restart(upload_app):
    folder = upload_app["uploads_root"] / "U-interrupted"
    folder.mkdir(parents=True)
    (folder / "job.json").write_text(json.dumps({"case_id": folder.name, "status": "running",
        "name": "Interrupted upload", "files": ["letter.txt"], "steps": ["The AI is reading"]}),
        encoding="utf-8")
    (folder / "letter.txt").write_text("Original kept", encoding="utf-8")
    with serving(None, None, None, **upload_app) as base, sync_playwright() as p:
        request = p.request.new_context()
        job = request.get(base + f"/api/uploads/{folder.name}").json()
        assert job["status"] == "failed"
        assert job["message"] == "The checks were interrupted; your files are kept."
        assert (folder / "letter.txt").read_text(encoding="utf-8") == "Original kept"
        request.dispose()


def test_upload_page_numbers_and_hash_pin(tmp_path):
    folder = tmp_path / "upload"
    folder.mkdir()
    files = [("one.txt", b"Page one.\fPage two."), ("two.txt", b"Another document.")]
    docs = []
    for n, (name, content) in enumerate(files, 1):
        (folder / name).write_bytes(content)
        docs.append({"doc_id": f"d{n:02d}", "name": name, "file": name})
    case_file = prepare_upload("U-test", "Test case", docs, folder, dater=UndatedDater())
    meta, passages = case_passages("U-test", case_file)
    assert meta["sha256"] == hashlib.sha256(case_file.read_bytes()).hexdigest()
    assert [p["page"] for p in passages] == [1, 2, 3]
    assert [p["doc_page"] for p in passages] == [1, 2, 1]
    assert [p["passage_id"] for p in passages] == ["U-test-d01:p1:1", "U-test-d01:p2:1", "U-test-d02:p3:1"]
    with pytest.raises(IngestError, match="does not match"):
        case_passages("U-other", case_file)


def test_uploaded_run_replays_byte_identically_without_any_model_call(upload_app, monkeypatch):
    def generate(prompt, schema, model):
        if schema == DATE_SCHEMA:
            return {"model": "fake-claude", "output": {"date": None, "quote": ""}}
        case_file = next(upload_app["uploads_root"].glob("*/case.json"))
        cid = case_file.parent.name
        meta, passages = case_passages(cid, case_file)
        spec = load_question_list("tiny-review", upload_app["lists_dir"])
        return {"model": "fake-claude", "output": UploadWriter().write(meta, passages,
                                                                          spec["clauses"], {})}

    def post(self, body):
        if "relation" in body["questions"]:
            return {"model": "fake-jev", "answers": {
                "relation": {"choice": "supports", "confidence": 0.99},
                "supports": {"noul": 0.99}}}
        return {"model": "fake-jev", "answers": {key: {"score": 0.0}
                                                   for key in body["questions"]}}

    monkeypatch.setattr("readmark.writer.claude_cli.generate", generate)
    monkeypatch.setattr("readmark.jev.JevChecker._post", post)
    upload_app["pipeline_runner"] = run
    upload_app["dater"] = None
    with serving(None, None, None, **upload_app) as base, sync_playwright() as p:
        request = p.request.new_context()
        cid = request.post(base + "/api/cases", data=payload()).json()["case_id"]
        assert wait_job(request, base, cid)["status"] == "ready"
        request.dispose()
    out = upload_app["runs_root"] / cid
    before = {path.relative_to(out).as_posix(): path.read_bytes() for path in out.rglob("*") if path.is_file()}
    assert any(name.startswith("cache/writer-") for name in before)
    assert sum(name.startswith("cache/dating-") for name in before) == 2
    assert any(name.startswith("cache/jev-") for name in before)

    def forbidden(*args, **kwargs):
        pytest.fail("offline replay attempted a model call")

    monkeypatch.setattr("readmark.writer.claude_cli.generate", forbidden)
    monkeypatch.setattr("readmark.jev.JevChecker._post", forbidden)
    monkeypatch.setattr("readmark.ingest.DATA", upload_app["uploads_root"].parent)
    run(cid, replay=True, lists_dir=upload_app["lists_dir"], out_dir=out, audit=False)
    assert before == {path.relative_to(out).as_posix(): path.read_bytes() for path in out.rglob("*") if path.is_file()}


def test_dragging_two_files_uploads_them_together(upload_app):
    with serving(None, None, None, **upload_app) as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(base)
        page.get_by_test_id("new-case").click()
        page.get_by_test_id("upload-name").fill("Dropped documents")
        page.get_by_test_id("upload-drop").evaluate("""el => {
            const data = new DataTransfer();
            data.items.add(new File(['The student is enrolled.'], 'enrolment.txt', {type: 'text/plain'}));
            data.items.add(new File(['The student explains the request.'], 'explanation.txt', {type: 'text/plain'}));
            el.dispatchEvent(new DragEvent('drop', {bubbles: true, dataTransfer: data}));
        }""")
        expect(page.get_by_test_id("upload-file-list").locator("li")).to_have_count(2)
        page.get_by_test_id("run-checks").click()
        expect(page.get_by_test_id("upload-status")).to_have_text("Ready", timeout=15000)
        page.get_by_test_id("open-new-case").click()
        expect(page.locator("h1")).to_contain_text("Dropped documents")
        browser.close()


def test_upload_byte_limit_is_enforced_before_saving(upload_app, monkeypatch):
    monkeypatch.setattr("readmark.serve.MAX_UPLOAD_BYTES", 40)
    with serving(None, None, None, **upload_app) as base, sync_playwright() as p:
        request = p.request.new_context()
        response = request.post(base + "/api/cases", data=payload([("big.txt", b"x" * 41)]))
        assert response.status == 413
        assert not upload_app["uploads_root"].exists()
        # A streamed oversized request is rejected before JSON parsing too.
        response = request.post(base + "/api/cases", data=b"x" * (1024 * 1024 + 100))
        assert response.status == 413
        request.dispose()


def test_missing_writer_cli_keeps_uploads(upload_app, monkeypatch):
    monkeypatch.setattr("readmark.serve.load_dotenv_key", lambda name: "fake")
    monkeypatch.setattr("readmark.serve.shutil.which", lambda name: None)
    monkeypatch.setattr("readmark.serve.run", lambda *args, **kwargs: pytest.fail("writer called"))
    upload_app["pipeline_runner"] = None
    with serving(None, None, None, **upload_app) as base, sync_playwright() as p:
        request = p.request.new_context()
        cid = request.post(base + "/api/cases", data=payload()).json()["case_id"]
        job = wait_job(request, base, cid)
        assert job["status"] == "failed"
        assert job["message"] == "The AI reader is unavailable; your files are kept."
        assert len(list((upload_app["uploads_root"] / cid / "originals").iterdir())) == 2
        request.dispose()


def test_unfinished_view_never_blocks_the_home_list(upload_app):
    # A failed write can leave partial stage JSON; only Ready uploads join the case list.
    cid = "U-partial"
    folder = upload_app["uploads_root"] / cid
    folder.mkdir(parents=True)
    (folder / "job.json").write_text(json.dumps({"case_id": cid, "status": "failed",
        "name": "Incomplete checks", "files": ["letter.txt"], "steps": ["Second reader"],
        "message": "The checks could not finish; your files are kept."}), encoding="utf-8")
    out = upload_app["runs_root"] / cid
    out.mkdir(parents=True)
    (out / "view.json").write_text("{", encoding="utf-8")
    with serving(None, None, None, **upload_app) as base, sync_playwright() as p:
        request = p.request.new_context()
        response = request.get(base + "/api/cases")
        assert response.status == 200
        assert response.json()["cases"] == []
        assert response.json()["uploads"][0]["status"] == "failed"
        request.dispose()
