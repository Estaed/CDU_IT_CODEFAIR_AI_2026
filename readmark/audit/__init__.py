"""Summary under audit: a plain AI summary of the case file, checked claim by claim.

Readmark's riskiest assumption is that it finds real errors in a summary we did not write
(Blueprint). On the demo file this runs after the evidence map:

1. Claude writes the summary once from the one line "Summarise this file." with the case file as
   data; it is frozen in the cache with its model id, prompt and date (``claude.ClaudeAuditor``).
2. Code splits the summary into sentences and keeps every one, in order (``split_sentences``).
3. Claude splits each sentence into the claims it makes, seeing only the summary.
4. Every claim goes through the reusable claim path (``readmark.audit.claims.check_claims``):
   located passages with verbatim quotes, then the map's own checks.
5. Supported evidence-map claims on decisive clauses that rest on the file and that the summary
   never states are listed as left out of it, by clause (``omitted``).

The audit runs after the reading gate and never feeds it: required reading stays the evidence
map's, capped at 8. If the audit finds no error, that is the result; nothing is staged.
"""

import re

from readmark.audit.claims import check_claims, map_pairs
from readmark.checklist import CLAUSE_IDS

__all__ = ["AUDIT_CASES", "audit_summary", "check_claims", "map_pairs", "split_sentences",
           "view_block"]

# The demo file is the one with a summary under audit; every other case's view has audit: null.
AUDIT_CASES = ("A-0142",)
STATUSES = ("supported", "contradicted", "quote_not_found", "checker_disagrees")

# -- Sentences --------------------------------------------------------------------------------

# A line that starts a block of its own: a heading, a list item or a quote.
_BLOCK = re.compile(r"^\s*(?:#{1,6}\s+|[-*+•]\s+|\d{1,2}[.)]\s+|>\s*)")
_EMPHASIS = re.compile(r"\*\*|__|`|(?<!\w)\*(?=\S)|(?<=\S)\*(?!\w)")
_TABLE_RULE = re.compile(r"^\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)*\|?$")
_RULE = re.compile(r"^\s*(?:[-*_]\s*){3,}$")
# A full stop after these is not the end of a sentence ("Ms K.", "e.g.", "p. 8", "15 Jan.").
_ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "st", "no", "nos", "vs", "etc", "e.g", "i.e", "approx", "ref",
    "p", "pp", "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov",
    "dec",
}
_END = re.compile(r"[.!?]+[\"”’)\]]*\s+")


def _blocks(text: str) -> list[str]:
    """Paragraphs, headings, list items and table rows, with their markdown markup removed."""
    blocks: list[list[str]] = []
    open_block = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or _RULE.match(line) or _TABLE_RULE.match(line):
            open_block = False
            continue
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            blocks.append(["; ".join(c for c in cells if c)])
            open_block = False
            continue
        starts = bool(_BLOCK.match(line))
        line = _EMPHASIS.sub("", _BLOCK.sub("", line, count=1)).strip()
        if not line:
            continue
        if starts or not open_block:
            blocks.append([])
        blocks[-1].append(line)
        # A heading is a block of its own; a list item may run on to the next line.
        open_block = not raw.lstrip().startswith("#")
    return [" ".join(b) for b in blocks if b]


def _split_block(block: str) -> list[str]:
    out, start = [], 0
    for m in _END.finditer(block):
        if m.end() >= len(block):
            break
        before = block[start:m.start()]
        word = re.search(r"([\w.]*\w)$", before)
        token = word.group(1) if word else ""
        if block[m.start()] == "." and (
            token.lower() in _ABBREVIATIONS or re.fullmatch(r"[A-Z]", token)
        ):
            continue  # an abbreviation or an initial ("Ms K.")
        if block[m.end()].islower():
            continue  # a sentence never starts in lower case
        out.append(block[start:m.end()].strip())
        start = m.end()
    tail = block[start:].strip()
    return [*out, tail] if tail else out


def split_sentences(text: str) -> list[str]:
    """Every sentence of the summary, in order, with markdown markup removed and nothing else
    dropped: the words of the sentences, read in order, are the words of the summary. Headings,
    list items and table rows count as sentences; where the split is unsure (an initial before a
    capital letter) two sentences stay together rather than lose a word."""
    return [s for block in _blocks(text) for s in _split_block(block)]


# -- Audit ------------------------------------------------------------------------------------


def omission_candidates(map_claims: list[dict], case_ids: set[str]) -> list[dict]:
    """The evidence-map claims a summary of the file should state: supported, on a decisive
    clause, and resting on the file (at least one cited case passage). A claim that only cites
    policy is not a fact of the file, so a summary of the file cannot leave it out."""
    return [c for c in map_claims
            if c["status"] == "supported" and c["clause_id"] in CLAUSE_IDS
            and any(cit["passage_id"] in case_ids for cit in c["citations"])]


def counts(claims: list[dict], omitted: list[dict], candidates: int, sentences: int) -> dict:
    """Every number with its n (Blueprint, Verification)."""
    return {
        "sentences": {"count": sentences, "n": sentences},
        "claims": {"count": len(claims), "n": len(claims)},
        "claims_by_status": {s: {"count": sum(c["status"] == s for c in claims),
                                 "n": len(claims)} for s in STATUSES},
        "omitted": {"count": len(omitted), "n": candidates},
    }


def audit_summary(case_id: str, case_text: str, map_claims: list[dict], case_ids: set[str], *,
                  auditor, checker, pairs: list[dict], required: set[str],
                  cache=None) -> dict:
    """The audit record (``runs/<case>/audit.json``); ``view_block`` takes the view's part.

    ``map_claims`` are the evidence map's found claims with ``claim_id, clause_id, claim,
    status, citations``; ``pairs`` its contradicting pairs; ``required`` its required passages.
    ``auditor`` gives the four model calls (``claude.ClaudeAuditor``)."""
    summary = auditor.summarise(case_id, case_text)

    # Sentences by code, then the claims in each by the model. A sentence the model skipped is
    # checked whole, so no sentence of the summary goes unchecked.
    sentences = [{"sentence_id": f"s{n:02d}", "text": t}
                 for n, t in enumerate(split_sentences(summary["text"]), start=1)]
    split = auditor.split(sentences) if sentences else {}
    texts, n = [], 0
    for s in sentences:
        own = [c for c in split.get(s["sentence_id"], [s["text"]]) if c.strip()]
        s["claim_ids"] = [f"a{n + i:02d}" for i in range(1, len(own) + 1)]
        n += len(own)
        texts += own
    claims = check_claims(case_id, texts, locator=auditor, checker=checker, pairs=pairs,
                          required=required, cache=cache)

    # Left out: the supported, file-based map claims the summary never states, by clause.
    candidates = omission_candidates(map_claims, case_ids)
    stated = auditor.covered(summary["text"], candidates) if candidates else set()
    order = {cid: i for i, cid in enumerate(CLAUSE_IDS)}
    left_out = sorted((c for c in candidates if c["claim_id"] not in stated),
                      key=lambda c: (order[c["clause_id"]], candidates.index(c)))
    omitted = [{"claim_id": c["claim_id"], "clause_id": c["clause_id"]} for c in left_out]

    return {
        "case_id": case_id,
        "model": summary["model"],
        "prompt": summary["prompt"],
        "created": summary["created"],
        "summary": summary["text"],
        "sentences": sentences,
        "claims": claims,
        "omitted": omitted,
        "considered_for_omission": [c["claim_id"] for c in candidates],
        "counts": counts(claims, omitted, len(candidates), len(sentences)),
        "models": {"auditor": getattr(auditor, "model_id", None),
                   "checker": getattr(checker, "model_id", None)},
        "calls": getattr(auditor, "calls", []),
    }


def view_block(record: dict | None) -> dict | None:
    """The view's ``audit``: the Fixed shape, ``null`` when no summary was audited."""
    if record is None:
        return None
    return {k: record[k] for k in ("model", "prompt", "created", "summary", "sentences",
                                   "claims", "omitted")}
