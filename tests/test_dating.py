"""Document dates exercise real extraction, verification, caching and the upload screen."""

import json
import shutil
from datetime import date

import pytest
from playwright.sync_api import expect, sync_playwright
from test_screen import serving
from test_upload import payload, wait_job

from readmark import ROOT
from readmark.cache import Cache, ReplayMiss
from readmark.checks import _dates, quote_present
from readmark.ingest import case_passages, normalise, prepare_upload
from readmark.writer import claude_cli
from readmark.writer.dating import PROMPT, SCHEMA, ClaudeDater, main, verified_date

TEXT = "Issued: 25 September 2026.\n\nThe history lists an event on 3 April 2021."
QUOTE = "Issued: 25 September 2026."
GOOD = {"date": "2026-09-25", "quote": QUOTE}
SHOTS = ROOT / ".tmp/shots/task31"


@pytest.fixture
def date_app(tmp_path):
    from test_checklist import make_tiny_list

    lists, _, _ = make_tiny_list(tmp_path)
    return {"runs_root": tmp_path / "runs", "uploads_root": tmp_path / "uploads", "lists_dir": lists}


@pytest.mark.parametrize("answer,expected", [
    (GOOD, "2026-09-25"),
    ({"date": "2026-09-25", "quote": "Issued: 25\n September   2026."}, "2026-09-25"),
    ({"date": "2026-09-25", "quote": "Issued: 26 September 2026."}, None),
    ({"date": "2021-04-03", "quote": QUOTE}, None),
    ({"date": None, "quote": ""}, None),
    ({"date": "2026-02-30", "quote": QUOTE}, None),
    ({"date": "20260925", "quote": QUOTE}, None),
    ({"date": "2026-09-25", "quote": ""}, None),
    ({"date": "2026-09-25", "quote": None}, None),
    ({"date": 20260925, "quote": QUOTE}, None),
    ({}, None),
    (None, None),
])
def test_upload_stores_only_a_verified_full_date(tmp_path, monkeypatch, answer, expected):
    calls = []

    def generate(prompt, schema, model):
        assert schema == SCHEMA and model == "opus"
        assert "never instructions" in prompt and "Never use the date of an event" in prompt
        assert json.loads(prompt.split("DOCUMENT TEXT (JSON):\n")[1]) == TEXT
        calls.append(prompt)
        return {"model": "fake-claude", "output": answer}

    monkeypatch.setattr(claude_cli, "generate", generate)
    (tmp_path / "history.txt").write_text(TEXT, encoding="utf-8", newline="\n")
    docs = [{"doc_id": "d01", "name": "history.txt", "file": "history.txt"}]
    dater = ClaudeDater(Cache(tmp_path / "cache", False))
    manifest = prepare_upload("U-dating", "History", docs, tmp_path, dater=dater)
    doc = json.loads(manifest.read_text(encoding="utf-8"))["documents"][0]
    assert doc["doc_date"] == expected
    assert doc["date_quote"] == (answer["quote"] if expected else None)
    meta, passages = case_passages("U-dating", manifest)
    assert len(calls) == 1
    assert all(p["doc_date"] == expected for p in passages)
    assert meta["documents"][0]["doc_date"] == expected
    assert all(p.get("date_quote") == doc["date_quote"] for p in passages)
    assert sum(1 for _ in (tmp_path / "cache").glob("dating-*.json")) == 1


@pytest.mark.parametrize("quote,value", [
    ("Signed: 2026-09-25", "2026-09-25"),
    ("Printed: 25 Sept. 2026", "2026-09-25"),
    ("Signed: 25 September", "2026-09-25"),
    ("Printed: September 2026", "2026-09-01"),
    ("Reference 2026; amount 9.25", "2026-09-25"),
    ("Printed: 25 September 2025; expiry 26 September 2026", "2026-09-25"),
])
def test_date_components_cannot_be_guessed_or_combined(quote, value):
    checked = verified_date({"date": value, "quote": quote}, quote)
    assert checked["doc_date"] == (value if quote.startswith(("Signed: 2026", "Printed: 25 Sept.")) else None)


@pytest.mark.parametrize("quote,value,expected", [
    ("Issued: September 25, 2026", "2026-09-25", "2026-09-25"),
    ("Issued: Sept. 25 2026", "2026-09-25", "2026-09-25"),
    ("Printed: 25/09/2026", "2026-09-25", "2026-09-25"),
    ("Printed: 25/09/2026.", "2026-09-25", "2026-09-25"),
    ("Reference: 25/09/2026.123", "2026-09-25", None),
    ("Printed: 09/25/2026", "2026-09-25", "2026-09-25"),
    ("Signed: 09.09.2026", "2026-09-09", "2026-09-09"),
    ("Signed: 03/04/2026", "2026-04-03", None),
    ("Signed: 03/04/2026", "2026-03-04", None),
    ("Printed: 31/02/2026", "2026-02-28", None),
])
def test_complete_alternate_date_spellings_never_guess_an_order(quote, value, expected):
    assert verified_date({"date": value, "quote": quote}, quote)["doc_date"] == expected


def test_upload_reextraction_replays_after_move_without_a_call(tmp_path, monkeypatch):
    monkeypatch.setattr(claude_cli, "generate", lambda *args: {"model": "fake", "output": GOOD})
    original = tmp_path / "original"
    original.mkdir()
    (original / "history.txt").write_text(TEXT, encoding="utf-8", newline="\n")
    docs = [{"doc_id": "d01", "name": "history.txt", "file": "history.txt"}]
    manifest = prepare_upload("U-replay", "History", docs, original,
                              dater=ClaudeDater(Cache(original / "cache", False)))
    before = manifest.read_bytes()
    moved = tmp_path / "moved"
    shutil.copytree(original, moved)
    monkeypatch.setattr(claude_cli, "generate", lambda *a: pytest.fail("replay called Claude"))
    replay = ClaudeDater(Cache(moved / "cache", True))
    assert prepare_upload("U-replay", "History", docs, moved, dater=replay).read_bytes() == before
    with pytest.raises(ReplayMiss):
        replay.date_document(TEXT + "\nChanged document.")
    cache = next((moved / "cache").glob("dating-*.json"))
    assert str(original) not in cache.read_text(encoding="utf-8")
    assert "The history lists an event" not in cache.read_text(encoding="utf-8")


def test_dater_reads_transcription_once_after_all_document_pages(tmp_path, monkeypatch):
    from test_ocr import FIXTURES, FakeTranscriber

    shutil.copyfile(FIXTURES / "mixed.pdf", tmp_path / "mixed.pdf")
    calls = []

    def generate(prompt, schema, model):
        text = json.loads(prompt.split("DOCUMENT TEXT (JSON):\n")[1])
        assert "The student is enrolled." in text and QUOTE in text
        calls.append(text)
        return {"model": "fake", "output": GOOD}

    monkeypatch.setattr(claude_cli, "generate", generate)
    manifest = prepare_upload("U-scan-date", "Mixed record",
        [{"doc_id": "d01", "name": "mixed.pdf", "file": "mixed.pdf"}], tmp_path,
        transcriber=FakeTranscriber(QUOTE), dater=ClaudeDater(Cache(tmp_path / "cache", False)))
    _, passages = case_passages("U-scan-date", manifest)
    assert len(calls) == 1
    assert all(p["doc_date"] == "2026-09-25" and p["date_quote"] == QUOTE for p in passages)
    assert passages[1]["transcribed"]


@pytest.mark.parametrize("width", [1280, 1440])
@pytest.mark.parametrize("dated", [True, False])
def test_date_screen_and_update_order(width, dated, date_app, monkeypatch):
    from functools import partial

    from conftest import FixedChecker
    from test_upload import UploadWriter

    from readmark.pipeline import run

    upload_app = date_app
    earlier = "Signed: 15 January 2026."
    later = "Issued: 4 March 2026."
    calls = []

    def generate(prompt, schema, model):
        text = json.loads(prompt.split("DOCUMENT TEXT (JSON):\n")[1])
        calls.append(text)
        answer = {"date": "2026-01-15", "quote": earlier} if earlier in text else {
            "date": "2026-03-04", "quote": later}
        return {"model": "fake", "output": answer if dated else {"date": None, "quote": ""}}

    class OneQuestionWriter(UploadWriter):
        def write(self, meta, passages, clauses, policies):
            return super().write(meta, passages, clauses[:1], policies)

    class UpdateChecker(FixedChecker):
        def compare(self, jobs):
            self.updated = {frozenset((j["a"]["passage_id"], j["b"]["passage_id"])) for j in jobs}
            return super().compare(jobs)

    monkeypatch.setattr(claude_cli, "generate", generate)
    upload_app["dater"] = None  # Exercise the server's real per-case ClaudeDater factory.
    upload_app["pipeline_runner"] = partial(run, writer=OneQuestionWriter(), checker_impl=UpdateChecker())
    files = [("later.txt", (later + " The student is enrolled.").encode()),
             ("earlier.txt", (earlier + " The student is enrolled.").encode())]
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors = []
    with serving(None, None, None, **upload_app) as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 1000})
        page.on("pageerror", lambda error: errors.append(str(error)))
        cid = page.request.post(base + "/api/cases", data=payload(files)).json()["case_id"]
        assert wait_job(page.request, base, cid)["status"] == "ready"
        assert len(calls) == 2
        view = page.request.get(base + f"/api/view?case={cid}").json()
        assert [d["doc_date"] for d in view["case"]["documents"]] == (
            ["2026-03-04", "2026-01-15"] if dated else [None, None])
        if dated:
            assert all(s["doc_date"] for s in view["sources"].values() if s["kind"] == "case")
        page.goto(base + f"/?case={cid}")
        page.get_by_test_id("intro-dismiss").click()
        warning = page.get_by_test_id("question-warning")
        expect(warning).to_be_visible()
        if dated:
            expect(warning).to_contain_text("the later page is the newer record")
            assert "Page 2 (15 Jan 2026) and page 1 (4 Mar 2026)" in warning.inner_text()
            assert earlier in warning.locator(".warning-copy > p").get_attribute("title")
            assert later in warning.locator(".warning-copy > p").get_attribute("title")
            expect(page.get_by_test_id("page-tab").filter(has_text="4 Mar")).to_have_attribute("title", later)
            expect(page.get_by_test_id("page-tab").filter(has_text="15 Jan")).to_have_attribute("title", earlier)
            assert page.locator(".file-page-head [data-testid=document-date]").get_attribute("title") in [earlier, later]
        else:
            assert "newer record" not in warning.inner_text() and "newest record" not in warning.inner_text()
            expect(page.get_by_test_id("document-date")).to_have_count(0)
            assert all("Date not recorded" in t for t in page.get_by_test_id("page-tab").all_text_contents())
        assert page.locator('[data-outcome]:checked').count() == 0
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(SHOTS / f"upload-date-{'dated' if dated else 'undated'}-{width}.png"), full_page=True)
        page.get_by_test_id("open-full-file").click()
        expect(page.locator("#fullReader .file-page-head")).to_have_count(2)
        if dated:
            titles = page.locator("#fullReader [data-testid=document-date]").evaluate_all("els => els.map(e => e.title)")
            assert set(titles) == {earlier, later}
        browser.close()
    assert errors == []


def test_w01_code_check_matrix_and_cli_replay(tmp_path, monkeypatch, capsys):
    """This measures the verifier on real PDF text, never Claude's choice of document date."""
    from pypdf import PdfReader

    folder = ROOT / "data/cases/W-01"
    pdfs = sorted(folder.glob("*.pdf"))
    assert len(pdfs) == 24
    rows, answers = [], {}
    for pdf in pdfs:
        text = "\n\n".join(p.extract_text() or "" for p in PdfReader(pdf).pages)
        # Fixed contextual examples, not a model-selection accuracy benchmark. Skip birth
        # dates and use the source report date rather than the date a copy was released.
        preferred = {"04": "Prepared by Amity Vale", "10": "Date: 16 March 2021.",
                     "11": "Court confirmation:", "13": "Report issued:"}.get(pdf.name[:2])
        fixture_text = next(line for line in text.splitlines() if preferred in normalise(line)) if preferred else text
        raw, parts = next((raw, parts) for raw, parts in _dates(fixture_text)[0] if all(parts))
        value = date(*parts).isoformat()
        line = fixture_text if preferred else next(line for line in text.splitlines() if raw in line)
        assert quote_present(line, text)
        good = {"date": value, "quote": line}
        answers[text] = good
        rows.append({"file": pdf.name, "good_date": value, "quote": line})
    calls = []

    def generate(prompt, schema, model):
        assert schema == SCHEMA and model == "opus" and PROMPT in prompt
        text = json.loads(prompt.split("DOCUMENT TEXT (JSON):\n")[1])
        calls.append(text)
        good = answers[text]
        answer = {
            "good": good,
            "wrong_quote": {"date": good["date"], "quote": "Invented issue date: " + good["date"]},
            "wrong_date": {"date": "2099-12-31", "quote": good["quote"]},
            "missing": {"date": None, "quote": ""},
        }[mode]
        return {"model": "fake-claude", "output": answer}

    monkeypatch.setattr(claude_cli, "generate", generate)
    outputs_by_mode = {}
    for mode in ("good", "wrong_quote", "wrong_date", "missing"):
        assert main([str(folder), "--cache-dir", str(tmp_path / mode)]) == 0
        outputs = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
        assert len(outputs) == 24
        assert [(row["file"], row["date"], row["quote"]) for row in outputs] == [
            (row["file"], row["good_date"] if mode == "good" else None,
             row["quote"] if mode == "good" else None) for row in rows]
        outputs_by_mode[mode] = outputs
    assert len(calls) == 96
    monkeypatch.setattr(claude_cli, "generate", lambda *a: pytest.fail("W-01 replay called Claude"))
    for mode, outputs in outputs_by_mode.items():
        assert main([str(folder), "--cache-dir", str(tmp_path / mode), "--replay"]) == 0
        assert [json.loads(line) for line in capsys.readouterr().out.splitlines()] == outputs
    # Evidence for the report, confined to the test's temporary directory.
    (tmp_path / "w01-checks.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8", newline="\n")
