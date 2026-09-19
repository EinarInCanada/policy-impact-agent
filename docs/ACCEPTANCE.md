# Delivery audit

This is a requirement-to-evidence audit, not a production certification. On September 18, 2026 (Toronto), the owner explicitly chose to **finish other delivery work and leave real-model verification as a pending task**. Accordingly, live Gemini comparison and human semantic adjudication of those future responses remain visibly deferred; they are not reported as passed.

| Requirement | Evidence | Disposition |
|---|---|---|
| Public GitHub repository, English README first | Public `EinarInCanada/policy-impact-agent`; initial docs commit precedes implementation | Delivered |
| Verified increments committed/pushed | Repository history; remote main and CI checked | Delivered; continue for subsequent increments |
| Two policy revisions, procedures and explicit investigation date | `Task`, corpus roles, current/planning checks; retrieval and investigation tests | Delivered offline |
| Immutable source/evidence references | Fingerprint/span/quote checks and tampering tests in `test_evidence.py` | Delivered; not an authenticity guarantee |
| Runnable RAG path | Fixed retrieval + provider call + packet validation; stub transport/investigation tests | Implemented; real provider verification deferred |
| Genuine bounded agent, not renamed rules | Model-directed action loop and four scoped read-only tools; multistep, rejection and budget tests | Implemented; live behavior deferred |
| User-owned API key and explicit remote opt-in | CLI environment configuration; local password/consent UI; provider and HTTP tests | Delivered offline; no universal free-quota claim |
| No autonomous source edits or unconstrained tools | Tool allowlist, scoped arguments, model cannot choose output paths; adversarial scripted tests | Delivered within tested boundary; not a general security proof |
| Rules/retrieval baseline versus fixed RAG versus agent | Development and final runners preserve every case/path and failures | Harness delivered; live comparison deferred |
| Distinct final cases frozen before model evaluation | Eight cases, new corpus, hash-locked rubric and integrity tests | Delivered; author-designed synthetic set, not independent bank data |
| Honest measured failures and resources | Published final baseline report, row checkpoints, resource metadata and null unknown usage | Offline baseline measured; model metrics pending |
| Human semantic scoring separate from citation checks | Frozen rubric, blank forms, result-bound scoring; failure/duplicate/incomplete-label tests | Tooling delivered; actual human review deferred until live responses exist |
| English-first review experience | Local workspace with source passages, changes, uncertainty, trace and export | Implemented; see browser verification record below |
| Reproducible demo, architecture, limitations | `REVIEW_WORKSPACE.md`, `ARCHITECTURE.md`, `FINAL_RUN.md`, README | Delivered |
| No secrets/private source material published | Authored fictional corpora; tracked-file inventory and staged changes inspected | No secret/private material identified in this delivery; not an exhaustive historical secret audit |

## Checks and their limits

The current local suite passes 80 standard-library tests. The four-version Python 3.11–3.14 CI succeeded at `9f4ad6e`; subsequent changes require their own CI status. JavaScript syntax passes `node --check policy_impact/static/app.js`. Unit and HTTP tests use scripted model responses and cannot prove live model behavior.

Actual browser interactions and export verification are recorded in [BROWSER_CHECK.md](BROWSER_CHECK.md). Screenshot capture timed out repeatedly, so visual acceptance remains pending; the audit does not claim it passed. A successful browser interaction test is not a comprehensive accessibility/security audit. The interface is local-only and English-only for this project; multilingual ingestion and mixed-file cleaning belong to the earlier, separate project and are not claimed here.

## Deferred owner-approved work

1. Locally configure an available Gemini key/model and explicitly authorize sending the fictional development corpus; smoke-test both fixed and agent paths.
2. If adapter compatibility requires changes, commit/version them and disclose them before final execution. Do not tune against the observed final cases.
3. Run the frozen comparison with its full attempt budget, preserve all failures and publish sanitized results.
4. Have a human reviewer adjudicate the actual packets, then publish scores with attribution and limitations. No human-time-saving claim without a separate controlled study.

No data has been sent to Gemini by the agent during this delivery. The deferred items must not be silently converted into successful milestones in a resume, README or future completion report.
