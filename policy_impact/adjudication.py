"""Prepare human review forms and aggregate completed labels; never infer labels."""
import argparse
from datetime import date
import json

from .cli import save_artifact
from .final_evaluation import digest, frozen_inputs
from .provider import strict_json
from pathlib import Path


FLAGS = ('appropriate_abstention', 'unnecessary_refusal', 'forbidden_claim', 'date_or_scope_error')


def verified_rows(result, manifest):
    if result.get('split') != 'final' or result.get('benchmark_id') != manifest['benchmark_id']:
        raise ValueError('not this final benchmark')
    if result.get('comparison_complete') is not True:
        raise ValueError('human comparison requires all three paths')
    expected = {(c['id'], mode) for c in manifest['cases'] for mode in ('baseline', 'fixed', 'agent')}
    rows = result['rows']
    if len(rows) != len(expected) or {(r['case_id'], r['mode']) for r in rows} != expected:
        raise ValueError('missing or duplicate attempted cases')
    for row in rows:
        if type(row['operational_success']) is not bool:
            raise ValueError('invalid success state')
        if row['mode'] != 'baseline':
            if row['operational_success'] != (row['status'] == 'draft_ready'):
                raise ValueError('inconsistent result state')
            if row['operational_success'] and not row['result']['packet']['findings']:
                raise ValueError('missing successful packet')
    return [r for r in rows if r['mode'] != 'baseline']


def template(result, manifest):
    rows = verified_rows(result, manifest)
    reviews = []
    for row in rows:
        findings = row['result']['packet']['findings'] if row['operational_success'] else []
        reviews.append(dict(case_id=row['case_id'], mode=row['mode'],
            finding_reviews=[dict(finding_index=i, matched_reference=None, supported=None,
                                  date_or_scope_error=None, rationale='') for i in range(len(findings))],
            **{flag: None for flag in FLAGS}, rationale=''))
    return dict(schema_version=1, result_sha256=digest(result), reviewer='', reviewed_on='',
                reviewer_kind='human', notice='Unfilled form. No semantic labels or human review are implied.', reviews=reviews)


def score(result, labels, manifest):
    rows = verified_rows(result, manifest)
    if labels.get('result_sha256') != digest(result):
        raise ValueError('review belongs to a different result')
    if labels.get('reviewer_kind') != 'human' or not isinstance(labels.get('reviewer'), str) or not labels['reviewer'].strip():
        raise ValueError('human reviewer attribution required')
    date.fromisoformat(labels['reviewed_on'])
    reviews = labels['reviews']
    if len(reviews) != len(rows):
        raise ValueError('incomplete review coverage')
    keyed = {(r['case_id'], r['mode']): r for r in reviews}
    if len(keyed) != len(rows) or set(keyed) != {(r['case_id'], r['mode']) for r in rows}:
        raise ValueError('duplicate or mismatched reviews')
    cases = {c['id']: c for c in manifest['cases']}
    summaries = {}
    for mode in ('fixed', 'agent'):
        total = dict(cases=0, failed_cases=0, findings=0, reference_items=0, credited_matches=0,
                     abstention_required=0, appropriate_abstentions=0, unnecessary_refusals=0,
                     forbidden_claim_cases=0, date_or_scope_error_cases=0)
        for row in [r for r in rows if r['mode'] == mode]:
            case, review = cases[row['case_id']], keyed[(row['case_id'], mode)]
            refs = {r['id']: r for r in case['reference_items']}
            total['cases'] += 1
            total['reference_items'] += len(refs)
            total['abstention_required'] += case['required_abstention']
            if not row['operational_success']:
                if review['finding_reviews'] or any(review[f] is not None for f in FLAGS):
                    raise ValueError('failed packets cannot receive semantic credit')
                total['failed_cases'] += 1
                continue
            if not isinstance(review['rationale'], str) or not review['rationale'].strip():
                raise ValueError('case rationale required')
            if any(type(review[f]) is not bool for f in FLAGS):
                raise ValueError('all case flags require explicit booleans')
            if review['appropriate_abstention'] and not case['required_abstention']:
                raise ValueError('abstention credit only on annotated cases')
            findings = row['result']['packet']['findings']
            annotations = review['finding_reviews']
            if len(annotations) != len(findings):
                raise ValueError('every emitted finding must be reviewed')
            credited = set()
            has_error = review['date_or_scope_error']
            for i, annotation in enumerate(annotations):
                if type(annotation['finding_index']) is not int or annotation['finding_index'] != i:
                    raise ValueError('finding indices must be consecutive and exact')
                if any(type(annotation[f]) is not bool for f in ('supported', 'date_or_scope_error')):
                    raise ValueError('finding labels incomplete')
                if not isinstance(annotation['rationale'], str) or not annotation['rationale'].strip():
                    raise ValueError('finding rationale required')
                matched = annotation['matched_reference']
                if matched is not None:
                    if not isinstance(matched, str) or matched not in refs or matched in credited:
                        raise ValueError('unknown or duplicate reference match')
                    if not annotation['supported'] or annotation['date_or_scope_error'] or findings[i]['status'] != refs[matched]['status']:
                        raise ValueError('unsupported, wrong-status or date-invalid finding cannot earn credit')
                    credited.add(matched)
                has_error |= annotation['date_or_scope_error']
            total['findings'] += len(findings)
            total['credited_matches'] += len(credited)
            total['appropriate_abstentions'] += review['appropriate_abstention']
            total['unnecessary_refusals'] += review['unnecessary_refusal']
            total['forbidden_claim_cases'] += review['forbidden_claim']
            total['date_or_scope_error_cases'] += has_error
        successes = total['cases'] - total['failed_cases']
        def ratio(a, b):
            return a / b if b else None
        summaries[mode] = dict(**total,
            finding_precision=ratio(total['credited_matches'], total['findings']),
            finding_recall=ratio(total['credited_matches'], total['reference_items']),
            case_completion=ratio(successes, total['cases']),
            appropriate_abstention_rate=ratio(total['appropriate_abstentions'], total['abstention_required']),
            unnecessary_refusal_rate=ratio(total['unnecessary_refusals'], total['cases']),
            unnecessary_refusal_successful_rate=ratio(total['unnecessary_refusals'], successes),
            forbidden_claim_rate=ratio(total['forbidden_claim_cases'], total['cases']),
            date_or_scope_error_rate=ratio(total['date_or_scope_error_cases'], total['cases']))
    return dict(result_sha256=digest(result), labels_sha256=digest(labels), reviewer=labels['reviewer'],
                reviewed_on=labels['reviewed_on'], summaries=summaries,
                limitations=['Arithmetic over supplied human labels; reviewer identity and label truth are not authenticated.',
                             'Single-reviewer authored synthetic benchmark; not independent bank validation.',
                             'Failure is not correctness: inspect failed-case counts beside error rates.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['template', 'score'])
    parser.add_argument('--result', required=True)
    parser.add_argument('--labels')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    _, manifest, _ = frozen_inputs()
    result = strict_json(Path(args.result).read_bytes())
    if args.command == 'score':
        if not args.labels:
            parser.error('--labels is required for score')
        output = score(result, strict_json(Path(args.labels).read_bytes()), manifest)
    else:
        output = template(result, manifest)
    save_artifact(args.output, output)


if __name__ == '__main__':
    main()
