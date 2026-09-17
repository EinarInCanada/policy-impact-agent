"""Preview retrieved evidence offline, or explicitly opt into a Gemini draft."""
import argparse
import json
import os
from pathlib import Path
import sys

from .investigation import Task, prepare_fixed, run_fixed
from .agent import run_agent
from .provider import GeminiProvider, ProviderError
from .retrieval import DEFAULT_CORPUS, load_index


def validate_output_path(path):
    path = Path(path)
    root = Path('artifacts').resolve()
    if path.exists() or path.resolve() == root or not path.resolve().is_relative_to(root):
        raise ValueError('choose a new file under artifacts/')
    return path


def save_artifact(path, result):
    path = validate_output_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['preview', 'investigate'])
    parser.add_argument('--corpus', default=str(DEFAULT_CORPUS))
    parser.add_argument('--document', default='review-policy')
    parser.add_argument('--before', default='v1')
    parser.add_argument('--after', default='v2')
    parser.add_argument('--at', default='2026-10-15')
    parser.add_argument('--question', default='Investigate how high-risk customer review scheduling and ownership changed, including exceptions and affected procedures.')
    parser.add_argument('--intent', choices=['current_review', 'planning_review'], default='current_review')
    parser.add_argument('--model', help='explicit available Gemini model ID; no universal default or free-quota claim')
    parser.add_argument('--mode', choices=['fixed', 'agent'], default='fixed')
    parser.add_argument('--allow-remote', action='store_true', help='consent to send retrieved document excerpts to Google Gemini')
    parser.add_argument('--output', help='new JSON file under artifacts/')
    args = parser.parse_args()
    try:
        if args.output:
            validate_output_path(args.output)
        task = Task(args.document, args.before, args.after, args.at, args.question, args.intent)
        index = load_index(args.corpus)
        if args.command == 'preview':
            result = dict(mode='offline_preview', model_calls=0, investigation=prepare_fixed(index, task)[0],
                          notice='Retrieved evidence only; no generated findings, no model or agent evaluation.')
        else:
            provider = GeminiProvider(api_key=os.environ.get('GEMINI_API_KEY', ''), model=args.model,
                                      allow_remote=args.allow_remote)
            result = run_agent(index, task, provider) if args.mode == 'agent' else run_fixed(index, task, provider)
        if args.output:
            save_artifact(args.output, result)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 1 if result.get('mode') == 'bounded_agent' and result.get('status') != 'draft_ready' else 0
    except (ValueError, ProviderError, OSError, TypeError, KeyError):
        # Avoid leaking a key, confidential input, server body or arbitrary path through errors.
        print('Investigation failed. Check local input, output path, explicit remote consent, model ID and API-key configuration. '
              'No successful draft is being reported. Existing artifacts are not overwritten.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
