"""Answer-key review, full case pages, opening/time/lock and both record exports."""

import csv
import hashlib
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

from readmark import ROOT, dumps
from readmark import record as rec
from readmark.serve import create_app
from readmark.ingest import case_passages

STUB_RUN = ROOT / "runs" / "stub"
VIEW = json.loads((STUB_RUN / "view.json").read_text(encoding="utf-8"))
A0142_RUN = ROOT / "runs" / "A-0142"
A0142 = json.loads((A0142_RUN / "view.json").read_text(encoding="utf-8"))

# What the main screen must never show (acceptance): claim ids, model ids, the pilcrow, and raw
# passage ids. "About these checks" is a closed dialog, so its text is not in innerText.
NOT_ON_SCREEN = [re.compile(r"\bc\d{2}\b"), re.compile(r"claude-|jev-", re.I), re.compile("¶"),
                 re.compile(r"[\w-]+:p\d+:\d+")]

CLAIM_LABELS = {"supported": "Supported", "contradicted": "Contradicted by another passage",
                "checker_disagrees": "Checker disagrees", "quote_not_found": "Quote not found"}


def flagged_clause_ids(view):
    claims = {c["claim_id"]: c for c in view["claims"]}
    required = {cid for r in view["required_reading"] for cid in r["clause_ids"]}
    return {c["clause_id"] for c in view["clauses"]
            if c["contradictions"] or c["missing"] or c["coverage"] == "no_evidence_in_file"
            or c["clause_id"] in required
            or any(claims[cid]["status"] != "supported" for cid in c["claim_ids"])}


@pytest.fixture(params=["current", "one-flag-supported"])
def a0142_screen(request, tmp_path):
    # Snapshot the current cache: concurrent work can change it between test cases.
    view = json.loads((A0142_RUN / "view.json").read_text(encoding="utf-8"))
    if request.param == "one-flag-supported":
        sole_flags = {r["claim_ids"][0] for r in view["required_reading"]
                      if len(r["claim_ids"]) == 1 and r["reasons"] == ["checker_disagrees"]}
        flagged = [c for c in view["claims"] if c["status"] != "supported"]
        claim = next((c for c in flagged if c["claim_id"] in sole_flags), flagged[0])
        claim["status"] = "supported"
        # A sole checker-disagreement gate item disappears when that check becomes supported.
        view["required_reading"] = [r for r in view["required_reading"]
                                    if not (r["claim_ids"] == [claim["claim_id"]]
                                            and r["reasons"] == ["checker_disagrees"])]
        for rank, item in enumerate(view["required_reading"], 1):
            item["rank"] = rank
    run = tmp_path / "run"
    run.mkdir()
    (run / "view.json").write_text(dumps(view), encoding="utf-8", newline="\n")
    return view, run


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
    assert "decision_label" not in record and "required_reading" not in record
    assert "case_sha256" not in record and "view_sha256" not in record
    assert record["integrity"]["case_sha256"] == A0142["case"]["sha256"]
    assert record["integrity"]["view_sha256"] == hashlib.sha256(
        dumps(A0142).encode("utf-8")).hexdigest()
    assert all(p["opened_at"] and p["seconds_in_view"] == 3.2 and p["required"]
               for p in record["passages_opened"])
    assert record["models"] == A0142["models"] and record["reason"] == payload["reason"]
    assert rec.DECISIONS[payload["decision"]] in page
    assert all(record["integrity"][key] in page for key in ("case_note", "view_note"))

    # One zone: the UTC openings appear in the signing zone, and no UTC stamp is left.
    assert "14:00:05" in page and "14:01:00" in page and "14:05:12" in page
    assert "04:30:05" not in page and "04:31:00" not in page
    assert not re.search(r"\d{2}:\d{2}:\d{2}(\.\d+)?Z", page)
    assert page.count("UTC+09:30") >= 1

    # A dispute carries the claim's own words, in the record and on the export.
    claim = next(c for c in A0142["claims"] if c["claim_id"] == "c15")["claim"]
    assert record["disputes"][0]["claim"] == claim
    assert record["disputes"][0]["clause"] == "Debts, Eligibility §3.4"
    quotes = record["disputes"][0]["citations"]
    assert quotes and all(q["quote_found"] for q in quotes)
    assert all(html.escape(q["quote"]) in page for q in quotes)
    assert html.escape(claim) in page

    # Its only CSS is the screen's own styling files, verbatim; no inline styles.
    blocks = re.findall(r"<style>(.*?)</style>", page, re.S)
    assert len(blocks) == 1 and blocks[0].strip() == rec.styles().strip()
    assert "web/theme.css" not in page and "style=" not in page
    assert (ROOT / "web" / "theme.css").read_text(encoding="utf-8").strip() in blocks[0]
    assert "¶" not in page and "Page 8, paragraph 3" in page


def assert_plain(page):
    text = page.evaluate("document.body.innerText")
    for pattern in NOT_ON_SCREEN:
        found = pattern.search(text)
        assert not found, f"{pattern.pattern!r} on screen: {found.group(0)!r}"
    assert "Summary under audit" not in text
    assert page.get_by_test_id("audit-tab").count() == 0


def assert_no_overflow(page):
    assert page.evaluate("document.documentElement.scrollWidth - window.innerWidth") <= 0


def screenshot(page, width, state):
    shots = ROOT / ".tmp" / "shots"
    shots.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(shots / f"task-11-{state}-{width}.png"), full_page=True)


def assert_scrolled_to(page, pid):
    paragraph = page.locator(f'#fileScroll .file-paragraph[data-pid="{pid}"]').bounding_box()
    viewport = page.locator("#fileScroll").bounding_box()
    assert viewport["y"] <= paragraph["y"] < viewport["y"] + viewport["height"]


def test_light_default_saved_theme_and_historical_context(tmp_path, a0142_screen):
    from playwright.sync_api import expect, sync_playwright

    view, run = a0142_screen
    with (ROOT / "data/context/urban-public-housing-2020-12.csv").open(
            encoding="utf-8-sig", newline="") as file:
        rows = list(csv.reader(file))
    darwin = next(row for row in rows if row and row[0] == "Darwin/Casuarina")
    with serving("A-0142", run, tmp_path / "records") as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900}, color_scheme="dark")
        page.goto(base)
        expect(page.locator("html")).to_have_attribute("data-theme", "light")
        expect(page.locator("#fileScroll")).to_be_visible()
        context = page.locator("#casebar").get_by_test_id("wait-context")
        expect(context).to_contain_text("Darwin/Casuarina, general housing (2–3 bedrooms)")
        expect(context).to_contain_text(darwin[2].replace(" to ", "–"))
        expect(context).to_contain_text("NT open data, Dec 2020")
        expect(context).to_contain_text("historical, not priority-specific")
        expect(context.locator("a")).to_have_attribute(
            "href", "https://data.nt.gov.au/dataset/urban-public-housing-wait-times-"
                    "wait-list-and-allocations-december-2020")
        assert page.request.get(base + "/api/context").json()["period"] == "2020-12-31"
        # Context is served separately; the pipeline view and gate remain byte-for-byte data.
        assert page.request.get(base + "/api/view").json() == view
        assert_no_overflow(page)
        screenshot(page, 1280, "context-light")
        page.locator('[data-act="theme"]').click()
        expect(page.locator("html")).to_have_attribute("data-theme", "dark")
        page.reload()
        expect(page.locator("#fileScroll")).to_be_visible()
        expect(page.locator("html")).to_have_attribute("data-theme", "dark")
        expect(page.locator("#themeBtn")).to_have_text("Light mode")
        assert_no_overflow(page)
        screenshot(page, 1280, "context-dark")
        page.locator('[data-act="theme"]').click()
        page.reload()
        expect(page.locator("#fileScroll")).to_be_visible()
        expect(page.locator("html")).to_have_attribute("data-theme", "light")
        browser.close()


@pytest.mark.parametrize("width", [1280, 1440])
def test_saved_dispute_reason_uses_box_width(width, tmp_path):
    from playwright.sync_api import expect, sync_playwright

    reason = "The March statement supersedes the January arrears notice."
    claim = next(c for c in A0142["claims"] if c["claim_id"] == "c15")
    with serving("A-0142", A0142_RUN, tmp_path) as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.goto(base)
        page.get_by_test_id("intro-dismiss").click()
        page.locator('[data-testid="clause-row"][data-clause="elig-debts"]').click()
        page.get_by_test_id("claim-details").locator("summary").click()
        march = page.get_by_test_id("claim").filter(has_text=claim["claim"])
        march.get_by_test_id("dispute-btn").click()
        page.get_by_test_id("dispute-reason").fill(reason)
        page.get_by_test_id("dispute-save").click()
        saved = march.get_by_test_id("dispute-saved")
        expect(saved).to_contain_text(reason)
        metrics = saved.evaluate("""el => {
            const text = el.querySelector('.spacer');
            const walker = document.createTreeWalker(text, NodeFilter.SHOW_TEXT);
            let node;
            while ((node = walker.nextNode())) {
                const start = node.textContent.indexOf('supersedes');
                if (start < 0) continue;
                const range = document.createRange();
                range.setStart(node, start);
                range.setEnd(node, start + 'supersedes'.length);
                return {box: el.getBoundingClientRect().width,
                        text: text.getBoundingClientRect().width,
                        wordLines: range.getClientRects().length};
            }
        }""")
        print(f"Saved dispute at {width}px: {metrics}")
        screenshot(page, width, "dispute-saved")
        assert metrics["text"] >= 0.6 * metrics["box"], metrics
        assert metrics["wordLines"] == 1, metrics
        text_box = saved.locator(".spacer").bounding_box()
        for name in ("Edit", "Withdraw"):
            button_box = saved.get_by_role("button", name=name, exact=True).bounding_box()
            assert button_box["y"] >= text_box["y"] + text_box["height"]
        browser.close()


@needs_pdfs
@pytest.mark.parametrize("width", [1280, 1440])
def test_answer_key_review_flow_on_a0142(width, tmp_path, a0142_screen):
    from playwright.sync_api import expect, sync_playwright

    view, run = a0142_screen
    records_dir = tmp_path / "records"
    required = [r["passage_id"] for r in view["required_reading"]]
    decisive = [c["clause_id"] for c in view["clauses"] if c["clause_id"] != "other"]
    flagged = flagged_clause_ids(view)
    clean_ids = [cid for cid in decisive if cid not in flagged]
    debts = next(c for c in view["clauses"] if c["clause_id"] == "elig-debts")
    disputed = next(c for c in view["claims"] if c["clause_id"] == debts["clause_id"]
                    and any(view["sources"][q["passage_id"]]["kind"] == "case"
                            for q in c["citations"]))
    errors = []
    with serving("A-0142", run, records_dir) as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(base)
        expect(page.locator("#fileScroll")).to_be_visible()
        expect(page.locator("#fileScroll").get_by_test_id("file-page")).to_have_count(
            view["case"]["pages"])
        expect(page.get_by_test_id("intro")).to_contain_text("Follow the highlights")
        expect(page.locator("#outcomeCount")).to_have_text("0")
        expect(page.locator("#passageCount")).to_have_text("0")
        assert page.locator('[data-outcome][aria-checked="true"]').count() == 0
        clean = page.get_by_test_id("clean-questions")
        if clean_ids:
            assert clean.get_attribute("open") is None
            expect(clean.locator(f'[data-clause="{clean_ids[0]}"]')).to_be_hidden()
            expect(clean.locator("summary")).to_contain_text(str(len(clean_ids)))
        else:
            expect(clean).to_have_count(0)
        assert_plain(page)
        assert_no_overflow(page)
        screenshot(page, width, "opening")
        page.get_by_test_id("intro-dismiss").click()
        page.get_by_test_id("help-btn").click()
        expect(page.get_by_test_id("intro")).to_be_visible()
        page.get_by_test_id("intro-dismiss").click()
        screenshot(page, width, "file")

        # Full text comes from the case, including paragraphs no claim or scan cited.
        data = page.request.get(base + "/api/case-pages").json()
        meta, original = case_passages("A-0142")
        assert data["sha256"] == meta["sha256"]
        assert [p for sheet in data["pages"] for p in sheet["passages"]] == original
        unquoted = next(p for p in original if p["passage_id"] not in view["sources"])
        expect(page.locator(f'#fileScroll [data-pid="{unquoted["passage_id"]}"] p')).to_have_text(
            unquoted["text"])

        # Every verified case quote, including every flagged claim's quote, is marked with its
        # question. Reassemble split overlapping marks to check exact text, not just a count.
        for claim in view["claims"]:
            for cite in claim["citations"]:
                source = view["sources"][cite["passage_id"]]
                if not cite["quote_found"] or source["kind"] != "case":
                    continue
                marks = page.locator(f'#fileScroll [data-pid="{cite["passage_id"]}"] '
                                     f'mark[data-claims~="{claim["claim_id"]}"]')
                assert cite["quote"] in "".join(marks.all_text_contents())
                labels = page.locator(f'#fileScroll [data-testid="highlight-label"]'
                                      f'[data-pid="{cite["passage_id"]}"]'
                                      f'[data-clause="{claim["clause_id"]}"]')
                assert labels.count() > 0
                if claim["status"] != "supported":
                    assert any(
                        labels.nth(i).get_attribute("data-flag") == "true"
                        for i in range(labels.count()))

        # Both the browser and server refuse an early signature.
        payload = {"decision": "request_information", "reason": "Income missing.",
                   "clause_outcomes": {}, "passages_opened": [], "disputes": []}
        refused = page.request.post(base + "/api/records", data=payload)
        assert refused.status == 422 and not records_dir.exists()
        page.get_by_test_id("sign-btn").click()
        expect(page.get_by_test_id("missing-item")).to_have_count(len(decisive))
        page.locator('[data-testid="missing-item"][data-clause="elig-debts"]').click()
        expect(page.get_by_test_id("clause-detail")).to_have_attribute("data-clause", "elig-debts")
        debt_flags = [r["passage_id"] for r in view["required_reading"]
                      if debts["clause_id"] in r["clause_ids"]]
        expect(page.get_by_test_id("source")).to_have_attribute("data-pid", debt_flags[0])
        assert_scrolled_to(page, debt_flags[0])
        expect(page.get_by_test_id("claim-details")).not_to_have_attribute("open", "")
        screenshot(page, width, "debts")

        # Compare the two real pages together, without silently marking either as opened.
        before = page.locator("#passageCount").inner_text()
        page.get_by_test_id("compare-pages").click()
        comparison = page.locator("#comparison")
        expect(comparison).to_be_visible()
        pair = debts["contradictions"][0]
        for pid in (pair["a"], pair["b"]):
            expect(comparison.locator(f'[data-page="{view["sources"][pid]["page"]}"]')).to_have_count(1)
            expect(comparison).to_contain_text(view["sources"][pid]["text"])
        expect(page.locator("#passageCount")).to_have_text(before)
        screenshot(page, width, "comparison")
        comparison.locator('[data-act="compare-close"]').click()

        # Claims of any current status are one click away and remain disputable.
        page.get_by_test_id("claim-details").locator("summary").click()
        march = page.get_by_test_id("claim").filter(has_text=disputed["claim"])
        expect(march).to_contain_text(CLAIM_LABELS[disputed["status"]])
        march.get_by_test_id("dispute-btn").click()
        page.get_by_test_id("dispute-save").click()
        expect(march).to_contain_text("Write a reason")
        page.get_by_test_id("dispute-reason").fill("The March statement is the current record.")
        page.get_by_test_id("dispute-save").click()
        expect(march.get_by_test_id("dispute-saved")).to_contain_text("current record")

        # Pinned policy text is served on demand; it does not open another required case passage.
        page.get_by_test_id("clause-detail").locator("details").filter(
            has=page.get_by_test_id("open-policy")).locator("summary").click()
        page.get_by_test_id("open-policy").click()
        expect(page.locator("#policy").get_by_test_id("source")).to_contain_text(
            debts["policy_sentence"])
        expect(page.locator("#passageCount")).to_have_text(before)
        page.locator('[data-act="close-pane"]').click()

        # Next flag reaches every flagged highlight in its displayed order, including scan hits
        # and the second side of the pair. Several highlights can share one required passage.
        flags = page.locator('#fileScroll [data-testid="highlight-label"][data-flag="true"]')
        expected = flags.evaluate_all("els => els.map(e => [e.dataset.arg, e.dataset.pid])")
        # DOM file order differs from the deliberate gate-rank navigation order. Get the order
        # from the user-facing sequence by starting at the first required passage and check the
        # visited set, required-prefix rank, and that each jump is actually visible.
        seen = []
        visited = []
        for _ in range(len(expected)):
            page.get_by_test_id("next-flag").click()
            current = page.get_by_test_id("source")
            pid = current.get_attribute("data-pid")
            position = page.get_by_test_id("flag-position").inner_text()
            seen.append((position, pid))
            visited.append(page.locator(
                '#fileScroll [data-testid="highlight-label"][aria-current="true"]').get_attribute(
                    "data-arg"))
            assert_scrolled_to(page, pid)
            assert_plain(page)
            assert_no_overflow(page)
            page.wait_for_timeout(250)
        assert len({position for position, _ in seen}) == len(expected)
        assert set(visited) == {annotation for annotation, _ in expected}
        assert {pid for _, pid in seen} == {pid for _, pid in expected}
        distinct = list(dict.fromkeys(pid for _, pid in seen))
        assert distinct[:len(required)] == required
        expect(page.locator("#passageCount")).to_have_text(str(len(required)))
        page.get_by_test_id("previous-flag").click()
        expect(page.get_by_test_id("flag-position")).to_have_text(seen[-2][0])
        count = page.locator("#passageCount").inner_text()
        page.locator("#pageJump").select_option(str(view["case"]["pages"]))
        expect(page.locator("#passageCount")).to_have_text(count)
        expect(page.get_by_test_id("source")).to_have_count(0)

        # A clean question expands on click and still needs an officer's outcome.
        if clean_ids:
            page.get_by_test_id("clean-toggle").click()
            clean.locator(f'[data-clause="{clean_ids[0]}"]').click()
            expect(page.get_by_test_id("clause-detail")).to_have_attribute("data-clause", clean_ids[0])
            screenshot(page, width, "clean-question")
        outcomes = {}
        for cid in decisive:
            page.locator(f'[data-testid="clause-row"][data-clause="{cid}"]').click()
            value = "cannot_decide" if cid == "elig-income" else "met"
            page.get_by_test_id(f"outcome-{cid}-{value}").click()
            outcomes[cid] = value
        expect(page.locator("#outcomeCount")).to_have_text(str(len(decisive)))
        page.locator('[data-testid="clause-row"][data-clause="elig-income"]').click()
        income = next(c for c in view["clauses"] if c["clause_id"] == "elig-income")
        for missing in income["missing"]:
            expect(page.get_by_test_id("gaps")).to_contain_text(missing["statement"])
        screenshot(page, width, "income")
        page.locator('[data-act="theme"]').click()
        screenshot(page, width, "income-dark")
        page.locator('[data-act="theme"]').click()

        # Scrolling a timed passage out of the reader stops the clock. Browsing to page 60 does
        # not tick any gate item; elapsed sign-off time is also excluded from the record.
        page.wait_for_timeout(300)
        page.locator("#fileScroll").evaluate("el => { el.scrollTop = el.scrollHeight; }")
        page.wait_for_timeout(200)
        seconds = page.evaluate("secondsInView(S.current.pid)")
        page.wait_for_timeout(700)
        assert abs(page.evaluate("secondsInView(S.current.pid)") - seconds) < 0.1
        page.get_by_test_id("next-action").click()
        expect(page.get_by_test_id("missing-list")).to_have_count(0)
        expect(page.locator("#reader")).to_be_hidden()
        page.get_by_test_id("continue-btn").click()
        expect(page.get_by_test_id("form-helper")).to_contain_text("Choose a decision")
        page.get_by_test_id("decision-request_information").check()
        page.get_by_test_id("reason").fill("Eligibility §3: no current income statement in the file.")
        page.get_by_test_id("continue-btn").click()
        answers = page.get_by_test_id("check-answers")
        expect(answers).to_contain_text(disputed["claim"])
        expect(answers.get_by_test_id("change")).to_have_count(len(decisive) + 3)
        screenshot(page, width, "check-answers")
        answers.locator('[data-arg="elig-income"]').click()
        page.get_by_test_id("next-action").click()
        page.wait_for_timeout(2500)
        page.get_by_test_id("confirm-sign").click()
        expect(page.get_by_test_id("record")).to_be_visible()
        assert_plain(page)
        assert_no_overflow(page)
        screenshot(page, width, "record")
        record = page.request.get(base + page.get_by_test_id("export-json").get_attribute("href")).json()
        export = page.request.get(base + page.get_by_test_id("export-html").get_attribute("href"))
        assert export.ok and "Decision record" in export.text()
        assert html.escape(disputed["claim"]) in export.text()

        page.locator('[data-testid="clause-row"][data-clause="elig-debts"]').click()
        expect(page.locator("[data-outcome]:not([disabled])")).to_have_count(0)
        expect(page.get_by_test_id("dispute-btn")).to_have_count(0)
        expect(page.locator('[data-testid="flagged-item"]:not([disabled])')).to_have_count(0)
        browser.close()
    assert errors == []
    by_pid = {p["passage_id"]: p for p in record["passages_opened"]}
    assert set(required) <= set(by_pid)
    for pid in required:
        assert by_pid[pid]["opened_at"] and isinstance(by_pid[pid]["seconds_in_view"], float)
        assert by_pid[pid]["seconds_in_view"] > 0
    for passage in by_pid.values():
        assert passage["opened_at"] and isinstance(passage["seconds_in_view"], float)
        assert passage["required"] == (passage["passage_id"] in required)
    assert "decision_label" not in record and "required_reading" not in record
    assert "integrity" in record
    assert record["decision"] == "request_information"
    assert record["disputes"][0]["claim_id"] == disputed["claim_id"]
    assert {o["clause_id"]: o["outcome"] for o in record["clause_outcomes"]} == outcomes
    assert sorted(f.suffix for f in records_dir.iterdir()) == [".html", ".json"]


def test_case_pages_reject_a_changed_file_pin(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    view = dict(A0142, case=dict(A0142["case"], sha256="0" * 64))
    (run / "view.json").write_text(json.dumps(view), encoding="utf-8")
    with serving("A-0142", run, tmp_path / "records") as base:
        from urllib.error import HTTPError
        from urllib.request import urlopen

        with pytest.raises(HTTPError) as err:
            urlopen(base + "/api/case-pages")
        assert err.value.code == 409


@pytest.mark.parametrize("audit", ["present", "absent", None])
def test_audit_is_not_shown_and_bad_quotes_are_never_highlighted(audit, tmp_path):
    from playwright.sync_api import expect, sync_playwright

    view = json.loads(json.dumps(A0142))
    if audit == "absent":
        view.pop("audit", None)
    elif audit is None:
        view["audit"] = None
    else:
        view["audit"] = {"summary": "SECRET AUDIT TEXT", "model": "claude-secret"}
    claim = next(c for c in view["claims"] if c["claim_id"] == "c01")
    claim["status"] = "quote_not_found"
    claim["citations"][0]["quote"] = "A made-up residency sentence that is not in the file."
    claim["citations"][0]["quote_found"] = False
    run = tmp_path / "run"
    run.mkdir()
    (run / "view.json").write_text(json.dumps(view), encoding="utf-8")
    errors = []
    with serving("A-0142", run, tmp_path / "records") as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(base)
        page.get_by_test_id("intro-dismiss").click()
        page.locator('[data-testid="clause-row"][data-clause="elig-residency"]').click()
        expect(page.get_by_test_id("quote-warning")).to_contain_text("Quote not found")
        assert page.locator('#fileScroll mark[data-claims~="c01"]').count() == 0
        page.get_by_test_id("quote-warning").get_by_role("button").click()
        expect(page.get_by_test_id("claim").filter(has_text=claim["claim"])).to_contain_text(
            "Quote not found")
        assert "SECRET AUDIT TEXT" not in page.evaluate("document.body.innerText")
        assert_plain(page)
        assert_no_overflow(page)
        browser.close()
    assert errors == []
