from dataclasses import asdict
import http.client
import json
import threading
import unittest

from policy_impact.web import ReviewServer
from test_investigation import StubProvider, task


class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.configurations = []
        def factory(**kwargs):
            cls.configurations.append(kwargs)
            if kwargs['allow_remote'] is not True:
                raise ValueError('consent missing')
            return StubProvider()
        cls.server = ReviewServer(0, provider_factory=factory)
        cls.worker = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.worker.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.worker.join()

    def request(self, method='GET', path='/', data=None, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        connection.request(method, path, body=json.dumps(data) if data is not None else None, headers=headers or {})
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result

    def post(self, **changes):
        data = dict(task=asdict(task()), mode='preview', model=None, api_key='', allow_remote=False)
        data.update(changes)
        return self.request('POST', '/api/run', data, {'Origin': self.server.origin,
            'Content-Type': 'application/json', 'X-Review-Token': self.server.csrf_token})

    def test_assets_config_and_no_directory_serving(self):
        for path in ('/', '/app.js', '/style.css', '/api/config'):
            status, headers, body = self.request(path=path)
            self.assertEqual(status, 200)
            self.assertEqual(headers['Cache-Control'], 'no-store')
            self.assertIn("frame-ancestors 'none'", headers['Content-Security-Policy'])
            self.assertTrue(body)
        for path in ('/../AGENTS.md', '/.env', '/api/config?x=1'):
            self.assertEqual(self.request(path=path)[0], 404)

    def test_host_and_origin_guards(self):
        self.assertEqual(self.request(headers={'Host': 'attacker.example'})[0], 403)
        for headers in ({}, {'Origin': 'https://attacker.example'}, {'Origin': self.server.origin, 'X-Review-Token': 'wrong'}):
            self.assertEqual(self.request('POST', '/api/run', {}, headers)[0], 403)

    def test_preview_does_not_construct_provider(self):
        before = len(self.configurations)
        status, _, body = self.post()
        self.assertEqual(status, 200)
        result = json.loads(body)
        self.assertEqual(result['mode'], 'offline_preview')
        self.assertEqual(result['model_calls'], 0)
        self.assertIsNone(result['packet'])
        self.assertEqual(len(self.configurations), before)
        self.assertEqual(self.post(api_key='must-not-send')[0], 400)

    def test_fixed_result_does_not_export_key(self):
        status, _, body = self.post(mode='fixed', model='gemini-test', api_key='offline-test-secret', allow_remote=True)
        self.assertEqual(status, 200)
        self.assertNotIn(b'offline-test-secret', body)
        self.assertEqual(json.loads(body)['model_calls'], 1)

    def test_provider_selection_reaches_factory(self):
        status, _, body = self.post(mode='fixed', provider='deepseek', model='test', api_key='offline-key', allow_remote=True)
        self.assertEqual(status, 200)
        self.assertEqual(self.configurations[-1]['provider'], 'deepseek')
        self.assertEqual(json.loads(body)['provider'], 'deepseek')
        _, _, config = self.request(path='/api/config')
        self.assertEqual(len(json.loads(config)['providers']), 5)

    def test_scope_dates_and_extra_fields_rejected(self):
        invalid = asdict(task(at='2026-09-15'))
        self.assertEqual(self.post(task=invalid)[0], 400)
        invalid = asdict(task()); invalid['document_id'] = 'other'
        self.assertEqual(self.post(task=invalid)[0], 400)
        self.assertEqual(self.post(command='shell')[0], 400)
        self.assertEqual(self.post(mode='fixed', api_key='offline-test-secret')[0], 400)

    def test_single_live_run_lock(self):
        self.server.run_lock.acquire()
        try:
            self.assertEqual(self.post(mode='fixed', api_key='test', allow_remote=True)[0], 409)
            self.assertEqual(self.post()[0], 200)
        finally:
            self.server.run_lock.release()


if __name__ == '__main__':
    unittest.main()
