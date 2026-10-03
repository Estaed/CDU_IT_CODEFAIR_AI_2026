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
SCREENSHOTS = ROOT / ".tmp/shots/wave6b"

# What the main screen must never show (acceptance): claim ids, model ids, the pilcrow, and raw
# passage ids. "About these checks" is a closed dialog, so its text is not in innerText.
NOT_ON_SCREEN = [re.compile(r"\bclauses?\b", re.I),
                 re.compile(r"\bc\d{2}\b"), re.compile(r"claude-|jev-", re.I), re.compile("¶"),
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


def assert_tab_labels_fit(tabs):
    metrics = tabs.evaluate_all("""els => els.map(el => ({
        label: el.textContent, scrollWidth: el.scrollWidth, clientWidth: el.clientWidth,
        stripScrollWidth: el.parentElement.scrollWidth,
        stripClientWidth: el.parentElement.clientWidth
    }))""")
    for tab in metrics:
        assert tab["scrollWidth"] <= tab["clientWidth"], tab
        assert tab["stripScrollWidth"] <= tab["stripClientWidth"], tab


def assert_wait_context_fits(page, width):
    context = page.get_by_test_id("wait-context")
    metrics = context.evaluate("""el => ({
        height: el.getBoundingClientRect().height,
        lineHeight: parseFloat(getComputedStyle(el).lineHeight),
        right: el.getBoundingClientRect().right,
        actionLeft: document.getElementById('next').getBoundingClientRect().left
    })""")
    assert metrics["height"] <= metrics["lineHeight"] * (1 if width == 1440 else 2) + 1
    assert metrics["right"] < metrics["actionLeft"]


def polish_screenshot(page, width, state):
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    page.evaluate("window.scrollTo(0, 0)")
    page.screenshot(path=str(SCREENSHOTS / f"fix-{state}-{width}.png"), full_page=True)


def screenshot(page, width, state):
    shots = SCREENSHOTS
    shots.mkdir(parents=True, exist_ok=True)
    # Altered-cache fixtures exercise resilience; delivered screenshots show the real cache.
    if page.request.get(page.url + "api/view").json() != A0142:
        return
    page.screenshot(path=str(shots / f"{state}-{width}.png"), full_page=True)


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
        assert page.locator('[data-act="theme"]').count() == 0
        assert not (ROOT / "web/tokens.css").exists()
        page.evaluate("localStorage.setItem('readmark-theme', 'dark')")
        page.reload()
        expect(page.locator("#fileScroll")).to_be_visible()
        expect(page.locator("html")).to_have_attribute("data-theme", "light")
        assert page.evaluate("getComputedStyle(document.body).backgroundColor") == "rgb(255, 255, 255)"
        assert_no_overflow(page)
        screenshot(page, 1280, "saved-dark-opens-light")
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
        expect(page.get_by_test_id("service-band")).to_be_visible()
        expect(page.locator("#casebar")).to_be_visible()
        expect(page.locator("#rail")).to_contain_text("Decide these questions")
        expect(page.get_by_test_id("clause-detail")).to_be_visible()
        expect(page.locator("#fileScroll").get_by_test_id("file-page")).to_have_count(1)
        expect(page.get_by_test_id("intro")).to_contain_text("Follow the highlights")
        expect(page.locator("#outcomeCount")).to_have_text("0")
        expect(page.locator("#passageCount")).to_have_text("0")
        assert page.locator('[data-outcome]:checked').count() == 0
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
        screenshot(page, width, "opening-question")
        page.get_by_test_id("open-full-file").click()
        expect(page.locator("#fileScroll").get_by_test_id("file-page")).to_have_count(
            view["case"]["pages"])
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
        page.locator('[data-act="full-close"]').click()
        page.get_by_test_id("sign-btn").click()
        expect(page.get_by_test_id("missing-item")).to_have_count(len(decisive))
        screenshot(page, width, "not-ready-to-sign")
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
        page.get_by_test_id("open-full-file").click()

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
        page.locator('[data-act="full-close"]').click()

        # A clean question expands on click and still needs an officer's outcome.
        if clean_ids:
            page.get_by_test_id("clean-toggle").click()
            clean.locator(f'[data-clause="{clean_ids[0]}"]').click()
            expect(page.get_by_test_id("clause-detail")).to_have_attribute("data-clause", clean_ids[0])
            screenshot(page, width, "clean-question")
        outcomes = {}
        for cid in decisive:
            page.locator(f'[data-testid="clause-row"][data-clause="{cid}"]').click()
            assert_wait_context_fits(page, width)
            value = "cannot_decide" if cid == "elig-income" else "met"
            page.get_by_test_id(f"outcome-{cid}-{value}").click()
            outcomes[cid] = value
        expect(page.locator("#outcomeCount")).to_have_text(str(len(decisive)))
        page.locator('[data-testid="clause-row"][data-clause="elig-income"]').click()
        income = next(c for c in view["clauses"] if c["clause_id"] == "elig-income")
        for missing in income["missing"]:
            page.get_by_test_id("gaps").evaluate("el => el.open = true")
            expect(page.get_by_test_id("gaps")).to_contain_text(missing["statement"])
        screenshot(page, width, "income")
        page.get_by_test_id("open-full-file").click()

        # Scrolling a timed passage out of the reader stops the clock. Browsing to page 60 does
        # not tick any gate item; elapsed sign-off time is also excluded from the record.
        page.wait_for_timeout(300)
        page.locator("#fileScroll").evaluate("el => { el.scrollTop = el.scrollHeight; }")
        page.wait_for_timeout(200)
        seconds = page.evaluate("secondsInView(S.current.pid)")
        page.wait_for_timeout(700)
        assert abs(page.evaluate("secondsInView(S.current.pid)") - seconds) < 0.1
        page.locator('[data-act="full-close"]').click()
        page.get_by_test_id("next-action").click()
        expect(page.get_by_test_id("missing-list")).to_have_count(0)
        expect(page.locator("#reader")).to_have_count(0)
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
        exported = browser.new_page(viewport={"width": width, "height": 900})
        exported.goto(base + f"/api/records/{record['record_id']}.html")
        expect(exported.locator(".service-band")).to_contain_text("Readmark")
        assert_no_overflow(exported)
        if view == A0142:
            exported.screenshot(path=str(SCREENSHOTS /
                                         f"exported-record-{width}.png"), full_page=True)
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


def question_page_groups(view, clause):
    """Distinct case pages in required, cited and existing suggestion rank order."""
    claims = {c["claim_id"]: c for c in view["claims"]}

    def keys(pids):
        return list(dict.fromkeys(f"case:{s['page']}" for pid in pids
                                  if (s := view["sources"][pid])["exists"]
                                  and s["kind"] == "case"))

    required = keys(r["passage_id"] for r in view["required_reading"]
                    if clause["clause_id"] in r["clause_ids"])
    cited = keys(q["passage_id"] for cid in clause["claim_ids"] for q in claims[cid]["citations"])
    optional_cited = [k for k in cited if k not in required]
    suggested = [k for k in keys(p["passage_id"] for p in clause["possibly_missed"])
                 if k not in required + cited]
    optional = optional_cited + suggested
    return required, cited, required + optional[:2], optional[2:]


@pytest.mark.parametrize("width", [1280, 1440])
def test_every_question_has_real_page_tabs_and_saves_to_next_undecided(width, tmp_path):
    from playwright.sync_api import expect, sync_playwright

    errors = []
    view = A0142
    clauses = view["clauses"]
    with serving("A-0142", A0142_RUN, tmp_path / "records") as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(base)
        page.get_by_test_id("intro-dismiss").click()
        if page.get_by_test_id("clean-questions").count():
            page.get_by_test_id("clean-toggle").click()
        # A save cannot silently invent an answer.
        page.get_by_test_id("save-next").click()
        expect(page.get_by_role("alert")).to_contain_text("Choose an outcome")
        assert page.locator('[data-outcome]:checked').count() == 0
        for clause in clauses:
            cid = clause["clause_id"]
            if cid == "other":
                page.locator(".other-group > summary").click()
            page.locator(f'[data-testid="clause-row"][data-clause="{cid}"]').click()
            assert_wait_context_fits(page, width)
            tabs = page.get_by_test_id("page-tab")
            required, cited, expected_tabs, expected_more = question_page_groups(view, clause)
            tab_keys = tabs.evaluate_all("els => els.map(e => e.dataset.arg)")
            more_keys = page.get_by_test_id("more-page").evaluate_all(
                "els => els.map(e => e.dataset.arg)")
            assert tab_keys == expected_tabs
            assert more_keys == expected_more
            assert len(tab_keys) <= len(required) + 2
            all_pages = {f"case:{view['sources'][pid]['page']}"
                         for pid in ([r["passage_id"] for r in view["required_reading"]
                                      if cid in r["clause_ids"]]
                                     + [q["passage_id"] for claim in view["claims"]
                                        if claim["claim_id"] in clause["claim_ids"]
                                        for q in claim["citations"]]
                                     + [p["passage_id"] for p in clause["possibly_missed"]])
                         if view["sources"][pid]["exists"]
                         and view["sources"][pid]["kind"] == "case"}
            assert set(tab_keys + more_keys) == all_pages
            assert len(set(tab_keys + more_keys)) == len(tab_keys + more_keys)
            assert page.get_by_test_id("more-pages").count() == bool(expected_more)
            if expected_more:
                expect(page.get_by_test_id("more-pages")).to_have_text(
                    f"More pages ({len(expected_more)})")
            for label, keys in [("Cited by the AI's claims", [k for k in more_keys if k in cited]),
                                ("Possibly missed", [k for k in more_keys if k not in cited])]:
                group = page.locator("#morePages section").filter(
                    has=page.get_by_role("heading", name=label, exact=True, include_hidden=True))
                assert group.count() == bool(keys)
                if keys:
                    assert group.get_by_test_id("more-page").evaluate_all(
                        "els => els.map(e => e.dataset.arg)") == keys
            if not required and tab_keys:
                assert tab_keys[0] == (cited[0] if cited else expected_tabs[0])
            if tab_keys:
                expect(page.get_by_test_id("file-page")).to_have_attribute(
                    "data-page", tab_keys[0].split(":")[1])
            controls = page.locator('[data-testid="page-tab"], [data-testid="more-pages"]')
            assert controls.count() <= len(required) + 2 + bool(expected_more)
            assert_tab_labels_fit(controls)
            assert tabs.evaluate_all("els => els.every(e => e.dataset.kind === 'case')")
            # If their combined width fits, the controls stay on one line at 1440.
            if width == 1440:
                layout = controls.evaluate_all("""els => ({
                    width: els.reduce((n, e) => n + e.getBoundingClientRect().width, 0),
                    available: els[0]?.parentElement.clientWidth || 0,
                    tops: els.map(e => e.getBoundingClientRect().top)
                })""")
                if layout["width"] <= layout["available"]:
                    assert len(set(layout["tops"])) <= 1
            assert page.locator('[data-outcome]:checked').count() == 0
            for key in tab_keys + more_keys:
                if key in more_keys:
                    more_control = page.get_by_test_id("more-pages")
                    before_opened = page.evaluate("Object.keys(S.opened)")
                    more_control.click()
                    expect(more_control).to_have_attribute("aria-expanded", "true")
                    expect(more_control).to_be_focused()
                    assert page.locator("#morePages").evaluate(
                        "el => el.scrollHeight === el.clientHeight")
                    assert page.evaluate("Object.keys(S.opened)") == before_opened
                    item = page.locator(f'[data-testid="more-page"][data-arg="{key}"]')
                    source = next(s for s in view["sources"].values()
                                  if s["kind"] == "case" and f"case:{s['page']}" == key)
                    expect(item).to_contain_text(f"Page {source['page']}")
                    expect(item).to_contain_text(source["doc_title"])
                    if source["doc_date"]:
                        date = datetime.fromisoformat(source["doc_date"])
                        expect(item).to_contain_text(f"{date.day} {date.strftime('%b %Y')}")
                    if key == more_keys[0]:
                        screenshot(page, width, f"more-pages-{cid}")
                    item.click()
                    expect(page.get_by_test_id("more-pages")).to_have_attribute(
                        "aria-expanded", "false")
                    expect(page.get_by_test_id("more-pages")).to_contain_text(
                        f"Page {source['page']} selected")
                    expect(item).to_have_attribute("aria-current", "page")
                    expect(item).to_contain_text("✓ opened")
                    # Opening an overflow page does not promote it into the tab row.
                    assert tabs.evaluate_all("els => els.map(e => e.dataset.arg)") == tab_keys
                else:
                    tab = page.locator(f'[data-testid="page-tab"][data-arg="{key}"]')
                    tab.click()
                    expect(tab).to_have_attribute("aria-selected", "true")
                    expect(tab).to_contain_text("✓ opened")
                assert_tab_labels_fit(controls)
                assert_wait_context_fits(page, width)
                current = page.get_by_test_id("source")
                expect(current).to_be_visible()
                pid = current.get_attribute("data-pid")
                source = view["sources"][pid]
                assert source["kind"] == "case"
                assert f"case:{source['page']}" == key
                expect(current).to_contain_text(source["text"])
                # A wrapped strip can put the passage below the viewport; timing starts in view.
                current.scroll_into_view_if_needed()
                page.wait_for_timeout(150)
                opening = page.evaluate("S.opened[S.current.pid]")
                assert datetime.fromisoformat(opening["opened_at"])
                assert page.evaluate("secondsInView(S.current.pid)") > 0
                # Case highlights are exact substrings of a code-verified citation.
                for mark in page.get_by_test_id("verified-highlight").all():
                    text = mark.inner_text()
                    claim_ids = mark.get_attribute("data-claims").split()
                    assert any(q["quote_found"] and text in q["quote"]
                               for c in view["claims"] if c["claim_id"] in claim_ids
                               for q in c["citations"])
                assert_no_overflow(page)
            # Photograph the first page of each real question, including every flag state.
            tabs.first.click()
            screenshot(page, width, f"question-{cid}")
        assert page.locator("#passageCount").inner_text() == str(len(view["required_reading"]))
        # Saving follows the task-list order, wrapping to the next undecided question.
        ordered = page.evaluate("railClauses().filter(c => c.clause_id !== 'other').map(c => c.clause_id)")
        for i, cid in enumerate(ordered):
            page.locator(f'[data-testid="clause-row"][data-clause="{cid}"]').click()
            page.get_by_test_id(f"outcome-{cid}-cannot_decide").check()
            expect(page.locator(f'[data-testid="clause-row"][data-clause="{cid}"]')).to_contain_text(
                "Decided: Cannot decide yet")
            page.get_by_test_id("save-next").click()
            if i + 1 < len(ordered):
                expect(page.get_by_test_id("clause-detail")).to_have_attribute("data-clause", ordered[i + 1])
            else:
                expect(page.get_by_test_id("signoff")).to_contain_text("Your decision")
        page.get_by_test_id("decision-request_information").check()
        page.get_by_test_id("reason").fill("Further evidence is needed before deciding.")
        page.get_by_test_id("continue-btn").click()
        page.get_by_test_id("confirm-sign").click()
        expect(page.get_by_test_id("record")).to_be_visible()
        record = page.request.get(base + page.get_by_test_id("export-json").get_attribute("href")).json()
        assert all(p["opened_at"] and p["seconds_in_view"] > 0 for p in record["passages_opened"])
        assert {r["passage_id"] for r in view["required_reading"]} <= {
            p["passage_id"] for p in record["passages_opened"]}
        browser.close()
    assert errors == []


@pytest.mark.parametrize("width", [1280, 1440])
@pytest.mark.parametrize("case_id", ["A-0142", "E-02"])
def test_polish_question_words_identity_more_pages_and_warning_pairs(case_id, width, tmp_path):
    from playwright.sync_api import expect, sync_playwright

    run = ROOT / "runs" / case_id
    view = json.loads((run / "view.json").read_text(encoding="utf-8"))
    errors = []
    with serving(case_id, run, tmp_path / "records") as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(base)
        expect(page.get_by_test_id("wait-context")).to_contain_text("NT open data")
        assert_plain(page)
        page.get_by_test_id("intro-dismiss").click()
        page.get_by_test_id("sign-btn").click()
        expect(page.get_by_test_id("signoff")).to_contain_text("questions first")
        assert_plain(page)
        if case_id == "A-0142":
            polish_screenshot(page, width, "question-word")
        if page.get_by_test_id("clean-questions").count():
            page.get_by_test_id("clean-toggle").click()
        photographed_more = False
        photographed_identity = False
        for clause in view["clauses"]:
            cid = clause["clause_id"]
            if cid == "other":
                page.locator(".other-group > summary").click()
            page.locator(f'[data-testid="clause-row"][data-clause="{cid}"]').click()
            assert_wait_context_fits(page, width)
            page.get_by_test_id("claim-details").locator("summary").click()
            if page.get_by_test_id("gaps").count():
                page.get_by_test_id("gaps").locator("summary").click()
            assert_plain(page)
            page.get_by_test_id("claim-details").locator("summary").click()
            if page.get_by_test_id("more-pages").count():
                page.get_by_test_id("more-pages").click()
                more = page.locator("#morePages")
                assert more.evaluate("el => el.scrollHeight === el.clientHeight")
                for group in more.locator("section").all():
                    expect(group.get_by_role("heading")).to_be_visible()
                # Both groups and the page viewer stay in normal document flow.
                assert more.bounding_box()["y"] + more.bounding_box()["height"] <= (
                    page.locator("#fileScroll").bounding_box()["y"])
                if case_id == "A-0142" and more.locator("section").count() == 2:
                    polish_screenshot(page, width, "more-pages")
                    photographed_more = True
                page.get_by_test_id("more-pages").click()
            if case_id == "E-02" and cid == "prio-category":
                links = page.get_by_test_id("compare-pages")
                expected = {tuple(sorted((view["sources"][pair["a"]]["page"],
                                          view["sources"][pair["b"]]["page"])))
                            for pair in clause["contradictions"]}
                actual = [tuple(sorted(map(int, re.findall(r"\d+", label))))
                          for label in links.all_text_contents()]
                assert len(actual) == len(set(actual)) and set(actual) == expected
                boxes = [link.bounding_box() for link in links.all()]
                assert len({box["x"] for box in boxes}) == 1
                assert all(a["y"] + a["height"] <= b["y"]
                           for a, b in zip(boxes, boxes[1:], strict=False))
                sentence = page.get_by_test_id("question-warning").locator("p").inner_text()
                assert {int(n) for n in re.findall(r"\bpage (\d+)", sentence, re.I)} == {
                    n for pair in expected for n in pair}
                polish_screenshot(page, width, "warning-pairs")
                for i, pair in enumerate(actual):
                    before = page.locator("#passageCount").inner_text()
                    links.nth(i).click()
                    comparison = page.locator("#comparison")
                    expect(comparison).to_be_visible()
                    assert set(comparison.locator("[data-page]").evaluate_all(
                        "els => els.map(el => Number(el.dataset.page))")) == set(pair)
                    expect(page.locator("#passageCount")).to_have_text(before)
                    comparison.locator('[data-act="compare-close"]').click()
            for passage in page.get_by_test_id("flagged-item").all():
                passage.click()
            assert_wait_context_fits(page, width)
            if cid != "other":
                assert page.locator('[data-outcome]:checked').count() == 0
                if case_id == "A-0142" and not photographed_identity:
                    expect(page.get_by_test_id("next-action")).to_contain_text("set your outcome")
                    polish_screenshot(page, width, "identity-outcome")
                    photographed_identity = True
                page.get_by_test_id(f"outcome-{cid}-cannot_decide").check()
        if case_id == "A-0142":
            assert photographed_more and photographed_identity
        page.get_by_test_id("sign-btn").click()
        expect(page.get_by_test_id("reason")).to_have_attribute(
            "placeholder", re.compile("Name the questions and pages"))
        assert_plain(page)
        page.get_by_test_id("decision-request_information").check()
        page.get_by_test_id("reason").fill("Further evidence is needed before deciding.")
        page.get_by_test_id("continue-btn").click()
        expect(page.get_by_test_id("check-answers")).to_contain_text("Question outcomes")
        assert_plain(page)
        page.get_by_test_id("about-btn").click()
        assert not re.search(r"\bclauses?\b", page.locator("#about").inner_text(), re.I)
        browser.close()
    assert errors == []


def test_light_palette_text_pairs_have_wcag_contrast():
    """Compute contrast from the actual declared palette used by the single stylesheet."""
    css = (ROOT / "web/theme.css").read_text(encoding="utf-8")
    colours = dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6});", css))

    def luminance(hex_colour):
        values = [int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in values]
        return sum(c * w for c, w in zip(linear, (0.2126, 0.7152, 0.0722), strict=True))

    pairs = [("ink", "paper"), ("ink", "viewer"), ("ink", "highlight"),
             ("secondary", "paper"), ("secondary", "viewer"), ("secondary", "selected"),
             ("paper", "header"), ("paper", "primary"), ("paper", "button-edge"),
             ("primary", "paper"), ("primary", "viewer"), ("primary", "selected"),
             ("header", "secondary-button"), ("flag", "paper"), ("flag", "viewer"),
             ("flag", "warning-bg"), ("primary", "warning-bg"), ("ink", "warning-bg")]
    for foreground, background in pairs:
        light, dark = sorted((luminance(colours[foreground]), luminance(colours[background])),
                             reverse=True)
        ratio = (light + 0.05) / (dark + 0.05)
        assert ratio >= 4.5, (foreground, background, ratio)
    assert "data-theme=\"dark\"" not in css and "prefers-color-scheme" not in css
    for path in (ROOT / "web").iterdir():
        if path.suffix in (".html", ".js", ".css"):
            assert "tokens.css" not in path.read_text(encoding="utf-8")


@pytest.mark.parametrize("case_id", ["stub", "A-0142"])
@pytest.mark.parametrize("missed_only", [False, True])
def test_question_without_any_cited_page_keeps_outcome_unset(case_id, missed_only, tmp_path):
    from playwright.sync_api import expect, sync_playwright

    view = json.loads((ROOT / "runs" / case_id / "view.json").read_text(encoding="utf-8"))
    clause = next(c for c in view["clauses"] if c["clause_id"] != "other")
    cid = clause["clause_id"]
    removed = set(clause["claim_ids"])
    clause.update(claim_ids=[], possibly_missed=[], contradictions=[],
                  coverage="no_evidence_in_file", missing=[])
    if missed_only:
        # Preserve the scan's strength order rather than sorting by page number.
        pages = {}
        for pid, source in view["sources"].items():
            if source["exists"] and source["kind"] == "case":
                pages.setdefault(source["page"], pid)
        clause["possibly_missed"] = [
            {"passage_id": pages[n], "score": 100 - rank}
            for rank, n in enumerate(sorted(pages, reverse=True)[:5])]
        clause["coverage"] = "possibly_missed"
    view["claims"] = [c for c in view["claims"] if c["claim_id"] not in removed]
    view["required_reading"] = [dict(r, clause_ids=[c for c in r["clause_ids"] if c != cid],
                                     claim_ids=[c for c in r["claim_ids"] if c not in removed])
                                for r in view["required_reading"] if r["clause_ids"] != [cid]]
    run = tmp_path / "run"
    run.mkdir()
    (run / "view.json").write_text(dumps(view), encoding="utf-8", newline="\n")
    errors = []
    with serving(case_id, run, tmp_path / "records") as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(base)
        page.get_by_test_id("intro-dismiss").click()
        if page.get_by_test_id("clean-questions").count():
            page.get_by_test_id("clean-toggle").click()
        page.locator(f'[data-testid="clause-row"][data-clause="{cid}"]').click()
        expect(page.get_by_test_id("clause-title")).to_have_text(clause["title"])
        if missed_only:
            required, cited, expected_tabs, expected_more = question_page_groups(view, clause)
            assert not required and not cited
            tabs = page.get_by_test_id("page-tab")
            assert tabs.evaluate_all("els => els.map(e => e.dataset.arg)") == expected_tabs
            strongest = view["sources"][clause["possibly_missed"][0]["passage_id"]]
            expect(page.get_by_test_id("file-page")).to_have_attribute(
                "data-page", str(strongest["page"]))
            expect(page.get_by_test_id("more-pages")).to_have_text(
                f"More pages ({len(expected_more)})")
            page.get_by_test_id("more-pages").click()
            expect(page.locator("#morePages").get_by_role("heading")).to_have_text(
                "Possibly missed")
            assert page.get_by_test_id("more-page").evaluate_all(
                "els => els.map(e => e.dataset.arg)") == expected_more
            assert_tab_labels_fit(page.locator(".page-tabs button"))
        else:
            expect(page.get_by_test_id("question-warning")).to_contain_text("Evidence not found")
            expect(page.locator("#reader")).to_contain_text("No page is cited")
            expect(page.locator("#reader")).to_contain_text("Missing evidence does not mean")
            expect(page.get_by_test_id("page-tab")).to_have_count(0)
        expect(page.get_by_test_id("outcome-state")).to_have_text("not set")
        assert page.locator('[data-outcome]:checked').count() == 0
        page.get_by_test_id("open-full-file").click()
        expect(page.locator("#fileScroll").get_by_test_id("file-page")).to_have_count(
            view["case"]["pages"])
        assert_no_overflow(page)
        browser.close()
    assert errors == []


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
