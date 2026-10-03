"""``python -m readmark serve``: the review screen on localhost.

Serves ``web/`` as static files, the case's ``view.json``, policy passage text read from the
pinned PDFs on demand (so no policy text is ever stored under ``runs/``), and saves decision
records under ``runs/<case>/records/`` as JSON and HTML.
"""

import csv
import hashlib
import json
import sys
from functools import cache
from pathlib import Path
from typing import Annotated

import uvicorn
from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from readmark import DATA, WEB_DIR, dumps, runs_dir
from readmark import record as rec
from readmark.checklist import case_question_list, list_question_lists, load_question_list
from readmark.ingest import IngestError, case_passages, policy_passages


@cache
def _policy_text(list_id: str) -> dict[str, str]:
    return {p["passage_id"]: p["text"]
            for p in policy_passages(question_list=load_question_list(list_id))}


def create_app(case_id: str | None = None, run_dir: Path | None = None,
               records_dir: Path | None = None,
               opened_seconds: float = rec.OPENED_SECONDS,
               runs_root: Path | None = None) -> FastAPI:
    # opened_seconds is a parameter only so tests can run on a short clock; the CLI never sets it,
    # so the shipped screen and record always use rec.OPENED_SECONDS.
    root = runs_root if runs_root is not None else runs_dir()
    default_run = run_dir or (root / case_id if case_id else None)
    app = FastAPI(title="Readmark", docs_url=None, redoc_url=None, openapi_url=None)

    def folder(cid: str) -> Path:
        # A request can select an existing run, never supply an arbitrary filesystem path.
        if not rec.RECORD_ID.fullmatch(cid) or cid == "eval":
            raise HTTPException(404, "Unknown case.")
        return default_run if cid == case_id and default_run else root / cid

    def selected(request: Request) -> str:
        cid = request.query_params.get("case", case_id)
        if not cid:
            raise HTTPException(400, "Choose a case from the home screen.")
        folder(cid)
        return cid

    def record_folder(cid: str) -> Path:
        return records_dir if cid == case_id and records_dir else folder(cid) / "records"

    def view(cid: str) -> dict:
        path = folder(cid) / "view.json"
        if not path.exists():
            raise HTTPException(404, f"No view for {cid}: run `python -m readmark run "
                                     f"--case {cid} --replay` first.")
        return json.loads(path.read_text(encoding="utf-8"))

    def draft_key(v: dict) -> str:
        pin = hashlib.sha256(dumps(v).encode("utf-8")).hexdigest()
        return f"readmark-case-{v['case']['case_id']}-{pin}"

    def signed(cid: str) -> dict | None:
        record = rec.latest(record_folder(cid), cid)
        if record is None:
            return None
        rid = record["record_id"]
        return {"record_id": rid, "decision": record["decision"],
                "signed_at": record["signed_at"],
                "json_url": f"/api/records/{rid}.json?case={cid}",
                "html_url": f"/api/records/{rid}.html?case={cid}"}

    @app.get("/api/cases")
    def get_cases():
        ids = {p.parent.name for p in root.glob("*/view.json")}
        if case_id and default_run and (default_run / "view.json").exists():
            ids.add(case_id)
        result = []
        for cid in sorted(ids - {"stub", "eval"}):
            v = view(cid)
            spec = load_question_list(case_question_list(cid))
            clauses = [c for c in v["clauses"] if c["clause_id"] != "other"]
            claims = {c["claim_id"]: c for c in v["claims"]}
            required = {cid for r in v["required_reading"] for cid in r["clause_ids"]}
            flags = [c["title"] for c in clauses
                     if c["contradictions"] or c["missing"]
                     or c["coverage"] == "no_evidence_in_file" or c["clause_id"] in required
                     or any(claims[q]["status"] != "supported" for q in c["claim_ids"])]
            result.append({"case_id": cid, "name": v["case"].get("title") or f"Applicant file {cid}",
                           "pages": v["case"]["pages"],
                           "documents": v["case"].get("documents", []),
                           "question_list": {"id": spec["id"], "title": spec["title"]},
                           "question_ids": [c["clause_id"] for c in clauses],
                           "flags": flags, "required_count": len(v["required_reading"]),
                           "draft_key": draft_key(v), "signed": signed(cid),
                           "evaluation": cid in {"E-01", "E-02", "E-03", "H-01"}})
        return {"cases": result, "question_lists": list_question_lists()}

    @app.get("/api/question-list")
    def get_question_list(request: Request):
        cid = selected(request)
        view(cid)
        spec = load_question_list(case_question_list(cid))
        return {"id": spec["id"], "title": spec["title"], "policies": spec["policies"]}

    @app.get("/api/view")
    def get_view(request: Request):
        return view(selected(request))

    @app.get("/api/settings")
    def get_settings(request: Request):
        # One threshold, shared by browser timing, record validation and the footnote.
        cid = request.query_params.get("case", case_id)
        return {"opened_seconds": opened_seconds, "default_case": case_id,
                "draft_key": draft_key(view(cid)) if cid else None,
                "signed": signed(cid) if cid else None}

    @app.get("/api/context")
    def get_context():
        # This historical context stays separate from the view, checks and decision record.
        with (DATA / "context" / "urban-public-housing-2020-12.csv").open(
                encoding="utf-8-sig", newline="") as file:
            rows = [row for row in csv.reader(file) if row and any(row)]
        assert rows[0][0] == "Estimated Urban Public Housing Wait Times as at 31 December 2020"
        assert rows[1][1:4] == ["1 bedroom", "2 bedroom", "3 bedroom"]
        darwin = next(row for row in rows[2:] if row[0] == "Darwin/Casuarina")
        assert darwin[2] == darwin[3]
        return {
            "label": ("Darwin/Casuarina, general housing (2–3 bedrooms): estimated wait "
                      + darwin[2].replace(" to ", "–")),
            "source_url": "https://data.nt.gov.au/dataset/urban-public-housing-wait-times-"
                          "wait-list-and-allocations-december-2020",
            "period": "2020-12-31",
        }

    @app.get("/api/case-pages")
    def get_case_pages(request: Request):
        # Read only this app's synthetic case. No request parameter becomes a file path.
        cid = selected(request)
        try:
            meta, passages = case_passages(cid)
        except IngestError as exc:
            raise HTTPException(503, str(exc)) from None
        if meta["sha256"] != view(cid)["case"]["sha256"]:
            raise HTTPException(409, "The case file has changed since these checks were made.")
        pages = [{"page": n, "passages": []} for n in range(1, meta["pages"] + 1)]
        for passage in passages:
            pages[passage["page"] - 1]["passages"].append(passage)
        return {"case_id": cid, "sha256": meta["sha256"], "pages": pages}

    @app.get("/api/passages/{passage_id}")
    def get_passage(passage_id: str, request: Request):
        cid = selected(request)
        source = view(cid)["sources"].get(passage_id)
        if not source or source.get("kind") != "policy":
            raise HTTPException(404, "Only cited policy passages are served here.")
        try:
            text = _policy_text(case_question_list(cid)).get(passage_id)
        except IngestError as exc:
            raise HTTPException(503, str(exc)) from None
        if text is None:
            raise HTTPException(404, f"{passage_id} is not in the pinned policies.")
        return {"passage_id": passage_id, "text": text}

    @app.post("/api/records")
    def post_record(payload: Annotated[dict, Body()], request: Request):
        cid = selected(request)
        if signed(cid):
            raise HTTPException(409, "This case already has a signed decision record.")
        try:
            record = rec.build(payload, view(cid), opened_seconds=opened_seconds)
        except rec.RecordError as exc:
            return JSONResponse({"problems": exc.problems}, status_code=422)
        rec.save(record, record_folder(cid))
        rid = record["record_id"]
        return {"record": record, "json_url": f"/api/records/{rid}.json?case={cid}",
                "html_url": f"/api/records/{rid}.html?case={cid}"}

    @app.get("/api/records/{name}")
    def get_record(name: str, request: Request):
        cid = selected(request)
        stem, _, ext = name.rpartition(".")
        if ext not in ("json", "html") or not rec.RECORD_ID.match(stem):
            raise HTTPException(404, "Unknown record.")
        path = record_folder(cid) / name
        if not path.exists():
            raise HTTPException(404, "Unknown record.")
        return FileResponse(path, media_type="application/json" if ext == "json" else "text/html")

    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
    return app


def serve(case_id: str | None = None, port: int = 8765) -> None:
    # The CLI defaults to "stub" outside this task's lane. Distinguish its omitted flag from
    # an explicit --case stub, which must still open that file directly.
    explicit_case = any(arg == "--case" or arg.startswith("--case=") for arg in sys.argv[1:])
    case_id = None if case_id == "stub" and not explicit_case else case_id
    target = f"case {case_id}" if case_id else "case home"
    print(f"Readmark: http://localhost:{port}/  ({target}; Ctrl+C to stop)")
    uvicorn.run(create_app(case_id), host="127.0.0.1", port=port, log_level="warning")
