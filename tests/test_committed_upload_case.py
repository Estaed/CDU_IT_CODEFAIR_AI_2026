"""A case committed in upload form (its files beside a case.json) loads by its own id."""

import pytest

from readmark import ingest
from readmark.ingest import IngestError, case_passages, case_path, prepare_upload


class Undated:
    """Stands in for Claude: the loader is under test here, not the dater."""

    def date_document(self, text):
        return {"date": None, "quote": None}


def test_case_json_loads_by_its_own_id_and_case_md_as_before(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest, "CASES_DIR", tmp_path)
    folder = tmp_path / "W-99"
    folder.mkdir()
    (folder / "letter.txt").write_text("First paragraph.\n\nSecond paragraph.", encoding="utf-8")
    prepare_upload("W-99", "Committed upload", [{"doc_id": "d01", "name": "letter.txt",
                                                 "file": "letter.txt"}], folder, dater=Undated())

    assert case_path("W-99") == folder / "case.json"
    meta, passages = case_passages("W-99")
    assert meta["case_id"] == "W-99"
    # Upload passage ids name the case and the document: <case>-<doc_id>:p<page>:<k>.
    assert [p["passage_id"] for p in passages] == ["W-99-d01:p1:1", "W-99-d01:p1:2"]

    # The original files are pinned by hash, as for an upload: a changed file is refused.
    (folder / "letter.txt").write_text("Changed.", encoding="utf-8")
    with pytest.raises(IngestError, match="changed"):
        case_passages("W-99")

    # A case written in the contract format still loads from case.md.
    (tmp_path / "A-99").mkdir()
    (tmp_path / "A-99" / "case.md").write_text(
        "<!-- page 1 -->\n## Document: form | Application | 2026-03-10\n\nOne paragraph.\n",
        encoding="utf-8")
    assert case_path("A-99") == tmp_path / "A-99" / "case.md"
    assert [p["passage_id"] for p in case_passages("A-99")[1]] == ["A-99:p1:1"]


def test_document_dates_are_read_side_by_side(tmp_path):
    """Each live date call takes about 20 s; six documents must not wait for one another."""
    import threading
    import time

    seen, lock = [], threading.Lock()

    class Slow:
        def date_document(self, text):
            with lock:
                seen.append(text)
            time.sleep(0.3)
            return {"date": None, "quote": None}

    docs = []
    for n in range(6):
        (tmp_path / f"d{n}.txt").write_text(f"Document {n}.", encoding="utf-8")
        docs.append({"doc_id": f"d{n}", "name": f"d{n}.txt", "file": f"d{n}.txt"})
    start = time.monotonic()
    prepare_upload("U-parallel", "Six documents", docs, tmp_path, dater=Slow())
    assert len(seen) == 6
    assert time.monotonic() - start < 1.2  # one after another would take 1.8 s
