"""Run axe-core and keyboard checks against the local replay UI, without model calls.

Download axe-core 4.10.3 to .tmp/shots/axe-core-4.10.3.min.js, then run:
    python tests/audit_accessibility.py
Raw findings and accessible names go to .tmp/shots/wave13/accessibility.json.
This is an audit tool, not an application dependency or a network test in the gate.
"""

import hashlib
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from playwright.sync_api import expect, sync_playwright  # noqa: E402
from test_generate_list import RULES, fake_claude  # noqa: E402
from test_screen import serving  # noqa: E402

from readmark import ROOT  # noqa: E402
from readmark.checklist.generate import create_draft, suggest  # noqa: E402

AXE = ROOT / ".tmp/shots/axe-core-4.10.3.min.js"
AXE_SHA256 = "880970c081707360e64f34cea25ff91892f5bc95675b0776925b9709dd8a68bb"
OUT = ROOT / ".tmp/shots/wave13/accessibility.json"


def audit(page, name):
    page.add_script_tag(path=str(AXE))
    result = page.evaluate("""async () => {
      const r = await axe.run(document, {runOnly: {type: 'tag',
        values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice']}});
      return {version: axe.version, url: location.pathname + location.search,
        violations: r.violations, incomplete: r.incomplete,
        passes: r.passes.map(p => p.id)};
    }""")
    result["name"] = name
    result["accessible_names"] = page.locator("body").aria_snapshot()
    print(f"{name}: axe-core {result['version']}; "
          f"{len(result['violations'])} violations; "
          f"{len(result['incomplete'])} checks needing review")
    for violation in result["violations"]:
        print(f"  {violation['impact']}: {violation['id']} "
              + ", ".join(str(n["target"]) for n in violation["nodes"]))
    return result


def tab_to(page, locator, limit=180):
    """Use actual Tab presses to reach a control and inspect the drawn focus ring."""
    for _ in range(limit):
        page.keyboard.press("Tab")
        if locator.evaluate("el => el === document.activeElement"):
            focus = locator.evaluate("""el => {
              const s = getComputedStyle(el);
              return {width: s.outlineWidth, style: s.outlineStyle,
                color: s.outlineColor, visible: el.matches(':focus-visible')};
            }""")
            assert focus["visible"] and focus["style"] != "none" and focus["width"] != "0px"
            return focus
    raise AssertionError("Control was not reachable with Tab: " + str(locator))


def keyboard_review(page):
    focus = {}
    focus["open_case"] = tab_to(page, page.get_by_test_id("open-case"))
    page.keyboard.press("Enter")
    expect(page.get_by_test_id("intake-note")).to_be_visible()
    focus["close_note"] = tab_to(page, page.get_by_test_id("intake-dismiss"))
    page.keyboard.press("Enter")
    expect(page.get_by_test_id("case-search")).to_be_focused()
    focus["intro_dismiss"] = tab_to(page, page.get_by_test_id("intro-dismiss"))
    page.keyboard.press("Enter")
    focus["full_file"] = tab_to(page, page.get_by_test_id("open-full-file"))
    page.keyboard.press("Enter")
    expect(page.get_by_role("dialog", name="Full applicant file")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog", name="Full applicant file")).to_be_hidden()
    focus["outcome"] = tab_to(page, page.get_by_role("radio", name="Met", exact=True))
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    expect(page.get_by_role("radio", name="Cannot decide yet", exact=True)).to_be_checked()
    focus["next_question"] = tab_to(page, page.get_by_test_id("save-next"))
    page.keyboard.press("Enter")
    focus["about_checks"] = tab_to(page, page.get_by_test_id("about-btn"))
    page.keyboard.press("Enter")
    expect(page.get_by_test_id("about")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_test_id("about")).to_be_hidden()
    focus["recall_note"] = tab_to(page, page.get_by_test_id("intake-recall"))
    page.keyboard.press("Enter")
    expect(page.get_by_test_id("intake-dismiss")).to_be_focused()
    return focus


def main():
    if not AXE.exists():
        print(f"Missing audit tool: {AXE}", file=sys.stderr)
        return 2
    if hashlib.sha256(AXE.read_bytes()).hexdigest() != AXE_SHA256:
        print("The audit tool differs from the pinned axe-core 4.10.3 build.", file=sys.stderr)
        return 2
    (ROOT / ".tmp/runtime").mkdir(parents=True, exist_ok=True)
    reports = []
    keyboard = {}
    # Search and maintenance must stay offline even when the local .env has a real key.
    with tempfile.TemporaryDirectory(dir=ROOT / ".tmp/runtime") as temp, \
            patch("readmark.serve.load_dotenv_key", return_value=None), \
            serving(None, None, Path(temp) / "records") as base, sync_playwright() as p:
        browser = p.chromium.launch()
        for width in (1280, 1440):
            page = browser.new_page(viewport={"width": width, "height": 1000})
            page.goto(base)
            expect(page.get_by_test_id("home-case")).to_have_count(1)
            reports.append(audit(page, f"home-{width}"))
            page.get_by_test_id("open-case").click()
            expect(page.get_by_test_id("intake-note")).to_be_visible()
            reports.append(audit(page, f"case-intake-{width}"))
            page.get_by_test_id("intake-dismiss").click()
            page.get_by_test_id("intro-dismiss").click()
            reports.append(audit(page, f"question-{width}"))
            page.get_by_test_id("open-full-file").click()
            reports.append(audit(page, f"full-file-{width}"))
            page.keyboard.press("Escape")
            page.get_by_test_id("about-btn").click()
            reports.append(audit(page, f"about-{width}"))
            page.keyboard.press("Escape")
            page.close()
        page = browser.new_page(viewport={"width": 1280, "height": 1000})
        page.goto(base)
        expect(page.get_by_test_id("home-case")).to_have_count(1)
        keyboard = keyboard_review(page)
        page.close()
        browser.close()
    # Also audit the Task-27 question-list screen with a fixed, deliberately bad sentence.
    # The fixed test response replaces the model entirely; there is no live generation.
    with tempfile.TemporaryDirectory(dir=ROOT / ".tmp/runtime") as temp, \
            patch("readmark.writer.claude_cli.generate", fake_claude), \
            patch("readmark.serve.load_dotenv_key", return_value=None):
        lists = Path(temp) / "lists"
        create_draft("audit-rules", "Extension rules", "Student extensions.",
                     [("rules.txt", RULES)], lists_dir=lists)
        suggest("audit-rules", lists_dir=lists)
        with serving(None, None, None, lists_dir=lists) as base, sync_playwright() as p:
            browser = p.chromium.launch()
            for width in (1280, 1440):
                page = browser.new_page(viewport={"width": width, "height": 1000})
                page.goto(base + "/?list=audit-rules")
                rows = page.get_by_test_id("question-suggestion")
                expect(rows).to_have_count(2)
                expect(rows.nth(1).get_by_role("button", name="Approve")).to_be_disabled()
                reports.append(audit(page, f"question-list-review-{width}"))
                keyboard[f"edit_suggestion_{width}"] = tab_to(
                    page, rows.nth(1).get_by_role("button", name="Edit", exact=True))
                page.keyboard.press("Enter")
                keyboard[f"sentence_field_{width}"] = tab_to(
                    page, rows.nth(1).get_by_label("Verbatim sentence", exact=True))
                page.keyboard.press("Control+A")
                page.keyboard.type("Applicants must explain their request.")
                keyboard[f"check_sentence_{width}"] = tab_to(
                    page, rows.nth(1).get_by_role("button", name="Check changes"))
                page.keyboard.press("Enter")
                expect(rows.nth(1).get_by_role("button", name="Approve")).to_be_enabled()
                keyboard[f"approve_suggestion_{width}"] = tab_to(
                    page, rows.nth(1).get_by_role("button", name="Approve", exact=True))
                page.keyboard.press("Enter")
                expect(rows.nth(1).get_by_test_id("review-choice")).to_contain_text("Approved")
                page.close()
            browser.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"pages": reports, "keyboard": keyboard}, indent=2) + "\n",
                   encoding="utf-8", newline="\n")
    violations = sum(len(r["violations"]) for r in reports)
    print(f"Keyboard checks: {len(keyboard)} actions passed; findings: {OUT.relative_to(ROOT)}")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
