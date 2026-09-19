# M3: fixed RAG and Gemini interface

**Multi-provider update:** see [PROVIDERS.md](PROVIDERS.md) for OpenAI, DeepSeek, Claude and custom OpenAI-compatible endpoints. Gemini-specific setup below remains valid; Gemini is no longer the only adapter.

**Implementation and mocked/offline tests exist. No real Gemini request has been made in this project yet.** Live compatibility and model quality remain unverified until the owner provides a key locally and opts into sending the fictional test excerpts. Offline test responses are test doubles, not measured model performance.

## Fixed RAG

`prepare_fixed` compares the two named policy revisions, retrieves up to six policy and six procedure passages, and constructs a source-grounded payload. `run_fixed` makes one generation call and validates the structured packet. The model emits evidence IDs; source quotes/fingerprints are resolved by the application, not trusted from generated text.

A needs-review finding requires evidence from both specified policy revisions and at least one procedure. Unknown/unseen IDs, duplicate references, unexpected fields and unsupported status values are rejected. An insufficient-evidence finding must explain missing information. Current-review intent checks that the after revision is the unambiguous effective policy; planning intent permits a published future-effective revision with an explicit warning.

These are structural checks, not a semantic judge. A syntactically valid but unsupported statement can still pass. A test explicitly demonstrates that boundary; final evaluation must measure claim support separately.

## Transport and safeguards

- One fixed HTTPS Gemini GenerateContent endpoint; the model ID cannot be a URL or path.
- Key supplied through `GEMINI_API_KEY`, placed in `x-goog-api-key`, not the URL or model payload. No key in CLI arguments, repr, persisted configuration or investigation output.
- Explicit `--allow-remote` is required. Preview performs no model call.
- HTTP redirects are rejected, ambient proxy configuration is not used, and ordinary TLS certificate validation remains enabled.
- Default timeout 30 seconds; accepted maximum 60. Maximum output 4,096 tokens by default (hard configurable ceiling 8,192); request capped at 128 KiB and response at 1 MiB. No automatic retries or hidden fallback model.
- Only a complete STOP candidate and strict JSON object are accepted. Truncated/blocked/malformed/duplicate-key outputs fail. Usage fields are recorded when returned; absent fields stay null, not zero.
- Failures are sanitized without copying raw request headers, HTTP bodies or transport exceptions. CLI does not report a failed generation as a successful draft.
- Output path checks occur before remote calls; existing artifacts are not overwritten.

The implementation uses the documented GenerateContent JSON configuration, including `responseMimeType` and `responseJsonSchema`. Google's documentation currently labels the GenerateContent guide legacy; the interface needs a real-request smoke check before a support claim. References reviewed 2026-09-17: [API](https://ai.google.dev/api/generate-content), [structured outputs](https://ai.google.dev/gemini-api/docs/generate-content/structured-output?hl=en). No model availability, pricing or free-quota guarantee is made. A user must choose an available compatible model explicitly.

## Safe local setup

First inspect what would leave the machine:

```sh
python3 -m policy_impact.cli preview --output artifacts/preview-01.json
```

Set the key in a terminal without placing it in command history (zsh):

```sh
read -rs 'GEMINI_API_KEY?Gemini API key (hidden): '
export GEMINI_API_KEY
```

Then replace `YOUR_AVAILABLE_MODEL_ID` with an actual compatible Gemini model ID:

```sh
python3 -m policy_impact.cli investigate --model YOUR_AVAILABLE_MODEL_ID --allow-remote --output artifacts/fixed-rag-01.json
unset GEMINI_API_KEY
```

Do not paste real keys into chat, screenshots, git or issue reports. Shell environment inheritance is not a secrets vault; only use a trusted local environment. Remote inference sends selected source passages to Google and is subject to its applicable terms. We have not approved this prototype for confidential bank documents.

The fictional October investigation date is deliberate and separate from the real execution date. To compare a published revision before it takes effect, choose `--at 2026-09-15 --intent planning_review`; this must not produce a current-compliance claim.
