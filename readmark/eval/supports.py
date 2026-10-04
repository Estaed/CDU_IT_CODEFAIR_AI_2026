"""Task-14 comparisons from replay stages, after fixing the SummEdits-only rule.

The pre-change snapshot and H-01's first run are immutable. First-run labels cover
only reviewed flags, so class retention is not recall over all summary errors.
"""

import hashlib

from readmark import case_run_dir
from readmark.eval import eval_dir, write_part
from readmark.eval.cases import ALL_CASES, EVALUATION_CASES, load, rate
from readmark.eval.round2 import audit_metrics

PART = 'jev_supports'
AUDITS = ('A-0142', 'H-01')
KINDS = ('real_summary_error', 'file_inconsistency', 'false_alarm')


def cache_inventory() -> dict:
    """Pin responses byte for byte, including the outside-data calibration caches."""
    folders = [case_run_dir(cid) / 'cache' for cid in ALL_CASES]
    folders.append(eval_dir() / 'cache')
    root = eval_dir().parent
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in folders for p in sorted(folder.rglob('*.json'))}


def freeze_before() -> None:
    """Call once before rebuilding; never overwrite an existing baseline."""
    if (eval_dir() / f'{PART}.json').exists():
        raise RuntimeError('Task-14 baseline already exists; it must not be replaced.')
    cases = load(eval_dir() / 'cases.json')['cases']
    audits = {cid: [{k: c[k] for k in ('claim_id', 'claim', 'status')}
                    for c in load(case_run_dir(cid) / 'audit.json')['claims']]
              for cid in AUDITS}
    mutations = {}
    for cid in EVALUATION_CASES:
        stage = load(case_run_dir(cid) / 'mutations.json')
        mutations[cid] = [{**{k: c[k] for k in ('claim_id', 'claim', 'status')},
                           'label': label['label'], 'mutation_type': label['mutation_type']}
                          for c, label in zip(stage['claims'], stage['labels'], strict=True)]
    write_part(PART, {
        'part': PART, 'label': 'Task-14: after changes, not held-out',
        'before': {'cases': cases, 'audit': audits, 'mutations': mutations,
                   'mutation_metrics': load(eval_dir() / 'mutations.json'),
                   'audit_labels': load(eval_dir() / 'audit_labels.json'),
                   'cache_sha256': cache_inventory()},
    })


def labelled_flags(audits: dict, labels: list[dict]) -> tuple[list[dict], dict]:
    rows = []
    for label in labels:
        claim = next(c for c in audits[label['case']] if c['claim_id'] == label['claim_id'])
        rows.append({**label, 'after_status': claim['status'],
                     'remains_flagged': claim['status'] != 'supported'})
    h_labels = [r for r in rows if r['case'] == 'H-01']
    flags = [c for c in audits['H-01'] if c['status'] != 'supported']
    retained = {kind: rate(sum(r['remains_flagged'] for r in h_labels if r['label'] == kind),
                           sum(r['label'] == kind for r in h_labels)) for kind in KINDS}
    ids = {r['claim_id'] for r in h_labels}
    return rows, {
        'label': 'after changes, not held-out',
        'flags': rate(len(flags), len(audits['H-01'])),
        **{kind: rate(metric['count'], len(flags)) for kind, metric in retained.items()},
        'retained_by_label': retained,
        'useful_flags': rate(retained['real_summary_error']['count']
                             + retained['file_inconsistency']['count'], len(flags)),
        'new_unlabelled_flags': rate(sum(c['claim_id'] not in ids for c in flags), len(flags)),
    }


def judgment(claim: dict) -> dict:
    checker = claim['checker']
    return {'claim_id': claim['claim_id'], 'claim': claim['claim'],
            'status': claim['status'], 'remains_flagged': claim['status'] != 'supported',
            'checker': {**(checker or {}), 'n': 1}}


def refresh() -> None:
    """Rebuild only current results; the Task-12 comparison remains historical."""
    result = load(eval_dir() / f'{PART}.json')
    before = result['before']
    audits = {cid: load(case_run_dir(cid) / 'audit.json')['claims'] for cid in AUDITS}
    original_labels = before['audit_labels']['first_run']
    rows, labels = labelled_flags(audits, original_labels['labels'])
    write_part('audit_labels', {
        **before['audit_labels'], 'first_run': original_labels,
        'after_changes': labels, 'labels': rows,
    })
    cases = load(eval_dir() / 'cases.json')['cases']
    mutations = load(eval_dir() / 'mutations.json')
    result['rule'] = load(eval_dir() / 'checker.json')['checkers']['jev']['backing_rule']
    result['headline_comparisons'] = {
        'audit': {cid: {'before': audit_metrics(before['audit'][cid]),
                        'after': audit_metrics(audits[cid])} for cid in AUDITS},
        'h01_labels': {'before': before['audit_labels']['after_changes'], 'after': labels},
        'mutations': {'before': before['mutation_metrics']['overall'],
                      'after': mutations['overall']},
        'required_reading': {cid: {
            'before': {k: before['cases'][cid][k]
                       for k in ('required_reading', 'gold_page_coverage')},
            'after': {k: cases[cid][k] for k in ('required_reading', 'gold_page_coverage')},
        } for cid in ALL_CASES},
    }
    result['audit_changes'] = {
        cid: [{**judgment(c), 'before_status': old['status']}
              for old, c in zip(before['audit'][cid], audits[cid], strict=True)
              if old['status'] != c['status']] for cid in AUDITS
    }
    result['real_errors'] = {
        cid: [judgment(c) for c in audits[cid] if c['claim_id'] in ids]
        for cid, ids in {'A-0142': {'a36', 'a47'}, 'H-01': {'a52'}}.items()
    }
    changes = []
    for cid in EVALUATION_CASES:
        stage = load(case_run_dir(cid) / 'mutations.json')
        for old, c in zip(before['mutations'][cid], stage['claims'], strict=True):
            if old['status'] != c['status']:
                changes.append({**judgment(c), 'case': cid, 'before_status': old['status'],
                                'label': old['label'], 'mutation_type': old['mutation_type'],
                                'lost_catch': old['label'] != 'supported'
                                and old['status'] != 'supported' and c['status'] == 'supported'})
    result['mutation_changes'] = changes
    current_cache = cache_inventory()
    added = sorted(current_cache.keys() - before['cache_sha256'].keys())
    changed = sorted(k for k, digest in before['cache_sha256'].items()
                     if k in current_cache and current_cache[k] != digest)
    result['response_cache'] = {
        'n': len(before['cache_sha256']),
        'unchanged': current_cache == before['cache_sha256'],
        'original_responses_unchanged': not changed and not (
            before['cache_sha256'].keys() - current_cache.keys()),
        'changed_or_added': sorted(k for k in current_cache
                                   if current_cache[k] != before['cache_sha256'].get(k)),
        'removed': sorted(before['cache_sha256'].keys() - current_cache.keys()),
        'new_model_calls': {'count': len(added), 'n': len(added),
                            'method': 'Successful response files added since the frozen '
                            'Task-14 baseline, including later live pair measurements. '
                            'Refreshing this comparison itself makes no model calls.'},
    }
    result['first_run_h01'] = before['cases']['H-01']['first_run']
    write_part(PART, result)
