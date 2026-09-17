"""Opt-in Gemini REST transport. Offline test doubles are not model evaluations."""
from dataclasses import dataclass
import json
import re
import urllib.error
import urllib.request


class ProviderError(RuntimeError):
    """Sanitized provider failure; never includes request headers or raw response bodies."""


def strict_json(text):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError('duplicate JSON field')
            result[key] = value
        return result

    def invalid_constant(_):
        raise ValueError('nonfinite JSON constant')

    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid_constant)


@dataclass(frozen=True)
class ModelReply:
    output: dict
    usage: dict


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _https_transport(url, headers, body, timeout):
    request = urllib.request.Request(url, data=body, headers=headers, method='POST')
    # Never forward the API-key header to a redirected host; ignore ambient proxy configuration.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    with opener.open(request, timeout=timeout) as response:
        raw = response.read(1_048_577)
        if len(raw) > 1_048_576:
            raise ProviderError('provider response exceeded byte limit')
        return raw


class GeminiProvider:
    def __init__(self, *, api_key, model, allow_remote=False, timeout=30, max_output_tokens=4096, transport=None):
        if allow_remote is not True:
            raise ValueError('explicit consent required before document excerpts leave this machine')
        if not isinstance(api_key, str) or not api_key.strip() or any(c.isspace() for c in api_key):
            raise ValueError('configure a nonempty API key without whitespace')
        if not isinstance(model, str) or not re.fullmatch(r'gemini-[A-Za-z0-9._-]{1,100}', model):
            raise ValueError('choose an explicit Gemini model ID, not a URL or path')
        if type(timeout) not in (int, float) or not 0 < timeout <= 60:
            raise ValueError('timeout must be in (0, 60] seconds')
        if type(max_output_tokens) is not int or not 1 <= max_output_tokens <= 8192:
            raise ValueError('output budget must be in 1–8192 tokens')
        self._api_key, self.model = api_key, model
        self.timeout, self.max_output_tokens = timeout, max_output_tokens
        self._transport = transport or _https_transport

    def __repr__(self):
        return f'GeminiProvider(model={self.model!r}, api_key=<redacted>)'

    def generate(self, *, system, payload, schema):
        request = dict(systemInstruction={'parts': [{'text': system}]},
            contents=[{'role': 'user', 'parts': [{'text': json.dumps(payload, ensure_ascii=False, allow_nan=False)}]}],
            generationConfig={'temperature': 0, 'maxOutputTokens': self.max_output_tokens,
                              'responseMimeType': 'application/json', 'responseJsonSchema': schema})
        body = json.dumps(request, ensure_ascii=False, allow_nan=False).encode('utf-8')
        if len(body) > 131072:
            raise ValueError('request exceeded 128 KiB input budget')
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent'
        try:
            raw = self._transport(url, {'Content-Type': 'application/json', 'x-goog-api-key': self._api_key}, body, self.timeout)
            if len(raw) > 1_048_576:
                raise ProviderError('provider response exceeded byte limit')
            response = strict_json(raw)
            candidates = response.get('candidates', [])
            if len(candidates) != 1 or candidates[0].get('finishReason') != 'STOP':
                raise ProviderError('provider did not return one complete, unblocked candidate')
            parts = candidates[0]['content']['parts']
            text_parts = [p['text'] for p in parts if 'text' in p and not p.get('thought', False)]
            if not text_parts:
                raise ProviderError('provider returned no answer text')
            output = strict_json(''.join(text_parts))
            if not isinstance(output, dict):
                raise ProviderError('provider output must be a JSON object')
            usage = {}
            for key in ('promptTokenCount', 'candidatesTokenCount', 'totalTokenCount', 'thoughtsTokenCount'):
                value = response.get('usageMetadata', {}).get(key)
                if value is not None and (type(value) is not int or value < 0):
                    raise ProviderError('invalid provider usage metadata')
                usage[key] = value
            return ModelReply(output, usage)
        except urllib.error.HTTPError as error:
            # Never include an HTTP response body, headers, exception string or key in output.
            raise ProviderError(f'Gemini HTTP {error.code}; check model, credentials, quota and service status') from None
        except ProviderError:
            raise
        except Exception:
            raise ProviderError('Gemini transport or response validation failed; no automatic retry performed') from None
