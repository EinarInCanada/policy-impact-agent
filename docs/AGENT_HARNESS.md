# M4: bounded investigation harness

The bounded agent loop and four read-only tools are implemented and tested with scripted model replies. **Real-model behavior has not been evaluated yet.** The scripted tests verify execution contracts, not model reasoning or prompt-injection resistance rates.

## Decisions and execution

The model produces one structured action per call: request one tool or finish with a packet. The controller validates the action, executes an allowed read-only tool, and returns the observation on the next model call. It is a model-directed loop, not a hardcoded sequence of search terms. JSON structured actions are used rather than provider-native function calls; no MCP transport is currently implemented.

Fixed RAG and agent receive identical initial evidence. The agent may retrieve additional definitions, exceptions and procedures; that extra work is counted, not hidden. Prompts tell the model to treat source text as untrusted. The real security boundary is outside the prompt: the tool registry cannot change the task date, policy pair or corpus scope and exposes no write, shell, code or network tool.

## Tools

| Tool | Accepted arguments | Enforced scope |
|---|---|---|
| search_clauses | query; optional revision_id | Only the task's two published policy revisions |
| read_passage | passage_id | Only approved policy and effective procedure passages |
| compare_clauses | empty object | The fixed task's policy pair and date |
| search_procedures | query | Only unambiguous effective procedures at the task date |

Unknown arguments are rejected. A model cannot request a different date, path, URL or revision. A missing attachment stays missing. Returned evidence is exact-reference validated; findings may cite only passages actually exposed in the initial context or a successful tool observation.

## Default budgets and failures

- Six model calls and five tool attempts. Failed attempts count; no automatic retries.
- 60,000 serialized context characters, 40 distinct evidence passages, and the provider's independent request/response limits.
- 120-second wall budget checked between calls and after responses. Synchronous calls are not forcibly interrupted; an in-flight call may extend actual duration by at most its configured transport timeout (default 30 seconds). A late response is discarded.
- Invalid tools/actions, provider failures, citation/schema rejection and exhausted budgets have distinct failure statuses with no successful packet. CLI exits nonzero for failed agent runs and may save their audit record.

The packet validator enforces evidence presence and allowed status fields, not semantic truth. An unsupported statement with valid citations can still pass. No automated certification is produced.

## Offline checks and live command

```sh
python3 -m unittest discover -s tests -v
python3 -m policy_impact.cli investigate --mode agent --model YOUR_AVAILABLE_MODEL_ID --allow-remote --output artifacts/agent-01.json
```

The second command requires prior local key configuration and consent described in [MODEL_INTERFACE.md](MODEL_INTERFACE.md). It has not been run against a real model yet. Do not interpret scripted tests as a substitute.

Tests include multi-step completion, all four tools, scope/date restrictions, malformed actions, budget exhaustion, late replies, provider failure, unseen references and document-borne instructions requesting forbidden scope. The injection test deliberately scripts the model's unsafe request and verifies that the controller rejects it; it does not measure whether Gemini would be induced to issue that request.
