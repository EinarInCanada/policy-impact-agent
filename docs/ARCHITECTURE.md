# Architecture and engineering tradeoffs

## One investigation, three execution paths

The task fixes a policy document, earlier/later revisions, date, review intent and question. All paths share the same registered corpus and date-selection rules. The model never chooses the investigation's authority or changes its date.

| Layer | Implementation | Responsibility and boundary |
|---|---|---|
| Source identity | `evidence.py` | Frozen revision metadata, content hashes and exact Unicode spans; not source authenticity or legal authority |
| Evidence access | `retrieval.py` | Publication/effective-date selection, labeled-clause diff and lexical search; not semantic impact judgment |
| Fixed RAG | `investigation.py` | One predetermined retrieval context, one model response and strict packet validation |
| Bounded agent | `agent.py` | Model-directed tool/finish actions; allowlisted read-only tools, scope checks and call/context/time budgets |
| Remote boundary | `provider.py` | Explicit user key and consent, fixed Gemini HTTPS endpoint, bounded request/response size, no redirects or automatic retries |
| Additional protocols | `providers.py` | OpenAI-compatible and Anthropic Messages adapters; provider-specific credentials, public-IP-pinned custom HTTPS endpoints and shared output validation |
| User interfaces | `cli.py`, `web.py`, `static/` | Offline preview or opt-in model run; English local review workspace and JSON export |
| Measurement | `evaluation.py`, `final_evaluation.py` | Comparable task runs, immutable final inputs, preflight metadata and failure-preserving checkpoints |
| Human adjudication | `adjudication.py` | Empty reviewer forms and arithmetic over supplied labels; no automated claim verification |

The baseline stops after evidence retrieval. Fixed RAG adds one draft. The agent starts with the same context and can retrieve more before finishing. It uses structured JSON actions, **not a multi-agent swarm, MCP transport or the provider's native function-calling protocol**.

## Why this implementation is deliberately small

- Python standard library keeps the local demo install-free and the execution boundary inspectable. No framework is required to explain the tool permissions or state transitions.
- Lexical retrieval is a transparent baseline, not a claim that embeddings are unnecessary. Measured misses are published; introducing embeddings would be a new declared experiment, not a quiet change after final-set exposure.
- Authored clauses have stable IDs so moved paragraphs can retain identity. Unstructured ingestion, OCR and cross-document clause alignment are separate problems; this project does not claim to solve them.
- Model-produced evidence IDs are resolved by application code. The model cannot supply replacement source text and have it treated as registered evidence.
- Fixed RAG remains a first-class comparison. An agent's additional calls must earn their complexity through measured usefulness, which has not yet been established.

## Trust boundaries

Source text, user questions, model outputs and tool observations are untrusted data. Exact hashes bind quotes to registered revisions, but do not make a document authoritative. A syntactically valid cited finding can still be false; human review and separate semantic scoring are mandatory boundaries.

The agent has no shell, arbitrary HTTP, filesystem write, SQL or document-update tool. The provider adapter itself necessarily makes an authorized remote request. Local application code writes only requested artifacts/checkpoints; the model cannot choose those paths. This separation is an application-level control, **not an operating-system sandbox**.

The web workspace binds to `127.0.0.1`, rejects unexpected Host/Origin headers, requires a per-server request token and uses an allowlist for static routes. It renders source/model text as text and sets a restrictive content-security policy. These measures do not make Python's development HTTP server suitable for public hosting or protect a compromised local machine.

API keys are not prompt content. The CLI reads a user-configured environment variable; the browser submits a password field to the local server for one run. Keys are not intentionally persisted in browser storage, reports or access logs. Transient process memory, extensions and external provider retention remain outside that guarantee. Do not use confidential banking data in the demo.

## Failure and resource behavior

The default agent permits six model attempts, five tool attempts, forty observed passages, 60,000 serialized context characters and a 120-second wall budget. Transport timeout is thirty seconds. Budget checks occur around synchronous calls: they cannot cancel an in-flight provider request exactly at the wall deadline. Failed attempts count; there is no silent retry, fallback model or scope expansion.

Final evaluation records configuration before execution and writes each completed case/path separately. A interrupted run can leave partial checkpoints and consumed quota; it is not a complete comparison. Semantic review forms are bound to the exact result by canonical hash. Hashes establish identity, not authenticity of reviewer attribution or quality of human judgments.

## What is and is not demonstrated

Implemented artifacts demonstrate source modeling, deterministic validation, retrieval, a constrained agent loop, API integration boundaries, local interface design, evaluation bookkeeping and negative testing. They do not establish production banking integration, autonomous compliance review, legal reliability, model accuracy or business savings. Live model verification and subsequent human adjudication are explicitly deferred by the project owner.
