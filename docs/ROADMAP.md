# Roadmap

User-approved direction: policy-change impact investigation with RAG and a bounded agent. Establish the public repository and README first. Commit and push each completed, verified milestone.

## M0 — initialization: complete

- Public repository, scope, README, design, evaluation plan, license and contribution rules.
- Explicitly distinguish proposed functionality from implemented behavior.
- No dataset acquisition, live model calls or product-performance claims.

## M1 — source and evidence contracts: next

- Immutable source revision metadata and deterministic content fingerprint.
- Exact evidence spans with revision/hash/quote checks.
- Explicit roles and dates; reject malformed metadata and ambiguous identifiers.
- Unit tests for tampering, invalid coordinates, Unicode and duplicate revisions.
- Document the boundary: reference validity does not establish entailment or applicability.

## M2 — corpus and retrieval baseline: planned

- Select one narrow topic and publish authored, labeled fixtures with a provenance manifest.
- Separate document roles, policy revisions and effective-date eligibility.
- Baseline retrieval and clause comparison; development retrieval evaluation.
- Inspect public-source reuse and existing components before expanding the corpus.

## M3 — fixed RAG: planned

- Provider-neutral interface, one tested bring-your-own-key adapter and mock/offline tests.
- Explicit opt-in before excerpts leave the local environment; keys excluded from reports/logs.
- Structured findings with evidence validation and insufficient-information outcomes.

## M4 — bounded agent: planned

- Read-only tool registry, strict arguments, call/context limits and deterministic stop conditions.
- Cross-reference investigation, explicit trace, timeout/retry behavior and failure reporting.
- Tests for injection, invalid tool requests and budget exhaustion. No unrestricted execution.

## M5 — comparative evaluation: planned

- Freeze benchmark, scoring rubric and resource configuration before final execution.
- Compare baseline, fixed RAG and agent; publish all errors and resource use.
- Do not assert bank-level accuracy, legal reliability or human time savings from fixture tests.

## M6 — review experience and handoff: planned

- English-first review interface showing evidence and uncertainty, not a generic chat-only view.
- Reproducible demo, architecture explanation, limitations and final requirement audit.
- Public code and reviewed artifacts only; no keys or confidential documents.

## Publication rule

Each coherent increment: run relevant checks, inspect changes and staged paths, commit a factual message, push, and verify the remote outcome. No empty or backdated commits. A local blocked milestone is not complete merely because code exists.
