"""Comparable development runs; operational success is not answer correctness."""
import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys
import time

from .agent import Budgets, run_agent
from .cli import save_artifact, validate_output_path
from .investigation import Task, prepare_fixed, run_fixed
from .provider import GeminiProvider, strict_json
from .providers import PROVIDERS, make_provider
from .retrieval import DEFAULT_CORPUS, load_index

DEFAULT_CASES = DEFAULT_CORPUS.parent / 'investigations-development.json'


class MeteredProvider:
    """Keep attempted calls and available usage even when packet validation fails."""
    def __init__(self, provider):
        self.provider = provider
        self.model = provider.model
        self.calls = 0
        self.usage = []

    def generate(self, **kwargs):
        self.calls += 1
        reply = self.provider.generate(**kwargs)
        self.usage.append(reply.usage)
        return reply


def load_cases(path, index):
    manifest = strict_json(Path(path).read_text(encoding='utf-8'))
    if manifest.get('split') != 'development' or not manifest.get('cases'):
        raise ValueError('this runner currently accepts development cases only')
    seen = set()
    for case in manifest['cases']:
        if not isinstance(case['id'], str) or not case['id'] or case['id'] in seen:
            raise ValueError('case IDs must be nonempty and unique')
        seen.add(case['id'])
        task = Task(**case['task'])
        prepare_fixed(index, task)  # reject invalid tasks before any remote request
        expected = case['expected_evidence']
        if not isinstance(expected, list) or len(set(expected)) != len(expected):
            raise ValueError('expected evidence must be a unique list')
        if not all(e in index.by_id for e in expected):
            raise ValueError('unknown reference in annotation')
    return manifest


def evaluate(index, manifest, modes=('baseline',), provider=None, on_row=None):
    if not modes or len(set(modes)) != len(modes) or set(modes) - {'baseline', 'fixed', 'agent'}:
        raise ValueError('choose unique supported modes')
    if set(modes) - {'baseline'} and provider is None:
        raise ValueError('model modes require an explicitly configured provider')
    rows = []
    for case in manifest['cases']:
        task = Task(**case['task'])
        expected = set(case['expected_evidence'])
        for mode in modes:
            started = time.perf_counter()
            meter = MeteredProvider(provider) if mode != 'baseline' else None
            row = dict(case_id=case['id'], mode=mode, expected_evidence=sorted(expected),
                       status='failed', result=None, observed_evidence=[], error_type=None)
            try:
                if mode == 'baseline':
                    context, evidence = prepare_fixed(index, task)
                    result = dict(investigation=context, packet=None)
                    row['status'] = 'evidence_ready'
                elif mode == 'fixed':
                    result = run_fixed(index, task, meter)
                    evidence = {e['id']: e for e in result['investigation']['evidence']}
                    row['status'] = 'draft_ready'
                else:
                    result = run_agent(index, task, meter)
                    evidence = {e['id']: e for e in result['discovered_evidence']}
                    row['status'] = result['status']
                row.update(result=result, observed_evidence=sorted(evidence))
            except Exception as exc:
                # Preserve one failed row, never a raw provider/input exception message.
                # KeyboardInterrupt/SystemExit still abort rather than silently spending more.
                row['error_type'] = type(exc).__name__
            success = row['status'] in ('evidence_ready', 'draft_ready')
            row.update(elapsed_seconds=time.perf_counter() - started,
                       attempted_model_calls=meter.calls if meter else 0,
                       usage_per_completed_call=meter.usage if meter else [],
                       operational_success=success,
                       required_evidence_recall=(len(expected & set(row['observed_evidence'])) / len(expected)
                                                 if expected and success else 0.0 if expected else None),
                       semantic_review='pending' if mode != 'baseline' else 'not_applicable')
            rows.append(row)
            if on_row is not None:
                on_row(row)  # checkpoint failure aborts; do not silently spend more quota
    summaries = {}
    for mode in modes:
        selected = [r for r in rows if r['mode'] == mode]
        recall = [r['required_evidence_recall'] for r in selected if r['required_evidence_recall'] is not None]
        summaries[mode] = dict(total_cases=len(selected), successful_runs=sum(r['operational_success'] for r in selected),
                               mean_required_evidence_recall=sum(recall) / len(recall) if recall else None,
                               recall_denominator=len(recall), attempted_model_calls=sum(r['attempted_model_calls'] for r in selected))
    return dict(schema_version=1, split=manifest['split'], rows=rows, summaries=summaries,
                model=provider.model if provider else None, agent_budgets=asdict(Budgets()),
                corpus_fingerprints=sorted(s.fingerprint for s in index.sources),
                limitations=['Authored synthetic cases; not independent bank data or a population estimate.',
                             'Operational success and reference recall do not establish semantic correctness.',
                             'Failed runs remain in denominators; missing usage is unknown, not zero.',
                             'Sequential single runs; ordering and warm-up effects are not controlled.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', default=str(DEFAULT_CASES))
    parser.add_argument('--corpus', default=str(DEFAULT_CORPUS))
    parser.add_argument('--modes', nargs='+', choices=['baseline', 'fixed', 'agent'], default=['baseline'])
    parser.add_argument('--model')
    parser.add_argument('--provider', choices=list(PROVIDERS), default='gemini')
    parser.add_argument('--endpoint', default='')
    parser.add_argument('--allow-remote', action='store_true')
    parser.add_argument('--output', required=True, help='new file under artifacts/')
    args = parser.parse_args()
    validate_output_path(args.output)
    index = load_index(args.corpus)
    manifest = load_cases(args.cases, index)
    provider = None
    if set(args.modes) - {'baseline'}:
        provider = make_provider(provider=args.provider, endpoint=args.endpoint,
                                 api_key=os.environ.get(PROVIDERS[args.provider]['env'], ''), model=args.model, allow_remote=args.allow_remote)
    result = evaluate(index, manifest, tuple(args.modes), provider)
    result['provider'] = args.provider if provider else None
    source_paths = [Path(args.cases), Path(args.corpus), *sorted(Path(__file__).parent.glob('*.py'))]
    result['input_sha256'] = [dict(name=p.name, sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in source_paths]
    save_artifact(args.output, result)
    print(json.dumps(result['summaries'], indent=2))
    return 0 if all(r['operational_success'] for r in result['rows']) else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError):
        print('Evaluation setup failed. Check cases, corpus, new artifact path and explicit model consent/configuration.', file=sys.stderr)
        raise SystemExit(1)
