from dataclasses import FrozenInstanceError, replace
import hashlib
import unittest

from policy_impact.evidence import Corpus, EvidenceRef, SourceRevision


def source(**changes):
    values = dict(document_id='review-policy', revision_id='v1', role='policy',
                  text='Review high-risk records every 12 months.\nException: see Annex A.',
                  provenance='authored fictional unit-test fixture', published_on='2026-01-01',
                  effective_on='2026-02-01')
    values.update(changes)
    return SourceRevision(**values)


class EvidenceTests(unittest.TestCase):
    def test_exact_reference_round_trip(self):
        item = source()
        corpus = Corpus([item])
        reference = corpus.cite(item.document_id, item.revision_id, 0, 40)
        self.assertEqual(corpus.verify(reference), item.text[:40])
        self.assertEqual(item.content_sha256, hashlib.sha256(item.text.encode()).hexdigest())

    def test_content_and_metadata_bound_to_fingerprint(self):
        original = source()
        for changes in ({'text': original.text + ' '}, {'effective_on': '2026-03-01'},
                        {'published_on': None}, {'role': 'procedure'}, {'provenance': 'other'},
                        {'document_id': 'other'}, {'revision_id': 'v2'}):
            with self.subTest(changes=changes):
                self.assertNotEqual(original.fingerprint, source(**changes).fingerprint)
        self.assertEqual(original.fingerprint, source().fingerprint)

    def test_tampered_quote_rejected(self):
        corpus = Corpus([source()])
        ref = corpus.cite('review-policy', 'v1', 0, 40)
        with self.assertRaisesRegex(ValueError, 'quote'):
            corpus.verify(replace(ref, quote=ref.quote.replace('12', '6')))

    def test_changed_source_or_metadata_rejected(self):
        ref = Corpus([source()]).cite('review-policy', 'v1', 0, 10)
        for changed in (source(text='Changed content'), source(effective_on='2026-03-01')):
            with self.assertRaisesRegex(ValueError, 'fingerprint'):
                Corpus([changed]).verify(ref)

    def test_revision_isolation(self):
        first, second = source(), source(revision_id='v2')
        corpus = Corpus([first, second])
        ref = corpus.cite(first.document_id, first.revision_id, 0, 10)
        with self.assertRaisesRegex(ValueError, 'fingerprint'):
            corpus.verify(replace(ref, revision_id='v2'))

    def test_invalid_offsets(self):
        corpus = Corpus([source()])
        for start, end in [(-1, 2), (2, 2), (3, 2), (0, 1000), (False, 2), (0, 1.5)]:
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                corpus.cite('review-policy', 'v1', start, end)
        ref = corpus.cite('review-policy', 'v1', 0, 10)
        with self.assertRaisesRegex(ValueError, 'outside'):
            corpus.verify(replace(ref, end=1000))

    def test_unicode_uses_python_codepoint_offsets(self):
        item = source(text='Échéance 📄：半年\n')
        corpus = Corpus([item])
        start = item.text.index('📄')
        self.assertEqual(corpus.verify(corpus.cite(item.document_id, item.revision_id, start, start + 1)), '📄')
        self.assertNotEqual(source(text='é').fingerprint, source(text='e\u0301').fingerprint)

    def test_newline_and_whitespace_not_normalized(self):
        self.assertNotEqual(source(text='a\nb').fingerprint, source(text='a\r\nb').fingerprint)
        with self.assertRaises(ValueError):
            Corpus([source(text='a   b')]).cite('review-policy', 'v1', 1, 4)

    def test_sources_and_references_frozen(self):
        item = source()
        with self.assertRaises(FrozenInstanceError):
            item.text = 'modified'
        ref = Corpus([item]).cite(item.document_id, item.revision_id, 0, 10)
        with self.assertRaises(FrozenInstanceError):
            ref.quote = 'modified'

    def test_duplicate_identity_rejected_and_input_list_copied(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            Corpus([source(), source(text='changed')])
        originals = [source()]
        corpus = Corpus(originals)
        originals.clear()
        self.assertEqual(corpus.get('review-policy', 'v1'), source())

    def test_invalid_identity_and_unknown_reference(self):
        for value in ('', '../secret', 'with space', 'x' * 129, 42):
            with self.subTest(value=value), self.assertRaises(ValueError):
                source(document_id=value)
        with self.assertRaisesRegex(ValueError, 'unknown'):
            Corpus([source()]).get('missing', 'v1')

    def test_invalid_dates_and_explicit_unknown(self):
        for value in ('2026-02-30', '2026-1-01', 'tomorrow', 20260101):
            with self.subTest(value=value), self.assertRaises(ValueError):
                source(effective_on=value)
        self.assertIsNone(source(effective_on=None).effective_on)
        # Retroactive dates are retained, not silently corrected or deemed applicable.
        self.assertEqual(source(effective_on='2025-12-01').effective_on, '2025-12-01')

    def test_invalid_text_role_provenance_and_corpus(self):
        for changes in ({'text': ''}, {'text': ' '}, {'role': 'draft'},
                        {'provenance': ''}, {'text': '\ud800'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                source(**changes)
        for revisions in ([], ['not a revision']):
            with self.assertRaises(ValueError):
                Corpus(revisions)

    def test_invalid_reference_shape(self):
        for digest in ('0', 'G' * 64):
            with self.assertRaises(ValueError):
                EvidenceRef('p', 'v1', digest, 0, 2, 'hi')
        with self.assertRaises(ValueError):
            EvidenceRef('p', 'v1', '0' * 64, True, 2, 'hi')
        with self.assertRaises(ValueError):
            Corpus([source()]).verify({'quote': 'not validated'})


if __name__ == '__main__':
    unittest.main()
