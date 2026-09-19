import copy
import json
from pathlib import Path
import tempfile
import unittest

from policy_impact.evaluation import DEFAULT_CASES, evaluate, load_cases
from policy_impact.provider import ModelReply, ProviderError
from policy_impact.retrieval import load_index


class Provider:
    model = 'offline-test-double'
    def generate(self, **kwargs):
        raise ProviderError('sensitive error must not be exported')


class InvalidPacketProvider(Provider):
    def generate(self, **kwargs):
        return ModelReply({'invalid': True}, {'totalTokenCount': 17})


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.index = load_index()
        self.manifest = load_cases(DEFAULT_CASES, self.index)

    def test_baseline_has_no_model_or_semantic_claim(self):
        result = evaluate(self.index, self.manifest)
        self.assertEqual(result['summaries']['baseline']['total_cases'], 5)
        self.assertEqual(result['summaries']['baseline']['attempted_model_calls'], 0)
        self.assertTrue(all(r['result']['packet'] is None for r in result['rows']))
        self.assertTrue(all(r['semantic_review'] == 'not_applicable' for r in result['rows']))

    def test_provider_failures_remain_in_denominators(self):
        result = evaluate(self.index, self.manifest, ('baseline', 'fixed', 'agent'), Provider())
        self.assertEqual(len(result['rows']), 15)
        for mode in ('fixed', 'agent'):
            summary = result['summaries'][mode]
            self.assertEqual(summary['total_cases'], 5)
            self.assertEqual(summary['successful_runs'], 0)
            self.assertEqual(summary['recall_denominator'], 5)
            self.assertEqual(summary['mean_required_evidence_recall'], 0)
            self.assertEqual(summary['attempted_model_calls'], 5)
        self.assertNotIn('sensitive error', json.dumps(result))

    def test_invalid_packet_retains_completed_usage(self):
        result = evaluate(self.index, self.manifest, ('fixed',), InvalidPacketProvider())
        for row in result['rows']:
            self.assertFalse(row['operational_success'])
            self.assertEqual(row['usage_per_completed_call'], [{'totalTokenCount': 17}])
            self.assertEqual(row['attempted_model_calls'], 1)

    def test_invalid_configuration_before_calls(self):
        for modes in ((), ('other',), ('baseline', 'baseline'), ('fixed',)):
            with self.assertRaises(ValueError):
                evaluate(self.index, self.manifest, modes)

    def test_checkpoints_include_failures_and_checkpoint_errors_stop_run(self):
        checkpoints = []
        result = evaluate(self.index, self.manifest, ('fixed',), Provider(), on_row=checkpoints.append)
        self.assertEqual(checkpoints, result['rows'])
        self.assertEqual(len(checkpoints), 5)
        def failing_checkpoint(row):
            raise OSError('disk failure')
        with self.assertRaises(OSError):
            evaluate(self.index, self.manifest, on_row=failing_checkpoint)

    def test_manifest_rejects_unknown_evidence_duplicates_and_final_split(self):
        for variant in ('unknown', 'duplicate', 'final'):
            manifest = copy.deepcopy(self.manifest)
            if variant == 'unknown':
                manifest['cases'][0]['expected_evidence'] = ['invented/v1/X']
            elif variant == 'duplicate':
                manifest['cases'].append(manifest['cases'][0])
            else:
                manifest['split'] = 'final'
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'cases.json'
                path.write_text(json.dumps(manifest), encoding='utf-8')
                with self.assertRaises(ValueError):
                    load_cases(path, self.index)


if __name__ == '__main__':
    unittest.main()
