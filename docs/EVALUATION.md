# Evaluation plan — before experiments

Development lexical retrieval has been measured; no live model comparison or human productivity study has been run. Metrics below are acceptance-design targets unless explicitly linked to measured results. Freeze concrete cases, split, model/configuration and budget before final evaluation.

## Runnable development harness

`python3 -m policy_impact.evaluation --output artifacts/evaluation-dev-01.json`

Runs five explicitly fictional development investigations without a key. These reuse the development corpus and are **not held out**. The output includes per-case evidence recall, failures, source/code hashes and resource records. Baseline output contains evidence, not generated findings. This recall measures the complete retrieved context (including changed clauses), **not** the M2 search-only recall@3.

After following [local model setup](MODEL_INTERFACE.md), append `--modes baseline fixed agent --model YOUR_AVAILABLE_MODEL_ID --allow-remote` to opt into a three-path run. This sends excerpts to Gemini and may consume paid quota depending on your account. Five cases can attempt up to 35 model calls with current default budgets: five fixed calls and up to thirty agent calls. There are no automatic retries. The same configured provider is used for both generative paths.

All attempted cases remain in summaries. Failed runs receive zero required-evidence recall even if some evidence was retrieved before failure; inspect the raw row for diagnostic evidence. Cases with no expected passages have null recall and are excluded only from that metric. Token counts are recorded as returned; missing counts are unknown, not zero. Completed response usage is retained even when subsequent packet validation fails. A transport failure can consume provider resources without returning usage.

Draft success is structural/operational only. Semantic precision, recall, applicability and abstention remain **unscored**, not implicitly perfect. The development runner rejects a `final` split; use the separate [frozen final runner and human review workflow](FINAL_RUN.md). Final cases and a [semantic annotation rubric](FINAL_SCORING.md) are frozen under `fixtures/final-review/freeze.json`; they are newly authored synthetic text, not independently collected or human-validated data. Do not relabel development fixtures as held out. Model latency is a single sequential observation, not a controlled performance benchmark. Raw artifacts can contain all source excerpts; review them before publishing.

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
