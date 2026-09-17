# M1: source and evidence contract

Implemented with Python's standard library. No parser, retriever, model or network access is involved.

## Registered source

`SourceRevision` records a document ID, revision ID, policy/procedure role, exact text, provenance, publication date and effective date. Dates use ISO YYYY-MM-DD or explicit `None`. Malformed dates are rejected. Missing dates stay missing; retroactive dates are retained without declaring them valid or applicable.

`content_sha256` hashes the UTF-8 encoding of exact registered text. `fingerprint` additionally binds document/revision identity, role, provenance and both dates through canonical JSON with schema version 1. The hash is an integrity identifier, not a digital signature or a statement that the source is authoritative.

No whitespace, line-ending or Unicode normalization occurs. A future ingestion step must preserve its source bytes separately and record how extraction produced this text. M1 hashes registered text, **not original PDF/DOCX bytes**, and has no page-coordinate mapping.

## Reference

`EvidenceRef` carries document ID, revision ID, source fingerprint, half-open `[start, end)` offsets and an exact quote. Offsets count Python Unicode code points, not UTF-8 bytes or browser UTF-16 code units. Future UI adapters must convert explicitly. Empty and whitespace-only quotations are rejected.

`Corpus` copies a provided collection into a read-only mapping, rejects duplicate document/revision identities and never reads arbitrary paths or URLs. Its immutable source objects and references prevent normal accidental field changes; this is not a sandbox against hostile in-process Python code.

`verify()` rejects an unknown revision, changed fingerprint, out-of-range span or mismatched quote. A successful check means only that the quoted text matches a registered revision at those coordinates. It does not verify claim support, applicable version, policy completeness or legal correctness.

## Checks

```sh
python3 -m unittest discover -s tests -v
```

Fourteen tests cover exact round-trips, content and metadata changes, false quotations, revision substitution, invalid bounds, Unicode, line endings, immutability, duplicate identity, source-list copying, dates, metadata and malformed references. No API key or external package is required. These tests are not a model accuracy or security benchmark.
