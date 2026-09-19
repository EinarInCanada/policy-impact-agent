# Local review workspace

Run from the repository root:

```sh
python3 -m policy_impact.web --port 8766
```

Open **http://127.0.0.1:8766/**, exactly as printed. The server binds only to IPv4 loopback. Stop it with Ctrl+C. Do not expose it through a reverse proxy, tunnel, shared server or public network: it is a single-user research interface, not a production web service.

## Five-minute demo

1. Open the default interval investigation. The page automatically prepares an **offline evidence preview**; this does not call a model.
2. Compare the earlier twelve-month and later six-month clauses. The change list is an exact textual comparison, not an AI impact judgment.
3. Read the evidence register and source provenance. The annual procedure, aligned current procedure and low-risk distractor are different documents. A relevant keyword alone does not establish applicability.
4. Choose `future planning`. Its September date precedes the new policy's October effective date. Planning is permitted, but the notice explicitly distinguishes it from current applicability. Switching to currently effective policy at that date causes input rejection.
5. Choose `missing annex`. The corpus mentions Annex A but does not contain it. The preview cannot invent its contents. A future model draft must leave the individual customer's exemption unresolved.
6. Optionally export the current record as JSON. Editing the question/date/intent invalidates the displayed record and disables export until another run completes.

All dates, procedures and customer references are fictional. The initial October date belongs to the authored scenario, not the machine's current date.

## Your own model key

Expand **Generate a model draft** after inspecting the preview. Choose fixed RAG or the bounded agent, enter an available Gemini model ID and your own API key, and explicitly consent. No model ID, quota or free tier is assumed. The fixed path makes one model call; the agent can make up to six under its other budgets. Provider charges and quotas depend on your account.

The page sends credentials to the local server over loopback HTTP; the provider adapter sends its request to Gemini over HTTPS. The UI does not use cookies, localStorage, sessionStorage, third-party assets or analytics. It clears the password field and consent on submission. Credentials are not included in response/export objects or access logs and are not saved by the application. They still exist transiently in browser/server memory; this is not secure memory erasure or protection against a compromised local computer, browser extension or debugging tools.

The agent can send additional passages from the same registered corpus. The source register describes that corpus; the initial preview is not a guarantee that no additional source passage will be sent. Do not enter confidential data into this demo. Reloading/closing the page does **not** cancel an already-started provider call. There are no automatic retries; only one model investigation may run at a time. A second attempt receives a conflict response.

## Reading a result

- **Offline preview:** no generated findings and zero model calls.
- **Draft ready:** model output passed structural and exact-reference validation. Semantic correctness remains unverified.
- **Agent stopped/failed:** no successful draft; inspect the trace and budget/failure status.
- **Evidence links:** jump to exact registered quotes and their Unicode coordinates/fingerprints.
- **Execution record:** model/tool calls, available usage, retrieval exclusions and trace. Missing usage remains unknown.

Export contains excerpts and model-generated text, so inspect it before sharing. It never constitutes a compliance certificate. Source and model text are rendered as text, not HTML or executable Markdown.

## Verification and limitations

Automated HTTP tests cover loopback configuration, static-route allowlisting, Host/Origin/token checks, offline provider isolation, scoped inputs, credential exclusion from a mocked response and the single-run lock. JavaScript syntax is checked separately. [Browser checks](BROWSER_CHECK.md) verify offline previews, date rejection, stale-result invalidation, consent guard and an actual JSON download. Screenshot capture failed, so visual acceptance remains pending. These checks are not a penetration test, comprehensive accessibility audit or live Gemini verification.

The interface currently exposes only the authored customer-review corpus and fixed revision pair. Arbitrary uploads, user accounts, persistent investigations and policy edits are deliberately absent. The CLI supports explicitly selected compatible corpus manifests for research. English is the interface language for this project milestone.
