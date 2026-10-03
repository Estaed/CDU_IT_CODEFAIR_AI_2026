"""Decision record: what the officer decided, why, and what they opened first.

The server checks the same lock the screen shows (every required passage opened, every clause
outcome set by the officer) so a record can never claim a sign-off the gate did not allow. The
record says "opened", never "read": opening a passage does not prove it was read.
"""

import hashlib
import html
import json
import re
from datetime import datetime
from pathlib import Path

from readmark import dumps

DECISIONS = {
    "approve": "Approve priority housing",
    "decline": "Decline",
    "request_information": "Request more information",
}
OUTCOMES = {"met": "Met", "not_met": "Not met", "cannot_decide": "Cannot decide yet"}
RECORD_ID = re.compile(r"^[0-9A-Za-z-]{1,64}$")
OPENED_NOTE = "Opening a passage is recorded; it does not prove the passage was read."


class RecordError(ValueError):
    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = problems


def validate(payload: dict, view: dict) -> None:
    problems = []
    if payload.get("decision") not in DECISIONS:
        problems.append("Choose a decision.")
    if not str(payload.get("reason") or "").strip():
        problems.append("Write a reason.")
    outcomes = payload.get("clause_outcomes") or {}
    for clause in view["clauses"]:
        if clause["clause_id"] != "other" and outcomes.get(clause["clause_id"]) not in OUTCOMES:
            problems.append(f"Set an outcome for {clause['title']}.")
    opened = {p.get("passage_id"): p for p in payload.get("passages_opened") or []}
    for pid, p in opened.items():
        if pid not in view["sources"]:
            problems.append(f"Unknown passage {pid}.")
        elif not isinstance(p.get("seconds_in_view"), int | float) or not p.get("opened_at"):
            problems.append(f"Passage {pid} needs opened_at and seconds_in_view.")
    for item in view["required_reading"]:
        if item["passage_id"] not in opened:
            problems.append(f"Open required passage {item['passage_id']}.")
    claims = {c["claim_id"] for c in view["claims"]}
    for d in payload.get("disputes") or []:
        if d.get("claim_id") not in claims or not str(d.get("reason") or "").strip():
            problems.append("Each dispute needs a known claim and a reason.")
    if problems:
        raise RecordError(problems)


def source_label(source: dict) -> str:
    if not source.get("exists"):
        return f"{source['passage_id']} (not in the file)"
    if source["kind"] == "policy":
        return f"{source['doc_title']} {source.get('section') or ''}, p. {source['page']}".replace(
            "  ", " ")
    paragraph = source["passage_id"].rsplit(":", 1)[-1]
    return f"{source['doc_title']} ({source['doc_date']}), p. {source['page']} ¶{paragraph}"


def build(payload: dict, view: dict, now: datetime | None = None) -> dict:
    validate(payload, view)
    signed_at = (now or datetime.now().astimezone()).isoformat(timespec="seconds")
    view_sha = hashlib.sha256(dumps(view).encode("utf-8")).hexdigest()
    required = [i["passage_id"] for i in view["required_reading"]]
    stamp = re.sub(r"[^0-9]", "", signed_at)[:14]
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    record_id = f"{view['case']['case_id']}-{stamp}-{digest[:6]}"
    return {
        "record_id": record_id,
        "case_id": view["case"]["case_id"],
        "case_sha256": view["case"]["sha256"],
        "view_sha256": view_sha,
        "signed_at": signed_at,
        "officer": str(payload.get("officer") or "Delegated officer"),
        "decision": payload["decision"],
        "decision_label": DECISIONS[payload["decision"]],
        "reason": str(payload["reason"]).strip(),
        "clause_outcomes": [
            {"clause_id": c["clause_id"], "title": c["title"],
             "outcome": payload["clause_outcomes"][c["clause_id"]]}
            for c in view["clauses"] if c["clause_id"] != "other"
        ],
        "passages_opened": [
            {
                "passage_id": p["passage_id"],
                "label": source_label(view["sources"][p["passage_id"]]),
                "required": p["passage_id"] in required,
                "opened_at": str(p["opened_at"]),
                "seconds_in_view": round(float(p["seconds_in_view"]), 1),
            }
            for p in payload.get("passages_opened") or []
        ],
        "required_reading": required,
        "disputes": [
            {"claim_id": d["claim_id"], "reason": str(d["reason"]).strip(),
             "at": str(d.get("at") or "")}
            for d in payload.get("disputes") or []
        ],
        "models": view["models"],
        "note": OPENED_NOTE,
    }


def to_html(record: dict) -> str:
    e = html.escape
    outcomes = "".join(
        f"<tr><td>{e(o['title'])}</td><td>{e(OUTCOMES[o['outcome']])}</td></tr>"
        for o in record["clause_outcomes"]
    )
    opened = "".join(
        f"<tr><td>{e(p['label'])}{' (required)' if p['required'] else ''}</td>"
        f"<td>{e(p['opened_at'])}</td><td>{p['seconds_in_view']:.1f} s</td></tr>"
        for p in record["passages_opened"]
    ) or "<tr><td colspan=3>None</td></tr>"
    disputes = "".join(
        f"<li>{e(d['claim_id'])}: {e(d['reason'])}</li>" for d in record["disputes"]
    ) or "<li>None</li>"
    m = record["models"]
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Decision record {e(record['record_id'])}</title>
<style>body{{font:15px/1.5 system-ui,sans-serif;max-width:760px;margin:32px auto;padding:0 16px}}
table{{border-collapse:collapse;width:100%}}td,th{{border-top:1px solid #ccc;padding:6px 8px;
text-align:left;vertical-align:top}}h1{{font-size:22px}}h2{{font-size:16px;margin-top:24px}}
.muted{{color:#555}}</style></head><body>
<h1>Decision record, case {e(record['case_id'])}</h1>
<p><strong>{e(record['decision_label'])}</strong></p>
<p>Reason: {e(record['reason'])}</p>
<p class="muted">Signed {e(record['signed_at'])} by {e(record['officer'])}. Record
{e(record['record_id'])}; case file SHA-256 {e(record['case_sha256'][:16])}…</p>
<h2>Clause outcomes, set by the officer</h2><table>{outcomes}</table>
<h2>Passages opened before signing</h2>
<table><tr><th>Passage</th><th>Opened at</th><th>Time in view</th></tr>{opened}</table>
<p class="muted">{e(record['note'])}</p>
<h2>Disputed claims</h2><ul>{disputes}</ul>
<h2>Models</h2><p>Writer: {e(m['writer']['name'])} ({e(str(m['writer']['model']))}).
Checker: {e(m['checker']['name'])} ({e(str(m['checker']['model']))}).</p>
</body></html>
"""


def save(record: dict, directory: Path) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / f"{record['record_id']}.json"
    html_path = directory / f"{record['record_id']}.html"
    json_path.write_text(dumps(record), encoding="utf-8", newline="\n")
    html_path.write_text(to_html(record), encoding="utf-8", newline="\n")
    return json_path, html_path
