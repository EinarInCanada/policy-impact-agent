from dataclasses import replace
import unittest

from policy_impact.evidence import EvidenceRef
from policy_impact.retrieval import DEFAULT_CORPUS, Index, evaluate_development, load_index
from test_evidence import source


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.index = load_index()

    def test_every_passage_exactly_resolves(self):
        self.assertEqual(len(self.index.sources), 7)
        for passage in self.index.passages:
            self.assertEqual(self.index.corpus.verify(passage.reference), passage.reference.quote)

    def test_current_and_historical_revision(self):
        for at, revision in [('2026-09-15', 'v1'), ('2026-10-01', 'v2')]:
            selected, _ = self.index.select(at, 'policy')
            self.assertEqual([(s.document_id, s.revision_id) for s in selected], [('review-policy', revision)])

    def test_published_comparison_preserves_both_versions(self):
        sources, excluded = self.index.select('2026-09-15', 'policy', [('review-policy', 'v1'), ('review-policy', 'v2')], 'published')
        self.assertEqual(len(sources), 2)
        self.assertEqual(excluded, [])
        self.assertGreater(sources[1].effective_on, '2026-09-15')

    def test_future_and_unknown_dates_excluded(self):
        sources, excluded = self.index.select('2026-10-15', 'procedure')
        self.assertNotIn('future-review-procedure', [s.document_id for s in sources])
        self.assertNotIn('undated-procedure', [s.document_id for s in sources])
        self.assertEqual({e['reason'] for e in excluded}, {'not_yet_published', 'unknown_effective_date'})

    def test_unknown_published_revision_prevents_current_claim(self):
        index = Index([source(), source(revision_id='v2', published_on='2026-03-01', effective_on=None)])
        sources, excluded = index.select('2026-10-15')
        self.assertEqual(sources, [])
        self.assertIn('ambiguous_revision_timeline', [e['reason'] for e in excluded])

    def test_ambiguous_equal_effective_dates_not_arbitrarily_resolved(self):
        index = Index([source(), source(revision_id='v2')])
        sources, excluded = index.select('2026-10-15')
        self.assertEqual(sources, [])
        self.assertEqual(len(excluded), 2)

    def test_compare_exact_changes_without_claiming_semantics(self):
        result = self.index.compare('review-policy', 'v1', 'v2', at='2026-09-15')
        changes = {c['clause_id']: c['change'] for c in result['changes']}
        self.assertEqual(changes, {'INTERVAL': 'modified', 'OWNER': 'modified', 'ESCALATION': 'added'})
        self.assertNotIn('RETENTION', changes)  # moved unchanged clause
        for change in result['changes']:
            for side in ('before', 'after'):
                if change[side]:
                    self.index.corpus.verify(EvidenceRef(**change[side]['reference']))

    def test_compare_rejects_unpublished_and_same_version(self):
        for before, after, at in [('v1', 'v2', '2026-07-31'), ('v1', 'v1', '2026-10-15')]:
            with self.assertRaises(ValueError):
                self.index.compare('review-policy', before, after, at=at)

    def test_compare_add_remove_and_reword(self):
        index = Index([source(text='[A] One.\n\n[B] Two.'), source(revision_id='v2', text='[A] One!\n\n[C] Three.')])
        changes = index.compare('review-policy', 'v1', 'v2', at='2026-10-15')['changes']
        self.assertEqual({c['clause_id']: c['change'] for c in changes}, {'A': 'modified', 'B': 'removed', 'C': 'added'})

    def test_stable_search_and_no_zero_match_padding(self):
        first = self.index.search('high risk reviews', at='2026-10-15', role='policy')
        self.assertEqual(first, self.index.search('high risk reviews', at='2026-10-15', role='policy'))
        self.assertEqual(self.index.search('asteroids', at='2026-10-15')['hits'], [])
        self.assertTrue(all(h['reference']['revision_id'] == 'v2' for h in first['hits']))

    def test_search_role_and_explicit_version_scope(self):
        result = self.index.search('months', at='2026-10-15', role='policy', keys=[('review-policy', 'v1')])
        self.assertTrue(result['hits'])
        self.assertTrue(all(h['reference']['revision_id'] == 'v1' for h in result['hits']))

    def test_duplicate_clause_id_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate clause'):
            Index([source(text='[A] One.\n\n[A] Two.')])

    def test_unnumbered_paragraphs_keep_unicode_and_crlf(self):
        index = Index([source(text='Évidence 📄.\r\n\r\nDeuxième élément.')])
        self.assertEqual([p.clause_id for p in index.passages], ['P001', 'P002'])
        self.assertEqual(index.passages[1].reference.quote, 'Deuxième élément.')
        for passage in index.passages:
            index.corpus.verify(passage.reference)

    def test_invalid_search_parameters(self):
        for kwargs in ({'query': ''}, {'limit': True}, {'limit': 21}, {'role': 'anything'},
                       {'at': None}, {'mode': 'latest'}, {'mode': 'published'}, {'keys': [('no', 'v1')]}):
            params = dict(query='review', at='2026-10-15')
            params.update(kwargs)
            with self.subTest(params=params), self.assertRaises(ValueError):
                self.index.search(**params)

    def test_fixture_development_reports_every_case(self):
        report = evaluate_development(self.index, DEFAULT_CORPUS.with_name('development.json'))
        self.assertEqual(len(report['rows']), 11)
        self.assertEqual(report['split'], 'development')
        self.assertTrue(next(r for r in report['rows'] if r['id'] == 'd9')['empty_query_correct'])
        # Synonym-only failure stays visible; do not turn a baseline into an answer oracle.
        self.assertEqual(next(r for r in report['rows'] if r['id'] == 'd10')['recall'], 0)


if __name__ == '__main__':
    unittest.main()
