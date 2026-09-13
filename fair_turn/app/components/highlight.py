"""Highlighting verified spans in a report's raw text (PRD 3.2).

Evidence phrases are guaranteed to be substrings of the report after whitespace
normalisation (``core.verify_spans.normalise``), not necessarily before it: a phrase
may wrap across a line break in the report. ``spans`` locates each phrase in the raw
text with a plain substring search first, falling back to a whitespace-tolerant regex.
"""

import re

_MD_CONTROL = re.compile(r"([*_`#\[\]<>])")


def _escape(text: str) -> str:
    return _MD_CONTROL.sub(r"\\\1", text)


def _locate(phrase: str, report_text: str) -> tuple[int, int] | None:
    idx = report_text.find(phrase)
    if idx != -1:
        return idx, idx + len(phrase)
    tokens = phrase.split()
    if not tokens:
        return None
    pattern = r"\s+".join(re.escape(t) for t in tokens)
    match = re.search(pattern, report_text, re.DOTALL)
    if match is None:
        return None
    return match.start(), match.end()


def spans(report_text: str, evidence: dict[str, str]) -> list[tuple[int, int, str]]:
    """One ``(start, end, field)`` per locatable phrase in ``evidence``, sorted by
    position. Overlapping spans keep the earlier one, or the longer one on a tie."""
    found = []
    for field, phrase in evidence.items():
        location = _locate(phrase, report_text)
        if location is not None:
            found.append((location[0], location[1], field))
    found.sort(key=lambda s: (s[0], -(s[1] - s[0])))
    kept: list[tuple[int, int, str]] = []
    last_end = -1
    for start, end, field in found:
        if start < last_end:
            continue
        kept.append((start, end, field))
        last_end = end
    return kept


def render(report_text: str, spans_: list[tuple[int, int, str]]) -> str:
    """Markdown with ``**...**`` around each span, escaping Markdown control characters
    everywhere else in the text (and inside the bolded spans themselves)."""
    ordered = sorted(spans_, key=lambda s: s[0])
    out = []
    pos = 0
    for start, end, _field in ordered:
        out.append(_escape(report_text[pos:start]))
        out.append("**" + _escape(report_text[start:end]) + "**")
        pos = end
    out.append(_escape(report_text[pos:]))
    return "".join(out)
