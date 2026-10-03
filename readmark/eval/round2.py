"""Compare frozen first-run metrics with rebuilt, cached stage outputs for Task-12.

No label enters a model. Only originally flagged H-01 claims have independent labels;
retained counts measure those reviewed flags, not recall over all summary errors.
"""

from readmark import case_run_dir
from readmark.audit.claims import nothing_to_check
from readmark.eval import eval_dir, write_part
from readmark.eval.cases import ALL_CASES, EVALUATION_CASES, load, rate


def audit_metrics(claims: list[dict]) -> dict:
    n = len(claims)
    return {
        'flags': rate(sum(c['status'] != 'supported' for c in claims), n),
        'by_status': {status: rate(sum(c['status'] == status for c in claims), n)
                      for status in ('supported', 'quote_not_found', 'checker_disagrees',
                                     'contradicted')},
    }


def refresh() -> None:
    """Reassemble comparisons deterministically; never replace the stored 'before' inputs."""
    baseline = load(eval_dir() / 'checks_round2.json')
    before = baseline['before']
    audits = {cid: load(case_run_dir(cid) / 'audit.json')['claims']
              for cid in before['audit']}
    original_labels = before['parts']['audit_labels']
    labels = []
    for label in original_labels['labels']:
        claim = next(c for c in audits[label['case']] if c['claim_id'] == label['claim_id'])
        labels.append({**label, 'after_status': claim['status'],
                       'remains_flagged': claim['status'] != 'supported'})
    h_labels = [r for r in labels if r['case'] == 'H-01']
    retained = {
        kind: rate(sum(r['remains_flagged'] for r in h_labels if r['label'] == kind),
                   sum(r['label'] == kind for r in h_labels))
        for kind in ('real_summary_error', 'file_inconsistency', 'false_alarm')
    }
    flags = [c for c in audits['H-01'] if c['status'] != 'supported']
    labelled_ids = {r['claim_id'] for r in h_labels}
    # Use both denominators: precision among remaining flags, and retention among each
    # originally labelled class. A removed false alarm must not shrink the recall denominator.
    after_labels = {
        'label': 'after changes, not held-out',
        'flags': rate(len(flags), len(audits['H-01'])),
        **{kind: rate(metric['count'], len(flags)) for kind, metric in retained.items()},
        'useful_flags': rate(retained['real_summary_error']['count']
                             + retained['file_inconsistency']['count'], len(flags)),
        'retained_by_label': retained,
        'new_unlabelled_flags': rate(
            sum(c['claim_id'] not in labelled_ids for c in flags), len(flags)),
    }
    exemptions = {cid: {
        'display': 'nothing to check',
        'representation': 'Non-flagged supported bucket in the fixed view schema; '
                          'checker verdict, probability and support are null, never positive.',
        'count': sum(nothing_to_check(c['claim']) for c in claims), 'n': len(claims),
        'claims': [{'claim_id': c['claim_id'], 'claim': c['claim']}
                   for c in claims if nothing_to_check(c['claim'])],
    } for cid, claims in audits.items()}
    write_part('audit_labels', {
        **original_labels, 'label': 'First-run labels; after changes, not held-out',
        'first_run': original_labels,
        'after_changes': after_labels,
        'labels': labels, 'suggestions': exemptions,
    })

    parts = {p: load(eval_dir() / f'{p}.json') for p in ('cases', 'mutations', 'ablation')}
    mutation_changes = []
    for cid in EVALUATION_CASES:
        stage = load(case_run_dir(cid) / 'mutations.json')
        for old, new in zip(before['mutations'][cid], stage['claims'], strict=True):
            if old['status'] != new['status']:
                mutation_changes.append({**old, 'case': cid, 'after_status': new['status'],
                                         'lost_catch': old['label'] != 'supported'
                                         and old['status'] != 'supported'
                                         and new['status'] == 'supported'})
    cache_files = {f.relative_to(case_run_dir(cid).parent).as_posix()
                   for cid in ALL_CASES for f in (case_run_dir(cid) / 'cache').glob('*.json')}
    new_files = sorted(cache_files - set(before['cache_files']))
    jev_files = [p for p in new_files if p.rsplit('/', 1)[-1].startswith('jev-')]
    baseline['after'] = {
        'cases': parts['cases']['cases'], 'mutations': parts['mutations'],
        'ablation': parts['ablation'], 'audit_labels': after_labels,
    }
    baseline['headline_comparisons'] = {
        'mutations': {'before': before['parts']['mutations']['overall'],
                      'after': parts['mutations']['overall']},
        'audit': {cid: {'before': audit_metrics(before['audit'][cid]),
                        'after': audit_metrics(claims)} for cid, claims in audits.items()},
        'cases': {cid: {'before': score, 'after': parts['cases']['cases'][cid]}
                  for cid, score in before['parts']['cases']['cases'].items()},
        'ablation': {'before': before['parts']['ablation'], 'after': parts['ablation']},
        'h01_labels': {'before': original_labels['cases']['H-01'], 'after': after_labels},
    }
    baseline['suggestions'] = exemptions
    baseline['mutation_changes'] = mutation_changes
    baseline['real_errors'] = {
        cid: [{'claim_id': c['claim_id'], 'claim': c['claim'], 'status': c['status'],
               'remains_flagged': c['status'] != 'supported'}
              for c in audits[cid] if c['claim_id'] in ids]
        for cid, ids in {'A-0142': {'a36', 'a47'}, 'H-01': {'a52'}}.items()
    }
    baseline['new_model_calls'] = {
        'jev': rate(len(jev_files), len(new_files)),
        'claude': rate(len(new_files) - len(jev_files), len(new_files)),
        'new_cache_files': new_files,
        'method': 'New successful response cache entries since the frozen pre-change inventory. '
                  'Replays make no live calls; failed requests would need separate reporting.',
    }
    write_part('checks_round2', baseline)
