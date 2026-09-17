from copy import deepcopy
from dataclasses import replace
import unittest

from policy_impact.investigation import Task, prepare_fixed, run_fixed, validate_packet
from policy_impact.provider import ModelReply
from policy_impact.retrieval import load_index


def task(**changes):
    fields = dict(document_id='review-policy', before='v1', after='v2', at='2026-10-15',
                  question='high-risk customer reviews every months schedule')
    fields.update(changes)
    return Task(**fields)


def packet():
    return dict(summary='Fictional test draft.', findings=[dict(status='needs_review',
        statement='The annual procedure needs human review against the changed interval, subject to exceptions.',
        evidence_ids=['review-policy/v1/INTERVAL', 'review-policy/v2/INTERVAL', 'annual-review-procedure/v1/SCHEDULE'],
        missing_information=['Annex A is absent.'])], limitations=['Fictional test, not a semantic model evaluation.'])


class StubProvider:
    model = 'offline-test-double'
    def __init__(self):
        self.calls = []
    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return ModelReply(packet(), {'totalTokenCount': None})


class InvestigationTests(unittest.TestCase):
    def setUp(self):
        self.index = load_index()
        self.context, self.evidence = prepare_fixed(self.index, task())

    def test_fixed_rag_retrieves_before_one_generation(self):
        provider = StubProvider()
        result = run_fixed(self.index, task(), provider)
        self.assertEqual(len(provider.calls), 1)
        self.assertEqual(result['model_calls'], 1)
        self.assertTrue(provider.calls[0]['payload']['evidence'])
        self.assertEqual(len(result['packet']['findings'][0]['evidence']), 3)

    def test_current_rejects_future_after_but_planning_allows_comparison(self):
        with self.assertRaisesRegex(ValueError, 'effective'):
            prepare_fixed(self.index, task(at='2026-09-15'))
        context, _ = prepare_fixed(self.index, task(at='2026-09-15', intent='planning_review'))
        self.assertIn('planning', context['timing_warning'])
        self.assertEqual(context['after_effective_on'], '2026-10-01')

    def test_planning_still_rejects_not_published(self):
        with self.assertRaises(ValueError):
            prepare_fixed(self.index, task(at='2026-07-01', intent='planning_review'))

    def test_no_fabricated_or_unseen_references(self):
        for evidence_id in ('unknown/v1/A', 'future-review-procedure/v1/SCHEDULE'):
            data = packet()
            data['findings'][0]['evidence_ids'].append(evidence_id)
            with self.assertRaisesRegex(ValueError, 'unseen'):
                validate_packet(data, self.evidence, self.index, task())

    def test_requires_both_policy_versions_and_procedure(self):
        for omitted in range(3):
            data = packet()
            data['findings'][0]['evidence_ids'].pop(omitted)
            with self.assertRaisesRegex(ValueError, 'both policy'):
                validate_packet(data, self.evidence, self.index, task())

    def test_abstention_needs_missing_information(self):
        data = packet()
        data['findings'][0].update(status='insufficient_evidence', evidence_ids=[], missing_information=['Missing Annex A.'])
        self.assertEqual(validate_packet(data, self.evidence, self.index, task())['findings'][0]['evidence'], [])
        data['findings'][0]['missing_information'] = []
        with self.assertRaises(ValueError):
            validate_packet(data, self.evidence, self.index, task())

    def test_schema_status_duplicates_and_empty_findings_rejected(self):
        variants = []
        data = packet(); data['findings'][0]['status'] = 'compliant'; variants.append(data)
        data = packet(); data['findings'] = []; variants.append(data)
        data = packet(); data['findings'][0]['evidence_ids'] *= 2; variants.append(data)
        data = packet(); data['hidden_command'] = 'execute'; variants.append(data)
        data = packet(); data['findings'][0]['statement'] = ''; variants.append(data)
        for data in variants:
            with self.subTest(data=data), self.assertRaises(ValueError):
                validate_packet(data, self.evidence, self.index, task())

    def test_missing_information_is_not_semantically_verified(self):
        # Explicit boundary: a schema-valid but nonsensical statement is not magically rejected.
        data = packet()
        data['findings'][0]['statement'] = 'This deliberately unsupported claim passes structural checks.'
        result = validate_packet(data, self.evidence, self.index, task())
        self.assertIn('not semantic correctness', result['mandatory_notice'])


if __name__ == '__main__':
    unittest.main()
