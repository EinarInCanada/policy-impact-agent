import json
from unittest.mock import patch, MagicMock
import unittest

from policy_impact.provider import GeminiProvider, ProviderError
from policy_impact.providers import JSONProvider, endpoint_url, make_provider, public_https_transport
from policy_impact.agent import run_agent
from policy_impact.investigation import run_fixed
from policy_impact.retrieval import load_index
from test_investigation import packet, task


def response(provider='openai', finish=None):
    if provider == 'anthropic':
        data = dict(stop_reason=finish or 'end_turn', content=[dict(type='text', text='{"ok":true}')], usage=dict(input_tokens=8, output_tokens=4))
    else:
        data = dict(choices=[dict(finish_reason=finish or 'stop', message=dict(content='{"ok":true}'))], usage=dict(prompt_tokens=8, completion_tokens=4, total_tokens=12))
    return json.dumps(data).encode()


class MultiProviderTests(unittest.TestCase):
    def test_each_protocol_routes_and_authenticates(self):
        for provider in ('openai', 'deepseek', 'anthropic', 'compatible'):
            calls = []
            def transport(url, headers, body, timeout):
                calls.append((url, headers, json.loads(body)))
                return response(provider)
            p = make_provider(provider=provider, api_key='fake-key', model='vendor/model-id', allow_remote=True,
                              endpoint='https://example.com/v1/chat/completions' if provider == 'compatible' else '', transport=transport)
            reply = p.generate(system='s', payload={'test':1}, schema={'type':'object'})
            self.assertEqual(reply.output, {'ok':True})
            url, headers, body = calls[0]
            self.assertNotIn('fake-key', url + json.dumps(body) + repr(p))
            if provider == 'anthropic':
                self.assertEqual(headers['x-api-key'], 'fake-key')
                self.assertEqual(headers['anthropic-version'], '2023-06-01')
                self.assertIsNone(reply.usage['totalTokenCount'])
            else:
                self.assertEqual(headers['Authorization'], 'Bearer fake-key')
                self.assertEqual(body['response_format']['type'], 'json_object')
                self.assertEqual(reply.usage['totalTokenCount'], 12)
            self.assertEqual(body.get('max_completion_tokens', body.get('max_tokens')), 4096)

    def test_factory_validation_and_gemini_compatibility(self):
        self.assertIsInstance(make_provider(api_key='fake', model='gemini-test', allow_remote=True), GeminiProvider)
        for changes in ({'allow_remote':False},{'provider':'unknown'},{'api_key':'key\nheader'}, {'model':'bad model'}, {'endpoint':'https://evil.example/chat/completions'}):
            args = dict(provider='openai', api_key='fake', model='test', allow_remote=True)
            args.update(changes)
            with self.assertRaises(ValueError): make_provider(**args)

    def test_custom_endpoint_restrictions(self):
        for url in ('http://example.com/v1/chat/completions','https://127.0.0.1/chat/completions',
                    'https://localhost/chat/completions','https://10.0.0.1/chat/completions',
                    'https://example.com:8443/chat/completions','https://user:key@example.com/chat/completions',
                    'https://example.com/chat/completions?key=secret','https://example.com/other'):
            with self.subTest(url=url), self.assertRaises(ValueError): endpoint_url(url)

    def test_custom_dns_private_and_mixed_answers_rejected_before_connection(self):
        for ips in (['127.0.0.1'], ['1.1.1.1', '10.0.0.1'], ['169.254.169.254']):
            answers = [(2,1,6,'',(ip,443)) for ip in ips]
            with patch('policy_impact.providers.socket.getaddrinfo',return_value=answers), patch('policy_impact.providers.socket.create_connection') as connect:
                with self.assertRaises(ProviderError):
                    public_https_transport('https://example.com/chat/completions', {}, b'{}', 30)
                connect.assert_not_called()

    def test_errors_incomplete_and_budget_never_retry(self):
        for provider in ('openai','anthropic'):
            for raw in (response(provider,finish='length'), b'not-json', b'x'*1048577):
                calls = []
                def transport(*args): calls.append(1); return raw
                p=JSONProvider(provider=provider, api_key='fake',model='test',allow_remote=True,transport=transport)
                with self.assertRaises(ProviderError): p.generate(system='s',payload={},schema={})
                self.assertEqual(len(calls),1)
        def bad_transport(*args): raise RuntimeError('SECRET-KEY')
        p=JSONProvider(provider='openai',api_key='SECRET-KEY',model='test',allow_remote=True,transport=bad_transport)
        with self.assertRaises(ProviderError) as caught: p.generate(system='s',payload={},schema={})
        self.assertNotIn('SECRET-KEY',str(caught.exception))
        with self.assertRaises(ValueError): p.generate(system='x'*131073,payload={},schema={})

    def test_custom_transport_pins_ip_and_keeps_tls_hostname(self):
        tls = MagicMock()
        response_mock = MagicMock(status=200)
        response_mock.read.return_value = b'{}'
        with patch('policy_impact.providers.socket.getaddrinfo',return_value=[(2,1,6,'',('1.1.1.1',443))]) as dns, \
             patch('policy_impact.providers.socket.create_connection') as connect, \
             patch('policy_impact.providers.ssl.create_default_context',return_value=tls), \
             patch('http.client.HTTPConnection.request',lambda self,*a,**k:self.connect()), \
             patch('http.client.HTTPConnection.getresponse',return_value=response_mock):
            self.assertEqual(public_https_transport('https://example.com/chat/completions',{},b'{}',30),b'{}')
            dns.assert_called_once()
            connect.assert_called_once_with(('1.1.1.1',443),timeout=30)
            tls.wrap_socket.assert_called_once_with(connect.return_value,server_hostname='example.com')

    def test_fixed_and_agent_share_new_adapters(self):
        index = load_index()
        for provider in ('openai','deepseek','anthropic','compatible'):
            for agent in (False, True):
                output = dict(action='finish',tool=None,packet=packet()) if agent else packet()
                raw = json.loads(response(provider))
                if provider == 'anthropic': raw['content'][0]['text'] = json.dumps(output)
                else: raw['choices'][0]['message']['content'] = json.dumps(output)
                p=make_provider(provider=provider,api_key='fake',model='test',allow_remote=True,
                    endpoint='https://example.com/chat/completions' if provider=='compatible' else '',
                    transport=lambda *args:json.dumps(raw).encode())
                result = run_agent(index,task(),p) if agent else run_fixed(index,task(),p)
                self.assertEqual(result['model_calls'],1)
                self.assertTrue(result['packet']['findings'])
