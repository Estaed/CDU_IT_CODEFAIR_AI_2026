"""Decision record: what the officer decided, why, and what they opened first.

The server checks the same lock the screen shows (every required passage opened, every clause
outcome set by the officer) so a record can never claim a sign-off the gate did not allow. The
record says "opened", never "read": opening a passage does not prove it was read.

The HTML export is styled only by ``web/theme.css``, the Blueprint's single styling file,
inlined so the export stands alone, and
it shows every time in one zone: the one the record was signed in.
"""

import hashlib
import html
import json
import math
import re
from datetime import datetime, tzinfo
from pathlib import Path

from readmark import WEB_DIR, dumps

DECISIONS = {
    "approve": "Approve priority housing",
    "decline": "Decline",
    "request_information": "Request more information",
}
OUTCOMES = {"met": "Met", "not_met": "Not met", "cannot_decide": "Cannot decide yet"}
RECORD_ID = re.compile(r"^[0-9A-Za-z-]{1,64}$")
OPENED_SECONDS = 3
OPENED_NOTE = (f"A passage counts as opened after {OPENED_SECONDS} seconds in view, accumulated "
               "across visits. Opening a passage is recorded; it does not prove it was read.")
# The same light-only government look as the screen; no separate export stylesheet.
STYLE_FILES = ("theme.css",)


class RecordError(ValueError):
    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = problems


def _date(iso: str) -> str:
    """'2026-01-15' -> '15 Jan 2026'; anything else unchanged."""
    try:
        d = datetime.strptime(iso, "%Y-%m-%d")
    except (TypeError, ValueError):
        return str(iso or "")
    return f"{d.day} {d:%b %Y}"


def source_label(source: dict) -> str:
    """A passage in plain words: 'Page 8, paragraph 3 · <document> (15 Jan 2026)'."""
    if not source.get("exists"):
        return "A passage that is not in the file"
    if source["kind"] == "policy":
        section = (source.get("section") or "").strip()
        return f"{source['doc_title']}{' ' + section if section else ''}, page {source['page']}"
    paragraph = source["passage_id"].rsplit(":", 1)[-1]
    return (f"Page {source['page']}, paragraph {paragraph} · {source['doc_title']} "
            f"({_date(source['doc_date'])})")


def clause_label(clause: dict) -> str:
    if clause["clause_id"] == "other":
        return "Background facts (no decision needed)"
    return f"{clause['title']}, {clause['source']}" if clause.get("source") else clause["title"]


def validate(payload: dict, view: dict, opened_seconds: float = OPENED_SECONDS) -> None:
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
        elif (not isinstance(p.get("seconds_in_view"), int | float)
              or isinstance(p.get("seconds_in_view"), bool)
              or not math.isfinite(p["seconds_in_view"])
              or p["seconds_in_view"] < opened_seconds or not p.get("opened_at")):
            problems.append(f"Open {source_label(view['sources'][pid])} for at least "
                            f"{opened_seconds:g} seconds in view.")
    for item in view["required_reading"]:
        if item["passage_id"] not in opened:
            label = source_label(view["sources"][item["passage_id"]]).lower()
            problems.append(f"Open required passage {label}.")
    claims = {c["claim_id"] for c in view["claims"]}
    for d in payload.get("disputes") or []:
        if d.get("claim_id") not in claims or not str(d.get("reason") or "").strip():
            problems.append("Each dispute needs a known claim and a reason.")
    if problems:
        raise RecordError(problems)


def build(payload: dict, view: dict, now: datetime | None = None,
          opened_seconds: float = OPENED_SECONDS) -> dict:
    validate(payload, view, opened_seconds)
    signed_at = (now or datetime.now().astimezone()).isoformat(timespec="seconds")
    view_sha = hashlib.sha256(dumps(view).encode("utf-8")).hexdigest()
    required = [i["passage_id"] for i in view["required_reading"]]
    stamp = re.sub(r"[^0-9]", "", signed_at)[:14]
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    record_id = f"{view['case']['case_id']}-{stamp}-{digest[:6]}"
    claims = {c["claim_id"]: c for c in view["claims"]}
    clauses = {c["clause_id"]: c for c in view["clauses"]}
    return {
        "record_id": record_id,
        "case_id": view["case"]["case_id"],
        "integrity": {
            "case_sha256": view["case"]["sha256"],
            "case_note": "SHA-256 of the synthetic case file used for these checks.",
            "view_sha256": view_sha,
            "view_note": "SHA-256 of the review view at signing, including checks and models.",
        },
        "signed_at": signed_at,
        "officer": str(payload.get("officer") or "Delegated officer"),
        "decision": payload["decision"],
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
        # A dispute carries the claim's own words, so the record reads without the view.
        "disputes": [
            {"claim_id": d["claim_id"], "claim": claims[d["claim_id"]]["claim"],
             "clause_id": claims[d["claim_id"]]["clause_id"],
             "clause": clause_label(clauses[claims[d["claim_id"]]["clause_id"]]),
             "check_result": note_result(claims[d["claim_id"]], view),
             "citations": [dict(q, label=source_label(view["sources"][q["passage_id"]]))
                           for q in claims[d["claim_id"]]["citations"]],
             "reason": str(d["reason"]).strip(), "at": str(d.get("at") or "")}
            for d in payload.get("disputes") or []
        ],
        "models": view["models"],
        "note": OPENED_NOTE,
    }


def note_result(claim: dict, view: dict) -> str:
    """The same plain check result is used on a note and in its dispute record."""
    if claim["status"] == "quote_not_found":
        return "Quote not found in the file"
    if claim["status"] == "contradicted":
        pages = list(dict.fromkeys(view["sources"][pid]["page"]
                                  for pid in claim["contradicted_by"]))
        return (f"Page {pages[0]} says the opposite" if len(pages) == 1 else
                f"Pages {', '.join(map(str, pages))} say the opposite")
    if claim["status"] == "checker_disagrees":
        return "The second reader is not sure"
    if claim["status"] == "supported":
        return "Found in the file ✓"
    return "Nothing to check"


def for_export(record: dict) -> dict:
    """Officer-facing JSON uses question names and note text instead of internal identifiers.

    The API response still carries the internal record for the screen; file exports carry the
    same evidence, times, model provenance and integrity pins in readable terms.
    """
    return {
        **{k: v for k, v in record.items()
           if k not in ("clause_outcomes", "passages_opened", "disputes", "decision")},
        "decision": DECISIONS[record["decision"]],
        "answers_label": "Your answers to the questions",
        "question_answers": [{"question": o["title"], "answer": OUTCOMES[o["outcome"]]}
                             for o in record["clause_outcomes"]],
        "passages_opened": [{k: v for k, v in p.items() if k != "passage_id"}
                            for p in record["passages_opened"]],
        "disputes": [{"note": d["claim"], "question": d["clause"],
                      "check_result": d["check_result"], "reason": d["reason"], "at": d["at"],
                      "quotes": [{"quote": q["quote"], "source": q["label"],
                                  "check_result": ("Found in the file ✓" if q["quote_found"]
                                                   else "Quote not found in the file")}
                                 for q in d["citations"]]}
                     for d in record["disputes"]],
    }


def _zone_name(tz: tzinfo, at: datetime) -> str:
    offset = tz.utcoffset(at)
    minutes = int(offset.total_seconds() // 60) if offset is not None else 0
    sign = "+" if minutes >= 0 else "-"
    return f"UTC{sign}{abs(minutes) // 60:02d}:{abs(minutes) % 60:02d}"


def _in_zone(stamp: str, tz: tzinfo, day: datetime) -> str:
    """A timestamp from the browser (UTC, 'Z') or the server, shown in the signing zone; the
    date is added only when it differs from the signing day."""
    try:
        t = datetime.fromisoformat(str(stamp))
    except ValueError:
        return str(stamp or "")
    t = (t if t.tzinfo else t.replace(tzinfo=tz)).astimezone(tz)
    clock = f"{t:%H:%M:%S}"
    return clock if t.date() == day.date() else f"{t.day} {t:%b %Y}, {clock}"


def styles() -> str:
    """The review screen's styling files, verbatim: the export carries no CSS of its own."""
    return "\n".join((WEB_DIR / name).read_text(encoding="utf-8") for name in STYLE_FILES)


def _record_quotes(citations: list[dict]) -> str:
    # A disputed claim keeps its evidence alongside it in a standalone export.
    return "".join(
        f'<blockquote class="record-quote">“{html.escape(q["quote"])}”'
        f'<div class="sub">{html.escape(q["label"])}'
        f'{"" if q["quote_found"] else " · Quote not found"}</div></blockquote>'
        for q in citations
    ) or '<p class="note">Quote not found: no quote given.</p>'


def to_html(record: dict) -> str:
    e = html.escape
    signed = datetime.fromisoformat(record["signed_at"])
    if signed.tzinfo is None:
        signed = signed.astimezone()
    tz = signed.tzinfo
    zone = _zone_name(tz, signed)
    outcomes = "".join(
        f"<tr><td>{e(o['title'])}</td><td class=\"r\">{e(OUTCOMES[o['outcome']])}</td></tr>"
        for o in record["clause_outcomes"]
    )
    opened = "".join(
        f"<tr><td>{e(p['label'])}<div class=\"sub\">{'Required' if p['required'] else 'Optional'}"
        f"</div></td><td class=\"r mono\">{e(_in_zone(p['opened_at'], tz, signed))}</td>"
        f"<td class=\"r mono\">{p['seconds_in_view']:.1f} s</td></tr>"
        for p in record["passages_opened"]
    ) or "<tr><td colspan=\"3\">None</td></tr>"
    disputes = "".join(
        f"<li><div class=\"c\">{e(d.get('clause') or '')} · disputed at "
        f"<span class=\"mono\">{e(_in_zone(d['at'], tz, signed))}</span></div>"
        f"{_record_quotes(d.get('citations', []))}"
        f"<span class=\"tag ai\">AI note</span> “{e(d.get('claim') or '')}”"
        f"<p>{e(d.get('check_result') or '')}</p>"
        f"<div><b>Reason:</b> {e(d['reason'])}</div></li>"
        for d in record["disputes"]
    )
    disputes = (f"<ul class=\"rec-disp\">{disputes}</ul>" if disputes
                else "<p class=\"note\">The officer disputed no AI note.</p>")
    m = record["models"]
    when = f"{signed.day} {signed:%b %Y}, {signed:%H:%M:%S}"
    return f"""<!doctype html>
<html lang="en" data-theme="light"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Decision record {e(record['record_id'])}</title>
<style>
{styles()}
</style></head>
<body class="doc"><header class="service-band"><div><b>Readmark</b>
<div>Priority housing review · Decision record</div></div></header><main class="rec rec-doc">
<div class="rec-head"><h2>Decision record, applicant file {e(record['case_id'])}</h2>
<span class="tag done">Signed</span></div>
<div class="rec-dec">{e(DECISIONS[record['decision']])}</div>
<dl class="rec-dl"><dt>Reason</dt><dd><div class="rec-reason">{e(record['reason'])}</div></dd>
<dt>Signed</dt><dd><span class="mono">{e(when)}</span> by {e(record['officer'])}</dd>
<dt>Times</dt><dd>All times on this record are in {zone}, the zone it was signed in.</dd>
<dt>Record</dt><dd><span class="mono">{e(record['record_id'])}</span></dd>
<dt>Integrity</dt><dd>{e(record['integrity']['case_note'])}
<span class="mono">{e(record['integrity']['case_sha256'][:16])}…</span><br>
{e(record['integrity']['view_note'])}
<span class="mono">{e(record['integrity']['view_sha256'][:16])}…</span></dd></dl>
<h4>Your answers to the questions</h4>
<table class="rec-t"><tbody>{outcomes}</tbody></table>
<h4>Passages opened before signing</h4>
<table class="rec-t"><thead><tr><th>Passage</th><th class="r">Opened ({zone})</th>
<th class="r">Time in view</th></tr></thead><tbody>{opened}</tbody></table>
<p class="rec-note">{e(record['note'])}</p>
<h4>Disputed AI notes</h4>
{disputes}
<h4>About these checks</h4>
<p class="note">Claims drafted by {e(m['writer']['name'])} ({e(str(m['writer']['model']))}),
re-checked by {e(m['checker']['name'])} ({e(str(m['checker']['model']))}). The officer set every
question outcome and the decision; the tool recommends neither.</p>
</main></body></html>
"""


def save(record: dict, directory: Path) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / f"{record['record_id']}.json"
    html_path = directory / f"{record['record_id']}.html"
    json_path.write_text(dumps(for_export(record)), encoding="utf-8", newline="\n")
    html_path.write_text(to_html(record), encoding="utf-8", newline="\n")
    return json_path, html_path
