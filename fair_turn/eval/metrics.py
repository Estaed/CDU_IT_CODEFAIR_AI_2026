"""Per-field precision, recall and F1 with Wilson intervals, SemEval-2013 span scores and the
substring-verification rate (PRD section 7). Plain lists in, plain dicts out.
"""

from sklearn.metrics import multilabel_confusion_matrix
from statsmodels.stats.proportion import proportion_confint

F1_TARGET = 0.85  # macro-F1 bar for fault_type and safety_class, provisional (PRD section 7)
EMPTY = "__empty__"  # prediction for a field the extractor left empty or sent to a human
ABSENT = "__absent__"  # a factor not in the set, when a multi-label field is scored per factor


def wilson(count: float, nobs: int) -> list[float]:
    """Wilson 95 % interval; with no observations the proportion is unknown: [0, 1]."""
    if nobs == 0:
        return [0.0, 1.0]
    low, high = proportion_confint(count, nobs, alpha=0.05, method="wilson")
    return [max(0.0, float(low)), min(1.0, float(high))]


def _ratio(num: float, den: float) -> float:
    return num / den if den else 0.0  # zero_division=0


def prf(gold: list[str], pred: list[str], labels: list[str]) -> dict:
    """Per-class and macro P/R/F1 over ``labels`` only. A prediction outside ``labels``
    (``EMPTY``) is a false negative for the gold class and a false positive of none."""
    matrices = multilabel_confusion_matrix(gold, pred, labels=labels)
    per_class = {}
    for label, ((_, fp), (fn, tp)) in zip(labels, matrices.tolist(), strict=True):
        per_class[label] = {
            "precision": _ratio(tp, tp + fp),
            "precision_ci": wilson(tp, tp + fp),
            "recall": _ratio(tp, tp + fn),
            "recall_ci": wilson(tp, tp + fn),
            "f1": _ratio(2 * tp, 2 * tp + fp + fn),
            "support": tp + fn,
        }
    correct = sum(g == p for g, p in zip(gold, pred, strict=True))
    return {
        "n": len(gold),
        "accuracy": _ratio(correct, len(gold)),
        "accuracy_ci": wilson(correct, len(gold)),
        "macro_precision": sum(c["precision"] for c in per_class.values()) / len(labels),
        "macro_recall": sum(c["recall"] for c in per_class.values()) / len(labels),
        "macro_f1": sum(c["f1"] for c in per_class.values()) / len(labels),
        "per_class": per_class,
    }


def multilabel_prf(gold: list[set[str]], pred: list[set[str]], labels: list[str]) -> dict:
    """Each factor scored as binary presence, macro over ``labels``, plus the share of
    items whose predicted set equals the gold set."""
    per_class = {}
    for label in labels:
        present = [label if label in g else ABSENT for g in gold]
        found = [label if label in p else ABSENT for p in pred]
        per_class[label] = prf(present, found, [label])["per_class"][label]
    exact = sum(set(g) == set(p) for g, p in zip(gold, pred, strict=True))
    return {
        "n": len(gold),
        "exact_set_match": _ratio(exact, len(gold)),
        "exact_set_match_ci": wilson(exact, len(gold)),
        "macro_precision": sum(c["precision"] for c in per_class.values()) / len(labels),
        "macro_recall": sum(c["recall"] for c in per_class.values()) / len(labels),
        "macro_f1": sum(c["f1"] for c in per_class.values()) / len(labels),
        "per_class": per_class,
    }


def _overlaps(a: dict, b: dict) -> bool:
    return a["job_id"] == b["job_id"] and a["start"] < b["end"] and b["start"] < a["end"]


def _same_bounds(a: dict, b: dict) -> bool:
    return a["job_id"] == b["job_id"] and (a["start"], a["end"]) == (b["start"], b["end"])


def span_scores(gold_spans: list[dict], pred_spans: list[dict]) -> dict:
    """SemEval-2013 Task 9.1 ``exact`` and ``partial`` regimes over ``{job_id, field, start,
    end}`` spans (end exclusive). Both regimes ignore the field, as SemEval's ignore the type.
    Each gold span is matched at most once: identical bounds first, then any overlap.
    COR = identical bounds; an overlap is INC under exact and PAR under partial; an
    unmatched prediction is SPU, an unmatched gold span MIS.
    exact P = COR / ACT, R = COR / POS; partial P = (COR + 0.5 PAR) / ACT, R = ... / POS;
    ACT = COR + INC + PAR + SPU (predicted), POS = COR + INC + PAR + MIS (gold)."""
    free = list(range(len(gold_spans)))
    cor = overlap = 0
    unmatched = []
    for pred in pred_spans:
        hit = next((i for i in free if _same_bounds(gold_spans[i], pred)), None)
        if hit is None:
            unmatched.append(pred)
        else:
            free.remove(hit)
            cor += 1
    for pred in unmatched:
        hit = next((i for i in free if _overlaps(gold_spans[i], pred)), None)
        if hit is not None:
            free.remove(hit)
            overlap += 1
    act, pos = len(pred_spans), len(gold_spans)
    spu, mis = act - cor - overlap, len(free)

    def regime(credit: float) -> dict:
        precision, recall = _ratio(credit, act), _ratio(credit, pos)
        return {
            "precision": precision,
            "precision_ci": wilson(credit, act),
            "recall": recall,
            "recall_ci": wilson(credit, pos),
            "f1": _ratio(2 * precision * recall, precision + recall),
        }

    return {
        "counts": {"cor": cor, "overlap": overlap, "spu": spu, "mis": mis, "act": act, "pos": pos},
        "exact": regime(cor),
        "partial": regime(cor + 0.5 * overlap),
    }


def challenge_sentence(challenge: dict) -> str:
    """The cross-vendor check of ``eval.json`` in one line: text by another model family,
    read by the same extractor."""
    fields = challenge["fields"]
    base = challenge["baseline"]
    return (
        f"Cross-vendor check: {challenge['n']} reports written by "
        f"{', '.join(challenge['writer'])} (another model family), read by the same extractor. "
        f"Safety class {fields['safety_class']['macro_f1']:.0%} against the baseline's "
        f"{base['safety_class']['macro_f1']:.0%}; fault type "
        f"{fields['fault_type']['macro_f1']:.0%} against "
        f"{base['fault_type']['macro_f1']:.0%}. The baseline learns the generator's style; "
        "the extractor does not depend on it."
    )


def substring_rate(rows: list[dict]) -> dict:
    """Share of extraction rows whose every evidence phrase was a span of the report."""
    count = sum(bool(r["substring_ok"]) for r in rows)
    return {"rate": _ratio(count, len(rows)), "rate_ci": wilson(count, len(rows)), "n": len(rows)}
