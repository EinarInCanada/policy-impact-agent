# Scope and design decisions

## Objective

Produce evidence-backed review packets for a policy-version change and its possible effect on a bounded set of procedures. Help a reviewer find and verify relevant passages; never certify compliance or perform policy changes.

## Initial decisions

- Python for the deterministic core, model/tool interfaces and evaluation. Begin with standard-library tests; introduce dependencies only with a concrete requirement.
- Keep document acquisition, source identity, retrieval, generation, validation and export separate. No framework-specific objects in core evidence contracts.
- Use immutable document revisions. Document ID, revision ID, source hash and passage coordinates must be independently checked.
- Distinguish publication date, effective date and the requested investigation date. Missing or conflicting dates must not silently become “latest applies.” Comparing a future version for planning is different from asserting it is currently applicable.
- Earlier and later revisions of one policy may both be intentionally retrieved for comparison. Procedures are a different document role. A date filter must not erase the old side of a comparison.
- A bounded agent is part of the project, but its advantage over fixed RAG is an empirical question. Both paths must use the same approved corpus and evidence contract.
- No arbitrary Python, SQL, shell, URLs or file paths supplied by the model may be executed. Retrieval tools will resolve IDs within an approved corpus.
- No autonomous edits. Human confirmation is a workflow boundary, not a mechanism that excuses unchecked generated claims.
- Provider integration is planned as bring-your-own-key. Do not call any provider until key handling, opt-in data transfer and resource ceilings are implemented.

## Proposed read-only tools

These are proposed interfaces, not implemented capabilities:

1. `search_clauses`: search approved policy revisions and return references.
2. `read_passage`: resolve a verified reference to source text.
3. `compare_clauses`: compare explicitly identified passages; do not infer missing source content.
4. `search_procedures`: return candidate procedure passages, not a confirmed impact judgment.

Tool budgets, schemas, retry rules and per-call audit events will be frozen before the first agent evaluation. All tool output and source text are untrusted data, never system instructions.

## Provenance versus truth

Exact-reference validation can establish that an excerpt matches a registered source revision. It cannot establish that the source is authoritative, that the excerpt entails a finding, that the policy applies, or that the review is complete. Those checks must not be conflated in the UI, tests or README.

## Data gate before retrieval work

Select one narrow policy topic. Author a small, explicitly fictional set of policy versions and procedures with known changes, exceptions and missing attachments. Inspect potential public sources separately; record their URLs, snapshot dates, version identity and terms before acquisition/publication. Do not infer production performance from synthetic fixtures.

## Existing work and contribution boundary

The prior feasibility discussion identified Dify's retrieval/metadata/citation functionality, LangSmith's RAG evaluations and Regology's advertised policy-change mapping. These are references for reuse and overlap, not products independently benchmarked here:

- https://github.com/langgenius/dify-docs/blob/main/en/cloud/use-dify/nodes/knowledge-retrieval.mdx
- https://docs.langchain.com/langsmith/evaluate-rag-tutorial
- https://regology.com/blog/making-sense-of-the-noise-staying-ahead-of-compliance-changes

Do not claim an unmet market or superior performance. The potential contribution is a measured, inspectable implementation of a limited task. If a component works off the shelf, integrate it rather than rebuilding it for novelty.
