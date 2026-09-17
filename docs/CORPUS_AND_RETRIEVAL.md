# M2: authored corpus and lexical baseline

## Provenance and component choice

The `fixtures/customer-review` directory contains seven authored fictional source revisions: one policy in two versions, three procedure examples (outdated, aligned and low-risk), a future publication and an undated procedure. The corpus JSON is the source manifest; each source declares provenance and dates, and the manifest declares MIT for our original text. None is a real bank requirement or a legal interpretation. Annex A is intentionally absent; its contents must never be invented.

The initial development set contains eleven authored queries. Ten have required evidence annotations; one has no matching content. This is not held-out data. No third-party corpus has been downloaded or redistributed. Public-source acquisition remains optional behind the documented terms/version gate.

Existing retrieval, metadata and evaluation components were reviewed in DESIGN.md. This increment uses a deliberately small standard-library lexical baseline and `difflib` for text comparison, not a new search engine or a claim that embeddings/frameworks are unnecessary. It establishes a reproducible comparator before generation and adaptive investigation.

## Behavior

- Paragraph chunks retain exact Unicode source offsets and stable explicit `[CLAUSE_ID]` labels where present. Unlabeled paragraphs receive positional IDs, which are not semantic alignment across revisions.
- Search uses lowercase Unicode word tokens, log term-frequency, inverse-document-frequency weights and a square-root length normalization. There is no stemming, embedding, reranker or semantic entailment check. Stable passage IDs break ties. Zero-overlap passages are not padded into results.
- `effective` mode selects the latest published, effective revision per document. Unknown dates and tied effective dates are explicit exclusions; a published revision with unknown dates prevents silently calling an older revision current. Explicit revision scope may intentionally select a historical revision and is not a current-version assertion.
- `published` comparison mode requires explicit revision IDs and checks publication date. It retains both sides even if the later version has not yet taken effect. Effective dates are returned so a planning comparison is not confused with present applicability.
- Scope/role filtering occurs before search scoring. A missing date or unregistered revision never falls back to the newest file.
- Clause comparison returns added/removed/modified text with verified references. Unchanged clauses moved to another position are not reported as content changes when labels persist. Rewording is still a text change; semantic equivalence and downstream impact are not determined here.

## Measured development result

At top 3, mean required-evidence recall is **0.85 across ten answer-bearing queries**. Eight have complete retrieval, one synonym-only query retrieves no evidence, and one scope question retrieves only one of two required passages. The unrelated query returns no results. All results are in [the aggregate report](results/m2-development.json), including source hashes.

This deliberately exposes lexical limitations rather than tuning every authored question to pass. It is not 85% answer accuracy, a held-out result or a production estimate. Valid citations only identify text; they do not validate the inference made from it.

## Reproduce

```sh
python3 -m unittest discover -s tests -v
python3 -m policy_impact.retrieval search --query "temporary exemption Annex A" --role policy --at 2026-10-15
python3 -m policy_impact.retrieval compare --at 2026-09-15
python3 -m policy_impact.retrieval evaluate --output artifacts/m2-development-repeat.json
```

All commands are offline. File output requires a new path under `artifacts/`. Tests cover historical/current selection, explicit comparison, date ambiguity, future publications, role isolation, exact Unicode quotations, moved clauses and deterministic ranking. No model, autonomous agent or policy conclusion is implemented in M2.
