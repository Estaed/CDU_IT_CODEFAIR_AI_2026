"""Approved question lists and the small per-case selection file."""

import json
import re
from pathlib import Path

import yaml

from readmark.ingest import IngestError, case_path

QUESTION_LISTS_DIR = Path(__file__).resolve().parent / "lists"
DEFAULT_LIST_ID = "nt-priority-housing"
CASE_LIST_FILE = "question-list.json"
_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_KEY = re.compile(r"^[a-zA-Z0-9_-]+$")


def _id(value: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise IngestError(f"Invalid question list id: {value!r}")
    return value


def read_yaml(path: Path):
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise IngestError(f"Cannot load {path}: {exc}") from exc


def validate_clauses(clauses, path: Path, policy_keys: set[str] | None = None) -> list[dict]:
    if not isinstance(clauses, list) or not clauses:
        raise IngestError(f"{path}: questions must be a non-empty list")
    seen = set()
    for clause in clauses:
        if not isinstance(clause, dict) or any(
            not isinstance(clause.get(k), str) or not clause[k].strip()
            for k in ("clause_id", "policy", "source", "title", "sentence", "decides")
        ):
            raise IngestError(f"{path}: each question needs id, policy, source, title, sentence, decides")
        cid = clause["clause_id"]
        if not _KEY.fullmatch(cid) or cid == "other" or cid in seen:
            raise IngestError(f"{path}: invalid or duplicate question id {cid!r}")
        seen.add(cid)
        if policy_keys is not None and clause["policy"] not in policy_keys:
            raise IngestError(f"{path}: {cid} names an unknown policy {clause['policy']!r}")
        items = clause.get("items", [])
        if not isinstance(items, list) or any(not isinstance(i, str) or not i.strip() for i in items):
            raise IngestError(f"{path}: {cid} items must be verbatim strings")
    return clauses


def load_question_list(list_id: str = DEFAULT_LIST_ID,
                       lists_dir: Path = QUESTION_LISTS_DIR) -> dict:
    """Load metadata, inline pins and questions; never read policy text or call a model."""
    folder = Path(lists_dir) / _id(list_id)
    path = folder / "list.yaml"
    spec = read_yaml(path)
    if (not isinstance(spec, dict) or spec.get("id") != list_id
            or not isinstance(spec.get("title"), str) or not spec["title"].strip()):
        raise IngestError(f"{path}: list id must match its folder and title must be present")
    scope = spec.get("scope")
    if "scope" in spec and (not isinstance(scope, str) or not scope.strip()):
        raise IngestError(f"{path}: scope must be a non-empty sentence")
    policies = spec.get("policies")
    if not isinstance(policies, list) or not policies:
        raise IngestError(f"{path}: policies must be a non-empty list")
    keys, files = set(), set()
    for policy in policies:
        if not isinstance(policy, dict) or any(
            not isinstance(policy.get(k), str) or not policy[k].strip()
            for k in ("key", "file", "title")
        ):
            raise IngestError(f"{path}: each policy needs key, file and title")
        key, name = policy["key"], policy["file"]
        if (not _KEY.fullmatch(key) or key in keys or name in files
                or "/" in name or "\\" in name or ":" in name
                or Path(name).suffix.lower() not in (".pdf", ".txt")):
            raise IngestError(f"{path}: invalid or duplicate policy key/file: {key!r}, {name!r}")
        keys.add(key)
        files.add(name)
        pin = policy.get("pin")
        if (not isinstance(pin, dict)
                or any(not isinstance(pin.get(k), str) or not pin[k].strip()
                       for k in ("sha256", "version", "approved", "url"))
                or not re.fullmatch(r"[0-9a-f]{64}", pin["sha256"])
                or type(pin.get("pages")) is not int or pin["pages"] < 1):
            raise IngestError(f"{path}: {name} needs SHA-256, version, approved, url and page count")
    directory = spec.get("policy_directory", "policies")
    if not isinstance(directory, str) or not directory.strip():
        raise IngestError(f"{path}: policy_directory must be a path")
    # Optional officer-facing labels for the three decisions (approve, decline, request
    # information); a list without them keeps the housing wording in readmark.record.
    decisions = spec.get("decisions", {})
    if (not isinstance(decisions, dict)
            or not set(decisions) <= {"approve", "decline", "request_information"}
            or not all(isinstance(v, str) and v.strip() for v in decisions.values())):
        raise IngestError(f"{path}: decisions must map approve/decline/request_information to labels")
    # Optional screen wording: the service name, what a case is called, and who decides. A list
    # without them keeps the housing wording on the screen.
    labels = spec.get("labels", {})
    if (not isinstance(labels, dict) or not set(labels) <= {"service", "case_noun", "officer"}
            or not all(isinstance(v, str) and v.strip() for v in labels.values())):
        raise IngestError(f"{path}: labels may set service, case_noun and officer as text")
    return {
        "id": spec["id"], "title": spec["title"], "policies": policies, "decisions": decisions,
        "labels": labels, "scope": scope,
        "policies_dir": (folder / directory).resolve(),
        "clauses": validate_clauses(read_yaml(folder / "clauses.yaml"),
                                   folder / "clauses.yaml", keys),
    }


def list_question_lists(lists_dir: Path = QUESTION_LISTS_DIR) -> list[dict]:
    """Return id/title pairs in id order; a malformed list fails loudly."""
    result = []
    for path in sorted(Path(lists_dir).glob("*/list.yaml")):
        spec = load_question_list(path.parent.name, lists_dir)
        result.append({"id": spec["id"], "title": spec["title"]})
    return result


def case_question_list(case_id: str, *, case_dir: Path | None = None,
                       lists_dir: Path = QUESTION_LISTS_DIR) -> str:
    """Read a case's list id; only an absent selection file falls back to housing."""
    path = (case_dir if case_dir is not None else case_path(case_id).parent) / CASE_LIST_FILE
    list_id = DEFAULT_LIST_ID
    if path.exists():
        try:
            selection = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise IngestError(f"Cannot load {path}: {exc}") from exc
        if not isinstance(selection, dict) or set(selection) != {"question_list"}:
            raise IngestError(f"{path}: expected {{\"question_list\": \"<id>\"}}")
        list_id = selection["question_list"]
    load_question_list(list_id, lists_dir)
    return list_id


def set_case_question_list(case_id: str, list_id: str, *, case_dir: Path | None = None,
                           lists_dir: Path = QUESTION_LISTS_DIR) -> None:
    """Validate and save a selection in an existing case folder, before its first run."""
    load_question_list(list_id, lists_dir)
    folder = case_dir if case_dir is not None else case_path(case_id).parent
    if not folder.is_dir():
        raise IngestError(f"Case folder not found: {folder}")
    (folder / CASE_LIST_FILE).write_text(
        json.dumps({"question_list": list_id}, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
