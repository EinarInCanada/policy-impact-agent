"""User-selected model protocols; no credential guessing or cross-provider fallback."""
import http.client
import ipaddress
import json
import re
import socket
import ssl
from urllib.parse import urlsplit

from .provider import GeminiProvider, ModelReply, ProviderError, _https_transport, strict_json

PROVIDERS = {
    'gemini': dict(label='Google Gemini', endpoint='https://generativelanguage.googleapis.com', env='GEMINI_API_KEY'),
    'openai': dict(label='OpenAI', endpoint='https://api.openai.com/v1/chat/completions', env='OPENAI_API_KEY'),
    'deepseek': dict(label='DeepSeek', endpoint='https://api.deepseek.com/chat/completions', env='DEEPSEEK_API_KEY'),
    'anthropic': dict(label='Anthropic Claude', endpoint='https://api.anthropic.com/v1/messages', env='ANTHROPIC_API_KEY'),
    'compatible': dict(label='Other OpenAI-compatible API', endpoint='', env='MODEL_API_KEY'),
}


def endpoint_url(value):
    if not isinstance(value, str) or not value.isascii() or len(value) > 2048 or any(c.isspace() for c in value):
        raise ValueError('invalid endpoint')
    url = urlsplit(value)
    if (url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment
            or url.port not in (None, 443) or not re.fullmatch(r'[A-Za-z0-9.-]+', url.hostname)
            or not url.path.endswith('/chat/completions')):
        raise ValueError('use an HTTPS chat/completions endpoint without credentials or query parameters')
    if url.hostname.lower() == 'localhost' or url.hostname.lower().endswith(('.localhost', '.local')):
        raise ValueError('local endpoints are not supported')
    try:
        address = ipaddress.ip_address(url.hostname)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError('private endpoints are not supported')
    return value


def public_https_transport(url, headers, body, timeout):
    """Resolve once, reject non-public addresses, pin connection IP with TLS hostname validation."""
    target = urlsplit(endpoint_url(url))
    addresses = socket.getaddrinfo(target.hostname, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ProviderError('endpoint must resolve only to public addresses')
    address = addresses[0][4][0]
    class PinnedHTTPS(http.client.HTTPSConnection):
        def connect(self):
            raw = socket.create_connection((address, 443), timeout=self.timeout)
            try:
                self.sock = self._context.wrap_socket(raw, server_hostname=target.hostname)
            except Exception:
                raw.close()
                raise
    connection = PinnedHTTPS(target.hostname, timeout=timeout, context=ssl.create_default_context())
    try:
        connection.request('POST', target.path, body=body, headers=headers)
        response = connection.getresponse()
        if response.status != 200:
            raise ProviderError(f'Provider HTTP {response.status}; no redirect or retry performed')
        return response.read(1_048_577)
    finally:
        connection.close()


class JSONProvider:
    def __init__(self, *, provider, api_key, model, endpoint='', allow_remote=False, transport=None):
        if allow_remote is not True:
            raise ValueError('explicit remote consent required')
        if not isinstance(api_key, str) or not 1 <= len(api_key) <= 4096 or any(ord(c) < 33 or ord(c) > 126 for c in api_key):
            raise ValueError('invalid API key')
        if not isinstance(model, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}', model):
            raise ValueError('invalid model ID')
        if provider not in PROVIDERS or provider == 'gemini':
            raise ValueError('unsupported provider')
        if provider != 'compatible' and endpoint:
            raise ValueError('preset endpoints cannot be overridden')
        self.provider, self.model, self._api_key = provider, model, api_key
        self.endpoint = endpoint_url(endpoint) if provider == 'compatible' else PROVIDERS[provider]['endpoint']
        self.timeout, self.max_output_tokens = 30, 4096
        self._transport = transport or (public_https_transport if provider == 'compatible' else _https_transport)

    def __repr__(self):
        return f'JSONProvider(provider={self.provider!r}, model={self.model!r}, api_key=<redacted>)'

    def generate(self, *, system, payload, schema):
        instruction = system + '\nReturn ONLY one JSON object matching this schema, without Markdown fences:\n' + json.dumps(schema)
        user = json.dumps(payload, ensure_ascii=False, allow_nan=False)
        headers = {'Content-Type': 'application/json'}
        if self.provider == 'anthropic':
            headers.update({'x-api-key': self._api_key, 'anthropic-version': '2023-06-01'})
            request = dict(model=self.model, max_tokens=self.max_output_tokens, system=instruction,
                           messages=[dict(role='user', content=user)])
        else:
            headers['Authorization'] = 'Bearer ' + self._api_key
            request = dict(model=self.model, messages=[dict(role='system', content=instruction), dict(role='user', content=user)],
                           response_format={'type': 'json_object'}, stream=False)
            request['max_completion_tokens' if self.provider == 'openai' else 'max_tokens'] = self.max_output_tokens
        body = json.dumps(request, ensure_ascii=False, allow_nan=False).encode()
        if len(body) > 131072:
            raise ValueError('request exceeded 128 KiB input budget')
        try:
            raw = self._transport(self.endpoint, headers, body, self.timeout)
            if len(raw) > 1048576:
                raise ProviderError('provider response exceeded byte limit')
            data = strict_json(raw)
            if self.provider == 'anthropic':
                if data.get('stop_reason') != 'end_turn' or any(b.get('type') != 'text' for b in data['content']):
                    raise ProviderError('incomplete or non-text provider response')
                answer = ''.join(b['text'] for b in data['content'])
                usage = {k: data.get('usage', {}).get(v) for k, v in [('promptTokenCount','input_tokens'),('candidatesTokenCount','output_tokens')]}
                usage['totalTokenCount'] = None  # cache-accounting semantics differ; do not invent a total
            else:
                choices = data['choices']
                if len(choices) != 1 or choices[0].get('finish_reason') != 'stop' or choices[0]['message'].get('refusal') or choices[0]['message'].get('tool_calls'):
                    raise ProviderError('incomplete, refused or non-text provider response')
                answer = choices[0]['message']['content']
                usage = {k: data.get('usage', {}).get(v) for k, v in [('promptTokenCount','prompt_tokens'),('candidatesTokenCount','completion_tokens'),('totalTokenCount','total_tokens')]}
            if any(v is not None and (type(v) is not int or v < 0) for v in usage.values()):
                raise ProviderError('invalid usage')
            output = strict_json(answer)
            if not isinstance(output, dict):
                raise ProviderError('JSON object required')
            return ModelReply(output, usage)
        except ProviderError:
            raise
        except Exception:
            raise ProviderError('Provider transport or response validation failed; check configuration and quota. No retry performed.') from None


def make_provider(*, provider='gemini', endpoint='', **kwargs):
    if provider == 'gemini':
        if endpoint:
            raise ValueError('Gemini endpoint cannot be overridden')
        return GeminiProvider(**kwargs)
    return JSONProvider(provider=provider, endpoint=endpoint, **kwargs)


def provider_options():
    return [dict(id=k, label=v['label'], endpoint=v['endpoint']) for k, v in PROVIDERS.items()]
