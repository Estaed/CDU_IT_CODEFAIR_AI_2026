"""Advisory rulebook coverage, independent of every case and decision record."""

import json
import re
from pathlib import Path

from readmark import dumps
from readmark.cache import Cache
from readmark.checklist.lists import QUESTION_LISTS_DIR, load_question_list
from readmark.ingest import IngestError, policy_passages
from readmark.jev.coverage import CoverageChecker

RULE_THRESHOLD = 3
COVERAGE_THRESHOLD = 1
SCOPE_THRESHOLD = 2.0


def section_label(passage: dict) -> str:
    # Text policies have no ingested headings. Preserve their numbered procedure locator.
    number = re.match(r"^\((\d+)\)", passage["text"])
    return (f"Procedure ({number[1]})" if number else passage.get("section")
            or f"Page {passage['page']}, paragraph {passage['k']}")


def read_coverage(list_id: str, lists_dir: Path = QUESTION_LISTS_DIR) -> dict | None:
    load_question_list(list_id, lists_dir)  # Validate before constructing a path.
    path = Path(lists_dir) / list_id / "coverage.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def run_coverage(list_id: str, *, replay: bool = False,
                 lists_dir: Path = QUESTION_LISTS_DIR) -> dict:
    spec = load_question_list(list_id, lists_dir)
    passages = policy_passages(question_list=spec)
    folder = Path(lists_dir) / list_id
    checker = CoverageChecker(Cache(folder / "coverage-cache", replay=replay))
    scores = checker.coverage(spec["clauses"], passages)
    candidates = [p for p in passages
                  if scores[p["passage_id"]]["rule"] >= RULE_THRESHOLD
                  and scores[p["passage_id"]]["coverage"] <= COVERAGE_THRESHOLD]
    scope = spec.get("scope")
    if scope:
        scope_scores = checker.scope(spec["title"], scope, candidates)
        for passage in candidates:
            scores[passage["passage_id"]]["scope"] = scope_scores[passage["passage_id"]]
        candidates = [p for p in candidates if scope_scores[p["passage_id"]] >= SCOPE_THRESHOLD]
    suggestions = []
    for passage in candidates:
        score = scores[passage["passage_id"]]
        if score["rule"] >= RULE_THRESHOLD and score["coverage"] <= COVERAGE_THRESHOLD:
            words = passage["text"].split()
            # A verbatim prefix, bounded to 25 words; short paragraphs are never copied whole.
            excerpt = " ".join(words[:min(25, max(0, len(words) - 1))])
            if not excerpt or excerpt not in passage["text"]:
                raise IngestError(f"Cannot verify coverage excerpt: {passage['passage_id']}")
            suggestions.append({"passage_id": passage["passage_id"],
                                "section": section_label(passage),
                                "policy": passage["policy"], "page": passage["page"],
                                "excerpt": excerpt, "scores": score})
    result = {"list_id": list_id, "method": "rule-and-question-coverage-v1",
              "thresholds": {"rule_min": RULE_THRESHOLD, "coverage_max": COVERAGE_THRESHOLD},
              "model": checker.job_models["coverage"], "date": checker.coverage_date,
              "n_scanned": len(passages), "n_reported": len(suggestions),
              "policy_pins": {p["key"]: p["pin"]["sha256"] for p in spec["policies"]},
              "suggestions": suggestions}
    if scope:
        result.update(method="rule-question-coverage-and-scope-v2", scope=scope,
                      scope_model=checker.job_models["scan"],
                      n_scope_scanned=len(scope_scores))
        result["thresholds"]["scope_min"] = SCOPE_THRESHOLD
    (folder / "coverage.json").write_text(dumps(result), encoding="utf-8", newline="\n")
    return result
