# Evaluation plan — before experiments

No experiments or human productivity study have been run. Metrics below are acceptance-design targets, not results. Freeze concrete cases, split, model/configuration and budget before final evaluation.

## Three comparable paths

1. **Rules/retrieval baseline:** explicit passage differences and keyword retrieval; no generative conclusions.
2. **Fixed RAG:** predetermined retrieval followed by structured draft generation.
3. **Bounded agent:** the same sources and tools, with limited additional investigation steps.

Use the same task inputs, approved corpus and eligibility rules. Report retrieval-only performance separately when the first path cannot emit comparable semantic findings. For fixed RAG versus agent, keep the model version the same and report total retrieval/model work rather than hiding extra agent computation.

## Cases to include

- Direct changes to a frequency, responsibility or threshold.
- Relevant definitions and exceptions in another passage.
- Published-but-not-effective revisions and questions about an earlier date.
- Rewording or moved clauses with no intended substantive change.
- Procedures that already reflect the new policy.
- Missing referenced attachments, conflicting passages and unanswerable questions.
- Distractor documents, document-borne prompt injection and tool failures.

Begin with a small development set. Expand and freeze a separate final set before tuning stops. Label synthetic and public-source cases separately. Authored cases are not real bank ground truth. Maintain an annotation guide and manually verify the source passage behind each answer; do not use an LLM's answer as its own reference truth.

## Measurements

| Measure | What it checks | Important limitation |
|---|---|---|
| Evidence retrieval recall | Expected passages retrieved | Requires a declared set of relevant passages |
| Exact-reference validity | Revision, boundaries and quote match | Does not prove a supported conclusion |
| Finding precision and recall | Correct review items versus labeled items | Matching and partial-credit rules must be declared |
| Version/applicability errors | Wrong policy date, scope or exception | No general legal-interpretation guarantee |
| Appropriate abstention | Stops when evidence is insufficient | Also report unnecessary refusals |
| Tool-policy violations | Calls outside schema, allowlist or budget | Test coverage is not proof against every attack |
| Latency and provider usage | Time, calls and token usage | Report cold/warm effects and price assumptions separately |

Record model and prompt versions, corpus hashes, tool traces, failures and retries. Redact secrets. A structured answer can still be wrong; failed runs must remain in denominators.

## Human usefulness

Reduced review time is a hypothesis, not a claim. Demonstrating it requires a declared review task, a manual baseline, a consistent correctness requirement and a human study design that addresses practice/order effects. Until such a study exists, report software latency and evidence quality—not “hours saved.” No bank deployment or financial savings claim follows from a local benchmark.

## Decision rule

Publish the comparison even if fixed RAG is better. Retain the bounded agent implementation as an evaluated alternative, not the default merely because it sounds advanced. Identify which task classes justify extra investigation. Do not modify the final set to hide errors or claim percentage improvements without denominators and actual runs.
