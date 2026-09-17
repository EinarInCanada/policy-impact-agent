import json
import unittest
import urllib.error

from policy_impact.provider import GeminiProvider, ProviderError, _NoRedirect, strict_json


def response(output=None, finish='STOP'):
    return json.dumps({'candidates': [{'finishReason': finish, 'content': {'parts': [
        {'text': json.dumps(output or {'answer': 'test'})}]}}],
        'usageMetadata': {'promptTokenCount': 10, 'candidatesTokenCount': 4, 'totalTokenCount': 14}}).encode()


class ProviderTests(unittest.TestCase):
    def provider(self, transport, **kwargs):
        return GeminiProvider(api_key='fictional-test-key', model='gemini-test-model', allow_remote=True,
                              transport=transport, **kwargs)

    def test_remote_consent_and_model_validation(self):
        with self.assertRaises(ValueError):
            GeminiProvider(api_key='fictional-test-key', model='gemini-test-model')
        for model in ('https://other-host', '../secret', None):
            with self.assertRaises(ValueError):
                GeminiProvider(api_key='fictional-test-key', model=model, allow_remote=True)

    def test_request_and_usage_contract(self):
        seen = []
        def transport(url, headers, body, timeout):
            seen.append((url, headers, json.loads(body), timeout))
            return response()
        provider = self.provider(transport)
        reply = provider.generate(system='system', payload={'data': 'fictional'}, schema={'type': 'object'})
        url, headers, payload, timeout = seen[0]
        self.assertEqual(url, 'https://generativelanguage.googleapis.com/v1beta/models/gemini-test-model:generateContent')
        self.assertNotIn('fictional-test-key', url)
        self.assertNotIn('fictional-test-key', json.dumps(payload))
        self.assertEqual(headers['x-goog-api-key'], 'fictional-test-key')
        self.assertEqual(payload['generationConfig']['responseMimeType'], 'application/json')
        self.assertEqual(reply.usage['totalTokenCount'], 14)
        self.assertIsNone(reply.usage['thoughtsTokenCount'])
        self.assertNotIn('fictional-test-key', repr(provider))

    def test_no_retry_and_sanitized_error(self):
        calls = []
        def transport(*args):
            calls.append(1)
            raise RuntimeError('fictional-test-key private source contents')
        with self.assertRaises(ProviderError) as caught:
            self.provider(transport).generate(system='s', payload={}, schema={})
        self.assertNotIn('fictional-test-key', str(caught.exception))
        self.assertNotIn('private source', str(caught.exception))
        self.assertEqual(len(calls), 1)

    def test_http_failure_sanitized(self):
        def transport(*args):
            raise urllib.error.HTTPError('secret-url', 429, 'fictional-test-key', {}, None)
        with self.assertRaisesRegex(ProviderError, 'HTTP 429') as caught:
            self.provider(transport).generate(system='s', payload={}, schema={})
        self.assertNotIn('fictional-test-key', str(caught.exception))

    def test_truncated_blocked_and_malformed_outputs_rejected(self):
        for raw in (response(finish='MAX_TOKENS'), response(finish='SAFETY'), b'not-json',
                    b'{"candidates":[]}', response(output=['array-not-object'])):
            with self.subTest(raw=raw), self.assertRaises(ProviderError):
                self.provider(lambda *args: raw).generate(system='s', payload={}, schema={})

    def test_input_budget_checked_before_request(self):
        calls = []
        with self.assertRaises(ValueError):
            self.provider(lambda *args: calls.append(1)).generate(system='x' * 131073, payload={}, schema={})
        self.assertEqual(calls, [])

    def test_output_budget_and_nonfinite_json(self):
        with self.assertRaises(ProviderError):
            self.provider(lambda *args: b'x' * 1048577).generate(system='s', payload={}, schema={})
        for text in ('{"x":1,"x":2}', '{"x":NaN}'):
            with self.assertRaises(ValueError):
                strict_json(text)

    def test_redirect_handler_never_forwards_request(self):
        self.assertIsNone(_NoRedirect().redirect_request(None, None, 302, '', {}, 'https://other-host'))


if __name__ == '__main__':
    unittest.main()
