"""``python -m readmark serve``: the review screen on localhost.

Serves ``web/`` as static files, the case's ``view.json``, policy passage text read from the
pinned PDFs on demand (so no policy text is ever stored under ``runs/``), and saves decision
records under ``runs/<case>/records/`` as JSON and HTML.
"""

import json
from functools import cache
from pathlib import Path
from typing import Annotated

import uvicorn
from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from readmark import WEB_DIR, case_run_dir
from readmark import record as rec
from readmark.ingest import IngestError, policy_passages


@cache
def _policy_text() -> dict[str, str]:
    return {p["passage_id"]: p["text"] for p in policy_passages()}


def create_app(case_id: str, run_dir: Path | None = None,
               records_dir: Path | None = None) -> FastAPI:
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
            record = rec.build(payload, view())
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
