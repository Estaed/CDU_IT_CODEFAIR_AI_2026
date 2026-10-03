"""Screenshots for the design A/B (Task-03).

Drives direction A and direction B through the same five states with the same clicks, at
1280x900, and saves the viewport of each state to design/shots/. A is shot in dark and light;
B has one mode. Exits 1 if either page logs a console or page error.

Run from the repo root: python design/shots/shoot.py
"""

import pathlib
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "design" / "shots"
DIRECTIONS = [
    ("A", ROOT / "design" / "direction-A.html", ["dark", "light"]),
    ("B", ROOT / "design" / "direction-B.html", [None]),
]
REASON = (
    "Urgent need is documented (p. 51) and the former debt is cleared (p. 23; s3.4). "
    "No income statement in the file: request it before priority can be approved."
)


def open_page(browser, path, mode, errors):
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    page.on("console", lambda m: errors.append(f"console: {m.text}") if m.type == "error" else None)
    url = path.as_uri() + (f"?theme={mode}" if mode else "")
    page.goto(url)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(600)
    return page


def shoot(page, name):
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(250)
    page.screenshot(path=str(OUT / name))
    print("wrote", name)


def run(browser, label, path, mode, errors):
    suffix = f"-{mode}" if mode else ""
    # Chain 1: start -> item open -> gate message -> decision record.
    page = open_page(browser, path, mode, errors)
    shoot(page, f"{label}-1-start{suffix}.png")
    page.click('[data-act="open-item"][data-arg="d1"]')
    page.wait_for_timeout(2200)
    shoot(page, f"{label}-2-item-open{suffix}.png")
    page.click('[data-act="sign"]')
    page.wait_for_timeout(400)
    shoot(page, f"{label}-3-gate-message{suffix}.png")
    for pid in ["s34", "p23", "p51"]:
        page.click(f'[data-act="open-req"][data-arg="{pid}"]')
        page.wait_for_timeout(1100)
    for arg in ["debts:met", "urgent:met", "tenancy:met", "income:undecided"]:
        page.click(f'[data-act="oc"][data-arg="{arg}"]')
    page.click('[data-act="dispute"][data-arg="d1"]')
    page.fill("#dr-d1", "p. 8 is from 15 Jan; p. 23 (4 Mar) shows the arrears cleared.")
    page.click('[data-act="dsave"][data-arg="d1"]')
    page.click('[data-act="sign"]')
    page.wait_for_timeout(300)
    page.check('input[name="dec"][value="request"]')
    page.fill("#reason", REASON)
    page.click("#dlgSign")
    page.wait_for_timeout(400)
    shoot(page, f"{label}-4-record{suffix}.png")
    page.close()
    # Chain 2: a fresh page, summary-under-audit tab with p. 23 opened from sentence 2.
    page = open_page(browser, path, mode, errors)
    page.click('[data-act="tab"][data-arg="audit"]')
    page.click('[data-act="open-ref"][data-arg="d1:p23"]')
    page.wait_for_timeout(1200)
    shoot(page, f"{label}-5-audit-tab{suffix}.png")
    page.close()


def main():
    errors = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for label, path, modes in DIRECTIONS:
            for mode in modes:
                run(browser, label, path, mode, errors)
        browser.close()
    if errors:
        print("errors:", *errors, sep="\n  ")
        return 1
    print("no console or page errors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
