"""Showcase visibility, neutral intake metadata and sober review details (no model calls)."""

import fnmatch
import hashlib
import json
from unittest.mock import patch

import pytest
from playwright.sync_api import expect, sync_playwright
from pypdf import PdfReader
from starlette.requests import Request
from test_screen import A0142, A0142_RUN, serving

from readmark import ROOT
from readmark.eval.cases import ALL_CASES
from readmark.serve import create_app
from scripts.fetch_wwcc_rules import LOCK, fetch_rules

SHOTS = ROOT / ".tmp/shots/wave13"


def endpoint(app, path):
    return next(route.endpoint for route in app.routes
                if route.path == path and "GET" in route.methods)


def test_only_ready_showcases_are_listed_but_evaluation_cases_are_addressable():
    app = create_app()
    expected = {cid for cid in ("A-0142", "W-01")
                if (ROOT / "runs" / cid / "view.json").exists()}
    # A finished local upload is listed by design; the gate must not depend on what was uploaded.
    expected |= {job.parent.name for job in (ROOT / "data/uploads").glob("U-*/job.json")
                 if (ROOT / "runs" / job.parent.name / "view.json").exists()
                 and json.loads(job.read_text(encoding="utf-8"))["status"] == "ready"}
    assert {c["case_id"] for c in endpoint(app, "/api/cases")()["cases"]} == expected
    assert {"E-01", "E-02", "E-03", "H-01"} <= set(ALL_CASES)
    for cid in ("E-01", "E-02", "E-03", "H-01", "stub"):
        request = Request({"type": "http", "query_string": f"case={cid}".encode()})
        assert endpoint(app, "/api/view")(request)["case"]["case_id"] == cid


def test_w01_joins_home_only_after_a_view_exists(tmp_path):
    root = tmp_path / "runs"
    (root / "W-01").mkdir(parents=True)
    # A temporary view stands in for Task-29's output; this test never makes W-01 a run.
    view = json.loads(json.dumps(A0142))
    view["case"]["case_id"] = "W-01"
    app = create_app(runs_root=root)
    with patch("readmark.serve.case_question_list", return_value="nt-priority-housing"):
        assert endpoint(app, "/api/cases")()["cases"] == []
        (root / "W-01" / "view.json").write_text(json.dumps(view), encoding="utf-8")
        assert [c["case_id"] for c in endpoint(app, "/api/cases")()["cases"]] == ["W-01"]


def test_ochre_files_and_rules_are_pinned():
    folder = ROOT / "data/cases/W-01"
    pdfs = sorted(folder.glob("*.pdf"))
    assert len(pdfs) == 24
    assert sum(len(PdfReader(p).pages) for p in pdfs) == 104
    assert (folder / "facts.csv").is_file() and (folder / "gold.json").is_file()
    note = json.loads((folder / "intake-note.json").read_text(encoding="utf-8"))["intake_note"]
    assert "24 documents, 104 pages" in note and "assistant coach" in note
    patterns = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    pins = json.loads(LOCK.read_text(encoding="utf-8"))
    assert len(pins) == 2
    for name, pin in pins.items():
        relative = f"data/policies/nt-wwcc/{name}"
        assert any(fnmatch.fnmatchcase(relative, p) for p in patterns)
        path = LOCK.parent / name
        if path.exists():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == pin["sha256"]
            assert len(PdfReader(path).pages) == pin["pages"]


def test_rule_download_rejects_changed_response_without_replacing_any_pdf(tmp_path):
    from io import BytesIO

    good = b"%PDF-good"
    pins = {f"rule{n}.pdf": {"url": f"https://example.test/{n}",
                            "sha256": hashlib.sha256(good).hexdigest()} for n in (1, 2)}
    lock = tmp_path / "lock.json"
    lock.write_text(json.dumps(pins), encoding="utf-8")
    for name in pins:
        (tmp_path / name).write_bytes(b"previous pinned file")
    requests = []

    def download(request, timeout):
        requests.append(request)
        return BytesIO(good if len(requests) == 1 else b"%PDF-changed")

    with patch("urllib.request.urlopen", download), pytest.raises(ValueError, match="differs"):
        fetch_rules(tmp_path, lock)
    assert all("Mozilla/5.0" in r.get_header("User-agent") for r in requests)
    assert all((tmp_path / name).read_bytes() == b"previous pinned file" for name in pins)


@pytest.mark.parametrize("width", [1280, 1440])
def test_intake_note_closes_recalls_and_preserves_the_view(width, tmp_path):
    root = tmp_path / "runs"
    (root / "A-0142").mkdir(parents=True)
    (root / "A-0142" / "view.json").write_text(json.dumps(A0142), encoding="utf-8")
    with serving(None, None, tmp_path / "records", runs_root=root) as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 1000})
        page.goto(base)
        expect(page.get_by_test_id("home-case")).to_have_count(1)
        SHOTS.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(SHOTS / f"home-{width}.png"), full_page=True)
        page.get_by_test_id("open-case").click()
        panel = page.get_by_test_id("intake-note")
        expect(panel).to_contain_text("Intake note · Receiving officer")
        expect(panel).to_contain_text("Ms K. left her home")
        assert page.request.get(base + "/api/view?case=A-0142").json() == A0142
        assert page.locator('[data-outcome]:checked').count() == 0
        page.get_by_test_id("intro-dismiss").click()
        page.screenshot(path=str(SHOTS / f"case-intake-{width}.png"), full_page=True)
        page.get_by_test_id("intake-dismiss").focus()
        page.keyboard.press("Enter")
        expect(panel).to_be_hidden()
        expect(page.get_by_test_id("case-search")).to_be_focused()
        page.reload()
        expect(panel).to_be_hidden()
        expect(page.get_by_test_id("intake-recall")).to_be_visible()
        page.get_by_test_id("intake-recall").focus()
        page.keyboard.press("Enter")
        expect(panel).to_be_visible()
        expect(page.get_by_test_id("intake-dismiss")).to_be_focused()
        page.get_by_test_id("intake-dismiss").press("Enter")
        page.screenshot(path=str(SHOTS / f"question-{width}.png"), full_page=True)
        browser.close()


def test_optional_note_does_not_block_cases_without_metadata(tmp_path):
    with serving("stub", ROOT / "runs/stub", tmp_path / "records") as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(base)
        expect(page.get_by_test_id("clause-row").first).to_be_visible()
        expect(page.get_by_test_id("intake-note")).to_be_hidden()
        expect(page.get_by_test_id("intake-recall")).to_be_hidden()
        browser.close()


def test_unavailable_note_is_closable_and_does_not_block_review(tmp_path):
    with serving("A-0142", A0142_RUN, tmp_path / "records") as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.route("**/api/intake-note*", lambda route: route.fulfill(
            status=503, content_type="application/json", body='{"detail":"Unavailable"}'))
        page.goto(base)
        panel = page.get_by_test_id("intake-note")
        expect(panel).to_contain_text("You can still review this file")
        expect(page.get_by_test_id("clause-row").first).to_be_visible()
        panel.get_by_role("button", name="Close intake note").click()
        expect(panel).to_be_hidden()
        expect(page.get_by_test_id("case-search")).to_be_focused()
        browser.close()


def test_one_page_uses_singular_and_duplicate_tags_keep_all_quote_targets(tmp_path):
    with serving("A-0142", A0142_RUN, tmp_path / "records") as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(base)
        page.get_by_test_id("intro-dismiss").click()
        assert page.evaluate("pageCount(1)") == "1 page"
        assert page.evaluate("pageCount(2)") == "2 pages"
        page.evaluate("""() => {
          const p = S.pages[0].passages[0];
          S.fullFile = true;
          S.annotations = [1, 2].map(n => ({id: `duplicate-${n}`, pid: p.passage_id,
            cid: S.sel, quote: p.text.slice(0, 30), kind: n === 1 ? 'quote' : 'pair',
            claimIds: [], flagged: n === 1}));
          renderReader();
        }""")
        labels = page.locator('[data-testid="highlight-label"][data-evidence~="duplicate-1"]')
        expect(labels).to_have_count(1)
        assert labels.get_attribute("data-evidence") == "duplicate-1 duplicate-2"
        page.evaluate("openAnnotation('duplicate-2')")
        expect(page.locator('[data-testid="highlight-label"][aria-current="true"]')).to_have_count(1)
        assert page.evaluate("S.current.annotation") == "duplicate-2"
        browser.close()
