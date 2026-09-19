"""Frozen final benchmark execution with preflight and per-row checkpoints."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from .agent import AGENT_SYSTEM, Budgets
from .cli import save_artifact, validate_output_path
from .evaluation import evaluate
from .investigation import SYSTEM
from .provider import GeminiProvider, strict_json
from .providers import PROVIDERS, make_provider
from .retrieval import load_index

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / 'fixtures/final-review'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                                    separators=(',', ':')).encode()).hexdigest()


def frozen_inputs():
    freeze = strict_json((FINAL / 'freeze.json').read_bytes())
    required = {'fixtures/final-review/corpus.json', 'fixtures/final-review/cases.json', 'docs/FINAL_SCORING.md'}
    if set(freeze['sha256']) != required:
        raise ValueError('unexpected freeze paths')
    for name, expected in freeze['sha256'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError('frozen input changed')
    manifest = strict_json((FINAL / 'cases.json').read_bytes())
    if manifest['split'] != 'final' or manifest['benchmark_id'] != freeze['benchmark_id']:
        raise ValueError('benchmark identity mismatch')
    return freeze, manifest, load_index(FINAL / 'corpus.json')


def preflight(model, modes):
    freeze, manifest, index = frozen_inputs()
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip():
        raise ValueError('commit implementation before final execution')
    return dict(schema_version=1, created_at=datetime.now(timezone.utc).isoformat(), git_revision=revision,
        benchmark_id=manifest['benchmark_id'], freeze=freeze,
        implementation_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT / 'policy_impact').glob('*.py'))},
        model=model, modes=list(modes), case_order=[c['id'] for c in manifest['cases']], repetitions=1,
        provider=dict(temperature=0, max_output_tokens=4096, timeout_seconds=30, automatic_retries=0),
        agent_budgets=asdict(Budgets()), prompt_sha256=dict(fixed=hashlib.sha256(SYSTEM.encode()).hexdigest(),
                                                       agent=hashlib.sha256(AGENT_SYSTEM.encode()).hexdigest()),
        corpus_fingerprints=sorted(s.fingerprint for s in index.sources))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, help='new final JSON under artifacts/')
    parser.add_argument('--baseline-only', action='store_true', help='offline evidence-only run, not a full comparison')
    parser.add_argument('--model')
    parser.add_argument('--provider', choices=list(PROVIDERS), default='gemini')
    parser.add_argument('--endpoint', default='')
    parser.add_argument('--allow-remote', action='store_true')
    args = parser.parse_args()
    output = validate_output_path(args.output)
    companion = output.with_name(output.stem + '-records')
    if companion.exists():
        raise ValueError('choose new output and checkpoint directory')
    modes = ('baseline',) if args.baseline_only else ('baseline', 'fixed', 'agent')
    if args.baseline_only and (args.model or args.allow_remote or args.endpoint or args.provider != 'gemini'):
        raise ValueError('baseline-only must not configure remote execution')
    provider = None if args.baseline_only else make_provider(provider=args.provider, endpoint=args.endpoint,
        api_key=os.environ.get(PROVIDERS[args.provider]['env'], ''), model=args.model, allow_remote=args.allow_remote)
    config = preflight(provider.model if provider else None, modes)
    config['provider_id'] = args.provider if provider else None
    config['request_endpoint'] = (args.endpoint or PROVIDERS[args.provider]['endpoint']) if provider else None
    if provider and args.provider != 'gemini':
        config['provider']['temperature'] = 'provider default (not sent)'
    _, manifest, index = frozen_inputs()
    save_artifact(companion / 'preflight.json', config)  # must succeed BEFORE any provider request
    completed = 0
    def checkpoint(row):
        nonlocal completed
        save_artifact(companion / f'row-{completed:03d}.json', row)
        completed += 1
        print(f'Completed {completed}/{len(manifest["cases"]) * len(modes)}: {row["case_id"]} {row["mode"]} {row["status"]}', flush=True)
    result = evaluate(index, manifest, modes, provider, on_row=checkpoint)
    result.update(benchmark_id=manifest['benchmark_id'], preflight=config, preflight_sha256=digest(config),
                  completed_at=datetime.now(timezone.utc).isoformat(), comparison_complete=not args.baseline_only)
    save_artifact(output, result)
    print(json.dumps(result['summaries'], indent=2))
    return 0 if all(row['operational_success'] for row in result['rows']) else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, TypeError, KeyError, OSError, subprocess.SubprocessError):
        print('Final evaluation stopped. Check frozen inputs, clean committed checkout, new output path and model consent/configuration. Existing checkpoints are retained.', file=sys.stderr)
        raise SystemExit(1)
