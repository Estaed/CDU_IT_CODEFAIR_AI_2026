"""The review screen, headless: open the required passages one at a time, see the lock lift,
sign, and find the decision record with opened_at and seconds_in_view per passage."""

import json
import socket
import threading
import time

import pytest
import uvicorn
from conftest import needs_pdfs

from readmark import ROOT
from readmark import record as rec
from readmark.serve import create_app

STUB_RUN = ROOT / "runs" / "stub"
VIEW = json.loads((STUB_RUN / "view.json").read_text(encoding="utf-8"))


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def server(tmp_path):
    """The app on a free port (no shared-device lock needed), records in a temp folder."""
    port = _free_port()
    config = uvicorn.Config(create_app("stub", run_dir=STUB_RUN, records_dir=tmp_path),
                            host="127.0.0.1", port=port, log_level="warning")
    srv = uvicorn.Server(config)
    thread = threading.Thread(target=srv.run, daemon=True)
    thread.start()
    deadline = time.time() + 20
    while not srv.started and time.time() < deadline:
        time.sleep(0.05)
    assert srv.started, "server did not start"
    yield f"http://127.0.0.1:{port}", tmp_path
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


@needs_pdfs
def test_review_screen_end_to_end(server):
    from playwright.sync_api import expect, sync_playwright

    base, records_dir = server
    required = [i["passage_id"] for i in VIEW["required_reading"]]
    assert required, "the stub run should flag at least one passage"
    errors: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(base + "/")
        expect(page.get_by_test_id("req-item")).to_have_count(len(required))

        # No outcome is pre-filled: every outcome control starts unchecked.
        assert page.locator('[data-outcome][aria-checked="true"]').count() == 0

        # Locked before: the banner names what is missing.
        page.get_by_test_id("sign-btn").click()
        banner = page.get_by_test_id("lock-banner")
        expect(banner).to_contain_text("Sign-off is locked")
        expect(banner).to_contain_text("Open the required passages")
        expect(page.get_by_test_id("dialog")).to_be_hidden()

        # The officer sets every clause outcome.
        for clause in VIEW["clauses"]:
            if clause["clause_id"] == "other":
                continue
            value = "cannot_decide" if clause["clause_id"] == "elig-income" else "met"
            page.get_by_test_id(f"outcome-{clause['clause_id']}-{value}").click()
        expect(banner).not_to_contain_text("Set your outcome")

        # Dispute one claim with a reason.
        first = VIEW["claims"][0]["claim_id"]
        page.locator(f'[data-dispute="{first}"]').click()
        page.get_by_test_id("dispute-reason").fill("The birth certificate copy is not in the file.")
        page.locator(f'[data-dispute-save="{first}"]').click()

        # Open the required passages one by one; only one is ever shown.
        for n, pid in enumerate(required, start=1):
            page.locator(f'[data-testid="req-item"][data-pid="{pid}"]').click()
            expect(page.get_by_test_id("source")).to_have_count(1)
            expect(page.get_by_test_id("source")).to_have_attribute("data-pid", pid)
            expect(page.locator("#gateCount")).to_have_text(f"{n}/{len(required)}")
            page.wait_for_timeout(400)
            if n < len(required):
                page.get_by_test_id("sign-btn").click()
                expect(page.get_by_test_id("dialog")).to_be_hidden()

        # Unlocked after: the dialog asks for a decision and a reason.
        page.get_by_test_id("sign-btn").click()
        expect(page.get_by_test_id("dialog")).to_be_visible()
        expect(page.get_by_test_id("lock-banner")).to_have_count(0)
        page.get_by_test_id("decision-request_information").check()
        page.get_by_test_id("reason").fill("Eligibility §3: no income evidence in the file.")
        page.get_by_test_id("confirm-sign").click()
        expect(page.get_by_test_id("record")).to_be_visible()

        href = page.get_by_test_id("export-json").get_attribute("href")
        record = page.request.get(base + href).json()
        html = page.request.get(base + page.get_by_test_id("export-html").get_attribute("href"))
        assert html.ok and "Decision record" in html.text()
        page.set_viewport_size({"width": 1440, "height": 900})
        browser.close()

    assert errors == []
    opened = {p["passage_id"]: p for p in record["passages_opened"]}
    assert set(required) <= set(opened)
    for p in record["passages_opened"]:
        assert p["opened_at"] and isinstance(p["seconds_in_view"], float)
    assert all(opened[pid]["seconds_in_view"] > 0 for pid in required[:-1])
    assert record["decision"] == "request_information"
    assert record["disputes"][0]["claim_id"] == first
    assert {o["outcome"] for o in record["clause_outcomes"]} == {"met", "cannot_decide"}
    assert sorted(f.suffix for f in records_dir.iterdir()) == [".html", ".json"]
