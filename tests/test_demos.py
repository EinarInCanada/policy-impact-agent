from dataclasses import replace
import json
from unittest.mock import patch
import unittest

from policy_impact.demos import DEMO_FILE, load_demos
from policy_impact.evidence import EvidenceRef
from policy_impact.retrieval import Index, load_index


class DemoTests(unittest.TestCase):
    def setUp(self):
        self.index = load_index()

    def test_two_saved_examples_and_every_quote_verified(self):
        demos = load_demos(self.index)
        self.assertEqual(set(demos), {'policy-change', 'missing-evidence'})
        for result in demos.values():
            self.assertEqual(result['mode'], 'saved_demo')
            self.assertEqual(result['model_calls'], 0)
            self.assertIsNone(result['model'])
            self.assertIsNone(result['usage'])
            self.assertEqual(result['trace'], [])
            self.assertIn('Not captured', result['demo']['provenance'])
            for finding in result['packet']['findings']:
                for e in finding['evidence']:
                    self.index.corpus.verify(EvidenceRef(**e['reference']))
        self.assertEqual([f['status'] for f in demos['policy-change']['packet']['findings']],
                         ['needs_review','needs_review','no_issue_identified'])
        self.assertTrue(all(f['status']=='insufficient_evidence' and f['missing_information']
                            for f in demos['missing-evidence']['packet']['findings']))

    def test_changed_sources_are_not_silently_rebound(self):
        sources=list(self.index.sources)
        sources[0]=replace(sources[0],text=sources[0].text+'\nAltered')
        with self.assertRaises(ValueError): load_demos(Index(sources))

    def test_fabricated_or_future_demo_references_fail(self):
        for ref in ('invented/v1/X','future-review-procedure/v1/SCHEDULE'):
            raw=json.loads(DEMO_FILE.read_text())
            raw['demos'][0]['packet']['findings'][0]['evidence_ids'].append(ref)
            # Patch the manifest parser only; actual index permission checks still execute.
            with patch('policy_impact.demos.strict_json',return_value=raw):
                with self.assertRaises((ValueError,KeyError)):
                    load_demos(self.index)
