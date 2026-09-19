"""Fixture integrity only. Do not score/tune final retrieval in unit tests."""
import hashlib
import json
from pathlib import Path
import unittest

from policy_impact.investigation import Task, task_context
from policy_impact.retrieval import load_index

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'fixtures/final-review'


class FinalFixtureTests(unittest.TestCase):
    def test_frozen_bytes(self):
        freeze = json.loads((DIRECTORY / 'freeze.json').read_text())
        for name, expected in freeze['sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected, name)

    def test_references_resolve_and_cases_are_distinct(self):
        index = load_index(DIRECTORY / 'corpus.json')
        manifest = json.loads((DIRECTORY / 'cases.json').read_text())
        self.assertEqual(manifest['split'], 'final')
        self.assertEqual(len(manifest['cases']), 8)
        self.assertEqual(len({c['id'] for c in manifest['cases']}), 8)
        items = 0
        for case in manifest['cases']:
            task_context(index, Task(**case['task']))  # date validity, no retrieval ranking or model evaluation
            self.assertEqual(len(set(case['expected_evidence'])), len(case['expected_evidence']))
            for evidence_id in case['expected_evidence']:
                index.corpus.verify(index.by_id[evidence_id].reference)
            self.assertIs(type(case['required_abstention']), bool)
            self.assertEqual(len({r['id'] for r in case['reference_items']}), len(case['reference_items']))
            items += len(case['reference_items'])
        self.assertEqual(items, 10)
        development = load_index()
        self.assertFalse({s.fingerprint for s in index.sources} & {s.fingerprint for s in development.sources})


if __name__ == '__main__':
    unittest.main()
