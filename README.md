# Policy Impact Agent

**A policy changed. Find what needs human review—and show the evidence.**

A focused RAG and agent engineering project for investigating how policy changes may affect operating procedures. The intended output is an evidence-backed review packet, not a chatbot answer or an automated compliance verdict.

**Status: project initialized; implementation is starting.** There is no working retrieval pipeline, model integration, agent or UI yet. Examples below describe the intended behavior, not measured capabilities. No accuracy, time-saving or security result has been established.

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
| M1: immutable sources and evidence contracts | Planned | Exact source references, validation and negative tests |
| M2: versioned corpus and retrieval baseline | Planned | Authored fixtures, time/version filtering and measured retrieval quality |
| M3: fixed RAG and model adapter | Planned | User-owned key, structured outputs and evidence checks |
| M4: bounded investigation agent | Planned | Allowlisted tools, budgets, failure handling and injection tests |
| M5: comparative evaluation | Planned | Held-out comparison, errors, costs and limitations published |
| M6: review experience and handoff | Planned | Small English-first review interface, demo and reproduction guide |

Full acceptance criteria and the next action are in [ROADMAP.md](docs/ROADMAP.md). A completed research prototype would still not constitute a production certification.

## Get started

At initialization, there is no runnable agent. Clone the repository and read the design before extending it:

```sh
git clone https://github.com/EinarInCanada/policy-impact-agent.git
cd policy-impact-agent
```

Runnable commands will be added when the corresponding implementation exists. No paid service or API key is needed to read the project or contribute to deterministic tests.

## What this project should demonstrate

For AI application and software engineering roles: document data modeling, retrieval design, structured model integration, restricted tool execution, evaluation, testing and clear technical tradeoffs. It complements a statistical modeling project; it does not demonstrate a new foundation model or replace professional banking experience.

A future portfolio claim must cite actual artifacts and measurements. At present the truthful claim is **“initialized an evidence-first policy investigation project”**, not “automated bank compliance” or “reduced review time.”

## License and contribution history

Original code and authored documentation: [MIT](LICENSE). External documents retain their own terms. Never commit API keys, private policies or personal data. See [CONTRIBUTING.md](CONTRIBUTING.md).

Each completed and verified increment is committed and pushed separately. Commits document real progress; they are not backdated or manufactured to create a daily contribution streak.
