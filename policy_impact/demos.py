"""Saved, explicitly AI-authored examples; never fabricated provider-run records."""
from dataclasses import asdict
import hashlib
from pathlib import Path

from .agent import ToolRegistry
from .investigation import Task, prepare_fixed, validate_packet
from .provider import strict_json
from .retrieval import DEFAULT_CORPUS, load_index

DEMO_FILE = Path(__file__).resolve().parents[1] / 'fixtures/demos/reports.json'


def load_demos(index):
    raw = DEMO_FILE.read_bytes()
    manifest = strict_json(raw)
    if manifest['corpus_sha256'] != hashlib.sha256(DEFAULT_CORPUS.read_bytes()).hexdigest():
        raise ValueError('demo corpus changed; review saved examples before publishing')
    if sorted(s.fingerprint for s in index.sources) != sorted(s.fingerprint for s in load_index().sources):
        raise ValueError('saved examples require the exact authored demo corpus')
    results = {}
    for demo in manifest['demos']:
        if demo['id'] in results:
            raise ValueError('duplicate demo ID')
        task = Task(**demo['task'])
        context, evidence = prepare_fixed(index, task)
        tools = ToolRegistry(index, task)
        # Curated examples can name additional passages, but cannot bypass source/date permissions.
        for finding in demo['packet']['findings']:
            for evidence_id in finding['evidence_ids']:
                for passage in tools.call('read_passage', {'passage_id': evidence_id})['evidence']:
                    evidence[passage['id']] = passage
        context['evidence'] = list(evidence.values())
        results[demo['id']] = dict(mode='saved_demo', status='saved_example', model=None, provider=None,
            model_calls=0, tool_calls=0, usage=None, elapsed_seconds=None, trace=[], task=asdict(task),
            investigation=context, packet=validate_packet(demo['packet'], evidence, index, task),
            demo=dict(id=demo['id'], title=demo['title'], description=demo['description'],
                      scenario_id=demo['scenario_id'], next_steps=demo['next_steps'],
                      provenance=manifest['provenance'], reports_sha256=hashlib.sha256(raw).hexdigest()),
            notice='Saved AI-authored example on fictional sources. No live provider run or measured model performance. Evidence includes curated passages; not a retrieval benchmark.')
    return results
