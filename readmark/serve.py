"""``python -m readmark serve``: the review screen on localhost.

Serves ``web/`` as static files, the case's ``view.json``, policy passage text read from the
pinned PDFs on demand (so no policy text is ever stored under ``runs/``), and saves decision
records under ``runs/<case>/records/`` as JSON and HTML.
"""

import base64
import binascii
import csv
import hashlib
import json
import shutil
import sys
from contextlib import asynccontextmanager
from functools import cache
from pathlib import Path
from threading import Lock
from typing import Annotated
from uuid import uuid4

import uvicorn
from fastapi import BackgroundTasks, Body, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from readmark import DATA, WEB_DIR, dumps, load_dotenv_key, runs_dir
from readmark import record as rec
from readmark.cache import Cache
from readmark.checklist import (
    QUESTION_LISTS_DIR, case_question_list, list_question_lists, load_question_list,
    set_case_question_list,
)
from readmark.ingest import IngestError, case_passages, policy_passages, prepare_upload
from readmark.pipeline import run
from readmark.writer.transcription import ClaudeTranscriber

UPLOAD_STEPS = ["Splitting into passages", "The AI is reading", "Checking quotes",
                "Second reader", "Ready"]
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


@cache
def _policy_text(list_id: str, lists_dir: Path = QUESTION_LISTS_DIR) -> dict[str, str]:
    spec = (load_question_list(list_id) if lists_dir == QUESTION_LISTS_DIR
            else load_question_list(list_id, lists_dir))
    return {p["passage_id"]: p["text"]
            for p in policy_passages(question_list=spec)}


def create_app(case_id: str | None = None, run_dir: Path | None = None,
               records_dir: Path | None = None,
               opened_seconds: float = rec.OPENED_SECONDS,
               runs_root: Path | None = None, uploads_root: Path | None = None,
               lists_dir: Path = QUESTION_LISTS_DIR, pipeline_runner=None,
               transcriber=None) -> FastAPI:
    # opened_seconds is a parameter only so tests can run on a short clock; the CLI never sets it,
    # so the shipped screen and record always use rec.OPENED_SECONDS.
    root = runs_root if runs_root is not None else runs_dir()
    uploads = uploads_root if uploads_root is not None else DATA / "uploads"
    default_run = run_dir or (root / case_id if case_id else None)
    job_lock = Lock()

    def save_job(job: dict) -> None:
        path = uploads / job["case_id"] / "job.json"
        temporary = path.with_suffix(".tmp")
        # Windows readers can briefly prevent replacing an open file. Serialize reads
        # with publication so polling never sees partial JSON or blocks the worker's save.
        with job_lock:
            temporary.write_text(dumps(job), encoding="utf-8", newline="\n")
            temporary.replace(path)

    @asynccontextmanager
    async def lifespan(app):
        # A restarted process cannot still be running an old background check.
        for path in uploads.glob("*/job.json"):
            job = json.loads(path.read_text(encoding="utf-8"))
            if job["status"] == "running":
                job.update(status="failed", message="The checks were interrupted; your files are kept.")
                save_job(job)
        yield

    app = FastAPI(title="Readmark", docs_url=None, redoc_url=None, openapi_url=None,
                  lifespan=lifespan)

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

    def spec_for(cid: str) -> dict:
        if cid.startswith("U-"):
            list_id = case_question_list(cid, case_dir=uploads / cid, lists_dir=lists_dir)
            return load_question_list(list_id, lists_dir)
        return load_question_list(case_question_list(cid))

    def upload_job(cid: str) -> dict:
        folder(cid)
        path = uploads / cid / "job.json"
        if not cid.startswith("U-") or not path.is_file():
            raise HTTPException(404, "Unknown upload.")
        with job_lock:
            return json.loads(path.read_text(encoding="utf-8"))

    def check_upload(job: dict, documents: list[dict]) -> None:
        def progress(stage: str):
            if stage not in job["steps"]:
                job["steps"].append(stage)
                save_job(job)

        try:
            progress(UPLOAD_STEPS[0])
            cid = job["case_id"]
            # Test runners inject both model interfaces. Live runs fail before spending
            # writer quota when the second reader's key or the writer CLI is missing.
            if pipeline_runner is None:
                if not load_dotenv_key("TYPESAFE_API_KEY"):
                    raise IngestError("The second reader's key is missing; your files are kept.")
                if not shutil.which("claude"):
                    raise IngestError("The AI reader is unavailable; your files are kept.")
            reader = transcriber or ClaudeTranscriber(Cache(folder(cid) / "cache", replay=False))
            case_file = prepare_upload(cid, job["name"], documents, uploads / cid,
                                       transcriber=reader, progress=progress)
            (pipeline_runner or run)(cid, case_file=case_file, lists_dir=lists_dir,
                                     out_dir=folder(cid), audit=False, progress=progress)
            if not (folder(cid) / "view.json").exists():
                raise RuntimeError("The pipeline did not produce a case view")
            job.update(status="ready", message="Ready")
        except IngestError as exc:
            # Extraction and preflight errors above are already plain sentences. Policy
            # errors include paths and hashes, so do not expose their internal wording.
            known = ("A scanned page", "A document", "A text page", "The second reader's key",
                     "The AI reader is unavailable")
            message = str(exc)
            job.update(status="failed", message=message if message.startswith(known) else
                       "The selected policies could not be read; your files are kept.")
        except Exception:
            stage = job["steps"][-1] if job["steps"] else UPLOAD_STEPS[0]
            message = {
                "Reading scanned pages": "The scanned pages could not be read; your files are kept.",
                "The AI is reading": "The AI reader could not finish; your files are kept.",
                "Second reader": "The second reader could not finish; your files are kept.",
            }.get(stage, "The checks could not finish; your files are kept.")
            job.update(status="failed", message=message)
        save_job(job)

    @app.post("/api/cases", status_code=202)
    async def post_case(request: Request, background: BackgroundTasks):
        # JSON with base64 files avoids a new multipart dependency. Bound the body before
        # decoding it, and save only generated paths, never a client-supplied file path.
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > MAX_UPLOAD_BYTES * 4 // 3 + 1024 * 1024:
                raise HTTPException(413, "Choose files totalling no more than 25 MB.")
        try:
            payload = json.loads(body)
            name = payload["name"].strip()
            list_id = payload["question_list"]
            files = payload["files"]
            if not name or len(name) > 120 or not isinstance(files, list) or not files:
                raise ValueError
            load_question_list(list_id, lists_dir)
            decoded = []
            for item in files:
                filename = item["name"].replace("\\", "/").rsplit("/", 1)[-1]
                suffix = Path(filename).suffix.lower()
                if suffix not in {".pdf", ".txt", ".md"} or len(filename) > 255:
                    raise ValueError
                content = base64.b64decode(item["content"], validate=True)
                decoded.append((filename, suffix, content))
        except (ValueError, KeyError, TypeError, AttributeError, IngestError, binascii.Error):
            raise HTTPException(422, "Enter a case name, choose a question list and add PDF or text files.") from None
        if sum(len(content) for _, _, content in decoded) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "Choose files totalling no more than 25 MB.")
        cid = "U-" + uuid4().hex
        destination = uploads / cid
        (destination / "originals").mkdir(parents=True)
        documents = []
        for n, (filename, suffix, content) in enumerate(decoded, 1):
            doc_id = f"d{n:02d}"
            relative = f"originals/{doc_id}{suffix}"
            (destination / relative).write_bytes(content)
            documents.append({"doc_id": doc_id, "name": filename, "file": relative})
        set_case_question_list(cid, list_id, case_dir=destination, lists_dir=lists_dir)
        job = {"case_id": cid, "name": name, "question_list": list_id,
               "files": [doc["name"] for doc in documents], "status": "running",
               "steps": [], "message": None}
        save_job(job)
        background.add_task(check_upload, job, documents)
        return {"case_id": cid, "status_url": f"/api/uploads/{cid}"}

    @app.get("/api/uploads/{cid}")
    def get_upload(cid: str):
        return upload_job(cid)

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
            if cid.startswith("U-") and upload_job(cid)["status"] != "ready":
                continue
            v = view(cid)
            spec = spec_for(cid)
            words = rec.wording(spec)
            clauses = [c for c in v["clauses"] if c["clause_id"] != "other"]
            claims = {c["claim_id"]: c for c in v["claims"]}
            problems = {c["clause_id"] for c in clauses
                        if c["contradictions"] or c["missing"]
                        or c["coverage"] == "no_evidence_in_file"
                        or any(claims[q]["status"] != "supported" for q in c["claim_ids"])}
            flags = [c["title"] for c in clauses if c["clause_id"] in problems]
            worth = [c["title"] for c in clauses
                     if c["clause_id"] not in problems and c["possibly_missed"]]
            result.append({"case_id": cid,
                           "name": v["case"].get("title") or f"{words['labels']['case_noun']} {cid}",
                           **words,
                           "pages": v["case"]["pages"],
                           "documents": v["case"].get("documents", []),
                           "question_list": {"id": spec["id"], "title": spec["title"]},
                           "question_ids": [c["clause_id"] for c in clauses],
                           "flags": flags, "worth_a_look": worth,
                           "required_count": len(v["required_reading"]),
                           "draft_key": draft_key(v), "signed": signed(cid),
                           "evaluation": cid in {"E-01", "E-02", "E-03", "H-01"}})
        with job_lock:
            pending = [json.loads(p.read_text(encoding="utf-8")) for p in
                       sorted(uploads.glob("*/job.json"))]
        return {"cases": result, "question_lists": list_question_lists(lists_dir),
                "uploads": [job for job in pending if job["status"] != "ready"]}

    @app.get("/api/question-list")
    def get_question_list(request: Request):
        cid = selected(request)
        view(cid)
        spec = spec_for(cid)
        return {"id": spec["id"], "title": spec["title"], "policies": spec["policies"],
                **rec.wording(spec)}

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
    def get_context(request: Request):
        # This historical context stays separate from the view, checks and decision record.
        cid = selected(request)
        if spec_for(cid)["id"] != "nt-priority-housing":
            return None
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

    def case_pages(cid: str):
        # Read only this app's synthetic case. No request parameter becomes a file path.
        try:
            if cid.startswith("U-"):
                meta, passages = case_passages(cid, uploads / cid / "case.json")
            else:
                meta, passages = case_passages(cid)
        except IngestError as exc:
            raise HTTPException(503, str(exc)) from None
        if meta["sha256"] != view(cid)["case"]["sha256"]:
            raise HTTPException(409, "The case file has changed since these checks were made.")
        pages = [{"page": n, "passages": []} for n in range(1, meta["pages"] + 1)]
        for passage in passages:
            page = pages[passage["page"] - 1]
            page["passages"].append(passage)
            if passage.get("transcribed"):
                page.update(transcribed=True,
                            image_url=f"/api/case-pages/{page['page']}/image?case={cid}")
        return {"case_id": cid, "sha256": meta["sha256"], "pages": pages}

    @app.get("/api/case-pages")
    def get_case_pages(request: Request):
        return case_pages(selected(request))

    @app.get("/api/case-pages/{page_number}/image")
    def get_scan_image(page_number: int, request: Request):
        cid = selected(request)
        pages = case_pages(cid)["pages"]
        if not cid.startswith("U-") or not 1 <= page_number <= len(pages):
            raise HTTPException(404, "No scanned image for this page.")
        page = pages[page_number - 1]
        if not page.get("transcribed"):
            raise HTTPException(404, "No scanned image for this page.")
        # The case manifest and original/image hashes were checked by case_pages.
        image = uploads / cid / page["passages"][0]["image"]
        return FileResponse(image, media_type="image/png", headers={"Cache-Control": "no-store"})

    @app.get("/api/passages/{passage_id}")
    def get_passage(passage_id: str, request: Request):
        cid = selected(request)
        source = view(cid)["sources"].get(passage_id)
        if not source or source.get("kind") != "policy":
            raise HTTPException(404, "Only cited policy passages are served here.")
        try:
            text = _policy_text(spec_for(cid)["id"], lists_dir).get(passage_id)
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
            record = rec.build(payload, view(cid), opened_seconds=opened_seconds,
                               question_list=spec_for(cid))
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
