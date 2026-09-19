"""Loopback-only review workspace. Not a production or multi-user web service."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import threading

from .agent import run_agent
from .evaluation import DEFAULT_CASES, load_cases
from .investigation import Task, prepare_fixed, run_fixed
from .provider import GeminiProvider, ProviderError, strict_json
from .providers import make_provider, provider_options
from .retrieval import DEFAULT_CORPUS, load_index

STATIC = Path(__file__).parent / 'static'
ASSETS = {'/': ('index.html', 'text/html; charset=utf-8'),
          '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
          '/style.css': ('style.css', 'text/css; charset=utf-8')}


class ReviewServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port=8766, index=None, provider_factory=make_provider):
        self.index = index or load_index()
        self.cases = load_cases(DEFAULT_CASES, self.index)['cases']
        self.provider_factory = provider_factory
        self.csrf_token = secrets.token_urlsafe(32)
        self.run_lock = threading.Lock()
        super().__init__(('127.0.0.1', port), ReviewHandler)
        self.origin = f'http://127.0.0.1:{self.server_port}'


class ReviewHandler(BaseHTTPRequestHandler):
    server_version = 'PolicyImpactLocal'

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, *_):
        pass  # no request paths, bodies, credentials or raw exceptions in access logs

    def send_body(self, status, body, mime='application/json; charset=utf-8'):
        raw = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False, allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(raw)

    def trusted_host(self):
        return self.headers.get_all('Host') == [self.server.origin.removeprefix('http://')]

    def do_GET(self):
        if not self.trusted_host():
            return self.send_body(403, {'error': 'Use the printed loopback URL.'})
        if self.path in ASSETS:
            filename, mime = ASSETS[self.path]
            return self.send_body(200, (STATIC / filename).read_bytes(), mime)
        if self.path == '/api/config':
            return self.send_body(200, dict(csrf_token=self.server.csrf_token, providers=provider_options(),
                cases=[dict(id=c['id'], task=c['task']) for c in self.server.cases],
                sources=[dict(document_id=s.document_id, revision_id=s.revision_id, role=s.role,
                              published_on=s.published_on, effective_on=s.effective_on,
                              fingerprint=s.fingerprint, provenance=s.provenance) for s in self.server.index.sources]))
        return self.send_body(404, {'error': 'Not found.'})

    def do_POST(self):
        if (not self.trusted_host() or self.headers.get_all('Origin') != [self.server.origin]
                or len(self.headers.get_all('X-Review-Token', [])) != 1
                or not secrets.compare_digest(self.headers.get('X-Review-Token', '').encode('utf-8'), self.server.csrf_token.encode('utf-8'))):
            return self.send_body(403, {'error': 'Request origin or session check failed. Reload the local page.'})
        if self.path != '/api/run':
            return self.send_body(404, {'error': 'Not found.'})
        if (self.headers.get('Content-Type') != 'application/json'
                or len(self.headers.get_all('Content-Length', [])) != 1 or self.headers.get('Transfer-Encoding')):
            return self.send_body(400, {'error': 'A length-bounded JSON request is required.'})
        try:
            length = int(self.headers['Content-Length'])
            if not 0 < length <= 16384:
                raise ValueError('body limit')
            payload = strict_json(self.rfile.read(length))
            required = {'task', 'mode', 'model', 'api_key', 'allow_remote'}
            if not isinstance(payload, dict) or not required.issubset(payload) or set(payload) - required - {'provider', 'endpoint'}:
                raise ValueError('fields')
            task = Task(**payload['task'])
            if (task.document_id, task.before, task.after) != ('review-policy', 'v1', 'v2'):
                raise ValueError('demo scope')
            mode = payload['mode']
            if mode not in ('preview', 'fixed', 'agent'):
                raise ValueError('mode')
            context, _ = prepare_fixed(self.server.index, task)
            if mode == 'preview':
                if payload['api_key'] or payload['allow_remote'] is not False:
                    raise ValueError('preview must not contain credentials or consent')
                return self.send_body(200, dict(mode='offline_preview', status='evidence_ready', model_calls=0,
                    investigation=context, packet=None, notice='Offline evidence preview. No model call or generated findings.'))
            if not self.server.run_lock.acquire(blocking=False):
                return self.send_body(409, {'error': 'Another model run is active. Wait for it to finish.'})
            try:
                provider = self.server.provider_factory(api_key=payload.pop('api_key'), model=payload['model'],
                                                         provider=payload.get('provider', 'gemini'), endpoint=payload.get('endpoint', ''),
                                                         allow_remote=payload['allow_remote'])
                result = run_agent(self.server.index, task, provider) if mode == 'agent' else run_fixed(self.server.index, task, provider)
                result['provider'] = payload.get('provider', 'gemini')
                return self.send_body(200, result)
            finally:
                self.server.run_lock.release()
        except ProviderError:
            return self.send_body(502, {'error': 'Model request failed. Check model availability, key and quota. No automatic retry was made.'})
        except (ValueError, TypeError, KeyError, UnicodeError):
            return self.send_body(400, {'error': 'Invalid input or rejected draft. Check date, intent, explicit consent and model configuration. No successful draft is reported.'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8766)
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error('port must be 0–65535')
    with ReviewServer(args.port) as server:
        print(f'Review workspace: {server.origin}', flush=True)
        print('Fictional data. Loopback only. Keys are request-scoped; selected-provider calls require explicit consent.', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
