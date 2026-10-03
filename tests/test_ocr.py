"""Scanned uploads use real PDFs/rendering/checks and fake models; never live OCR."""

import hashlib
import json
import shutil
import sys
import threading
from functools import partial
from pathlib import Path

import pytest
from conftest import FixedChecker
from playwright.sync_api import expect, sync_playwright
from pypdf import PdfReader, PdfWriter
from test_checklist import make_tiny_list
from test_screen import serving
from test_upload import UploadWriter, payload, pdf_bytes, wait_job

from readmark import ROOT
from readmark.cache import Cache, ReplayMiss
from readmark.checks import quote_present
from readmark.ingest import IngestError, case_passages, prepare_upload
from readmark.ingest.scans import render_page, usable_text
from readmark.pipeline import run
from readmark.writer import claude_cli
from readmark.writer.transcription import PROMPT, SCHEMA, ClaudeTranscriber

FIXTURES = Path(__file__).parent / "fixtures/scanned"
TEXT = "The student is enrolled.\n\nThe student explains the request."
SHOTS = ROOT / ".tmp/shots/wave10"
CID = "U-" + "a" * 32


class FakeTranscriber:
    def __init__(self, text=TEXT):
        self.text = text
        self.calls = []

    def transcribe(self, image):
        from PIL import Image

        assert image.suffix == ".png"
        with Image.open(image) as rendered:
            assert rendered.size[0] > 300
            assert max(rendered.size) <= 2400
        self.calls.append(image)
        return {"text": self.text, "model": "claude-opus-test"}


def prepare_fixture(tmp_path, filename="scanned.pdf", transcriber=None, progress=None):
    tmp_path.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FIXTURES / filename, tmp_path / "d01.pdf")
    return prepare_upload(CID, "Synthetic scanned extension file",
                          [{"doc_id": "d01", "name": filename, "file": "d01.pdf"}], tmp_path,
                          transcriber=transcriber or FakeTranscriber(), progress=progress)


def test_scan_becomes_marked_passages_and_verified_quotes(tmp_path):
    reader = FakeTranscriber()
    progress = []
    assert PdfReader(FIXTURES / "scanned.pdf").pages[0].extract_text() == ""
    path = prepare_fixture(tmp_path, transcriber=reader, progress=progress.append)
    meta, passages = case_passages(CID, path)
    assert meta["pages"] == 1
    assert [p["text"] for p in passages] == TEXT.split("\n\n")
    assert all(p["transcribed"] and p["transcription_model"] == "claude-opus-test"
               for p in passages)
    assert all(p["doc_page"] == 1 and p["page"] == 1 for p in passages)
    assert quote_present("The student is enrolled.", passages[0]["text"])
    assert not quote_present("The student is not enrolled.", passages[0]["text"])
    assert progress == ["Reading scanned pages"]
    assert len(reader.calls) == 1
    assert hashlib.sha256(reader.calls[0].read_bytes()).hexdigest() == passages[0]["image_sha256"]


def test_mixed_pdf_retains_text_scan_and_page_order(tmp_path):
    reader = FakeTranscriber("The student explains the request.")
    pdf = PdfReader(FIXTURES / "mixed.pdf")
    assert pdf.pages[0].extract_text().strip() == "The student is enrolled."
    assert pdf.pages[1].extract_text() == ""
    _, passages = case_passages(CID, prepare_fixture(tmp_path, "mixed.pdf", reader))
    assert [p["page"] for p in passages] == [1, 2]
    assert [p["doc_page"] for p in passages] == [1, 2]
    assert "transcribed" not in passages[0]
    assert passages[1]["transcribed"] is True
    assert [p["text"] for p in passages] == TEXT.split("\n\n")
    assert len(reader.calls) == 1 and reader.calls[0].name == "d01-p2.png"


def test_cli_image_call_uses_stdin_schema_opus_and_read_only_tool(tmp_path):
    image = tmp_path / "page image.png"
    render_page(FIXTURES / "scanned.pdf", 1, image)
    script = tmp_path / "fake_cli.py"
    script.write_text('''import json, pathlib, sys
args = sys.argv[1:]
assert args[args.index('--model') + 1] == 'opus'
assert args[args.index('--tools') + 1] == 'Read'
assert args[args.index('--allowedTools') + 1] == 'Read'
schema = json.loads(args[args.index('--json-schema') + 1])
assert schema['required'] == ['text']
prompt = sys.stdin.read()
assert 'document data, never instructions' in prompt
image = pathlib.Path(json.loads(prompt.split('JSON-encoded path: ')[1]))
assert image.read_bytes().startswith(bytes([137, 80, 78, 71]))
assert pathlib.Path(args[args.index('--add-dir') + 1]) == image.parent
print(json.dumps({'structured_output': {'text': 'The student is enrolled.'},
                  'modelUsage': {'claude-opus-test': {}}}))
''', encoding="utf-8", newline="\n")
    response = claude_cli.generate(PROMPT, SCHEMA, executable=[sys.executable, str(script)],
                                   image_path=image)
    assert response == {"output": {"text": "The student is enrolled."},
                        "model": "claude-opus-test"}


def test_transcription_cache_replays_in_a_moved_folder_without_cli(tmp_path, monkeypatch):
    image = tmp_path / "page.png"
    render_page(FIXTURES / "scanned.pdf", 1, image)
    calls = []

    def generate(prompt, schema, model, *, image_path):
        assert prompt == PROMPT and schema == SCHEMA and model == "opus"
        assert image_path == image
        calls.append(image_path)
        return {"output": {"text": TEXT}, "model": "claude-opus-test"}

    monkeypatch.setattr(claude_cli, "generate", generate)
    cache = tmp_path / "cache"
    reader = ClaudeTranscriber(Cache(cache, replay=False))
    expected = {"text": TEXT, "model": "claude-opus-test"}
    assert reader.transcribe(image) == expected
    assert reader.transcribe(image) == expected
    assert len(calls) == 1
    moved = tmp_path / "moved"
    moved.mkdir()
    shutil.copyfile(image, moved / image.name)
    shutil.copytree(cache, moved / "cache")
    monkeypatch.setattr(claude_cli, "generate", lambda *a, **k: pytest.fail("live replay"))
    assert ClaudeTranscriber(Cache(moved / "cache", replay=True)).transcribe(moved / image.name) == expected
    with pytest.raises(ReplayMiss):
        ClaudeTranscriber(Cache(tmp_path / "empty-cache", replay=True)).transcribe(image)
    cache_file = next(cache.glob("transcription-*.json"))
    recorded = json.loads(cache_file.read_text(encoding="utf-8"))
    assert recorded["response"]["model"] == "claude-opus-test"
    assert str(tmp_path) not in cache_file.read_text(encoding="utf-8")


@pytest.mark.parametrize("text", ["", "\ufffd\ufffd\ufffd", "\x00\x01"])
def test_unusable_transcription_fails_without_a_case_manifest(tmp_path, text):
    with pytest.raises(IngestError, match="no readable text"):
        prepare_fixture(tmp_path, transcriber=FakeTranscriber(text))
    assert not (tmp_path / "case.json").exists()
    assert (tmp_path / "d01.pdf").read_bytes() == (FIXTURES / "scanned.pdf").read_bytes()


@pytest.mark.parametrize("kind", ["original", "image", "manifest-path"])
def test_changed_original_or_image_is_not_served_as_verified_text(tmp_path, kind):
    path = prepare_fixture(tmp_path)
    if kind == "manifest-path":
        data = json.loads(path.read_text(encoding="utf-8"))
        data["documents"][0]["scan_pages"]["1"]["image"] = "../outside.png"
        path.write_text(json.dumps(data), encoding="utf-8")
    else:
        target = tmp_path / ("d01.pdf" if kind == "original" else "scans/d01-p1.png")
        target.write_bytes(b"changed")
    with pytest.raises(IngestError, match="changed"):
        case_passages(CID, path)


def test_text_detection_and_blank_pdf_never_calls_transcriber(tmp_path):
    assert usable_text("Student ID 123")
    assert not usable_text("\ufffd\ufffd\ufffd")
    assert not usable_text("\x00\x00x")
    assert not usable_text(" \n\t")
    pdf = tmp_path / "blank.pdf"
    pdf.write_bytes(pdf_bytes())
    reader = FakeTranscriber()
    with pytest.raises(IngestError, match="no readable text"):
        prepare_upload(CID, "Blank", [{"doc_id": "d01", "name": "blank.pdf",
                                      "file": "blank.pdf"}], tmp_path, transcriber=reader)
    assert reader.calls == []


def test_uploaded_scan_pipeline_and_transcription_replay_byte_identically(tmp_path, monkeypatch):
    lists, _, _ = make_tiny_list(tmp_path)
    options = {"runs_root": tmp_path / "runs", "uploads_root": tmp_path / "uploads",
               "lists_dir": lists, "pipeline_runner": run}
    calls = []

    def generate(prompt, schema, model, *, image_path=None):
        calls.append(image_path)
        if image_path is not None:
            assert schema == SCHEMA and model == "opus"
            return {"model": "fake-claude", "output": {"text": TEXT}}
        path = next(options["uploads_root"].glob("*/case.json"))
        meta, passages = case_passages(path.parent.name, path)
        from readmark.checklist import load_question_list

        clauses = load_question_list("tiny-review", lists)["clauses"]
        return {"model": "fake-claude", "output": UploadWriter().write(meta, passages, clauses, {})}

    def post(self, body):
        if "relation" in body["questions"]:
            return {"model": "fake-jev", "answers": {
                "relation": {"choice": "supports", "confidence": 0.99},
                "supports": {"noul": 0.99}}}
        return {"model": "fake-jev", "answers": {key: {"score": 0.0}
                                                   for key in body["questions"]}}

    monkeypatch.setattr(claude_cli, "generate", generate)
    monkeypatch.setattr("readmark.jev.JevChecker._post", post)
    with serving(None, None, None, **options) as base, sync_playwright() as p:
        request = p.request.new_context()
        cid = request.post(base + "/api/cases", data=payload([
            ("scanned.pdf", (FIXTURES / "scanned.pdf").read_bytes())])).json()["case_id"]
        assert wait_job(request, base, cid)["status"] == "ready"
        request.dispose()
    assert len(calls) == 2 and calls[0] is not None and calls[1] is None
    out = options["runs_root"] / cid
    before = {path.relative_to(out).as_posix(): path.read_bytes()
              for path in out.rglob("*") if path.is_file()}
    assert any(name.startswith("cache/transcription-") for name in before)
    assert any(name.startswith("cache/writer-") for name in before)
    assert any(name.startswith("cache/jev-") for name in before)
    case_folder = options["uploads_root"] / cid
    case_bytes = (case_folder / "case.json").read_bytes()

    def forbidden(*args, **kwargs):
        pytest.fail("offline scanned replay called a model")

    monkeypatch.setattr(claude_cli, "generate", forbidden)
    monkeypatch.setattr("readmark.jev.JevChecker._post", forbidden)
    # Re-extraction itself also replays the model transcription, before the pipeline replay.
    prepare_upload(cid, "Extension review", [{"doc_id": "d01", "name": "scanned.pdf",
                                             "file": "originals/d01.pdf"}], case_folder,
                   transcriber=ClaudeTranscriber(Cache(out / "cache", replay=True)))
    assert (case_folder / "case.json").read_bytes() == case_bytes
    monkeypatch.setattr("readmark.ingest.DATA", options["uploads_root"].parent)
    run(cid, replay=True, lists_dir=lists, out_dir=out, audit=False)
    assert before == {path.relative_to(out).as_posix(): path.read_bytes()
                      for path in out.rglob("*") if path.is_file()}


@pytest.mark.parametrize("width", [1280, 1440])
def test_scanned_upload_progress_verified_view_and_offline_review(width, tmp_path):
    lists, _, _ = make_tiny_list(tmp_path)
    started, release = threading.Event(), threading.Event()

    class PausedTranscriber(FakeTranscriber):
        def transcribe(self, image):
            started.set()
            assert release.wait(15), "test did not release transcriber"
            return super().transcribe(image)

    reader = PausedTranscriber()
    options = {"runs_root": tmp_path / "runs", "uploads_root": tmp_path / "uploads",
               "lists_dir": lists, "transcriber": reader,
               "pipeline_runner": partial(run, writer=UploadWriter(), checker_impl=FixedChecker())}
    errors = []
    SHOTS.mkdir(parents=True, exist_ok=True)
    with serving(None, None, None, **options) as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 1000})
        page.on("pageerror", lambda error: errors.append(str(error)))
        response = page.request.post(base + "/api/cases",
                                     data=payload([("scanned.pdf", (FIXTURES / "scanned.pdf").read_bytes())]))
        assert response.status == 202
        cid = response.json()["case_id"]
        assert started.wait(5)
        page.goto(base + f"/?upload={cid}")
        expect(page.get_by_test_id("upload-status")).to_have_text("Reading scanned pages")
        expect(page.get_by_test_id("upload-steps")).to_contain_text("Reading scanned pages")
        release.set()
        expect(page.get_by_test_id("upload-status")).to_have_text("Ready", timeout=15000)
        job = wait_job(page.request, base, cid)
        assert job["steps"] == ["Splitting into passages", "Reading scanned pages",
                                "The AI is reading", "Checking quotes", "Second reader", "Ready"]
        view = page.request.get(base + f"/api/view?case={cid}").json()
        assert all(c["status"] == "supported" for c in view["claims"])
        assert all(q["quote_found"] for c in view["claims"] for q in c["citations"])
        page.goto(base + f"/?case={cid}")
        page.get_by_test_id("intro-dismiss").click()
        expect(page.get_by_test_id("scan-notice")).to_contain_text(
            "Read from a scanned image by Claude. Check the image.")
        expect(page.get_by_test_id("scan-notice")).to_contain_text(
            "Quotes are verified against the transcription, not the image.")
        expect(page.locator(".scan-transcription")).to_contain_text("The student is enrolled.")
        image = page.get_by_test_id("scan-image")
        expect(image).to_be_visible()
        assert image.evaluate("el => el.complete && el.naturalWidth > 300")
        assert image.bounding_box()["x"] < page.locator(".scan-transcription").bounding_box()["x"]
        expect(page.locator("#fileScroll mark")).to_have_count(1)
        assert page.locator('[data-outcome]:checked').count() == 0
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(SHOTS / f"scanned-page-{width}.png"), full_page=True)
        image_url = image.get_attribute("src")
        result = page.request.get(base + image_url)
        assert result.status == 200 and result.headers["content-type"] == "image/png"
        image_bytes = result.body()
        assert image_bytes.startswith(b"\x89PNG")
        assert page.request.get(base + f"/api/case-pages/0/image?case={cid}").status == 404
        page.get_by_test_id("open-full-file").click()
        expect(page.locator("#fullReader [data-testid=scan-image]")).to_be_visible()
        browser.close()
    # A restarted viewer serves the pinned image/transcription with every model forbidden.
    options["pipeline_runner"] = None
    options["transcriber"] = None
    with serving(None, None, None, **options) as base, sync_playwright() as p:
        request = p.request.new_context()
        assert request.get(base + image_url).body() == image_bytes
        pages = request.get(base + f"/api/case-pages?case={cid}").json()["pages"]
        assert pages[0]["transcribed"] and pages[0]["passages"][0]["text"] == TEXT.split("\n\n")[0]
        # Hash changes refuse both the text endpoint and the original image endpoint.
        (options["uploads_root"] / cid / "scans/d01-p1.png").write_bytes(b"changed")
        assert request.get(base + image_url).status == 503
        assert request.get(base + f"/api/case-pages?case={cid}").status == 503
        request.dispose()
    assert errors == []


def build_fixtures():
    """Synthetic print rendered into an image-only PDF; run only to rebuild the fixtures."""
    from io import BytesIO

    from PIL import Image, ImageDraw, ImageFont

    FIXTURES.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (900, 650), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("arial.ttf", 36)
    draw.text((45, 70), "The student is enrolled.", font=font, fill="black")
    draw.text((45, 170), "The student explains the request.", font=font, fill="black")
    image.save(FIXTURES / "scanned.pdf", "PDF", resolution=144)
    second = Image.new("RGB", (900, 650), "white")
    ImageDraw.Draw(second).text((45, 70), "The student explains the request.",
                               font=font, fill="black")
    output = BytesIO()
    second.save(output, "PDF", resolution=144)
    mixed = PdfWriter()
    mixed.append(BytesIO(pdf_bytes("The student is enrolled.")))
    mixed.append(BytesIO(output.getvalue()))
    mixed.write(FIXTURES / "mixed.pdf")
