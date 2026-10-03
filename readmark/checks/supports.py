"""Jev backing rule, calibrated only on the committed SummEdits run1 (n=300).

The OR rule cannot repair false 'supports' verdicts. Only not-enough-information
verdicts can be rescued; an explicit contradiction or a missing verdict stays a flag.
"""

SUPPORTS_THRESHOLD = 0.1


def checker_backs(verdict: dict | None, threshold: float = SUPPORTS_THRESHOLD) -> bool:
    if not verdict:
        return False
    if verdict.get("verdict") == "supports":
        return True
    score = verdict.get("supports")
    return (verdict.get("verdict") == "not_enough_information"
            and isinstance(score, (int, float)) and not isinstance(score, bool)
            and threshold <= score <= 1)
