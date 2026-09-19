from copy import deepcopy
import unittest

from policy_impact.adjudication import FLAGS, score, template
from policy_impact.final_evaluation import digest, frozen_inputs


def synthetic_result(manifest, success=True):
    rows = []
    for case in manifest['cases']:
        for mode in ('baseline', 'fixed', 'agent'):
            findings = [dict(status=r['status'], statement='Test-only reference-shaped finding.') for r in case['reference_items']]
            rows.append(dict(case_id=case['id'], mode=mode,
                operational_success=success, status='draft_ready' if success else 'provider_failed',
                result={'packet': {'findings': findings}} if success else None))
    return dict(split='final', benchmark_id=manifest['benchmark_id'], comparison_complete=True, rows=rows)


def synthetic_labels(result, manifest):
    labels = template(result, manifest)
    labels.update(reviewer='unit-test-only-not-a-human-study', reviewed_on='2026-09-18')
    cases = {c['id']: c for c in manifest['cases']}
    for review in labels['reviews']:
        if not review['finding_reviews']:
            continue
        review.update({f: False for f in FLAGS})
        review['appropriate_abstention'] = cases[review['case_id']]['required_abstention']
        review['rationale'] = 'Test fixture label, not real adjudication.'
        for i, annotation in enumerate(review['finding_reviews']):
            annotation.update(matched_reference=cases[review['case_id']]['reference_items'][i]['id'],
                              supported=True, date_or_scope_error=False, rationale='Test-only arithmetic label.')
    return labels


class AdjudicationTests(unittest.TestCase):
    def setUp(self):
        _, self.manifest, _ = frozen_inputs()
        self.result = synthetic_result(self.manifest)
        self.labels = synthetic_labels(self.result, self.manifest)

    def test_template_is_unfilled_and_cannot_be_scored(self):
        blank = template(self.result, self.manifest)
        self.assertEqual(blank['reviewer'], '')
        self.assertIsNone(blank['reviews'][0]['finding_reviews'][0]['supported'])
        with self.assertRaises(ValueError):
            score(self.result, blank, self.manifest)

    def test_arithmetic_perfect_synthetic_labels(self):
        for summary in score(self.result, self.labels, self.manifest)['summaries'].values():
            self.assertEqual(summary['reference_items'], 10)
            self.assertEqual(summary['finding_precision'], 1)
            self.assertEqual(summary['finding_recall'], 1)
            self.assertEqual(summary['appropriate_abstention_rate'], 1)

    def test_all_failures_keep_recall_denominator(self):
        result = synthetic_result(self.manifest, success=False)
        labels = synthetic_labels(result, self.manifest)
        for summary in score(result, labels, self.manifest)['summaries'].values():
            self.assertEqual(summary['failed_cases'], 8)
            self.assertEqual(summary['finding_recall'], 0)
            self.assertIsNone(summary['finding_precision'])
            self.assertEqual(summary['appropriate_abstention_rate'], 0)

    def test_wrong_binding_and_missing_rows_rejected(self):
        for change in ('binding', 'missing_result', 'missing_review', 'duplicate_review'):
            result, labels = deepcopy(self.result), deepcopy(self.labels)
            if change == 'binding':
                labels['result_sha256'] = 'wrong'
            elif change == 'missing_result':
                result['rows'].pop(); labels['result_sha256'] = digest(result)
            elif change == 'missing_review':
                labels['reviews'].pop()
            else:
                labels['reviews'][-1] = labels['reviews'][0]
            with self.assertRaises(ValueError):
                score(result, labels, self.manifest)

    def test_unsupported_wrong_status_duplicate_or_missing_label_rejected(self):
        for change in ('unsupported', 'status', 'duplicate', 'missing', 'date_error'):
            result, labels = deepcopy(self.result), deepcopy(self.labels)
            finding = labels['reviews'][0]['finding_reviews'][0]
            if change == 'unsupported': finding['supported'] = False
            elif change == 'date_error': finding['date_or_scope_error'] = True
            elif change == 'missing': finding['supported'] = None
            elif change == 'status':
                result['rows'][1]['result']['packet']['findings'][0]['status'] = 'no_issue_identified'
                labels['result_sha256'] = digest(result)
            else:
                review = next(r for r in labels['reviews'] if r['case_id'] == 'f7-conflict')
                review['finding_reviews'][1]['matched_reference'] = review['finding_reviews'][0]['matched_reference']
            with self.assertRaises(ValueError):
                score(result, labels, self.manifest)

    def test_unmatched_finding_remains_in_precision_denominator(self):
        review = self.labels['reviews'][0]
        review['finding_reviews'][0].update(matched_reference=None, supported=False)
        result = score(self.result, self.labels, self.manifest)
        self.assertEqual(result['summaries']['fixed']['finding_precision'], .9)
        self.assertEqual(result['summaries']['fixed']['finding_recall'], .9)


if __name__ == '__main__':
    unittest.main()
