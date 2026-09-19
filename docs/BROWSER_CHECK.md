# Local browser verification record

Checked September 18, 2026 (Toronto), against the local workspace served at `http://127.0.0.1:8766/`, using Ego Lite. Application implementation: `9f4ad6e` (subsequent changes in this delivery are documentation only).

| Check | Observed result |
|---|---|
| Initial page and automatic preview | English workspace renders in the browser accessibility tree; status says offline preview ready, zero model calls; 3 changed clauses and 14 retrieved passages for the interval case |
| Scenario change invalidates old results | Switching to future planning clears findings and disables export before rerun |
| Future planning | September 15 planning preview succeeds and explicitly warns that this is planning, not current applicability |
| Same date, current-review intent | Request is rejected; error shown and export remains disabled |
| Missing-annex preview | Completes as evidence-only output, not a generated answer |
| Actual JSON download | Browser download saved locally; parsed as `offline_preview`, no packet, zero model calls; all 16 exported references independently verified against the corpus |
| Empty model configuration | Generate action displays a request for model ID, key and explicit consent; no model invocation |
| Narrow layout geometry | At an emulated 390-pixel viewport, document scroll width was 390 pixels; no horizontal overflow observed by DOM measurement |

## Limits and unresolved visual check

The snapshot checks establish rendered controls/text and the tested interactions. They do not establish visual polish, contrast, all responsive layouts or comprehensive accessibility.

The model-settings click initially encountered an automation hit-testing issue around a closed `details` element. After inspecting DOM state, the details panel was opened programmatically; a normal Generate-button click then exercised the missing-configuration guard. This does not prove the disclosure interaction is reliable on all browsers.

Screenshot capture repeatedly timed out in the browser's `Page.captureScreenshot` operation, including after reloading, clearing emulation and bringing the page forward. No screenshot was successfully inspected. **Visual screenshot acceptance remains pending**, rather than inferred from HTTP success or DOM geometry. Browser recovery or user visual confirmation is still needed. The same task space was preserved; no replacement space was created to bypass the error.

No real API key was entered, and no model/network request to Gemini was authorized by these checks. Live model rendering, full keyboard navigation and other browser engines were not tested. The local JSON download and attempted screenshots are ignored artifacts, not published research results.
