"""Checker evaluation (Task-08): Jev against Claude-as-checker on the SummEdits sample.

Both checkers go through the same seam the pipeline uses, ``make_checker(name, cache).check``.
Each SummEdits pair becomes one item: the summary is the claim, the whole document is its one
passage. A "supports" verdict counts as consistent; anything else (contradicts,
not_enough_information, or no verdict at all) counts as inconsistent.

Jev runs twice over the same sample, each run with its own cache directory, so the second run
is a real second call and the two can be compared. Every response is cached under
``runs/eval/cache/<run>/`` and committed; ``--replay`` rebuilds ``runs/eval/checker.json`` from
the cache with no key and no network.
"""

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from readmark.cache import Cache
from readmark.eval import eval_dir, write_part
from readmark.eval.summedits import (
    MAX_DOC_WORDS,
    PER_DOMAIN_PER_LABEL,
    SEED,
    SOURCE_SHA256,
    SOURCE_URL,
    load_sample,
)
from readmark.jev import make_checker

PART = "checker"
RUNS = {"claude": "claude", "jev": "jev-run1", "jev_run2": "jev-run2"}  # result key -> cache dir

# Claude-as-checker reads several pairs per call, as ClaudeChecker does for a case. A batch never
# holds two pairs on the same document, so Claude cannot compare two edits of one summary side by
# side (Jev sees one pair per call and gets no such hint).
CLAUDE_BATCH_ITEMS = 10
CLAUDE_BATCH_WORDS = 12_000
CLAUDE_PARALLEL = 4
JEV_CHUNK = 50

BIN_WIDTH = 0.1
# Unsure band: the highest probability t (a bin edge) such that Jev's calls below t, at least
# UNSURE_MIN_N of them, are right less than UNSURE_TARGET of the time. Recorded only; not wired
# into the gate. This rule was set AFTER the first live run: the rule fixed before it (lowest t
# where the calls at >= t are right >= 80 %) gave an empty band, because Jev is right 82.7 % of
# the time overall (n=300), so it could not separate anything.
UNSURE_TARGET = 0.70
UNSURE_MIN_N = 30
UNSURE_RULE = (f"highest bin edge t where the calls below t (n >= {UNSURE_MIN_N}) are right less "
               f"than {UNSURE_TARGET:.0%} of the time; set after the first live run, because the "
               "rule fixed before it (calls at >= t right >= 80 %) gave an empty band; recorded "
               "only, not in the gate")

RULE = ("A 'supports' verdict counts as consistent; contradicts, not_enough_information or no "
        "verdict counts as inconsistent. Positive class = consistent (SummEdits label 1).")


# ---------------------------------------------------------------- items and batches


def to_items(sample: list[dict]) -> list[dict]:
    """One checker item per pair; ids are the neutral sample ids (s001...)."""
    return [
        {
            "claim_id": s["sample_id"],
            "claim": s["summary"],
            "passages": [{"passage_id": f"{s['sample_id']}:doc", "text": s["doc"]}],
        }
        for s in sample
    ]


def claude_batches(items: list[dict]) -> list[list[dict]]:
    """First-fit batching in sample order: at most CLAUDE_BATCH_ITEMS pairs and
    CLAUDE_BATCH_WORDS document words per call, and never two pairs on the same document.
    Deterministic, so a replay rebuilds the same prompts and hits the same cache keys."""
    batches: list[dict] = []
    for item in items:
        doc = item["passages"][0]["text"]
        words = len(doc.split())
        batch = next((b for b in batches
                      if len(b["items"]) < CLAUDE_BATCH_ITEMS and doc not in b["docs"]
                      and b["words"] + words <= CLAUDE_BATCH_WORDS), None)
        if batch is None:
            batch = {"items": [], "docs": set(), "words": 0}
            batches.append(batch)
        batch["items"].append(item)
        batch["docs"].add(doc)
        batch["words"] += words
    return [b["items"] for b in batches]


# ---------------------------------------------------------------- running the checkers


def run_claude(items: list[dict], replay: bool) -> tuple[dict, list[str]]:
    """Claude over every batch, CLAUDE_PARALLEL calls at a time. A failed batch does not stop
    the others: what succeeded stays in the cache, and a rerun only calls what is missing."""
    cache = Cache(eval_dir() / "cache" / RUNS["claude"], replay)
    verdicts, models, failures = {}, set(), []

    def one(batch):
        checker = make_checker("claude", cache)
        result = checker.check(batch)
        return result, checker.model_id

    batches = claude_batches(items)
    with ThreadPoolExecutor(max_workers=1 if replay else CLAUDE_PARALLEL) as pool:
        futures = {pool.submit(one, b): k for k, b in enumerate(batches)}
        for future in as_completed(futures):
            try:
                result, model = future.result()
            except Exception as exc:  # noqa: BLE001 - reported below, the rest still record
                failures.append(f"batch {futures[future]}: {exc}")
                continue
            models.add(model)
            verdicts.update({v["claim_id"]: v for v in result})
    if failures:
        raise RuntimeError(f"Claude: {len(failures)} of {len(batches)} batches failed "
                           f"(the rest are cached; rerun to call only those):\n"
                           + "\n".join(sorted(failures)))
    return verdicts, sorted(models)


def run_jev(items: list[dict], cache_dir: str, replay: bool) -> tuple[dict, list[str]]:
    """Jev, one call per pair (JevChecker's own threads), in chunks so progress shows."""
    checker = make_checker("jev", Cache(eval_dir() / "cache" / cache_dir, replay))
    verdicts, models = {}, set()
    for start in range(0, len(items), JEV_CHUNK):
        chunk = items[start:start + JEV_CHUNK]
        verdicts.update({v["claim_id"]: v for v in checker.check(chunk)})
        models.update(checker.model_id.split(", "))
        if not replay:
            print(f"jev {cache_dir}: {start + len(chunk)}/{len(items)}", file=sys.stderr)
    return verdicts, sorted(models)


# ---------------------------------------------------------------- the numbers


def consistent_call(verdict: dict | None) -> int:
    """1 = the checker calls the summary consistent, 0 = anything else."""
    return int(bool(verdict) and verdict.get("verdict") == "supports")


def ratio(num: int, den: int) -> float | None:
    return round(num / den, 4) if den else None


def confusion(rows: list[dict]) -> dict:
    """Balanced accuracy with its confusion counts. Each row is {label, call, probability}.
    tp = consistent called consistent, tn = inconsistent called inconsistent."""
    tp = sum(1 for r in rows if r["label"] == 1 and r["call"] == 1)
    fn = sum(1 for r in rows if r["label"] == 1 and r["call"] == 0)
    tn = sum(1 for r in rows if r["label"] == 0 and r["call"] == 0)
    fp = sum(1 for r in rows if r["label"] == 0 and r["call"] == 1)
    tpr, tnr = ratio(tp, tp + fn), ratio(tn, tn + fp)
    balanced = None if tpr is None or tnr is None else round(
        (tp / (tp + fn) + tn / (tn + fp)) / 2, 4)
    return {
        "n": len(rows),
        "balanced_accuracy": balanced,
        "accuracy": ratio(tp + tn, len(rows)),
        "consistent_recall": tpr,
        "inconsistent_recall": tnr,
        "tp": tp, "fn": fn, "tn": tn, "fp": fp,
    }


def bin_index(p: float) -> int:
    """Bins [0,0.1), [0.1,0.2), ... [0.9,1.0]; 1.0 falls in the last bin."""
    return min(int(p / BIN_WIDTH + 1e-9), round(1 / BIN_WIDTH) - 1)


def calibration(rows: list[dict]) -> list[dict]:
    """Per probability bin (the checker's probability for its own verdict): how many pairs, the
    mean probability, and how often the consistent/inconsistent call was right. Pairs with no
    probability get their own row."""
    nbins = round(1 / BIN_WIDTH)
    groups: dict = {i: [] for i in range(nbins)}
    missing = []
    for r in rows:
        if r["probability"] is None:
            missing.append(r)
        else:
            groups[bin_index(r["probability"])].append(r)
    table = []
    for i in range(nbins):
        g = groups[i]
        table.append({
            "bin": f"{i * BIN_WIDTH:.1f}-{(i + 1) * BIN_WIDTH:.1f}",
            "n": len(g),
            "mean_probability": ratio(round(sum(r["probability"] for r in g), 6), len(g)),
            "accuracy": ratio(sum(r["call"] == r["label"] for r in g), len(g)),
        })
    if missing:
        table.append({"bin": "no probability", "n": len(missing),
                      "accuracy": ratio(sum(r["call"] == r["label"] for r in missing),
                                        len(missing))})
    return table


def unsure_band(rows: list[dict]) -> dict:
    """The highest bin edge t such that the calls below t, at least UNSURE_MIN_N of them, are
    right less than UNSURE_TARGET of the time: those calls are the unsure band. Every cutoff
    is listed too, so a reader can see the trade-off. If no t qualifies, no band (found = false).
    """
    scored = [r for r in rows if r["probability"] is not None]

    def right(rs):
        return ratio(sum(r["call"] == r["label"] for r in rs), len(rs))

    cutoffs, chosen = [], None
    for i in range(1, round(1 / BIN_WIDTH)):
        below = [r for r in scored if bin_index(r["probability"]) < i]
        above = [r for r in scored if bin_index(r["probability"]) >= i]
        cutoffs.append({"below": round(i * BIN_WIDTH, 1), "n": len(scored),
                        "unsure_n": len(below), "unsure_accuracy": right(below),
                        "sure_n": len(above), "sure_accuracy": right(above)})
        if len(below) >= UNSURE_MIN_N and right(below) < UNSURE_TARGET:
            chosen = cutoffs[-1]  # keep going: the highest qualifying edge wins
    return {
        "found": chosen is not None,
        "band": f"probability below {chosen['below']:.1f}" if chosen else "none",
        "rule": UNSURE_RULE,
        **(chosen or {"n": len(scored)}),
        "cutoffs": cutoffs,
    }


def agreement(a: dict, b: dict, ids: list[str]) -> dict:
    """Two runs of one checker on the same pairs: how often the call and the verdict match."""
    calls = sum(consistent_call(a.get(i)) == consistent_call(b.get(i)) for i in ids)
    verdicts = sum((a.get(i) or {}).get("verdict") == (b.get(i) or {}).get("verdict") for i in ids)
    diffs = [abs(a[i]["probability"] - b[i]["probability"]) for i in ids
             if a.get(i) and b.get(i) and a[i]["probability"] is not None
             and b[i]["probability"] is not None]
    return {
        "n": len(ids),
        "same_call": calls,
        "same_call_rate": ratio(calls, len(ids)),
        "same_verdict": verdicts,
        "same_verdict_rate": ratio(verdicts, len(ids)),
        "probability_compared_n": len(diffs),
        "mean_abs_probability_difference": ratio(round(sum(diffs), 6), len(diffs)),
        "max_abs_probability_difference": round(max(diffs), 4) if diffs else None,
    }


def rows_for(sample: list[dict], verdicts: dict) -> list[dict]:
    return [
        {
            "domain": s["domain"],
            "label": s["label"],
            "call": consistent_call(verdicts.get(s["sample_id"])),
            "probability": (verdicts.get(s["sample_id"]) or {}).get("probability"),
            "verdict": (verdicts.get(s["sample_id"]) or {}).get("verdict"),
        }
        for s in sample
    ]


def checker_block(rows: list[dict], models: list[str]) -> dict:
    domains = sorted({r["domain"] for r in rows})
    verdict_counts = {"n": len(rows)}
    for r in rows:
        key = r["verdict"] or "no_verdict"
        verdict_counts[key] = verdict_counts.get(key, 0) + 1
    return {
        "model": ", ".join(models),
        "overall": confusion(rows),
        "per_domain": {d: confusion([r for r in rows if r["domain"] == d]) for d in domains},
        "verdicts": verdict_counts,
        "calibration": calibration(rows),
    }


def cost(n: int) -> dict:
    """Live calls behind the cached numbers, counted from the cache files."""
    out = {"n": n}
    for key, directory in RUNS.items():
        files = sorted((eval_dir() / "cache" / directory).glob("*.json"))
        out[f"{key}_calls"] = len(files)
        if key.startswith("jev"):
            usage = [json.loads(f.read_text(encoding="utf-8"))["response"].get("usage") or {}
                     for f in files]
            out[f"{key}_input_tokens"] = sum(u.get("input_tokens", 0) for u in usage)
            out[f"{key}_output_tokens"] = sum(u.get("output_tokens", 0) for u in usage)
    return out


def evaluate(replay: bool) -> dict:
    """Run (or replay) both checkers on the sample and write runs/eval/checker.json."""
    sample = load_sample()
    items = to_items(sample)
    ids = [s["sample_id"] for s in sample]

    jev1, jev1_models = run_jev(items, RUNS["jev"], replay)
    jev2, jev2_models = run_jev(items, RUNS["jev_run2"], replay)
    claude, claude_models = run_claude(items, replay)

    jev_rows = rows_for(sample, jev1)
    result = {
        "part": PART,
        "rule": RULE,
        "sample": {
            "n": len(sample),
            "source": SOURCE_URL,
            "source_sha256": SOURCE_SHA256,
            "licence": "CC BY 4.0",
            "seed": SEED,
            "per_domain_per_label": PER_DOMAIN_PER_LABEL,
            "domains": len({s["domain"] for s in sample}),
            "consistent": sum(s["label"] == 1 for s in sample),
            "inconsistent": sum(s["label"] == 0 for s in sample),
            "max_doc_words": max(len(s["doc"].split()) for s in sample),
            "doc_word_limit": MAX_DOC_WORDS,
        },
        "checkers": {
            "claude": checker_block(rows_for(sample, claude), claude_models),
            "jev": {**checker_block(jev_rows, jev1_models), "unsure_band": unsure_band(jev_rows)},
            "jev_run2": checker_block(rows_for(sample, jev2), jev2_models),
        },
        "jev_agreement": agreement(jev1, jev2, ids),
        "claude_batching": {
            "n": len(items),
            "calls": len(claude_batches(items)),
            "max_pairs_per_call": CLAUDE_BATCH_ITEMS,
            "max_doc_words_per_call": CLAUDE_BATCH_WORDS,
        },
        "cost": cost(len(sample)),
    }
    write_part(PART, result)
    return result
