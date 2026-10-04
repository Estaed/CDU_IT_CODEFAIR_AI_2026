"""Jev's explicit relation reaches required reading and the screen without date/type guesses."""

import json
import shutil

import pytest
from conftest import FixedChecker, FixedWriter, fact, needs_pdfs
from test_screen import serving

from readmark import ROOT, dumps
from readmark.cache import Cache
from readmark.jev import PAIR_VERDICTS, JevChecker
from readmark.pipeline import run

JANUARY, MARCH = "A-0142:p8:3", "A-0142:p23:3"
SHOTS = ROOT / ".tmp/shots/pair-updates"


def test_jev_four_choices_keep_relation_probability_and_date_order(tmp_path):
    checker = JevChecker(Cache(tmp_path, replay=False))
    seen = []

    def fake(body):
        seen.append(body)
        assert tuple(body["questions"]["relation"]["criteria"]) == PAIR_VERDICTS
        assert "earlier" in body["state"]["passage_a"]
        return {"model": "fake-jev", "answers": {"relation": {
            "choice": "updated", "probabilities": {"agree": 0.01, "updated": 0.97,
                                                      "contradict": 0.02, "unrelated": 0}}}}

    checker._post = fake
    a = {"passage_id": "X:p2:1", "doc_date": "2026-03-04", "page": 2, "k": 1,
         "doc_type": "ledger", "doc_title": "later", "text": "Balance $0."}
    b = {**a, "passage_id": "X:p8:1", "doc_date": "2026-01-15", "page": 8,
         "doc_title": "earlier", "text": "Balance $2,400."}
    job = {"clause": {"clause_id": "debts", "title": "Debts", "decides": "Balance"},
           "a": a, "b": b}
    result = checker.compare([job])
    assert result[0]["verdict"] == "updated"
    assert result[0]["a"] == b["passage_id"]
    assert result[0]["probabilities"]["updated"] == 0.97
    checker.cache.replay = True
    assert checker.compare([job]) == result
    assert len(seen) == 1


@needs_pdfs
def test_stub_replays_byte_for_byte_without_any_key_or_live_model(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Offline replay attempted a live model or key lookup")

    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.setattr("readmark.jev.load_dotenv_key", forbidden)
    monkeypatch.setattr("readmark.jev.JevChecker._post", forbidden)
    monkeypatch.setattr("readmark.writer.claude_cli.generate", forbidden)
    original = ROOT / "runs/stub"
    shutil.copytree(original / "cache", tmp_path / "cache")
    for _ in range(2):
        run("stub", replay=True, out_dir=tmp_path)
        for stage in original.glob("*.json"):
            assert (tmp_path / stage.name).read_bytes() == stage.read_bytes()


@needs_pdfs
@pytest.mark.parametrize("relation", ["updated", "contradict"])
@pytest.mark.parametrize("dates", ["dated", "undated", "same-day"])
def test_fake_pair_answer_drives_warning_and_dialog(tmp_path, relation, dates):
    from playwright.sync_api import expect, sync_playwright

    checker = FixedChecker(scores={"elig-debts": {JANUARY: 3, MARCH: 3}},
                           verdicts={f"c01@{MARCH}": ("contradicts", 0.9)},
                           **{relation: [(JANUARY, MARCH)]})
    view = run("A-0142", writer=FixedWriter([
        fact("elig-debts", "The applicant owes $2,400.",
             (JANUARY, "Arrears balance $2,400.00.")),
    ]), checker_impl=checker, out_dir=tmp_path / "run")
    assert view["claims"][0]["contradicted_by"] == [MARCH]
    assert {JANUARY, MARCH} <= {r["passage_id"] for r in view["required_reading"]}
    if dates != "dated":
        for pid in (JANUARY, MARCH):
            view["sources"][pid]["doc_date"] = None if dates == "undated" else "2026-03-04"
    elif relation == "updated":
        # An update can be recorded by different document types; the model answer wins.
        view["sources"][MARCH]["doc_type"] = "letter"
    (tmp_path / "run/view.json").write_text(dumps(view), encoding="utf-8", newline="\n")
    errors = []
    with serving("A-0142", tmp_path / "run", tmp_path / "records") as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(base)
        page.get_by_test_id("intro-dismiss").click()
        page.locator('[data-testid="clause-row"][data-clause="elig-debts"]').click()
        warning = page.get_by_test_id("question-warning")
        if relation == "updated":
            expect(warning).to_contain_text("A later page updates this")
            sentence = ("Page 8 (15 Jan 2026) and page 23 (4 Mar 2026) differ; the later page "
                        "is the newer record. Open both before you decide." if dates == "dated"
                        else "Pages 8 and 23 record a change over time; open both before you decide.")
            expect(warning.locator("p")).to_have_text(sentence)
        else:
            expect(warning).to_contain_text("Two pages disagree")
            expect(warning.locator("p")).to_contain_text("disagree; open both before you decide.")
        assert page.locator('[data-outcome]:checked').count() == 0
        page.get_by_test_id("compare-pages").filter(has_text="Compare pages 8 and 23").click()
        dialog = page.locator("#comparison")
        expect(dialog.get_by_role("heading")).to_have_text(
            f"Pages 8 and 23 {'differ over time' if relation == 'updated' else 'disagree'}")
        if relation == "updated" and dates != "dated":
            expect(dialog).not_to_contain_text("newer")
            expect(dialog).not_to_contain_text("supersede")
        for pid in (JANUARY, MARCH):
            expect(dialog).to_contain_text(view["sources"][pid]["text"])
        browser.close()
    assert errors == []


@pytest.mark.parametrize("width", [1280, 1440])
def test_mixed_pair_relations_keep_each_comparison_and_disagreement(width, tmp_path):
    from playwright.sync_api import expect, sync_playwright

    view = json.loads((ROOT / "runs/A-0142/view.json").read_text(encoding="utf-8"))
    debts = next(c for c in view["clauses"] if c["clause_id"] == "elig-debts")
    update = next(p for p in debts["contradictions"] if p["a"] == JANUARY and p["b"] == MARCH)
    conflict = next(p for p in debts["contradictions"] if p["a"] != JANUARY)
    debts["contradictions"] = [update, {**conflict, "relation": "contradict"}]
    # A disagreement with different dates and matching types must still say disagree.
    view["sources"][conflict["a"]]["doc_type"] = view["sources"][conflict["b"]]["doc_type"]
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "view.json").write_text(dumps(view), encoding="utf-8", newline="\n")
    errors = []
    with serving("A-0142", run_dir, tmp_path / "records") as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(base)
        page.get_by_test_id("intro-dismiss").click()
        page.locator('[data-testid="clause-row"][data-clause="elig-debts"]').click()
        expect(page.get_by_test_id("question-warning")).to_contain_text("Pages in the file disagree")
        expect(page.get_by_test_id("question-warning")).to_contain_text("the newer record")
        expect(page.get_by_test_id("question-warning")).to_contain_text("disagree; open both")
        links = page.get_by_test_id("compare-pages")
        expect(links).to_have_count(2)
        boxes = [link.bounding_box() for link in links.all()]
        assert len({box["x"] for box in boxes}) == 1
        assert boxes[0]["y"] + boxes[0]["height"] <= boxes[1]["y"]
        for i, pair in enumerate(debts["contradictions"]):
            page.evaluate("() => { closePassage(); render(); }")
            before = page.locator("#passageCount").inner_text()
            links.nth(i).click()
            dialog = page.locator("#comparison")
            expect(dialog.get_by_role("heading")).to_have_text(
                f"Pages {view['sources'][pair['a']]['page']} and {view['sources'][pair['b']]['page']} "
                f"{'differ over time' if pair['relation'] == 'updated' else 'disagree'}")
            expect(page.locator("#passageCount")).to_have_text(before)
            for pid in (pair["a"], pair["b"]):
                expect(dialog).to_contain_text(view["sources"][pid]["text"])
            dialog.locator('[data-act="compare-close"]').click()
        assert page.locator('[data-outcome]:checked').count() == 0
        assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
        browser.close()
    assert errors == []


@pytest.mark.parametrize("width", [1280, 1440])
def test_a0142_debts_update_screenshots(width, tmp_path):
    from playwright.sync_api import expect, sync_playwright

    run_dir = ROOT / "runs/A-0142"
    view = json.loads((run_dir / "view.json").read_text(encoding="utf-8"))
    debts = next(c for c in view["clauses"] if c["clause_id"] == "elig-debts")
    assert debts["contradictions"][0]["relation"] == "updated"
    assert {JANUARY, MARCH} <= {r["passage_id"] for r in view["required_reading"]}
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors = []
    with serving("A-0142", run_dir, tmp_path / "records") as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(base)
        page.get_by_test_id("intro-dismiss").click()
        page.locator('[data-testid="clause-row"][data-clause="elig-debts"]').click()
        expect(page.get_by_test_id("question-warning")).to_contain_text("A later page updates this")
        expect(page.get_by_test_id("question-warning")).to_contain_text("the newer record")
        assert page.locator('[data-outcome]:checked').count() == 0
        assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
        page.screenshot(path=str(SHOTS / f"debts-warning-{width}.png"), full_page=True)
        page.get_by_test_id("compare-pages").filter(has_text="Compare pages 8 and 23").click()
        expect(page.locator("#comparison").get_by_role("heading")).to_have_text("Pages 8 and 23 differ over time")
        page.screenshot(path=str(SHOTS / f"debts-comparison-{width}.png"))
        browser.close()
    assert errors == []
