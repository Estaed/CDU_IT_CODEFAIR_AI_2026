"""The whole run: an injected bad claim reaches the screen, replay is byte-identical with no keys
and no ``claude``, and no policy text leaks into the run beyond the quotes the screen shows."""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from conftest import FixedChecker, FixedWriter, fact, needs_pdfs

from readmark import ROOT
from readmark.ingest import normalise, policy_passages
from readmark.pipeline import run, validate_view

STUB_RUN = ROOT / "runs" / "stub"


@needs_pdfs
def test_fabricated_quote_reaches_view_as_quote_not_found_and_is_required(tmp_path, stub_facts):
    fabricated = fact("elig-debts", "The applicant still owes rent arrears.",
                      ("stub:p3:2", "Arrears remain outstanding and unpaid."))
    view = run("stub", writer=FixedWriter([*stub_facts, fabricated]),
               checker_impl=FixedChecker(), out_dir=tmp_path)

    claim = next(c for c in view["claims"] if c["claim"] == fabricated["claim"])
    assert claim["status"] == "quote_not_found"
    assert claim["required"] is True
    assert claim["citations"][0]["quote"] == "Arrears remain outstanding and unpaid."
    required = {i["passage_id"]: i for i in view["required_reading"]}
    assert claim["claim_id"] in required["stub:p3:2"]["claim_ids"]
    # The other claims all passed, so nothing else is required.
    assert list(required) == ["stub:p3:2"]
    on_disk = json.loads((tmp_path / "view.json").read_text(encoding="utf-8"))
    validate_view(on_disk)
    assert on_disk == view


@needs_pdfs
def test_writer_found_false_becomes_no_evidence_in_file(tmp_path, stub_facts):
    view = run("stub", writer=FixedWriter(stub_facts), checker_impl=FixedChecker(),
               out_dir=tmp_path)
    income = next(c for c in view["clauses"] if c["clause_id"] == "elig-income")
    assert income["coverage"] == "no_evidence_in_file"
    assert income["missing"][0]["statement"] == "The file holds no income statement."
    assert "outcome" not in json.dumps(view["clauses"])  # the AI never pre-fills an outcome


def _replay(runs_dir: Path) -> bytes:
    env = {k: v for k, v in os.environ.items() if k != "TYPESAFE_API_KEY"}
    # PATH holds only the interpreter (and Windows' system folder), so `claude` cannot be found.
    path = os.pathsep.join([str(Path(sys.executable).parent),
                            os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32")])
    assert shutil.which("claude", path=path) is None
    env.update(PATH=path, READMARK_RUNS_DIR=str(runs_dir))
    subprocess.run([sys.executable, "-m", "readmark", "run", "--case", "stub", "--replay"],
                   cwd=ROOT, env=env, check=True, capture_output=True, timeout=300)
    return (runs_dir / "stub" / "view.json").read_bytes()


@needs_pdfs
def test_replay_is_byte_identical_without_keys_or_claude(tmp_path):
    for n in (1, 2):
        shutil.copytree(STUB_RUN / "cache", tmp_path / f"r{n}" / "stub" / "cache")
    first, second = _replay(tmp_path / "r1"), _replay(tmp_path / "r2")
    assert first == second
    assert first == (STUB_RUN / "view.json").read_bytes()  # matches the committed run


@needs_pdfs
def test_run_and_cache_hold_no_policy_text_beyond_shown_quotes():
    view = json.loads((STUB_RUN / "view.json").read_text(encoding="utf-8"))
    shown = [c["quote"] for claim in view["claims"] for c in claim["citations"]]
    shown += [c["policy_sentence"] or "" for c in view["clauses"]]
    shown += [i for c in view["clauses"] for i in c["policy_items"]]
    shown = [normalise(s) for s in shown]
    # Every file under runs/stub/, the replay cache included, as plain text.
    stored = "\n".join(
        normalise(p.read_text(encoding="utf-8")) for p in STUB_RUN.rglob("*") if p.is_file()
    )

    # A long sentence from Eligibility §3.4 that the screen never quotes.
    named = ("The CEO (Housing) will seek to recover outstanding debts in line with the Debt "
             "Management policy.")
    assert not any(named in s for s in shown)
    assert named not in stored

    sentences = {
        s.strip() for p in policy_passages() for s in re.split(r"(?<=[.;:])\s+", p["text"])
        if len(s.strip()) >= 60
    }
    leaked = [s for s in sentences if s in stored and not any(s in q for q in shown)]
    assert leaked == []
