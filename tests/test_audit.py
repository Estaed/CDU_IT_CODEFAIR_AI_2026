"""Summary under audit (Task-06): a plain summary is split into sentences and claims, each claim
gets the evidence map's own checks, supported map claims it leaves out are listed, and none of
it touches required reading. The last tests read the committed A-0142 audit."""

import json
import re

import jsonschema
import pytest
from conftest import FixedChecker, FixedWriter, fact, needs_pdfs

from readmark import ROOT
from readmark.audit import AUDIT_CASES, STATUSES, check_claims, split_sentences, view_block
from readmark.audit.claude import PROMPT, ClaudeAuditor, FrozenSummary
from readmark.cache import Cache
from readmark.pipeline import VIEW_SCHEMA, run, validate_view

JANUARY, MARCH = "stub:p2:2", "stub:p3:2"  # the stub's two ledger balances
STALE = "Ms K. currently owes $2,400 in rent arrears to the CEO (Housing)."
A_RUN = ROOT / "runs" / "A-0142"


class FixedAuditor:
    """Stands in for Claude's four audit calls. One claim per sentence that ends in a full stop
    (the sentence itself); ``located`` maps a claim to ``(clause_id, [(passage_id, quote)])``;
    a map fact counts as stated when its sentence appears word for word in the summary."""

    name = "fixed"
    model_id = "fixed-auditor"

    def __init__(self, summary: str = "", located: dict | None = None):
        self.summary = summary
        self.located = located or {}

    def summarise(self, case_id, case_text):
        return {"text": self.summary, "model": "fixed-summary", "prompt": PROMPT,
                "created": "2026-10-03"}

    def split(self, sentences):
        return {s["sentence_id"]: [s["text"]] if s["text"].endswith(".") else []
                for s in sentences}

    def locate(self, case_meta, case, clauses, claims):
        out = {}
        for c in claims:
            clause_id, cites = self.located.get(c["claim"], ("other", []))
            out[c["claim_id"]] = {"clause_id": clause_id, "citations": [
                {"passage_id": p, "quote": q} for p, q in cites]}
        return out

    def covered(self, summary, facts):
        return {f["claim_id"] for f in facts if f["claim"] in summary}


def words(text: str) -> list[str]:
    """The words of a text in order, numbered-list markers aside."""
    return re.findall(r"[^\W_]+", re.sub(r"(?m)^\s*\d{1,2}[.)]\s+", "", text))


def claim_schema() -> dict:
    schema = json.loads(VIEW_SCHEMA.read_text(encoding="utf-8"))
    return {"$defs": schema["$defs"], "$ref": "#/$defs/claim"}


@needs_pdfs
@pytest.mark.parametrize("citations", [[(JANUARY, "Arrears balance $2,400.00.")], []],
                         ids=["cites-the-january-ledger", "finds-no-passage"])
def test_summary_stating_the_january_arrears_as_current_is_flagged(tmp_path, stub_facts,
                                                                     citations):
    auditor = FixedAuditor(f"Ms K. applied for priority housing. {STALE}",
                           located={STALE: ("elig-debts", citations)})
    # The second key wrongly supports the stale claim, as it can on the January passage alone.
    checker = FixedChecker(contradict=[(JANUARY, MARCH)])
    view = run("stub", writer=FixedWriter(stub_facts), checker_impl=checker, out_dir=tmp_path,
               audit=True, auditor=auditor)

    claim = next(c for c in view["audit"]["claims"] if c["claim"] == STALE)
    assert claim["status"] != "supported"
    assert claim["status"] in {"contradicted", "checker_disagrees", "quote_not_found"}
    if citations:
        assert claim["status"] == "contradicted" and claim["contradicted_by"] == [MARCH]
        assert view["sources"][MARCH]["kind"] == "case"
    else:
        assert claim["status"] == "quote_not_found" and claim["citations"] == []
    validate_view(view)


@needs_pdfs
def test_supported_map_claims_the_summary_leaves_out_are_listed_by_clause(tmp_path, stub_facts):
    policy_only = fact("elig-debts", "Policy says a debt owed to the CEO (Housing) does not "
                       "withhold social housing.",
                       ("eligibility:p6:9", "The provision of social housing will not be "
                        "withheld based on a debt owed to the CEO (Housing)."))
    facts = [*stub_facts, policy_only]
    fleeing = next(f["claim"] for f in facts if f["clause_id"] == "prio-category")
    january = facts[0]["claim"]
    # The summary states every found fact but three: the support letter's (supported, so left
    # out), the January balance (contradicted by March, so not a fact to state) and the
    # policy-only one (not a fact of the file).
    summary = " ".join(f["claim"] for f in facts
                       if f["found"] and f["claim"] not in {fleeing, january, policy_only["claim"]})
    view = run("stub", writer=FixedWriter(facts),
               checker_impl=FixedChecker(contradict=[(JANUARY, MARCH)]), out_dir=tmp_path,
               audit=True, auditor=FixedAuditor(summary))

    by_text = {c["claim"]: c for c in view["claims"]}
    assert by_text[fleeing]["status"] == "supported"
    assert by_text[january]["status"] == "contradicted"
    assert view["audit"]["omitted"] == [
        {"claim_id": by_text[fleeing]["claim_id"], "clause_id": "prio-category"}]
    record = json.loads((tmp_path / "audit.json").read_text(encoding="utf-8"))
    assert by_text[policy_only["claim"]]["claim_id"] not in record["considered_for_omission"]
    assert record["counts"]["omitted"] == {"count": 1, "n": len(record["considered_for_omission"])}
    validate_view(view)


@needs_pdfs
def test_the_audit_adds_nothing_to_required_reading(tmp_path, stub_facts):
    invented = "The statutory declaration says Ms K. owns a unit in Palmerston."
    auditor = FixedAuditor(f"{STALE} {invented}", located={
        STALE: ("elig-debts", [(JANUARY, "Arrears balance $2,400.00.")]),
        invented: ("elig-property", [("stub:p6:1", "I own a unit in Palmerston.")])})

    def checker():
        return FixedChecker(contradict=[(JANUARY, MARCH)])

    plain = run("stub", writer=FixedWriter(stub_facts), checker_impl=checker(),
                out_dir=tmp_path / "plain", audit=False)
    audited = run("stub", writer=FixedWriter(stub_facts), checker_impl=checker(),
                  out_dir=tmp_path / "audited", audit=True, auditor=auditor)

    assert plain["audit"] is None
    assert [c["status"] for c in audited["audit"]["claims"]] == ["contradicted", "quote_not_found"]
    assert audited["required_reading"] == plain["required_reading"]
    assert audited["suggested_reading"] == plain["suggested_reading"]
    flagged = audited["audit"]["claims"][1]
    assert flagged["required"] is False  # stub:p6:1 is not in the map's required reading
    assert "stub:p6:1" in audited["sources"]


def test_every_sentence_of_the_summary_is_kept_in_order():
    summary = (
        "## Summary of file A-0142\n\n"
        "**Applicant:** Ms K. applies for urban housing in Darwin with two children, aged 7 and "
        "10. She fled family violence on 2 Feb. 2026, e.g. police attended.\n\n"
        "- Debt: a January ledger shows $2,400.00 owed. The March ledger shows it cleared!\n"
        "- Income evidence is still missing? Yes.\n"
        "  It was asked for on 20 March.\n"
        "1. The former tenancy ended on 12 June 2023 by mutual agreement.\n\n"
        "| Item | Status |\n|---|---|\n| Income | not received |\n\n"
        "---\n"
        "Overall, the officer should *request* income evidence."
    )
    sentences = split_sentences(summary)
    assert sentences == [
        "Summary of file A-0142",
        "Applicant: Ms K. applies for urban housing in Darwin with two children, aged 7 and 10.",
        "She fled family violence on 2 Feb. 2026, e.g. police attended.",
        "Debt: a January ledger shows $2,400.00 owed.",
        "The March ledger shows it cleared!",
        "Income evidence is still missing?",
        "Yes.",
        "It was asked for on 20 March.",
        "The former tenancy ended on 12 June 2023 by mutual agreement.",
        "Item; Status",
        "Income; not received",
        "Overall, the officer should request income evidence.",
    ]
    assert words(" ".join(sentences)) == words(summary)  # nothing dropped, nothing reordered


def test_claim_path_takes_two_claim_sentences_and_returns_two_view_claims():
    cleared = "The March ledger shows the arrears cleared in full."
    owns = "Ms K. owns a house in Palmerston."
    locator = FixedAuditor(located={cleared: ("elig-debts", [(MARCH, "Arrears cleared in full.")])})
    claims = check_claims("stub", [cleared, owns], locator=locator, checker=FixedChecker(),
                          required={MARCH})

    assert [(c["claim_id"], c["claim"]) for c in claims] == [("a01", cleared), ("a02", owns)]
    for c in claims:
        jsonschema.validate(c, claim_schema())
    assert claims[0]["status"] == "supported" and claims[0]["required"] is True
    # No passage bears on the second: it stays, as "quote not found", with no second key.
    assert claims[1]["status"] == "quote_not_found"
    assert claims[1]["citations"] == [] and claims[1]["checker"] is None


@needs_pdfs
def test_a_demo_file_run_with_fixed_models_never_reaches_claude(tmp_path, monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("a test run reached Claude")

    monkeypatch.setattr("readmark.audit.claude.call_claude", refuse)
    view = run("A-0142", writer=FixedWriter([]), checker_impl=FixedChecker(), out_dir=tmp_path)
    assert view["audit"] is None


def test_a_case_with_a_frozen_summary_is_never_summarised_again(tmp_path):
    cache = Cache(tmp_path, replay=False)
    (tmp_path / "summary-000000000000000000000000.json").write_text("{}", encoding="utf-8")
    with pytest.raises(FrozenSummary):
        ClaudeAuditor(cache).summarise("A-0142", "A different file text.")


# -- The committed demo run --------------------------------------------------------------------


def test_only_the_demo_file_has_a_summary_under_audit():
    assert AUDIT_CASES == ("A-0142",)
    stub = json.loads((ROOT / "runs" / "stub" / "view.json").read_text(encoding="utf-8"))
    assert stub["audit"] is None


def test_the_a0142_audit_record_holds_the_frozen_summary_and_its_counts():
    record = json.loads((A_RUN / "audit.json").read_text(encoding="utf-8"))
    view = json.loads((A_RUN / "view.json").read_text(encoding="utf-8"))
    assert view["audit"] == view_block(record)

    assert record["prompt"] == PROMPT
    assert record["model"].startswith("claude-")
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", record["created"])
    assert record["summary"].strip()

    # Every sentence is there, in order, and every claim belongs to exactly one sentence.
    texts = [s["text"] for s in record["sentences"]]
    assert texts == split_sentences(record["summary"])
    assert words(" ".join(texts)) == words(record["summary"])
    assert [i for s in record["sentences"] for i in s["claim_ids"]] == [
        c["claim_id"] for c in record["claims"]]

    counts = record["counts"]
    n = len(record["claims"])
    assert counts["claims"] == {"count": n, "n": n}
    assert set(counts["claims_by_status"]) == set(STATUSES)
    assert all(v["n"] == n for v in counts["claims_by_status"].values())
    assert sum(v["count"] for v in counts["claims_by_status"].values()) == n
    assert counts["omitted"] == {"count": len(record["omitted"]),
                                 "n": len(record["considered_for_omission"])}
    map_ids = {c["claim_id"] for c in view["claims"]}
    assert {o["claim_id"] for o in record["omitted"]} <= map_ids
