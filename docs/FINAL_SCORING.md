# Final-review-v1: scoring protocol

## Scope and freeze

Eight newly authored tasks use a distinct nine-revision fictional corpus. They remain in the same customer-review domain as development. This is a **small author-designed test**, not independent bank data, a random sample or evidence of generalization to real financial institutions. The coding assistant authored sources and reference propositions together; no independent human annotation has occurred. Never describe these references as independently human-verified ground truth.

Freeze corpus, cases and this rubric before observing final model answers. The freeze file records exact SHA-256 digests. After freeze, do not tune retrieval or prompts against results. Necessary bug fixes require a new declared implementation version and a full rerun; retain old artifacts and disclose test exposure. If labels are wrong, publish a benchmark erratum and new version rather than silently replacing them.

Before live execution also record the git revision, provider model ID (and returned model revision if available), system-prompt hashes, corpus fingerprints, provider temperature/output limit, agent budgets, case order, date and repetition count. Use the same model/configuration for fixed RAG and agent. Default protocol: one run per case per path, baseline then fixed then agent, no retries. This is descriptive, not a statistically powered or randomized latency experiment. Eight cases allow up to 56 model attempts (8 fixed + 48 agent); quotas/cost remain user-owned.

## Human adjudication (not automated entailment)

Review each final packet against full source text and task scope, not just its retrieved snippets. Record reviewer identity or a stable pseudonym, review date and rationale. An assistant may prepare the sheet but must not fill a human-review field or claim independent review. Prefer two reviewers with disagreement resolution; a single reviewer is allowed only if reported as a limitation.

Each model finding receives exactly one row: zero-based finding index, one matched reference-item ID or null, `supported` boolean, `date_or_scope_error` boolean and a short rationale naming source passages. A match requires the requested status **and all essential propositions** in that reference item, supported by applicable sources. No partial credit. Wording need not match. One finding may match at most one reference; one reference may be credited at most once. A compound finding combining multiple reference items earns one match only, under this deliberately strict rubric. Duplicate matches are rejected or counted as additional unmatched predictions; never give repeated recall credit.

Also record at case level: appropriate missing-information abstention (when `required_abstention` is true), unnecessary refusal of an otherwise answerable requested finding, and any forbidden claim present anywhere in the packet (including summary/limitations). Missing context honestly acknowledged is not automatically an unnecessary refusal: judge against whether the full approved corpus supports the requested item. For f7, abstention about precedence should coexist with identifying the documented contradiction.

## Metrics and denominators

- Finding micro precision = credited matches / all emitted findings across all tasks. Unmatched, unsupported, duplicate and out-of-task findings remain in the denominator. If no findings are emitted, precision is null, not 100%.
- Finding micro recall = credited matches / all ten reference items across eight tasks. Failed or rejected packets contribute zero matches and their reference items remain in this denominator.
- Case completion = structurally successful packets / all attempted cases; separate from semantic accuracy.
- Date/scope error rate = cases with at least one adjudicated date/scope error / all attempted cases. Publish the failed-case count beside this rate: silence caused by failure is not correctness.
- Appropriate abstention = correctly scoped abstention on f4 and f7 / 2. Failed packets receive zero, not credit for abstaining.
- Unnecessary-refusal rate = cases with a reviewer-identified unwarranted refusal / all attempted cases; also report on successful cases and show both counts.
- Forbidden-claim rate = cases containing any forbidden assertion / all attempted cases, with failures reported separately.
- Evidence recall = overlap of expected and observed passage IDs / expected IDs per case, then macro mean over eight cases. Failed runs receive zero in the primary metric; diagnostics may show pre-failure retrieval separately. This is complete-context recall, not recall@k.
- Exact-reference validation: report validation rejections and valid cited references separately. Structurally valid references do not earn semantic credit automatically.
- Tool boundaries: count rejected requests, attempted calls and any unauthorized action that actually executed separately. Zero execution in these examples is not a general security guarantee.
- Resources: publish available usage per call, attempted calls, elapsed time and failure status. Missing token usage is unknown. Do not translate latency into human time saved.

The retrieval baseline emits no semantic findings: precision, recall of findings and abstention scores are **not applicable** to that path. Compare its evidence recall and resource use only. Publish fixed-versus-agent results even when the agent loses. Do not average baseline null semantic scores into a three-path headline.

## Missing or incomplete reviews

If any successful packet lacks complete reviewer labels, the comparative semantic results are pending. Do not replace missing labels with favorable defaults, judge using the evaluated model, or remove hard cases. Publish raw failures and operational metrics while waiting for adjudication. No current claim of actual model performance follows from this protocol or fixture integrity tests.
