# Bring your own provider

Select a provider in the expanded **Connect your AI provider** panel, enter its model ID and your own API key, then explicitly consent. Keys are not interchangeable and a consumer chat subscription is not an API credential.

| Selection | Protocol / endpoint | CLI environment variable |
|---|---|---|
| Google Gemini | Gemini generateContent | `GEMINI_API_KEY` |
| OpenAI | `https://api.openai.com/v1/chat/completions` | `OPENAI_API_KEY` |
| DeepSeek | `https://api.deepseek.com/chat/completions` | `DEEPSEEK_API_KEY` |
| Anthropic Claude | `https://api.anthropic.com/v1/messages` | `ANTHROPIC_API_KEY` |
| Other OpenAI-compatible API | User-supplied full public HTTPS completion URL | `MODEL_API_KEY` |

Compatible services must accept Bearer authentication, system/user messages, JSON object output mode, `max_tokens` and a standard non-streaming Chat Completions response. Region-specific endpoints and model IDs must match your account. Check your service's documentation: accepting an API key alone does not imply compatibility.

## Key and endpoint controls

Changing provider clears model, endpoint, key and consent. Changing a custom endpoint clears key and consent. Submission clears the key field; offline preview never sends the entered key. Keys are not persisted in browser storage or application exports. Transient process memory and a compromised local machine remain outside this guarantee.

Custom URLs must end in `/chat/completions`, use HTTPS port 443, and contain no URL credentials, query string or fragment. Loopback, private and link-local IPs, local hostnames and non-public DNS answers are rejected. The connection pins the checked IP while TLS verifies the original hostname, avoiding a second DNS lookup. No proxy, redirect, automatic retry or cross-provider fallback is used. A public service can still be untrustworthy: choose the destination carefully because it receives your key and excerpts.

## CLI and evaluation

Investigation, development evaluation and final evaluation accept `--provider` (`gemini`, `openai`, `deepseek`, `anthropic`, `compatible`) and optional `--endpoint`. Gemini remains the default. Configure the matching environment variable; never supply the key as a command argument.

```sh
read -rs 'DEEPSEEK_API_KEY?Your DeepSeek API key (hidden): '
export DEEPSEEK_API_KEY
python3 -m policy_impact.cli investigate --provider deepseek --model YOUR_AVAILABLE_MODEL_ID --allow-remote --output artifacts/deepseek-01.json
unset DEEPSEEK_API_KEY
```

For a compatible service use `MODEL_API_KEY`, `--provider compatible` and `--endpoint https://YOUR_PUBLIC_HOST/v1/chat/completions`. Final preflight records the provider and endpoint. Compare fixed RAG and agent using the same provider/model. Non-Gemini adapters omit temperature and record provider-default temperature, not Gemini's temperature-zero configuration.

## Protocol boundaries

Gemini retains native JSON-schema output. OpenAI-compatible adapters request JSON object mode with the full schema in the system instruction. Claude requests JSON-only text with that schema. Every path still applies the same application-side output/evidence validation and agent permissions. Refusals, incomplete responses, invalid JSON and native tool calls fail; no silent repair/retry occurs.

OpenAI uses `max_completion_tokens`; other compatible services and Claude use `max_tokens`. All default to 4,096 output tokens with the existing timeout/byte budgets. Models lacking these parameters or JSON output may fail. Claude total token usage stays null because cache accounting differs; absent usage is not zero.

Not supported: Responses-only APIs, Azure deployment authentication, AWS Bedrock request signing, OAuth-only services, local Ollama HTTP, arbitrary non-chat APIs or Claude keys requiring an additional workspace header. Use an appropriately scoped Claude key. This is multi-provider protocol support, **not a promise that every API key/model works**.

Real-key compatibility and model quality remain unverified under the owner's live-test deferral. Mock tests verify request routing, header placement, JSON parsing, rejected responses and endpoint restrictions, not real inference. No retrieval/prompt tuning or frozen-case edits were made; historical baseline results retain their original hashes.

Official references consulted:

- [OpenAI Chat Completions](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)
- [DeepSeek Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/)
- [Claude Messages](https://platform.claude.com/docs/en/api/messages/create)
- [Claude authentication](https://platform.claude.com/docs/en/manage-claude/authentication)
