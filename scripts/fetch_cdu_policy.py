"""Fetch the CDU coursework assessment policy for the easy example's question list.

CDU publishes the policy as a web page, not a PDF. Its copyright terms allow downloading and
reproducing it for private or in-organisation, non-commercial use, but not publishing it. So the
repo keeps this script, the pin and the short question sentences, and never the policy text: the
text file is git-ignored, and each user rebuilds it with this script.

    python scripts/fetch_cdu_policy.py

The output is plain UTF-8 text, one paragraph per block, which the question-list ingest reads as a
single page. Ingest then checks the file's SHA-256 against the pin in the list's `list.yaml`, so a
changed web page fails loudly instead of silently changing the questions' source.
"""
import hashlib
import html
import re
import sys
import urllib.request
from pathlib import Path

URL = "https://policies.cdu.edu.au/view-current.php?id=177"
OUT = (Path(__file__).resolve().parents[1] / "data" / "policies" / "cdu-extension"
       / "cdu-coursework-assessment.txt")


def paragraphs(page: str) -> list[str]:
    # Drop scripts and styles, turn block ends into paragraph breaks, then strip the tags.
    page = re.sub(r"(?is)<(script|style).*?</\1>", "", page)
    page = re.sub(r"(?i)<br\s*/?>", "\n", page)
    page = re.sub(r"(?i)</(p|li|h[1-6]|tr|div|td|th)>", "\n\n", page)
    text = html.unescape(re.sub(r"<[^>]+>", "", page))
    lines = [re.sub(r"[ \t ]+", " ", line).strip() for line in text.splitlines()]
    out, current = [], []
    for line in lines:
        if line:
            current.append(line)
        elif current:
            out.append(" ".join(current))
            current = []
    if current:
        out.append(" ".join(current))
    return out


def policy_body(paras: list[str]) -> list[str]:
    # The page repeats the section list as a contents block; the body starts at the second
    # "Section 1 - Preamble" and ends before the site footer.
    starts = [i for i, p in enumerate(paras) if p.endswith("Section 1 - Preamble")]
    end = next(i for i, p in enumerate(paras) if p.startswith("Charles Darwin University acknowledges"))
    body = paras[starts[-1]:end]
    return [re.sub(r"^Top of Page", "", p).strip() for p in body if p.strip() != "Top of Page"]


def main() -> int:
    request = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (Readmark fetch)"})
    page = urllib.request.urlopen(request, timeout=60).read().decode("utf-8", errors="replace")
    body = policy_body(paragraphs(page))
    title = "Higher Education Coursework Assessment Policy and Procedure"
    text = "\n\n".join([title, *body]) + "\n"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(text.encode("utf-8"))
    digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
    print(f"{OUT} ({len(body)} paragraphs)\nsha256 {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
