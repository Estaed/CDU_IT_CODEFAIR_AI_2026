"""``python -m readmark serve``: the review screen on localhost.

Serves ``web/`` as static files, the case's ``view.json``, policy passage text read from the
pinned PDFs on demand (so no policy text is ever stored under ``runs/``), and saves decision
records under ``runs/<case>/records/`` as JSON and HTML.
"""

import csv
import json
from functools import cache
from pathlib import Path
from typing import Annotated

import uvicorn
from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from readmark import DATA, WEB_DIR, case_run_dir
from readmark import record as rec
from readmark.ingest import IngestError, case_passages, policy_passages


@cache
def _policy_text() -> dict[str, str]:
    return {p["passage_id"]: p["text"] for p in policy_passages()}


def create_app(case_id: str, run_dir: Path | None = None,
               records_dir: Path | None = None,
               opened_seconds: float = rec.OPENED_SECONDS) -> FastAPI:
    # opened_seconds is a parameter only so tests can run on a short clock; the CLI never sets it,
    # so the shipped screen and record always use rec.OPENED_SECONDS.
    run_dir = run_dir or case_run_dir(case_id)
    records_dir = records_dir or run_dir / "records"
    app = FastAPI(title="Readmark", docs_url=None, redoc_url=None, openapi_url=None)

    def view() -> dict:
        path = run_dir / "view.json"
        if not path.exists():
            raise HTTPException(404, f"No view for {case_id}: run `python -m readmark run "
                                     f"--case {case_id} --replay` first.")
        return json.loads(path.read_text(encoding="utf-8"))

    @app.get("/api/view")
    def get_view():
        return view()

    @app.get("/api/settings")
    def get_settings():
        # One threshold, shared by browser timing, record validation and the footnote.
        return {"opened_seconds": opened_seconds}

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
    def get_case_pages():
        # Read only this app's synthetic case. No request parameter becomes a file path.
        try:
            meta, passages = case_passages(case_id)
        except IngestError as exc:
            raise HTTPException(503, str(exc)) from None
        if meta["sha256"] != view()["case"]["sha256"]:
            raise HTTPException(409, "The case file has changed since these checks were made.")
        pages = [{"page": n, "passages": []} for n in range(1, meta["pages"] + 1)]
        for passage in passages:
            pages[passage["page"] - 1]["passages"].append(passage)
        return {"case_id": case_id, "sha256": meta["sha256"], "pages": pages}

    @app.get("/api/passages/{passage_id}")
    def get_passage(passage_id: str):
        source = view()["sources"].get(passage_id)
        if not source or source.get("kind") != "policy":
            raise HTTPException(404, "Only cited policy passages are served here.")
        try:
            text = _policy_text().get(passage_id)
        except IngestError as exc:
            raise HTTPException(503, str(exc)) from None
        if text is None:
            raise HTTPException(404, f"{passage_id} is not in the pinned policies.")
        return {"passage_id": passage_id, "text": text}

    @app.post("/api/records")
    def post_record(payload: Annotated[dict, Body()]):
        try:
            record = rec.build(payload, view(), opened_seconds=opened_seconds)
        except rec.RecordError as exc:
            return JSONResponse({"problems": exc.problems}, status_code=422)
        rec.save(record, records_dir)
        rid = record["record_id"]
        return {"record": record, "json_url": f"/api/records/{rid}.json",
                "html_url": f"/api/records/{rid}.html"}

    @app.get("/api/records/{name}")
    def get_record(name: str):
        stem, _, ext = name.rpartition(".")
        if ext not in ("json", "html") or not rec.RECORD_ID.match(stem):
            raise HTTPException(404, "Unknown record.")
        path = records_dir / name
        if not path.exists():
            raise HTTPException(404, "Unknown record.")
        return FileResponse(path, media_type="application/json" if ext == "json" else "text/html")

    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
    return app


def serve(case_id: str, port: int = 8765) -> None:
    print(f"Readmark: http://localhost:{port}/  (case {case_id}; Ctrl+C to stop)")
    uvicorn.run(create_app(case_id), host="127.0.0.1", port=port, log_level="warning")
