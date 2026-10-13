"""One self-contained HTML of the two showcase cases, for testers who cannot install Python.

    uv run python scripts/single_html.py      # writes dist/readmark.html

The server's answers are captured from a clean checkout of HEAD (a temporary git worktree), so
local uploads, signed records and the git-ignored policy PDFs never enter the file. As in the
README's quick start without PDFs, a full policy page stays closed and the quoted sentences show.
`single_html_shim.js` answers the screen's requests from those captures in the browser; word
search and signing run there too. Uploads, new question lists and meaning search need the app.
"""

import json
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dist" / "readmark.html"
SHIM = Path(__file__).with_name("single_html_shim.js")
CASES = ("A-0142", "W-01")
CASE_GETS = ("/api/view", "/api/case-pages", "/api/settings", "/api/question-list",
             "/api/intake-note", "/api/context")
SCRIPTS = ("home.js", "upload.js", "lists.js", "app.js", "search.js")


def serve(tree: Path, uploads: Path) -> str:
    """Start the real app from the clean checkout on a free local port; return its base URL."""
    sys.path.insert(0, str(tree))
    import uvicorn

    from readmark import serve as server
    assert Path(server.__file__).is_relative_to(tree), "readmark must load from the worktree"
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    app = server.create_app(runs_root=tree / "runs", uploads_root=uploads)
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    instance = uvicorn.Server(config)
    threading.Thread(target=instance.run, daemon=True).start()
    while not instance.started:
        time.sleep(0.05)
    return f"http://127.0.0.1:{port}"


def get(base: str, url: str) -> dict:
    try:
        with urllib.request.urlopen(base + url) as response:
            return {"status": response.status, "body": json.load(response)}
    except urllib.error.HTTPError as err:
        return {"status": err.code, "body": json.load(err)}


def capture(base: str) -> dict:
    answers = {}
    for url in ("/api/cases", "/api/settings"):
        answers[url] = get(base, url)
    home = answers["/api/cases"]["body"]
    # A clean checkout shows exactly the showcase cases, unsigned, with no uploads or drafts.
    assert sorted(c["case_id"] for c in home["cases"]) == sorted(CASES), home["cases"]
    assert not any(c["signed"] for c in home["cases"]) and not home["uploads"]
    for item in home["question_lists"]:
        if item["coverage_count"] is not None:
            url = f"/api/question-lists/{item['id']}/coverage"
            answers[url] = get(base, url)
    for cid in CASES:
        for path in CASE_GETS:
            url = f"{path}?case={cid}"
            answers[url] = get(base, url)
            assert answers[url]["status"] == 200, (url, answers[url])
    # Without the PDFs the server refuses a full policy page; the build keeps that refusal.
    view = answers["/api/view?case=A-0142"]["body"]
    pid = next(p for p, s in view["sources"].items() if s["kind"] == "policy")
    closed = get(base, f"/api/passages/{pid}?case=A-0142")
    assert closed["status"] == 503, closed
    return {"answers": answers, "policy_closed": closed}


def inline(snapshot: dict) -> str:
    web = ROOT / "web"
    page = (web / "index.html").read_text(encoding="utf-8")

    def script(text: str) -> str:
        return "<script>\n" + text.replace("</script", "<\\/script") + "\n</script>"

    def swap(old: str, new: str) -> None:
        nonlocal page
        assert page.count(old) == 1, old
        page = page.replace(old, new)

    swap('<link rel="stylesheet" href="theme.css">',
         "<style>\n" + (web / "theme.css").read_text(encoding="utf-8") + "\n</style>")
    icon = (web / "mark.svg").read_text(encoding="utf-8")
    swap('href="mark.svg"', 'href="data:image/svg+xml,' + urllib.request.quote(icon) + '"')
    data = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    shim = f"window.READMARK_SNAPSHOT = {data};\n" + SHIM.read_text(encoding="utf-8")
    for i, name in enumerate(SCRIPTS):
        text = (web / name).read_text(encoding="utf-8")
        if name == "search.js":
            # A file:// page has the origin "null", which URL() rejects as a base.
            assert text.count("location.origin") == 1
            text = text.replace("location.origin", "location.href")
        swap(f'<script src="{name}"></script>', (script(shim) + "\n" if i == 0 else "") + script(text))
    return page


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="readmark-single-"))
    tree = tmp / "tree"
    subprocess.run(["git", "worktree", "add", "--detach", str(tree), "HEAD"], cwd=ROOT,
                   check=True, capture_output=True)
    try:
        (tmp / "uploads").mkdir()
        snapshot = capture(serve(tree, tmp / "uploads"))
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(tree)], cwd=ROOT, check=True)
        shutil.rmtree(tmp, ignore_errors=True)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(inline(snapshot), encoding="utf-8", newline="\n")
    print(f"{OUT.relative_to(ROOT)}: {OUT.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
