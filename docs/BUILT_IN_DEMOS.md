# Two saved AI-authored demonstrations

Open the local workspace and the first saved report appears immediately. No API key, remote call or model wait is needed. Use the two buttons above the investigation record to switch examples.

1. **Find outdated procedures:** policy frequency changes from twelve to six months and the scheduling owner changes. The report flags two legacy instructions for review and distinguishes the already-aligned current procedure. It preserves exemption uncertainty.
2. **Stop when evidence is missing:** a customer exemption depends on an absent annex and missing customer records. The report leaves the decision unresolved, identifies the missing documents and suggests reviewer next steps.

Reports include clickable evidence references, old/new clause text, limitations and next steps. Export JSON saves the report with its provenance label. Input edits clear the saved report; **Preview evidence** runs a fresh deterministic preview, and **Generate draft** requires the user's own provider credentials and explicit consent.

## What generated these reports?

The coding assistant authored these example reports and saved them in [`fixtures/demos/reports.json`](../fixtures/demos/reports.json). They are **not cached Gemini/Claude/OpenAI API responses**, not outputs from a completed bounded-agent run, and not benchmark results. No hidden key, fabricated provider name, token count or agent trace is supplied. The visible sample notice and JSON provenance preserve that distinction.

These are curated teaching examples, not measured evidence that a deployed model will produce the same answers. Real-provider runs remain deferred. The examples use the development corpus only; the frozen final benchmark is untouched.

## Reference integrity

At startup the app checks the authored corpus's SHA-256 and requires the exact registered source fingerprints. Each cited passage passes through the task-scoped read-only registry and the normal packet validator before serving. A nonexistent or future-ineligible citation rejects the example. Curated examples may include passages not returned by the initial lexical search; the UI therefore calls them **included evidence**, not a retrieval-performance result.

Both reports are persisted in Git, not browser storage. Selecting a demo makes a local GET request; it never constructs a provider, sends a key, modifies documents or consumes model quota. The demo's model-call count is zero for playback. Runtime source validation is application work, not a simulated model tool trace.
