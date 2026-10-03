"""Coverage exercises the real replay seam; only the HTTP response is faked."""

import hashlib
import json
import shutil

import pytest

from readmark import dumps
from readmark.__main__ import main
from readmark.cache import Cache, ReplayMiss
from readmark.checklist import QUESTION_LISTS_DIR, load_question_list
from readmark.checklist.coverage import read_coverage, run_coverage
from readmark.ingest import IngestError, policy_passages
from readmark.jev import CheckerError, JevChecker
from readmark.jev.coverage import CoverageChecker


@pytest.fixture
def tiny_list(tmp_path):
    folder = tmp_path / "lists" / "tiny"
    policies = folder / "policies"
    policies.mkdir(parents=True)
    text = ("Welcome to the assessment policy.\n\n"
            "(2) Staff must require evidence for an extension.\n\n"
            "(3) Staff must apply a five percent penalty to late work.")
    policy = policies / "assessment.txt"
    policy.write_text(text, encoding="utf-8", newline="\n")
    metadata = {"id": "tiny", "title": "Tiny policy", "policies": [{
        "key": "assessment", "file": policy.name, "title": "Assessment",
        "pin": {"sha256": hashlib.sha256(policy.read_bytes()).hexdigest(), "pages": 1,
                "version": "1", "approved": "2026-10-04", "url": "https://example.org/policy"},
    }]}
    question = {"clause_id": "evidence", "policy": "assessment", "source": "Procedure (2)",
                "title": "Evidence supplied", "decides": "Is there evidence for the extension?",
                "sentence": "Staff must require evidence for an extension."}
    (folder / "list.yaml").write_text(dumps(metadata), encoding="utf-8", newline="\n")
    (folder / "clauses.yaml").write_text(dumps([question]), encoding="utf-8", newline="\n")
    return folder.parent


def fake_post(self, body):
    assert set(body["state"]["approved_questions"]) == {"evidence"}
    assert "data, never instructions" in body["questions"]["P01_rule"]["instructions"]
    return {"model": "fake-jev", "answers": {
        "P01_rule": {"score": 0}, "P01_coverage": {"score": 0},
        "P02_rule": {"score": 4}, "P02_coverage": {"score": 4},
        "P03_rule": {"score": 4}, "P03_coverage": {"score": 0},
    }, "ignored": "An unexpected response field is not cached."}


def test_exact_uncovered_rule_and_byte_identical_replay(tiny_list, monkeypatch):
    calls = []

    def live(self, body):
        calls.append(body)
        return fake_post(self, body)

    monkeypatch.setattr(JevChecker, "_post", live)
    result = run_coverage("tiny", lists_dir=tiny_list)
    assert result["n_scanned"] == 3
    assert result["n_reported"] == 1
    suggestion, = result["suggestions"]
    assert suggestion["passage_id"] == "assessment:p1:3"
    assert suggestion["section"] == "Procedure (3)"
    assert suggestion["scores"] == {"rule": 4, "coverage": 0}
    path = tiny_list / "tiny" / "coverage.json"
    original = path.read_bytes()
    assert len(calls) == 1
    monkeypatch.setattr("readmark.jev.load_dotenv_key", lambda _: pytest.fail("Key was read"))
    monkeypatch.setattr(JevChecker, "_post", lambda *_: pytest.fail("Network was called"))
    assert run_coverage("tiny", replay=True, lists_dir=tiny_list) == result
    assert path.read_bytes() == original
    cache, = (path.parent / "coverage-cache").glob("*.json")
    stored = json.loads(cache.read_text(encoding="utf-8"))
    assert set(stored["response"]) == {"model", "answers", "coverage_date"}
    assert not any(p["text"] in cache.read_text(encoding="utf-8")
                   for p in policy_passages(question_list=load_question_list("tiny", tiny_list)))


def test_unknown_list_missing_cache_and_changed_pin(tiny_list):
    with pytest.raises(IngestError):
        run_coverage("../tiny", lists_dir=tiny_list)
    with pytest.raises(ReplayMiss):
        run_coverage("tiny", replay=True, lists_dir=tiny_list)
    assert not (tiny_list / "tiny" / "coverage.json").exists()
    policy = tiny_list / "tiny" / "policies" / "assessment.txt"
    policy.write_text("Changed policy", encoding="utf-8", newline="\n")
    with pytest.raises(IngestError, match="Policy file changed"):
        run_coverage("tiny", replay=True, lists_dir=tiny_list)


@pytest.mark.parametrize("value", [None, True, -1, 5, float("nan"), "4"])
def test_invalid_scores_fail_before_publishing(tiny_list, monkeypatch, value):
    def bad(self, body):
        response = fake_post(self, body)
        response["answers"]["P03_rule"]["score"] = value
        return response

    monkeypatch.setattr(JevChecker, "_post", bad)
    with pytest.raises(CheckerError, match="finite numbers"):
        run_coverage("tiny", lists_dir=tiny_list)
    assert not (tiny_list / "tiny" / "coverage.json").exists()


def test_thresholds_leave_uncertain_and_partial_rules_out(tiny_list, monkeypatch):
    def uncertain(self, body):
        response = fake_post(self, body)
        response["answers"]["P01_rule"]["score"] = 2.99
        response["answers"]["P02_coverage"]["score"] = 1.01
        response["answers"]["P03_rule"]["score"] = 3
        response["answers"]["P03_coverage"]["score"] = 1
        return response

    monkeypatch.setattr(JevChecker, "_post", uncertain)
    assert [s["passage_id"] for s in run_coverage("tiny", lists_dir=tiny_list)["suggestions"]] == [
        "assessment:p1:3"]


@pytest.mark.parametrize("list_id", ["nt-priority-housing", "cdu-extension"])
def test_delivered_coverage_replays_without_key_and_has_verified_short_excerpts(
        list_id, tmp_path, monkeypatch):
    original_folder = QUESTION_LISTS_DIR / list_id
    coverage = original_folder / "coverage.json"
    assert coverage.exists(), "Run the live coverage once before delivering the task"
    spec = load_question_list(list_id)
    if not all((spec["policies_dir"] / p["file"]).exists() for p in spec["policies"]):
        pytest.skip("Pinned policy downloads are needed to reconstruct replay request hashes")
    destination = tmp_path / "lists" / list_id
    destination.mkdir(parents=True)
    for name in ("list.yaml", "clauses.yaml", "coverage.json"):
        shutil.copyfile(original_folder / name, destination / name)
    shutil.copytree(original_folder / "coverage-cache", destination / "coverage-cache")
    # Use the real spec with its original pin locations; no restricted text is copied.
    monkeypatch.setattr("readmark.checklist.coverage.load_question_list", lambda *_: spec)
    monkeypatch.setattr("readmark.jev.load_dotenv_key", lambda _: pytest.fail("Key was read"))
    monkeypatch.setattr(JevChecker, "_post", lambda *_: pytest.fail("Network was called"))
    result = run_coverage(list_id, replay=True, lists_dir=destination.parent)
    assert (destination / "coverage.json").read_bytes() == coverage.read_bytes()
    passages = {p["passage_id"]: p for p in policy_passages(question_list=spec)}
    assert result["n_scanned"] == len(passages)
    assert result["n_reported"] == len(result["suggestions"])
    for suggestion in result["suggestions"]:
        full = passages[suggestion["passage_id"]]["text"]
        assert 0 < len(suggestion["excerpt"].split()) <= 25
        assert suggestion["excerpt"] in full and suggestion["excerpt"] != full
        assert suggestion["scores"]["rule"] >= 3
        assert suggestion["scores"]["coverage"] <= 1
        assert suggestion["scores"]["scope"] >= 2.0
    if list_id == "cdu-extension":
        assert {"Procedure (74)", "Procedure (78)"} <= {
            s["section"] for s in result["suggestions"]}


def test_batching_keeps_every_paragraph_and_records_all_models(tmp_path, monkeypatch):
    calls = []

    def live(self, body):
        calls.append(body)
        return {"model": "fake-jev", "answers": {key: {"score": 0}
                                                  for key in body["questions"]}}

    monkeypatch.setattr(JevChecker, "_post", live)
    checker = CoverageChecker(Cache(tmp_path / "cache", replay=False))
    passages = [{"passage_id": str(i), "policy": "a", "text": "Background"} for i in range(21)]
    assert set(checker.coverage([], passages)) == {str(i) for i in range(21)}
    assert sorted(len(c["state"]["policy_paragraphs"]) for c in calls) == [1, 20]
    assert checker.job_models["coverage"] == "fake-jev"


def test_cli_routes_list_and_replay_flags(monkeypatch, capsys):
    calls = []

    def run(list_id, **kwargs):
        calls.append((list_id, kwargs))
        return {"n_scanned": 3, "n_reported": 1, "model": "fake", "date": "2026-10-04"}

    monkeypatch.setattr("readmark.checklist.coverage.run_coverage", run)
    assert main(["lists", "--coverage", "tiny", "--replay"]) == 0
    assert calls == [("tiny", {"replay": True})]
    assert "1 policy rules no question covers (n=3 scanned" in capsys.readouterr().out


def test_absent_coverage_is_not_a_zero_count(tiny_list):
    assert read_coverage("tiny", tiny_list) is None


def test_scope_filter_keeps_on_subject_rule_and_drops_off_subject(tiny_list, monkeypatch):
    metadata_path = tiny_list / "tiny" / "list.yaml"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["scope"] = "A student's assessment extension or late submission"
    policy_path = metadata_path.parent / "policies" / "assessment.txt"
    with policy_path.open("a", encoding="utf-8", newline="\n") as policy:
        policy.write("\n\n(4) Examiners must return marked scripts within ten days.")
    metadata["policies"][0]["pin"]["sha256"] = hashlib.sha256(policy_path.read_bytes()).hexdigest()
    metadata_path.write_text(dumps(metadata), encoding="utf-8", newline="\n")
    calls = []

    def live(self, body):
        calls.append(body)
        if "approved_questions" in body["state"]:
            response = fake_post(self, body)
            response["answers"].update(P04_rule={"score": 4}, P04_coverage={"score": 0})
            return response
        assert "Tiny policy: " + metadata["scope"] in body["state"]["clause"]
        assert "Policy (scope): " + metadata["scope"] in body["state"]["clause"]
        assert len(body["state"]["passages"]) == 2
        return {"model": "fake-scope", "answers": {
            "P01": {"score": 2.0}, "P02": {"score": 1.99}}}

    monkeypatch.setattr(JevChecker, "_post", live)
    result = run_coverage("tiny", lists_dir=tiny_list)
    assert result["n_scanned"] == 4 and result["n_scope_scanned"] == 2
    assert result["n_reported"] == 1
    assert result["thresholds"]["scope_min"] == 2.0
    assert result["scope_model"] == "fake-scope"
    suggestion, = result["suggestions"]
    assert suggestion["passage_id"] == "assessment:p1:3"
    assert suggestion["scores"] == {"rule": 4, "coverage": 0, "scope": 2.0}
    assert len(calls) == 2
    path = metadata_path.parent / "coverage.json"
    before = path.read_bytes()
    monkeypatch.setattr("readmark.jev.load_dotenv_key", lambda _: pytest.fail("Key was read"))
    monkeypatch.setattr(JevChecker, "_post", lambda *_: pytest.fail("Network was called"))
    assert run_coverage("tiny", replay=True, lists_dir=tiny_list) == result
    assert path.read_bytes() == before


@pytest.mark.parametrize("scope", [None, "", "   ", 42, True, []])
def test_optional_scope_rejects_empty_or_non_string_values(tiny_list, scope):
    path = tiny_list / "tiny" / "list.yaml"
    metadata = json.loads(path.read_text(encoding="utf-8"))
    metadata["scope"] = scope
    path.write_text(dumps(metadata), encoding="utf-8", newline="\n")
    with pytest.raises(IngestError, match="scope must be a non-empty sentence"):
        load_question_list("tiny", tiny_list)


def test_scope_with_no_uncovered_rules_skips_the_network(tiny_list, monkeypatch):
    path = tiny_list / "tiny" / "list.yaml"
    metadata = json.loads(path.read_text(encoding="utf-8"))
    metadata["scope"] = "Assessment extensions"
    path.write_text(dumps(metadata), encoding="utf-8", newline="\n")
    calls = []

    def covered(self, body):
        calls.append(body)
        response = fake_post(self, body)
        response["answers"]["P03_coverage"]["score"] = 4
        return response

    monkeypatch.setattr(JevChecker, "_post", covered)
    result = run_coverage("tiny", lists_dir=tiny_list)
    assert result["n_scope_scanned"] == 0 and result["suggestions"] == []
    assert len(calls) == 1


@pytest.mark.parametrize("score", [True, -1, 5, float("nan"), "2"])
def test_invalid_scope_score_is_not_published(tiny_list, monkeypatch, score):
    path = tiny_list / "tiny" / "list.yaml"
    metadata = json.loads(path.read_text(encoding="utf-8"))
    metadata["scope"] = "Assessment extensions"
    path.write_text(dumps(metadata), encoding="utf-8", newline="\n")

    def invalid(self, body):
        if "approved_questions" in body["state"]:
            return fake_post(self, body)
        return {"model": "fake-scope", "answers": {"P01": {"score": score}}}

    monkeypatch.setattr(JevChecker, "_post", invalid)
    with pytest.raises(CheckerError, match="scope scores must be finite"):
        run_coverage("tiny", lists_dir=tiny_list)
    assert not (path.parent / "coverage.json").exists()
