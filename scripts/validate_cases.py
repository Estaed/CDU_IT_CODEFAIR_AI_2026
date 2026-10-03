"""Validate synthetic case fixtures against the wave-1 data contract."""

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path


CLAUSE_IDS = {
    "elig-residency",
    "elig-property",
    "elig-income",
    "elig-debts",
    "elig-former-tenancy",
    "prio-category",
    "prio-documentation",
    "prio-discretion",
}
FACT_COLUMNS = [
    "fact_id", "clause_id", "statement", "value", "page", "quote", "role", "trap", "decisive"
]
FACT_ROLES = {"supports", "against", "contradicts", "stale", "missing"}
TRAPS = {
    "none", "stale_value", "contradiction", "omission", "policy_misread",
    "exclusion_2yr", "missing_doc", "discretion",
}
OUTCOMES = {"met", "not_met", "cannot_decide", "not_applicable"}
DECISIONS = {"approve", "decline", "request_information"}
MUTATION_TYPES = {
    "none", "number_swap", "date_swap", "negation", "stale_value",
    "entity_swap", "omission", "policy_misread",
}
LABELS = {"supported", "contradicted", "unsupported"}
PAGE_MARKER = re.compile(r"(?m)^<!-- page (\d+) -->$")
DOCUMENT_HEADER = re.compile(
    r"^## Document: ([^|\n]+) \| ([^|\n]+) \| (\d{4}-\d{2}-\d{2})$"
)
PAGE_REF = re.compile(r"p([1-9]\d*)$")
WORD = re.compile(r"\b[\w]+(?:['’\-][\w]+)*\b")
META_COMMENTARY = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"synthetic",
        r"fictional",
        r"\btrap\b",
        r"readmark",
        r"\bAI\b",
        r"assessing officer",
        r"the officer should",
        r"pre-entered",
        r"pre-filled",
        r"not a certificate",
    )
]

# Catch common Australian phone, TFN and Medicare layouts without treating ISO dates as IDs.
PII_PATTERNS = {
    "phone": re.compile(
        r"(?<!\d)(?:\+?61[ -]?[2378][ -]?\d{4}[ -]?\d{4}|"
        r"\+?61[ -]?4[ -]?\d{2}[ -]?\d{3}[ -]?\d{3}|"
        r"0[2378][ -]?\d{4}[ -]?\d{4}|04\d{2}[ -]?\d{3}[ -]?\d{3}|"
        r"13\d{4}|(?:1300|1800)[ -]?\d{3}[ -]?\d{3})(?!\d)"
    ),
    "TFN": re.compile(r"(?<!\d)\d{3}[ -]?\d{3}[ -]?\d{3}(?!\d)"),
    "Medicare": re.compile(r"(?<!\d)[2-6]\d{3}[ -]?\d{5}[ -]?\d(?!\d)"),
}


def check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def collapse(text: str) -> str:
    return " ".join(text.split())


def read_pages(case_file: Path, errors: list[str]) -> dict[int, str]:
    if not case_file.is_file():
        errors.append(f"{case_file}: missing")
        return {}
    text = case_file.read_text(encoding="utf-8-sig")
    matches = list(PAGE_MARKER.finditer(text))
    check(bool(matches), f"{case_file}: no page markers", errors)
    if not matches:
        return {}
    check(not text[:matches[0].start()].strip(), f"{case_file}: text before page 1", errors)
    pages = {}
    for index, match in enumerate(matches):
        number = int(match.group(1))
        check(number == index + 1, f"{case_file}: expected page {index + 1}, got {number}", errors)
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end():end].strip()
        check(bool(body), f"{case_file}: empty page {number}", errors)
        lines = body.splitlines()
        # The first page starts a document; later pages may continue it without a new header.
        if index == 0 or (lines and lines[0].startswith("## Document:")):
            check(
                bool(lines) and bool(DOCUMENT_HEADER.fullmatch(lines[0])),
                f"{case_file}: page {number} has an invalid document header",
                errors,
            )
        pages[number] = body
    return pages


def read_facts(path: Path, pages: dict[int, str], errors: list[str]) -> list[dict[str, str]]:
    if not path.is_file():
        errors.append(f"{path}: missing")
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        check(reader.fieldnames == FACT_COLUMNS, f"{path}: incorrect columns", errors)
        facts = list(reader)
    ids = set()
    for row_number, fact in enumerate(facts, start=2):
        prefix = f"{path}:{row_number}"
        check(None not in fact, f"{prefix}: extra CSV field", errors)
        check(bool(fact.get("fact_id")), f"{prefix}: empty fact_id", errors)
        check(fact.get("fact_id") not in ids, f"{prefix}: duplicate fact_id", errors)
        ids.add(fact.get("fact_id"))
        check(fact.get("clause_id") in CLAUSE_IDS, f"{prefix}: unknown clause_id", errors)
        check(bool(fact.get("statement")), f"{prefix}: empty statement", errors)
        check(fact.get("role") in FACT_ROLES, f"{prefix}: invalid role", errors)
        check(fact.get("trap") in TRAPS, f"{prefix}: invalid trap", errors)
        check(fact.get("decisive") in {"yes", "no"}, f"{prefix}: invalid decisive", errors)
        page = fact.get("page", "")
        quote = fact.get("quote", "")
        if fact.get("role") == "missing":
            check(not page and not quote, f"{prefix}: missing fact must have no page or quote", errors)
        elif not page or not page.isdecimal() or int(page) not in pages:
            errors.append(f"{prefix}: invalid page")
        else:
            check(bool(quote), f"{prefix}: empty quote", errors)
            check(
                bool(quote) and collapse(quote) in collapse(pages[int(page)]),
                f"{prefix}: quote not found on page {page}", errors,
            )
    check(bool(facts), f"{path}: no facts", errors)
    return facts


def read_gold(path: Path, case_id: str, page_count: int, errors: list[str]) -> None:
    if not path.is_file():
        errors.append(f"{path}: missing")
        return
    try:
        gold = json.loads(path.read_text(encoding="utf-8-sig"))
    except (ValueError, UnicodeError) as exc:
        errors.append(f"{path}: invalid JSON: {exc}")
        return
    if not isinstance(gold, dict):
        errors.append(f"{path}: expected object")
        return
    check(
        set(gold) == {"case_id", "outcomes", "correct_decision", "required_reading", "rationale"},
        f"{path}: incorrect top-level keys", errors,
    )
    check(gold.get("case_id") == case_id, f"{path}: case_id mismatch", errors)
    outcomes = gold.get("outcomes")
    check(isinstance(outcomes, dict) and set(outcomes) == CLAUSE_IDS,
          f"{path}: outcome clauses differ from contract", errors)
    if isinstance(outcomes, dict):
        for clause_id, outcome in outcomes.items():
            check(outcome in OUTCOMES, f"{path}: invalid outcome for {clause_id}", errors)
    check(gold.get("correct_decision") in DECISIONS, f"{path}: invalid decision", errors)
    rationale = gold.get("rationale")
    check(isinstance(rationale, dict) and set(rationale) == CLAUSE_IDS,
          f"{path}: rationale clauses differ from contract", errors)
    if isinstance(rationale, dict):
        for clause_id, sentence in rationale.items():
            check(isinstance(sentence, str) and bool(sentence.strip()),
                  f"{path}: empty rationale for {clause_id}", errors)
    reading = gold.get("required_reading")
    check(isinstance(reading, list) and len(reading) <= 8,
          f"{path}: required_reading must be a list of at most 8 pages", errors)
    if isinstance(reading, list):
        check(len(reading) == len(set(map(str, reading))),
              f"{path}: repeated required page", errors)
        for page_ref in reading:
            match = PAGE_REF.fullmatch(page_ref) if isinstance(page_ref, str) else None
            check(bool(match) and int(match.group(1)) <= page_count,
                  f"{path}: invalid required page {page_ref}", errors)


def read_mutations(path: Path, facts: list[dict[str, str]], required: bool,
                   errors: list[str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    if not path.is_file():
        if required:
            errors.append(f"{path}: required for evaluation case")
        return counts
    fact_ids = {fact.get("fact_id") for fact in facts}
    correct_count = 0
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            errors.append(f"{path}:{line_number}: blank JSONL line")
            continue
        try:
            row = json.loads(line)
        except ValueError as exc:
            errors.append(f"{path}:{line_number}: invalid JSON: {exc}")
            continue
        prefix = f"{path}:{line_number}"
        if not isinstance(row, dict):
            errors.append(f"{prefix}: expected object")
            continue
        check(set(row) == {"summary_id", "claim", "mutation_type", "source_fact_id", "label"},
              f"{prefix}: incorrect keys", errors)
        check(isinstance(row.get("summary_id"), str) and bool(row.get("summary_id")),
              f"{prefix}: invalid summary_id", errors)
        check(isinstance(row.get("claim"), str) and bool(row.get("claim")),
              f"{prefix}: invalid claim", errors)
        kind = row.get("mutation_type")
        check(kind in MUTATION_TYPES, f"{prefix}: invalid mutation_type", errors)
        check(row.get("label") in LABELS, f"{prefix}: invalid label", errors)
        check(row.get("source_fact_id") in fact_ids, f"{prefix}: unknown source_fact_id", errors)
        if kind in MUTATION_TYPES:
            counts[kind] += 1
            if kind == "none":
                correct_count += 1
                check(row.get("summary_id") == "correct" and row.get("label") == "supported",
                      f"{prefix}: correct-summary claim must be supported", errors)
    if required:
        check(6 <= correct_count <= 10,
              f"{path}: correct summary needs 6-10 claims, got {correct_count}", errors)
        for kind in MUTATION_TYPES - {"none"}:
            check(counts[kind] > 0, f"{path}: missing {kind} mutation", errors)
    return counts


def scan_pii(paths: list[Path], errors: list[str]) -> None:
    for path in paths:
        if not path.is_file():
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
            for kind, pattern in PII_PATTERNS.items():
                if pattern.search(line):
                    errors.append(f"{path}:{line_number}: possible {kind}")


def check_paperwork(case_file: Path, pages: dict[int, str], errors: list[str]) -> str:
    counts = [len(WORD.findall(body)) for body in pages.values()]
    mean = sum(counts) / len(counts) if counts else 0
    minimum = min(counts, default=0)
    check(mean >= 180, f"{case_file}: mean words/page {mean:.1f} is below 180", errors)
    for page, count in zip(pages, counts):
        check(count >= 80, f"{case_file}: page {page} has {count} words (minimum 80)", errors)
    if case_file.is_file():
        for line_number, line in enumerate(case_file.read_text(encoding="utf-8-sig").splitlines(), 1):
            if any(pattern.search(line) for pattern in META_COMMENTARY):
                errors.append(f"{case_file}:{line_number}: meta commentary")
    return f"words/page mean={mean:.1f} min={minimum}"


def validate_case(directory: Path) -> tuple[list[str], str]:
    errors: list[str] = []
    case_id = directory.name
    case_file = directory / "case.md"
    facts_file = directory / "facts.csv"
    gold_file = directory / "gold.json"
    mutations_file = directory / "mutations.jsonl"
    pages = read_pages(case_file, errors)
    facts = read_facts(facts_file, pages, errors)
    read_gold(gold_file, case_id, len(pages), errors)
    counts = read_mutations(mutations_file, facts, case_id.startswith("E-"), errors)
    scan_pii([case_file, facts_file, gold_file, mutations_file], errors)
    density_text = ""
    if case_id == "A-0142" or case_id.startswith("E-"):
        density_text = "; " + check_paperwork(case_file, pages, errors)
    if case_id == "A-0142":
        check(55 <= len(pages) <= 65, f"{directory}: A-0142 needs 55-65 pages", errors)
    elif case_id.startswith("E-"):
        check(10 <= len(pages) <= 15, f"{directory}: E case needs 10-15 pages", errors)
    traps = Counter(fact.get("trap") for fact in facts if fact.get("trap") != "none")
    trap_text = ", ".join(f"{kind} n={traps[kind]}" for kind in sorted(traps)) or "none"
    mutation_text = ", ".join(f"{kind} n={counts[kind]}" for kind in sorted(counts)) or "none"
    summary = (
        f"{case_id}: pages n={len(pages)}; facts n={len(facts)}{density_text}; "
        f"traps [{trap_text}]; mutations [{mutation_text}]"
    )
    return errors, summary


def case_directories(arguments: list[str]) -> list[Path]:
    roots = [Path(arg) for arg in arguments] if arguments else [Path("data/cases"), Path("data/heldout")]
    directories = []
    for root in roots:
        if not root.exists():
            if arguments:
                raise FileNotFoundError(root)
            continue
        if not root.is_dir():
            raise NotADirectoryError(root)
        if (root / "case.md").is_file():
            directories.append(root)
        else:
            directories.extend(child for child in root.iterdir() if child.is_dir())
    return sorted(set(directories))


def main(arguments: list[str]) -> int:
    try:
        directories = case_directories(arguments)
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if not directories:
        print("ERROR: no case directories found", file=sys.stderr)
        return 2
    failures = []
    for directory in directories:
        errors, summary = validate_case(directory)
        print(summary)
        failures.extend(errors)
    for error in failures:
        print(f"ERROR: {error}", file=sys.stderr)
    print(f"Validated cases n={len(directories)}; errors n={len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
