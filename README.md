# Policy Impact Agent

**A policy changed. Find what needs human review—and show the evidence.**

A focused RAG and agent engineering project for investigating how policy changes may affect operating procedures. The intended output is an evidence-backed review packet, not a chatbot answer or an automated compliance verdict.

**Status: fixed RAG, bounded agent, Gemini adapter and a local English review workspace are implemented with offline/mock tests; live verification is pending.** Version-scoped search, clause comparison and evidence preview run without a key. No real Gemini call, model accuracy, time-saving or security benchmark result has been established.

[Scope & design](docs/DESIGN.md) · [Roadmap](docs/ROADMAP.md) · [Evaluation plan](docs/EVALUATION.md) · [Development rules](CONTRIBUTING.md)

## The problem

Finding a changed sentence is only the beginning. A reviewer still needs to establish which version applies, read definitions and exceptions, locate the affected procedure, and explain why someone should examine it.

Consider this **fictional** example:

| Source | Text |
|---|---|
| Earlier policy | High-risk customer records must be reviewed every 12 months. |
| Later policy | High-risk customer records must be reviewed every 6 months. |
| Operating procedure | Schedule high-risk customer reviews annually. |

The useful output is not “your organization is non-compliant.” It is:

> **Potential review item:** the procedure's annual schedule may conflict with the later policy's six-month interval. Confirm that the later policy is effective for the investigation date and applies to this process. Review the linked policy clauses and procedure passage before taking action.

Each finding should identify its supporting passages, versions, applicability assumptions and unresolved questions. If the exception, attachment or effective date is missing, the system should say so.

## The workflow we are building

```text
Two policy versions + procedure documents + investigation date
                              |
                    Validate and index sources
                              |
                 Compare clauses and retrieve evidence
                              |
           Bounded investigation: retrieve, inspect, verify, stop
                              |
                   Validate proposed findings
                              |
          Evidence-backed review packet -> human review
```

### RAG finds the evidence

Version-aware retrieval should recover relevant clauses, definitions, exceptions and procedure passages. Every evidence reference must resolve to an immutable source revision and an exact passage. Semantic similarity alone is not proof that a source is applicable or that it supports a claim.

### The agent investigates missing context

A bounded agent may decide to inspect a referenced definition, look up an exception or search for affected procedures. It must operate through allowlisted, read-only tools with call and context budgets. It cannot rewrite a policy, change a business process or grant itself more permissions.

### Deterministic checks enforce the contract

Code—not the model—will validate reference identities, passage boundaries, allowed output types and tool arguments. A citation check proves that a passage exists; it does **not** prove semantic entailment. Claim support and applicability require separate evaluation and human review.

## What makes this worth evaluating?

Not a new vector database. Not an original claim that agents can review policies. Document comparison, RAG, evaluation frameworks and commercial policy-mapping products already exist.

The intended contribution is a small, inspectable implementation and benchmark of a specific investigation workflow:

- **Time and version awareness:** do not quietly treat the newest uploaded document as the currently applicable policy.
- **Evidence before conclusions:** preserve source passages and explicitly surface missing context.
- **Controlled agency:** measure whether additional investigation improves on a fixed retrieval workflow, and at what cost.
- **Failure visibility:** publish version mistakes, unsupported findings, missed changes, unnecessary refusals and tool failures—not just successful examples.

The [evaluation plan](docs/EVALUATION.md) compares a rules/retrieval baseline, fixed RAG and a bounded agent. Agent complexity is not assumed to be an improvement. If an existing component already solves a subproblem, reuse it and attribute it.

## Planned investigation output

| Field | Purpose |
|---|---|
| Investigation date and source revisions | Define what was examined and when it applies |
| Changed clause and linked procedure | Identify the potential review target |
| Evidence references and exact excerpts | Let a reviewer verify the source material |
| Status | Needs review, insufficient evidence, or no issue identified within the inspected scope |
| Missing information and assumptions | Prevent uncertainty from becoming an invented answer |
| Tool trace, model configuration and resource use | Support debugging, reproduction and cost analysis |

“No issue identified” must never mean “certified compliant.” The scope of inspected material must remain explicit.

## Project boundaries

**In scope:** one narrow policy domain, two versions, a small collection of procedures, explicit dates, structured review packets, a fixed RAG baseline, a bounded agent and a held-out evaluation set.

**Out of scope:** legal advice, automatic compliance decisions, internet-wide regulatory monitoring, production bank integration, automatic document edits, confidential customer records, multi-agent swarms and model training.

The first fixtures will be authored synthetic examples, labeled as such. Public documents may be added only after source, version and reuse conditions are checked. Public availability does not automatically authorize redistribution. Real bank procedure data is not required.

## API keys and privacy

This is an open-source project, not a hosted commercial service. The model interface will support a user-supplied key, starting with a Gemini adapter if the chosen API/model is suitable at implementation time. No universal free-quota or model-availability promise is made.

Keys must stay outside git, logs and exported investigation packets. Live model calls will be opt-in; unit tests must work without a key. Before any model request, users must understand which document excerpts leave their machine. A local interface does not make a remote model private. These are implementation requirements, not completed security guarantees.

## Development status

| Milestone | Status | Exit condition |
|---|---|---|
| M0: scope and public repository | Complete | README, design, evaluation plan and honest milestone history |
| M1: immutable sources and evidence contracts | Complete | Exact source references, validation and 14 negative/positive tests |
| M2: versioned corpus and retrieval baseline | Complete | Seven authored revisions; development evidence recall@3 = 0.85 (not answer accuracy) |
| M3: fixed RAG and model adapter | Implemented; live check pending | User-owned key, structured outputs, evidence checks and mocked transport tests |
| M4: bounded investigation agent | Implemented; live behavior pending | Four read-only tools, resource budgets, failure states and scripted adversarial tests |
| M5: comparative evaluation | Development harness implemented; final study pending | Held-out comparison, errors, costs and limitations published |
| M6: review experience and handoff | Local interface and demo guide implemented; final audit pending | Small English-first review interface, demo and reproduction guide |

Full acceptance criteria and the next action are in [ROADMAP.md](docs/ROADMAP.md). A completed research prototype would still not constitute a production certification.

## Get started

The deterministic core is runnable on Python 3.11–3.14 with no dependencies or API key. Model-backed paths require your own key and explicit opt-in:

```sh
git clone https://github.com/EinarInCanada/policy-impact-agent.git
cd policy-impact-agent
python3 -m unittest discover -s tests -v
python3 -m policy_impact.retrieval search --query "temporary exemption Annex A" --role policy
python3 -m policy_impact.retrieval compare --at 2026-09-15
python3 -m policy_impact.cli preview --output artifacts/preview-01.json
python3 -m policy_impact.evaluation --output artifacts/evaluation-dev-01.json
python3 -m policy_impact.web --port 8766
```

Open **http://127.0.0.1:8766/** for the local review workspace. Follow the [five-minute demo and privacy guide](docs/REVIEW_WORKSPACE.md). It starts with real retrieved fixture evidence, not simulated model answers. The optional password field accepts your own Gemini key for an explicitly consented run.

The [evidence contract](docs/EVIDENCE_CONTRACT.md) documents source fingerprints and quotations. The [corpus and retrieval report](docs/CORPUS_AND_RETRIEVAL.md) documents measured development retrieval and its failures. [Model setup](docs/MODEL_INTERFACE.md) and [agent harness](docs/AGENT_HARNESS.md) describe opt-in commands, execution limits and the unverified live boundary. CI is configured for Python 3.11–3.14. A preview is not a generated investigation.

## What this project should demonstrate

For AI application and software engineering roles: document data modeling, retrieval design, structured model integration, restricted tool execution, evaluation, testing and clear technical tradeoffs. It complements a statistical modeling project; it does not demonstrate a new foundation model or replace professional banking experience.

A future portfolio claim must cite actual artifacts and measurements. At present the truthful claim is **“implemented version-scoped retrieval, a fixed RAG path and a bounded agent with offline evidence/tool-contract tests”**, not “automated bank compliance” or “reduced review time.” Live model quality remains unmeasured.

## License and contribution history

Original code and authored documentation: [MIT](LICENSE). External documents retain their own terms. Never commit API keys, private policies or personal data. See [CONTRIBUTING.md](CONTRIBUTING.md).

Each completed and verified increment is committed and pushed separately. Commits document real progress; they are not backdated or manufactured to create a daily contribution streak.
