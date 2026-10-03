"""The review screen (layout B), headless on the demo file A-0142: the clause list, the case bar's
counters and next action, the linked "before you can sign" list, opening every required passage
one at a time, check your answers, the signed record with opened_at and seconds_in_view per
passage, both exports, and the "Summary under audit" tab fed a fixture in Task-06's shape."""

import html
import json
import re
import socket
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
import uvicorn
from conftest import needs_pdfs

from readmark import ROOT
from readmark import record as rec
from readmark.serve import create_app

STUB_RUN = ROOT / "runs" / "stub"
VIEW = json.loads((STUB_RUN / "view.json").read_text(encoding="utf-8"))
A0142_RUN = ROOT / "runs" / "A-0142"
A0142 = json.loads((A0142_RUN / "view.json").read_text(encoding="utf-8"))

# What the main screen must never show (acceptance): claim ids, model ids, the pilcrow, and raw
# passage ids. "About these checks" is a closed dialog, so its text is not in innerText.
NOT_ON_SCREEN = [re.compile(r"\bc\d{2}\b"), re.compile(r"claude-|jev-", re.I), re.compile("¶"),
                 re.compile(r"[\w-]+:p\d+:\d+")]
STATUS_WORDS = {"Supported", "Contradicted by another passage", "Checker disagrees",
                "Quote not found", "Nothing to check"}


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextmanager
def serving(case_id, run_dir, records_dir):
    """The app on a free port (no shared-device lock needed)."""
    port = _free_port()
    config = uvicorn.Config(create_app(case_id, run_dir=run_dir, records_dir=records_dir),
                            host="127.0.0.1", port=port, log_level="warning")
    srv = uvicorn.Server(config)
    thread = threading.Thread(target=srv.run, daemon=True)
    thread.start()
    deadline = time.time() + 20
    while not srv.started and time.time() < deadline:
        time.sleep(0.05)
    assert srv.started, "server did not start"
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        srv.should_exit = True
        thread.join(timeout=10)


def _cite(view, pid, quote, found=True):
    if found:
        assert quote in view["sources"][pid]["text"], (pid, quote)
    return {"passage_id": pid, "quote": quote, "quote_found": found, "passage_exists": True}


def _claim(cid, clause, text, cites, status, verdict="supports", contradicted_by=()):
    return {"claim_id": cid, "clause_id": clause, "claim": text, "citations": cites,
            "values_missing": [], "contradicted_by": list(contradicted_by), "status": status,
            "required": False,
            "checker": {"claim_id": cid, "verdict": verdict, "probability": 0.9, "supports": None}}


def audit_fixture(view):
    """An ``audit`` block in Task-06's Fixed shape, on A-0142's real passages: one sentence per
    claim status, one sentence that makes no claim, and two facts left out."""
    claims = [
        _claim("a01", "prio-category", "Ms K. and her two children are fleeing family violence.",
               [_cite(view, "A-0142:p51:3", "Ms K. and her two children are fleeing family "
                                            "violence")], "supported"),
        _claim("a02", "elig-debts", "The rent ledger shows arrears of $2,400.",
               [_cite(view, "A-0142:p8:3", "Arrears balance $2,400.00.")], "contradicted",
               verdict="not_enough_information", contradicted_by=["A-0142:p23:3"]),
        _claim("a03", "elig-income", "Her current income statement is on file.",
               [_cite(view, "A-0142:p48:1", "Current income statement received", found=False)],
               "quote_not_found"),
        _claim("a04", "prio-documentation", "The host has offered a stable long-term room.",
               [_cite(view, "A-0142:p34:4", "The host has offered a short stay in Darwin.")],
               "checker_disagrees", verdict="not_enough_information"),
    ]
    sentences = [
        {"sentence_id": "s01", "text": "Ms K. is fleeing family violence with her two children.",
         "claim_ids": ["a01"]},
        {"sentence_id": "s02", "text": "The rent ledger shows arrears of $2,400.",
         "claim_ids": ["a02"]},
        {"sentence_id": "s03", "text": "Her income statement is on file and the host has offered "
                                       "a stable room.", "claim_ids": ["a03", "a04"]},
        {"sentence_id": "s04", "text": "Recommendation: decline.", "claim_ids": []},
    ]
    return {"model": "claude-opus-5-5", "prompt": "Summarise this file.", "created": "2026-10-03",
            "summary": " ".join(s["text"] for s in sentences), "sentences": sentences,
            "claims": claims,
            "omitted": [{"claim_id": "c15", "clause_id": "elig-debts"},
                        {"claim_id": "c25", "clause_id": "prio-category"}]}


# The fixture's sentences, worst claim status first (the screen's rule).
AUDIT_EXPECTED = ["Supported", "Contradicted by another passage", "Quote not found",
                  "Nothing to check"]
STATUS_WORD = {"supported": "Supported", "contradicted": "Contradicted by another passage",
               "checker_disagrees": "Checker disagrees", "quote_not_found": "Quote not found"}
WORST_FIRST = ["contradicted", "quote_not_found", "checker_disagrees", "supported"]


def _norm(text):
    return re.sub(r"\s+", " ", text).strip()


def sentence_word(audit, sentence):
    """The screen's rule, restated: a sentence fares as its worst claim; with no claim there is
    nothing to check."""
    statuses = {c["status"] for c in audit["claims"] if c["claim_id"] in sentence["claim_ids"]}
    return next((STATUS_WORD[s] for s in WORST_FIRST if s in statuses), "Nothing to check")


def check_audit_tab(page, view):
    """The "Summary under audit" tab follows the data. No block (null or absent): a plain empty
    state. A block: every sentence in order with its status as a word (never colour alone), every
    left-out fact listed with its clause, nothing internal on screen, and a sentence's passage
    opening in the source pane with its quote highlighted. Opening is the last step, so the caller
    sees that passage in view."""
    from playwright.sync_api import expect

    page.get_by_test_id("audit-tab").click()
    audit = view.get("audit")
    if not audit:
        expect(page.get_by_test_id("audit-empty")).to_contain_text(
            "No summary was audited for this file")
        expect(page.get_by_test_id("audit-sentence")).to_have_count(0)
        return
    expect(page.get_by_test_id("audit-empty")).to_have_count(0)
    rows = page.get_by_test_id("audit-sentence")
    expect(rows).to_have_count(len(audit["sentences"]))
    shown = rows.evaluate_all("els => els.map((e) => [e.innerText, "
                              "e.querySelector('[data-testid=sentence-status]').innerText])")
    for i, (s, (text, word)) in enumerate(zip(audit["sentences"], shown, strict=True)):
        assert _norm(s["text"]) in _norm(text), (i, s["text"])
        assert word.strip() == sentence_word(audit, s), (i, s["text"], word)
        assert word.strip() in STATUS_WORDS

    omitted = page.get_by_test_id("omitted")
    expect(omitted).to_have_count(len(audit["omitted"]))
    for i, o in enumerate(audit["omitted"]):
        claim = next(c for c in view["claims"] if c["claim_id"] == o["claim_id"])
        clause = next(c for c in view["clauses"] if c["clause_id"] == o["clause_id"])
        expect(omitted.nth(i)).to_contain_text(claim["claim"])
        expect(omitted.nth(i)).to_contain_text(
            "Other facts" if clause["clause_id"] == "other" else clause["title"])
    assert_plain(page)
    assert_no_overflow(page)

    i, cite = next((i, x) for i, s in enumerate(audit["sentences"]) for c in audit["claims"]
                   if c["claim_id"] in s["claim_ids"] for x in c["citations"]
                   if x["quote_found"] and x["passage_exists"])
    rows.nth(i).locator(f'[data-testid="audit-cite"][data-pid="{cite["passage_id"]}"]').first.click()
    source = page.get_by_test_id("source")
    expect(source).to_have_count(1)
    expect(source).to_have_attribute("data-pid", cite["passage_id"])
    assert _norm(cite["quote"]) in _norm(" ".join(source.locator("mark").all_inner_texts()))


def rail_ids(view):
    has_other = any("other" in r["clause_ids"] for r in view["required_reading"])
    return [c["clause_id"] for c in view["clauses"]
            if c["clause_id"] != "other" or c["claim_ids"] or c["missing"] or has_other]


def expected_next(view, sel, opened, outcomes):
    """The screen's next-action rule, restated: from the selected clause on (wrapping), the first
    clause with work left; inside it, unopened flagged passages by rank, then its outcome."""
    ids = rail_ids(view)
    start = ids.index(sel) if sel in ids else 0
    for i in range(len(ids)):
        cid = ids[(start + i) % len(ids)]
        for r in view["required_reading"]:
            if cid in r["clause_ids"] and r["passage_id"] not in opened:
                return f"passage:{r['passage_id']}", cid
        if cid != "other" and cid not in outcomes:
            return f"outcome:{cid}", cid
    return "sign", None


def assert_plain(page):
    text = page.evaluate("document.body.innerText")
    for pattern in NOT_ON_SCREEN:
        found = pattern.search(text)
        assert not found, f"{pattern.pattern!r} on screen: {found.group(0)!r}"


def assert_no_overflow(page):
    extra = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
    assert extra <= 0, f"horizontal overflow of {extra}px"


def test_record_cannot_be_signed_past_the_lock():
    payload = {"decision": "request_information", "reason": "Income evidence missing.",
               "clause_outcomes": {}, "passages_opened": [], "disputes": []}
    with pytest.raises(rec.RecordError) as err:
        rec.build(payload, VIEW)
    problems = " ".join(err.value.problems)
    assert "Set an outcome for" in problems
    if VIEW["required_reading"]:
        assert "Open required passage" in problems


def test_exported_record_uses_one_zone_shows_dispute_text_and_only_the_theme():
    outcomes = {c["clause_id"]: "cannot_decide" for c in A0142["clauses"]
                if c["clause_id"] != "other"}
    payload = {
        "decision": "request_information", "reason": "No current income statement.",
        "clause_outcomes": outcomes,
        # The browser stamps openings in UTC; the server signs in its own zone (ACST here).
        "passages_opened": [{"passage_id": r["passage_id"], "opened_at": "2026-10-03T04:30:05.250Z",
                             "seconds_in_view": 3.2} for r in A0142["required_reading"]],
        "disputes": [{"claim_id": "c15", "reason": "The March statement is the current one.",
                      "at": "2026-10-03T04:31:00.000Z"}],
    }
    acst = timezone(timedelta(hours=9, minutes=30))
    record = rec.build(payload, A0142, now=datetime(2026, 10, 3, 14, 5, 12, tzinfo=acst))
    page = rec.to_html(record)

    # One zone: the UTC openings appear in the signing zone, and no UTC stamp is left.
    assert "14:00:05" in page and "14:01:00" in page and "14:05:12" in page
    assert "04:30:05" not in page and "04:31:00" not in page
    assert not re.search(r"\d{2}:\d{2}:\d{2}(\.\d+)?Z", page)
    assert page.count("UTC+09:30") >= 1

    # A dispute carries the claim's own words, in the record and on the export.
    claim = next(c for c in A0142["claims"] if c["claim_id"] == "c15")["claim"]
    assert record["disputes"][0]["claim"] == claim
    assert record["disputes"][0]["clause"] == "Debts, Eligibility §3.4"
    assert html.escape(claim) in page

    # Its only CSS is the screen's own styling files, verbatim; no inline styles.
    blocks = re.findall(r"<style>(.*?)</style>", page, re.S)
    assert len(blocks) == 1 and blocks[0].strip() == rec.styles().strip()
    assert "web/theme.css" not in page and "style=" not in page
    assert (ROOT / "web" / "theme.css").read_text(encoding="utf-8").strip() in blocks[0]
    assert "¶" not in page and "Page 8, paragraph 3" in page


@needs_pdfs
@pytest.mark.parametrize("width", [1280, 1440])
def test_guided_review_flow_on_a0142(width, tmp_path):
    from playwright.sync_api import expect, sync_playwright

    view = A0142
    required = [r["passage_id"] for r in view["required_reading"]]
    decisive = [c["clause_id"] for c in view["clauses"] if c["clause_id"] != "other"]
    c15 = next(c for c in view["claims"] if c["claim_id"] == "c15")
    errors: list[str] = []
    with serving("A-0142", A0142_RUN, tmp_path) as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(base + "/")
        rows = page.get_by_test_id("clause-row")
        expect(rows).to_have_count(len(rail_ids(view)))
        nxt = page.get_by_test_id("next-action")
        source = page.get_by_test_id("source")

        # First run: the panel explains the job with one passed and one flagged claim from this
        # file; it can be dismissed and brought back.
        intro = page.get_by_test_id("intro")
        expect(intro).to_be_visible()
        expect(intro).to_contain_text("What the AI did")
        expect(intro).to_contain_text("Supported")
        expect(intro).to_contain_text("Checker disagrees")
        assert_plain(page)
        assert_no_overflow(page)
        page.get_by_test_id("intro-dismiss").click()
        expect(intro).to_be_hidden()
        page.get_by_test_id("help-btn").click()
        expect(intro).to_be_visible()
        page.get_by_test_id("intro-dismiss").click()

        # No outcome is pre-filled, and the case bar starts at zero.
        assert page.locator('[data-outcome][aria-checked="true"]').count() == 0
        expect(page.locator("#outcomeCount")).to_have_text("0")
        expect(page.locator("#passageCount")).to_have_text("0")
        expect(page.get_by_test_id("outcome-counter")).to_contain_text(f"Outcomes 0 of {len(decisive)}")
        expect(page.get_by_test_id("passage-counter")).to_contain_text(
            f"Flagged passages 0 of {len(required)} opened")

        # An early "Sign decision" lists what is missing; each item selects its clause.
        page.get_by_test_id("sign-btn").click()
        missing = page.get_by_test_id("missing-item")
        expect(missing).to_have_count(len(decisive))
        expect(page.get_by_test_id("missing-list")).to_contain_text("Debts, Eligibility §3.4")
        assert_plain(page)
        page.locator('[data-testid="missing-item"][data-clause="elig-debts"]').click()
        expect(page.get_by_test_id("clause-detail")).to_have_attribute("data-clause", "elig-debts")
        expect(page.locator('[data-testid="clause-row"][data-clause="elig-debts"]')).to_have_attribute(
            "aria-current", "true")

        # The contradicting pair is in plain words, and the correct March claim is not called false.
        expect(page.get_by_test_id("pairs")).to_contain_text("disagree")
        march = page.get_by_test_id("claim").filter(has_text=c15["claim"])
        expect(march).to_contain_text("Supported")
        expect(march).to_contain_text("Quoted word for word, figures and dates included")
        expect(march).to_contain_text("the second checker agrees")
        assert_plain(page)
        assert_no_overflow(page)

        # Dispute the March claim: a reason is required.
        march.get_by_test_id("dispute-btn").click()
        page.get_by_test_id("dispute-save").click()
        expect(march).to_contain_text("Write a reason")
        page.get_by_test_id("dispute-reason").fill("The March statement is the current record.")
        page.get_by_test_id("dispute-save").click()
        expect(march.get_by_test_id("dispute-saved")).to_contain_text("current record")

        # After an outcome and an opened passage, both counters move and the next action points
        # at the next unresolved item.
        opened: set[str] = set()
        outcomes: dict[str, str] = {}
        sel = "elig-debts"
        expect(nxt).to_have_attribute("data-next", expected_next(view, sel, opened, outcomes)[0])
        page.get_by_test_id("outcome-elig-debts-met").click()
        outcomes["elig-debts"] = "met"
        expect(page.locator("#outcomeCount")).to_have_text("1")
        first = required[0]
        page.locator(f'[data-testid="flagged-item"][data-pid="{first}"]').click()
        opened.add(first)
        expect(source).to_have_count(1)
        expect(source).to_have_attribute("data-pid", first)
        expect(page.locator("#passageCount")).to_have_text("1")
        expect(nxt).to_have_attribute("data-next", expected_next(view, sel, opened, outcomes)[0])
        assert_plain(page)
        assert_no_overflow(page)
        page.wait_for_timeout(300)

        # The policy passage text comes from the pinned PDF, on demand.
        page.get_by_test_id("open-policy").click()
        expect(source).to_contain_text("will not be withheld based on a debt")
        expect(page.locator("#passageCount")).to_have_text("1")

        # Follow the next action to the end: every required passage opens one at a time, and the
        # officer sets every outcome. Half way, an early sign-off is still locked.
        checked_lock = False
        for _ in range(4 * len(required) + 4 * len(decisive)):
            target, cid = expected_next(view, sel, opened, outcomes)
            expect(nxt).to_have_attribute("data-next", target)
            if target == "sign":
                break
            if not checked_lock and len(opened) * 2 >= len(required):
                page.get_by_test_id("sign-btn").click()
                expect(page.get_by_test_id("missing-list")).to_be_visible()
                sel, checked_lock = "signoff", True
                continue
            nxt.click()
            sel = cid
            kind, _, rest = target.partition(":")
            if kind == "passage":
                opened.add(rest)
                expect(source).to_have_count(1)
                expect(source).to_have_attribute("data-pid", rest)
                expect(page.locator("#passageCount")).to_have_text(
                    str(len(opened & set(required))))
                page.wait_for_timeout(300)
            else:
                value = "cannot_decide" if rest == "elig-income" else "met"
                page.get_by_test_id(f"outcome-{rest}-{value}").click()
                outcomes[rest] = value
                expect(page.locator("#outcomeCount")).to_have_text(str(len(outcomes)))
        assert checked_lock and set(required) <= opened and set(decisive) == set(outcomes)
        expect(page.get_by_test_id("passage-counter")).to_contain_text(
            f"Flagged passages {len(required)} of {len(required)} opened")

        # The summary tab shows this file's audit block as it is: each sentence with how it fared,
        # the facts left out, a sentence's passage in the source pane; or, with no block, says so.
        check_audit_tab(page, view)

        # Unlocked: the decision, then check your answers with a Change on each line.
        nxt.click()
        expect(page.get_by_test_id("missing-list")).to_have_count(0)
        expect(page.get_by_test_id("pane-empty")).to_be_visible()
        page.get_by_test_id("continue-btn").click()
        expect(page.get_by_test_id("form-helper")).to_contain_text("Choose a decision")
        page.get_by_test_id("decision-request_information").check()
        page.get_by_test_id("reason").fill("Eligibility §3: no current income statement in the file.")
        page.get_by_test_id("continue-btn").click()
        answers = page.get_by_test_id("check-answers")
        expect(answers).to_contain_text("Request more information")
        expect(answers).to_contain_text("no current income statement")
        expect(answers).to_contain_text(c15["claim"])
        expect(answers.get_by_test_id("change")).to_have_count(2 + len(decisive) + 1)
        assert_plain(page)
        assert_no_overflow(page)
        answers.locator('[data-arg="elig-income"]').click()
        expect(page.get_by_test_id("clause-detail")).to_have_attribute("data-clause", "elig-income")
        expect(nxt).to_have_attribute("data-next", "sign")
        nxt.click()
        expect(answers).to_be_visible()
        # Time on the sign-off view is not time in view: no passage is open there.
        page.wait_for_timeout(2500)
        page.get_by_test_id("confirm-sign").click()
        record_box = page.get_by_test_id("record")
        expect(record_box).to_be_visible()
        expect(record_box).to_contain_text(c15["claim"])
        assert_plain(page)
        assert_no_overflow(page)

        # Locked after signing: outcomes, disputes and openings no longer change anything.
        page.locator('[data-testid="clause-row"][data-clause="elig-debts"]').click()
        expect(page.locator("[data-outcome]:not([disabled])")).to_have_count(0)
        expect(page.get_by_test_id("dispute-btn")).to_have_count(0)
        expect(page.locator('[data-testid="flagged-item"]:not([disabled])')).to_have_count(0)
        nxt.click()
        record = page.request.get(base + page.get_by_test_id("export-json").get_attribute("href")).json()
        export = page.request.get(base + page.get_by_test_id("export-html").get_attribute("href"))
        assert export.ok and "Decision record" in export.text()
        assert html.escape(c15["claim"]) in export.text()
        browser.close()

    assert errors == []
    by_pid = {p["passage_id"]: p for p in record["passages_opened"]}
    assert set(required) <= set(by_pid)
    for p in record["passages_opened"]:
        assert p["opened_at"] and isinstance(p["seconds_in_view"], float)
        assert "¶" not in p["label"]
    seconds = {pid: by_pid[pid]["seconds_in_view"] for pid in required}
    assert all(s > 0 for s in seconds.values()), seconds
    assert max(by_pid[pid]["seconds_in_view"] for pid in required) < 2.5
    assert record["decision"] == "request_information"
    assert record["disputes"][0]["claim_id"] == "c15" and record["disputes"][0]["claim"] == c15["claim"]
    assert {o["clause_id"]: o["outcome"] for o in record["clause_outcomes"]} == outcomes
    assert sorted(f.suffix for f in tmp_path.iterdir()) == [".html", ".json"]


@pytest.mark.parametrize("audit", ["fixture", None, "absent"])
def test_summary_under_audit_tab(audit, tmp_path):
    from playwright.sync_api import expect, sync_playwright

    fixture = audit_fixture(A0142)
    view = dict(A0142, audit=fixture if audit == "fixture" else None)
    if audit == "absent":
        del view["audit"]
    run = tmp_path / "run"
    run.mkdir()
    (run / "view.json").write_text(json.dumps(view), encoding="utf-8")
    errors: list[str] = []
    with serving("A-0142", run, tmp_path / "records") as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(base + "/")
        page.get_by_test_id("intro-dismiss").click()
        page.get_by_test_id("audit-tab").click()
        if audit != "fixture":
            check_audit_tab(page, view)
            # The short empty card must not push the tabs down: with the intro dismissed they
            # start level with the clause list (the taller rail once opened a band above them).
            tabs_top = page.locator(".tabs-row").bounding_box()["y"]
            assert abs(tabs_top - page.locator("#rail").bounding_box()["y"]) < 2, tabs_top
            browser.close()
            assert errors == []
            return

        # Every sentence, in order, with its status as a word (never colour alone).
        sentences = page.get_by_test_id("audit-sentence")
        expect(sentences).to_have_count(len(fixture["sentences"]))
        for i, (s, word) in enumerate(zip(fixture["sentences"], AUDIT_EXPECTED, strict=True)):
            row = sentences.nth(i)
            expect(row).to_contain_text(s["text"])
            status = row.get_by_test_id("sentence-status")
            expect(status).to_have_text(word)
            assert status.inner_text().strip() in STATUS_WORDS
        expect(sentences.nth(1)).to_contain_text(
            "which this claim quotes, disagrees with page 23, paragraph 3, a later record")
        expect(sentences.nth(2)).to_contain_text("Not word for word in this passage")

        # A sentence's passage opens in the source pane, with its quote highlighted.
        sentences.nth(1).get_by_test_id("audit-cite").first.click()
        source = page.get_by_test_id("source")
        expect(source).to_have_attribute("data-pid", "A-0142:p8:3")
        expect(source.locator("mark")).to_have_text("Arrears balance $2,400.00.")
        expect(page.locator("#passageCount")).to_have_text("1")

        # The facts the summary left out, by clause, with their passages.
        omitted = page.get_by_test_id("omitted")
        expect(omitted).to_have_count(2)
        c15 = next(c for c in A0142["claims"] if c["claim_id"] == "c15")
        expect(omitted.first).to_contain_text(c15["claim"])
        expect(omitted.first).to_contain_text("Debts, Eligibility §3.4")
        omitted.first.get_by_test_id("audit-cite").first.click()
        expect(source).to_have_attribute("data-pid", c15["citations"][0]["passage_id"])
        assert_plain(page)
        assert_no_overflow(page)

        # The same data-following check the A-0142 flow runs on the real block.
        check_audit_tab(page, view)

        # The summary's model id sits under "About these checks", not on the tab.
        page.get_by_test_id("about-btn").click()
        expect(page.get_by_test_id("about")).to_contain_text("claude-opus-5-5")
        expect(page.get_by_test_id("about")).to_contain_text("Summarise this file.")
        browser.close()
    assert errors == []
