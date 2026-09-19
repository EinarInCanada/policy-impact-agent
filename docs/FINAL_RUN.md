# Reproduce the frozen final comparison

The frozen corpus, cases and scoring rules live under `fixtures/final-review/` and [FINAL_SCORING.md](FINAL_SCORING.md). Their hashes are checked before execution. The final runner requires a clean committed checkout so the recorded git revision represents its implementation. It does not modify frozen inputs or tune on results.

## Offline baseline

From the repository root, use a new output name:

```sh
python3 -m policy_impact.final_evaluation --baseline-only --output artifacts/final-baseline-01.json
```

This runs all eight final tasks with no provider configuration and no model calls. It measures complete-context evidence recall, not answer quality. It cannot be used as a completed three-path semantic comparison.

## Live comparison (explicit opt-in)

First smoke-test your available Gemini model on a **development** case using [model setup](MODEL_INTERFACE.md). Then configure the key locally with the hidden prompt described there and run:

```sh
python3 -m policy_impact.final_evaluation --model YOUR_AVAILABLE_MODEL_ID --allow-remote --output artifacts/final-comparison-01.json
```

This sends fictional document passages and questions to Gemini. Up to **56 model attempts** can occur: eight fixed-RAG attempts plus up to 48 agent attempts. There are no automatic retries. Provider charges and free-tier eligibility are not assumed. The key is read only from `GEMINI_API_KEY`, not the command arguments, preflight or result files. Clear it afterwards with `unset GEMINI_API_KEY`.

Before any model request the runner saves `<output-stem>-records/preflight.json` with git revision, implementation hashes, model ID, frozen corpus/rubric digests, prompt hashes, provider settings, agent budgets, case order, timestamp and one-run repetition count. After each case/path it writes a new numbered row file. Existing files are never overwritten. Final results bind the preflight using a canonical JSON digest.

If interrupted, completed row files remain. An in-flight provider request may consume quota without producing a saved row. There is **no automatic resume** or duplicate-call retry. Do not treat a partial directory as a complete evaluation: preserve it, disclose the interruption, and deliberately choose a new run/output if repeating the experiment. Checkpoint write failure stops subsequent requests. Exit status 1 can mean saved failed investigations; inspect the result/checkpoints rather than assuming no work happened.

Model IDs may be aliases whose underlying version changes. The current adapter does not retain the provider's returned model-version field; record that reproducibility limitation rather than assuming a pinned model. Final artifacts contain fictional source text and model output; inspect them before publishing.

## Human review and scoring

```sh
python3 -m policy_impact.adjudication template --result artifacts/final-comparison-01.json --output artifacts/review-01.json
```

This produces a **blank**, result-bound JSON form. A human reviewer reads the full sources and packets and fills `reviewer`, `reviewed_on`, each successful case's four boolean flags and rationale, and every finding's labels/rationale according to [the rubric](FINAL_SCORING.md). A `matched_reference` is one case-local reference-item ID or null. Each source-supported match must also have the correct status and no date/scope error. For cases not requiring abstention, set `appropriate_abstention` false. Failed packets retain empty finding reviews and null flags; they cannot receive semantic credit.

```sh
python3 -m policy_impact.adjudication score --result artifacts/final-comparison-01.json --labels artifacts/review-01.json --output artifacts/scores-01.json
```

The scorer checks complete case/finding coverage, result binding, explicit labels, duplicate matches and incompatible matches. It performs arithmetic over supplied labels, **not semantic judging or reviewer authentication**. False human attribution or incorrect judgments can still be supplied; the tool cannot certify independence. Tests using synthetic labels exercise arithmetic only and are not research results. If human review has not happened, semantic results remain pending.
