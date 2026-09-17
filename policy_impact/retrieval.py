"""Small lexical reference baseline over explicitly versioned, authored text."""
import argparse
from collections import Counter
from dataclasses import asdict, dataclass
from difflib import unified_diff
import hashlib
import json
import math
from pathlib import Path
import re

from .evidence import Corpus, EvidenceRef, SourceRevision, _date

DEFAULT_CORPUS = Path(__file__).resolve().parent.parent / 'fixtures/customer-review/corpus.json'


@dataclass(frozen=True)
class Passage:
    clause_id: str
    reference: EvidenceRef

    @property
    def id(self):
        return f'{self.reference.document_id}/{self.reference.revision_id}/{self.clause_id}'

    def export(self):
        return dict(id=self.id, clause_id=self.clause_id, reference=asdict(self.reference))


def passages(source, corpus):
    result, seen = [], set()
    for number, match in enumerate(re.finditer(r'\S[\s\S]*?(?=\r?\n[ \t]*\r?\n|\Z)', source.text), 1):
        text = match.group().rstrip()
        header = re.match(r'\[([A-Z][A-Z0-9_-]*)\]', text)
        clause_id = header[1] if header else f'P{number:03}'
        if clause_id in seen:
            raise ValueError('duplicate clause identity in revision')
        seen.add(clause_id)
        result.append(Passage(clause_id, corpus.cite(source.document_id, source.revision_id,
                                                   match.start(), match.start() + len(text))))
    return tuple(result)


def tokens(text):
    return re.findall(r'[^\W_]+', text.casefold(), flags=re.UNICODE)


class Index:
    def __init__(self, sources):
        self.sources = tuple(sources)
        self.corpus = Corpus(self.sources)
        self.passages = tuple(p for source in self.sources for p in passages(source, self.corpus))
        self.by_id = {p.id: p for p in self.passages}

    def select(self, at, role=None, keys=None, mode='effective'):
        """Effective: latest eligible revision per document. Published: explicit comparison scope only."""
        _date(at)
        if at is None or mode not in ('effective', 'published') or role not in (None, 'policy', 'procedure'):
            raise ValueError('date, mode and role must be explicit valid values')
        if mode == 'published' and not keys:
            raise ValueError('published comparison requires explicit revision keys')
        keyset = None if keys is None else set(tuple(k) for k in keys)
        if keyset is not None:
            for key in keyset:
                if len(key) != 2:
                    raise ValueError('revision keys must be document/revision pairs')
                self.corpus.get(*key)
        candidates, excluded = [], []
        for source in self.sources:
            key = (source.document_id, source.revision_id)
            if (keyset is not None and key not in keyset) or (role and source.role != role):
                continue
            reason = None
            if source.published_on is None:
                reason = 'unknown_publication_date'
            elif source.published_on > at:
                reason = 'not_yet_published'
            elif mode == 'effective' and source.effective_on is None:
                reason = 'unknown_effective_date'
            elif mode == 'effective' and source.effective_on > at:
                reason = 'not_yet_effective'
            if reason:
                excluded.append(dict(document_id=key[0], revision_id=key[1], reason=reason))
            else:
                candidates.append(source)
        if mode == 'effective' and keyset is None:
            chosen = []
            for document_id in sorted({s.document_id for s in candidates}):
                group = [s for s in candidates if s.document_id == document_id]
                # Unknown dates in a published revision prevent certifying an older revision as current.
                if any(e['document_id'] == document_id and e['reason'].startswith('unknown_') for e in excluded):
                    excluded.extend(dict(document_id=s.document_id, revision_id=s.revision_id,
                                         reason='ambiguous_revision_timeline') for s in group)
                    continue
                latest_date = max(s.effective_on for s in group)
                latest = [s for s in group if s.effective_on == latest_date]
                if len(latest) != 1:
                    excluded.extend(dict(document_id=s.document_id, revision_id=s.revision_id,
                                         reason='ambiguous_revision_timeline') for s in group)
                    continue
                chosen.append(latest[0])
                excluded.extend(dict(document_id=s.document_id, revision_id=s.revision_id,
                                     reason='superseded_in_snapshot') for s in group if s != latest[0])
            candidates = chosen
        return candidates, excluded

    def search(self, query, *, at, role=None, keys=None, mode='effective', limit=3):
        if not isinstance(query, str) or not query.strip() or len(query) > 2000:
            raise ValueError('query must contain 1–2000 characters')
        if type(limit) is not int or not 1 <= limit <= 20:
            raise ValueError('limit must be an integer in 1–20')
        sources, excluded = self.select(at, role, keys, mode)
        eligible = {(s.document_id, s.revision_id) for s in sources}
        selected = [p for p in self.passages if (p.reference.document_id, p.reference.revision_id) in eligible]
        counts = [Counter(tokens(p.reference.quote)) for p in selected]
        query_tokens = set(tokens(query))
        frequency = {t: sum(t in c for c in counts) for t in query_tokens}
        scored = []
        for passage, count in zip(selected, counts):
            score = sum((1 + math.log(count[t])) * (1 + math.log((1 + len(counts)) / (1 + frequency[t])))
                        for t in query_tokens if count[t]) / math.sqrt(max(1, sum(count.values())))
            if score:
                scored.append(dict(**passage.export(), score=score))
        scored.sort(key=lambda r: (-r['score'], r['id']))
        return dict(query=query, at=at, mode=mode, hits=scored[:limit], excluded=excluded,
                    eligible_revisions=[dict(document_id=s.document_id, revision_id=s.revision_id,
                                             published_on=s.published_on, effective_on=s.effective_on) for s in sources])

    def compare(self, document_id, before, after, *, at):
        if before == after:
            raise ValueError('comparison requires two distinct revisions')
        sources, excluded = self.select(at, 'policy', [(document_id, before), (document_id, after)], 'published')
        if len(sources) != 2 or excluded:
            raise ValueError('both policy revisions must be registered and published by the comparison date')
        groups = [{p.clause_id: p for p in self.passages if p.reference.document_id == document_id
                   and p.reference.revision_id == rev} for rev in (before, after)]
        rows = []
        for clause_id in sorted(set(groups[0]) | set(groups[1])):
            old, new = (g.get(clause_id) for g in groups)
            if old and new and old.reference.quote == new.reference.quote:
                continue  # moving an unchanged labeled clause is not a text change
            rows.append(dict(clause_id=clause_id, change='added' if old is None else 'removed' if new is None else 'modified',
                             before=old.export() if old else None, after=new.export() if new else None,
                             diff='\n'.join(unified_diff(old.reference.quote.splitlines() if old else [],
                                  new.reference.quote.splitlines() if new else [], fromfile=before, tofile=after, lineterm=''))))
        return dict(document_id=document_id, before_revision=before, after_revision=after, at=at,
                    scope='published-version text comparison, NOT a semantic impact or applicability verdict',
                    revisions=[dict(revision_id=s.revision_id, effective_on=s.effective_on) for s in sources], changes=rows)


def load_index(path=DEFAULT_CORPUS):
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    if payload.get('schema_version') != 1 or not payload.get('provenance') or not payload.get('license'):
        raise ValueError('corpus manifest requires schema version, provenance and license')
    return Index(SourceRevision(**row) for row in payload['sources'])


def evaluate_development(index, path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if data['split'] != 'development' or not data['cases']:
        raise ValueError('this command accepts nonempty development retrieval cases only')
    rows = []
    for case in data['cases']:
        expected = set(case['expected'])
        if not expected.issubset(index.by_id):
            raise ValueError('unknown annotated passage')
        result = index.search(case['query'], at=case['at'], role=case['role'], limit=3)
        ids = [h['id'] for h in result['hits']]
        rows.append(dict(id=case['id'], expected=sorted(expected), retrieved=ids,
                         recall=len(expected.intersection(ids)) / len(expected) if expected else None,
                         empty_query_correct=not ids if not expected else None))
    recalls = [r['recall'] for r in rows if r['recall'] is not None]
    return dict(split='development', limit=3, rows=rows,
                mean_recall=sum(recalls) / len(recalls) if recalls else None,
                scope='authored lexical development cases; not held-out semantic accuracy or bank performance')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['search', 'compare', 'evaluate'])
    parser.add_argument('--corpus', default=str(DEFAULT_CORPUS))
    parser.add_argument('--at', default='2026-10-15')
    parser.add_argument('--query', default='high risk customer review months')
    parser.add_argument('--role', choices=['policy', 'procedure'])
    parser.add_argument('--output')
    args = parser.parse_args()
    index = load_index(args.corpus)
    if args.command == 'search':
        result = index.search(args.query, at=args.at, role=args.role)
    elif args.command == 'compare':
        result = index.compare('review-policy', 'v1', 'v2', at=args.at)
    else:
        cases = DEFAULT_CORPUS.with_name('development.json')
        result = evaluate_development(index, cases)
        result['sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                            [Path(args.corpus), cases, Path(__file__), Path(__file__).with_name('evidence.py')]}
    if args.output:
        path = Path(args.output)
        root = Path('artifacts').resolve()
        if path.exists() or path.resolve() == root or not path.resolve().is_relative_to(root):
            raise ValueError('choose a new file under artifacts/')
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write('\n')
    print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))


if __name__ == '__main__':
    main()
