# Roadmap

User-approved direction: policy-change impact investigation with RAG and a bounded agent. Establish the public repository and README first. Commit and push each completed, verified milestone.

## M0 — initialization: complete

- Public repository, scope, README, design, evaluation plan, license and contribution rules.
- Explicitly distinguish proposed functionality from implemented behavior.
- No dataset acquisition, live model calls or product-performance claims.

## M1 — source and evidence contracts: complete

Implemented in `policy_impact/evidence.py`; 14 offline unit tests pass locally. See [the evidence contract](EVIDENCE_CONTRACT.md). CI is configured for four Python versions. No retrieval or applicability decision is implemented yet.

- Immutable source revision metadata and deterministic content fingerprint.
- Exact evidence spans with revision/hash/quote checks.
- Explicit roles and dates; reject malformed metadata and ambiguous identifiers.
- Unit tests for tampering, invalid coordinates, Unicode and duplicate revisions.
- Document the boundary: reference validity does not establish entailment or applicability.

## M2 — corpus and retrieval baseline: complete

Seven authored fictional revisions, explicit date/version selection, lexical retrieval, text comparison and eleven development queries. Required-evidence mean recall@3 is 0.85 on ten answer-bearing queries; failures are published. See [corpus and retrieval](CORPUS_AND_RETRIEVAL.md). Total offline tests: 29. No model findings yet.

- Select one narrow topic and publish authored, labeled fixtures with a provenance manifest.
- Separate document roles, policy revisions and effective-date eligibility.
- Baseline retrieval and clause comparison; development retrieval evaluation.
- Inspect public-source reuse and existing components before expanding the corpus.

## M3 — fixed RAG: implemented, live validation pending

Provider-neutral reply interface, opt-in Gemini REST adapter, fixed retrieval/generation path, strict evidence-backed packet validation and offline preview. Mocked transport tests do not establish real API compatibility. A user-owned key and consent are still required for real-request validation; see [model interface](MODEL_INTERFACE.md).

- Provider-neutral interface, one tested bring-your-own-key adapter and mock/offline tests.
- Explicit opt-in before excerpts leave the local environment; keys excluded from reports/logs.
- Structured findings with evidence validation and insufficient-information outcomes.

## M4 — bounded agent: implemented, live behavior pending

Four scoped read-only tools and a model-directed structured-action loop. Scripted tests cover permissions, budget/timeout failures, evidence checks and document-injection execution boundaries; they do not measure actual Gemini behavior. See [agent harness](AGENT_HARNESS.md). MCP transport has not been implemented.

- Read-only tool registry, strict arguments, call/context limits and deterministic stop conditions.
- Cross-reference investigation, explicit trace, timeout/retry behavior and failure reporting.
- Tests for injection, invalid tool requests and budget exhaustion. No unrestricted execution.

## M5 — comparative evaluation: planned

Development runner implemented for five authored investigation tasks and all three paths. It preserves failed runs and available usage and deliberately leaves semantic correctness unscored. Final cases, a frozen semantic rubric and live comparison are still pending. See [evaluation instructions](EVALUATION.md).

- Freeze benchmark, scoring rubric and resource configuration before final execution.
- Compare baseline, fixed RAG and agent; publish all errors and resource use.
- Do not assert bank-level accuracy, legal reliability or human time savings from fixture tests.

## M6 — review experience and handoff: planned

Local English workspace and [demo/privacy guide](REVIEW_WORKSPACE.md) implemented. HTTP integration tests and JavaScript syntax checks pass; browser visual QA and the final acceptance audit remain pending. No hosted service or real Gemini verification is claimed.

- English-first review interface showing evidence and uncertainty, not a generic chat-only view.
- Reproducible demo, architecture explanation, limitations and final requirement audit.
- Public code and reviewed artifacts only; no keys or confidential documents.

## Publication rule

Each coherent increment: run relevant checks, inspect changes and staged paths, commit a factual message, push, and verify the remote outcome. No empty or backdated commits. A local blocked milestone is not complete merely because code exists.
