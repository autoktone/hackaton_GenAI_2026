# Nightshift integration requirements

## Status

Nightshift integration is required by accepted decision 0010.
Approval: Ok.

This document records requirements and the verified API-smoke milestone.
A minimal SELECT-one provider client, Analyzer/orchestrator and SQL executors
are implemented and passed 27 standalone checks; see
[report 0008](../validation/reports/0008-select-one-application-standalone.md).
The real SELECT-one application path also passed; see report 0009 below.
The useful hydrological feature, full workflow and durable trace remain pending.
Model selection and the exact AI-powered feature remain open.

## Sources

- Participant Setup Guide.pdf, dated 21 October 2026, pages 16 to 24:
  ../Participant%20Setup%20Guide.pdf
- [Local Nightshift source review](../references/meterless/nightshift/integration-notes.md).
- [Source provenance](../references/meterless/nightshift/provenance.json).
- [Captured Power contract](../references/meterless/nightshift/upstream/website/engines.html).

Use Runtime 1.4 / provider contract v4, also supplied by the project owner,
as the target provider contract. Verify installed Runtime compatibility
separately before claiming live integration.
The pinned repository provider guide describes Runtime 0.90.0.
The website also mentions a v5 specification whose content has not been
retrieved; that mention does not establish a reviewed v5 contract.
Local source snapshots are preserved. Installed Runtime version is unknown.

## Required outcome

Demonstrate Nightshift as the application's working primary AI provider.

Show a useful feature making an actual request through Nightshift and
consuming its result. A dependency declaration, simulated response, or
successful health probe is insufficient.

The guide's Power checklist includes a responding Nemotron lane.
Visible underlying Nemotron use is explicitly required for the NVIDIA award.
Model availability and selection must be verified separately.

## Reviewed provider contract

The official Power prompt specifies:
- An OpenAI-compatible provider with normalized base-URL handling.
- Real Bearer authentication and a stable lowercase meterless-app identifier.
- meterless-scope: user for chat requests.
- Route discovery through /v1/models, preserving unfamiliar meterless routes.
- Distinct unauthorized, online, and offline connection states.
- Plain-text requests and a 180-second request timeout.
- Automatic discovery and confidential handling of connection links.

Use the captured target contract and verify compatibility with the installed
Runtime through separately approved checks. Do not assume discovery proves successful inference.

The reviewed prompt includes normalization cases for endpoint suffixes and
rejects the rt-local token placeholder.

## Architecture boundary

Create a Python Nightshift provider client separate from the TypeScript
World Model bridge.

Keep these responsibilities distinct:
- Nightshift: configured inference and model routing.
- World Model: operational events and supported state reconstruction.
- Planner: permitted actions and data-selection decisions.
- Orchestrator: dispatch, supervision, and incident policies.
- Tracer: evidence, causal references, and completeness checks.

Model responses are untrusted proposals or generated artifacts.
They cannot grant approval or bypass workflow constraints.

Do not expose unrestricted SQL, filesystem operations, or arbitrary execution
to a model through this integration.

## Analyzer integration

The Analyzer must use Nightshift in the final demonstration.

Its workflow combines deterministic calculations with an explicit
Nightshift-backed analytical task. The exact task and model remain to be
selected and validated.

Provide the model with relevant calculation results, admissible data
references, assumptions, and uncertainty information.

The model's contribution must be identifiable in the analytical output.
A connection test or report rephrasing alone does not satisfy this requirement.

The Analyzer validates the response before incorporating it into its result.
Model-generated claims must remain distinguishable from measured observations
and computed results.

The Tracer links the invocation, supplied evidence, response, validation
outcome, and resulting analytical artifact to the owning run and task.

Nightshift does not replace numerical methods, uncertainty assessment,
or scientific validation. Generated confidence is not a calibrated
probability of flooding.

If Nightshift is unavailable, record the affected analytical task as blocked
or failed according to the approved workflow. A deterministic-only result
must not be presented as the completed Nightshift-backed demonstration.

## Verified live API smoke

On 2026-10-27, authenticated catalog reads and one real text inference
succeeded through an explicitly selected Windows-loopback transport called
from Python WSL. The catalog exposed 18 meterless routes including auto.
The Runtime reported nvidia/nemotron-3.5-lightning-30b-a3b and finish reason stop.
Native WSL loopback access was refused before HTTP.
See [report 0006](../validation/reports/0006-nightshift-live-api-smoke.md)
for the exact command, results, prerequisites, and limits.

This is provider API evidence, not a reusable project client or the required
Analyzer feature. The response was generated; no application content
verification or JUDGE-panel success was established.
Full provider-contract compatibility and the installed Runtime version
remain unverified.

## Endpoint and execution context

Sample mode must not require or consult a live Nightshift endpoint.
Live mode must use an explicit operator-supplied Console URL and transport.
There is no universal hostname that the application can safely guess.

Loopback identifies the network context executing HTTP. Native Python WSL
could not reach the Windows-only loopback listener in this setup.
A Python WSL caller using Windows curl successfully reached that same
Windows Runtime without changing listeners or network configuration.
This is an explicitly tested Windows-loopback development transport, not
an automatic fallback or an implemented general-purpose provider client.

The recorded smoke command contains the operator-supplied loopback address.
Do not promote that example to a hardcoded application default.
A different machine needs an explicitly reachable, securely configured
Runtime URL and an appropriate transport, followed by approved validation.
A future judge gateway is a separate application endpoint, not a reason to
give reviewers our Runtime token or upstream NVIDIA key.

The reusable configuration loader remains to be implemented.
Its sample mode must ignore live configuration; live mode must require
explicit configuration and keep secrets outside version control.

## Configuration and secrets

Obtain the Runtime URL and token from Nightshift Console.
Provider credentials, including NVIDIA keys, belong in Nightshift's provider
configuration rather than application events or source files.

Determine the private application configuration mechanism before coding.
Do not overwrite existing sensitive files or copy credentials from neighboring
projects.

Never log tokens, authorization headers, or secret-bearing connection links.
Diagnostic errors must be sanitized before storage or display.

Do not assume Windows and WSL share the same localhost connectivity.
Use an explicitly configured address and separately approved connection tests.

## Network and execution approvals

Configuration does not authorize network requests.

Connection checks, automatic discovery, model listing, inference, retries,
and installations each require approval under the project policy.

Do not run automatic port scans or silently try alternative hosts.

Do not silently switch to direct NVIDIA access or another provider when
Nightshift fails.

The prototype must distinguish mocked tests from live calls, including their
network, latency, and possible provider-cost effects.

## Invocation traceability

Associate each invocation with its run, task, attempt, actor, and logical
operation identity.

Record references to:
- Input data and dataset versions.
- Prompt template version and request artifact.
- Requested Runtime route and generation settings.
- Runtime and client versions when available.
- Response artifact and validation outcome.
- Actual serving provider or model evidence when available.
- Timing, failures, approvals, and reconciliation decisions.

A requested meterless route is not proof of the concrete serving model.
Mark unavailable model evidence explicitly.

Do not duplicate complete datasets in prompts, events, or logs unnecessarily.

## Failures and uncertain outcomes

Represent connection, authentication, discovery, timeout, rate-limit,
response-validation, and traceability failures distinctly.

A timeout does not prove that inference never ran.
Do not blindly resubmit an operation with an uncertain outcome.

Retry rules remain to be defined and approved.
Prevent hidden retries from SDK defaults where they conflict with the approved
policy.

An AI result cannot be treated as accepted until application checks and
required evidence are recorded.

## Reproducibility and historical replay

Store generated outputs as versioned artifacts.
Operational replay reconstructs recorded decisions and results without
automatically invoking a model again.

Re-running inference creates a new invocation and may produce different output.

Historical runs must restrict supplied observations and retrieved context to
information admissible at the simulated time.

A model may contain knowledge acquired after that time. Restricting input data
alone cannot prove a leakage-free historical forecast.

Treat historical model-assisted results as exploratory unless the evaluation
method addresses model knowledge and temporal contamination.

## Workflow evolution

Preserve workflow 1.1.0 as the current deterministic verification baseline
and 1.0.0 as its earlier version.

Define a new workflow version when selecting the AI-powered feature and its
success, approval, failure, and tracing rules.

Do not migrate an existing run silently.
The Tracer remains deterministic; Nightshift is not required for recording
operational evidence.

## Standalone provider tests

Inject a selected stub transport for isolated tests; do not start a mock
network server unless separately authorized.
Test URL normalization, required headers, rt-local rejection, unknown
meterless routes, unauthorized versus offline, connection-link secrecy,
response validation, the 180-second timeout setting, and uncertain outcomes.
Auto Detect remains an explicitly authorized network action.
No test or demo profile silently switches from live inference to a stub,
another provider, or a different host.

## Verification requirements

Mocked tests:
- Configuration and URL validation.
- Sanitized errors and connection-state classification.
- Discovery response handling.
- Text response validation.
- Timeout and uncertain-outcome handling.
- No unauthorized fallback, scan, or retry.

Live integration evidence:
- Real Runtime authentication and route discovery.
- A text response through Nightshift.
- A useful application feature using that response.
- Trace linkage to the owning run and task.
- Available underlying-model evidence, especially for Nemotron claims.

Mock tests do not satisfy live integration requirements.
Successful inference does not establish hydrological prediction accuracy.

## Open decisions

- Exact installed Runtime version and full contract compatibility beyond the tested Windows host.
- Exact AI-powered feature and model selection.
- Reusable provider transport, configuration loader, and supported deployment contexts.
- Prompt contracts, output validation, and tool permissions.
- Retry and reconciliation mechanisms.
- Installed Runtime compatibility with the captured v4 target contract.
- Full Participant Setup Guide requirement-to-evidence mapping.

No installation, configuration change, credential access, network probe,
or model invocation is authorized by this document.

## Structured tool loop inside the Analyzer

Verify structured tool calling experimentally before relying on it.

The Analyzer sends the question and authorized tool descriptions through
Nightshift, validates received tool requests, forwards permitted data requests
to the application orchestrator, and returns correlated tool results to
Nemotron before requesting further output.

The provider client handles transport and protocol messages, not business
authorization, collector dispatch or workflow progression.

Bound iterations, tool calls, elapsed time and result volumes. Do not execute
arguments extracted from free text as if they were structured tool calls.
Unavailable tool support requires an explicit limitation and approved
alternative, not fabricated calls.

Distinguish generated output from application checks and any observed
Runtime verification outcome. An undecided JUDGE result is not acceptance.

See [decision 0011](../decisions/0011-demand-driven-analysis.md).
The required analytical feature is now the demand-driven Analyzer loop.
Its exact payload schemas, numerical budgets and implementation remain pending.
Earlier open questions about the feature do not override this accepted scope.

## Verified structured-tool protocol probe

On 2026-10-27, the Windows Runtime returned a structured run_sql call for
SELECT 1 AS one. An explicitly selected standalone stub returned one=1 and
a fresh marker; the final Nemotron response reproduced that marker.
Two HTTP calls succeeded in a measured 6.23 seconds.

Both responses reported nvidia/nemotron-3.5-lightning-30b-a3b for the requested
meterless/auto route. See [report 0007](../validation/reports/0007-nightshift-structured-tool-round-trip.md)
for the exact command, output and limits.

This establishes the tested structured-tool round trip, not universal tool
support, a Python client, application orchestration or Zetaris access.
No successful JUDGE or VERIFY outcome was established.

The next owner-requested increment replaces the stub executor with a real
Zetaris SELECT 1 operation while preserving the run_sql argument contract
and tool-result correlation. Application components must be implemented and
tested before claiming the full orchestrator/Analyzer path.

## Verified live SELECT-one application path

On 2026-10-27, the reusable Python application completed the real path through
Nightshift and Zetaris: orchestrator -> Analyzer -> structured run_sql ->
orchestrator-controlled SELECT 1 -> tool result -> Nemotron -> structured
Analyzer result -> orchestrator.

The application reported PASSED, rows [[1]], two Runtime completion dispatches,
one SQL execution and 13 scoped events. Both model fields reported Nemotron
Lightning for the requested meterless/auto route.

See [report 0009](../validation/reports/0009-select-one-live-application.md)
for the exact command, full structured result and limits. This supplies later
execution evidence for the minimal reusable transport and SQL executor;
earlier pending-live statements describe the prior milestone.

The application-generated receipt was reproduced in final text. That check
does not establish source attestation, JUDGE acceptance or hydrological
validity. World Model, final workflow execution and durable tracing were
not exercised. No inference or SQL request was repeated during documentation.

## References

- Project instructions: ../../AGENTS.md
- Required integration: ../decisions/0010-nightshift-required-integration.md
- Workflow design: workflow-and-planner.md
- Execution model: execution-model.md
- Data validity: analysis-input-and-data-validity.md
- Validation register: ../validation/README.md

## Document history

| Date | Change |
|---|---|
| 2026-10-26 | Recorded Nightshift requirements, provider boundaries, tracing, historical-replay limits, and verification obligations. |
| 2026-10-26 | Required an identifiable Nightshift-backed analytical contribution from the Analyzer in the final demonstration. |
| 2026-10-26 | Linked preserved sources, selected v4 as the target, and specified explicit standalone provider tests. |
| 2026-10-27 | Recorded live API evidence, explicit endpoint contexts, and credential-free sample requirements without claiming a completed Analyzer. |
| 2026-10-27 | Specified the bounded structured tool loop and retained unverified tool-calling and implementation boundaries. |
| 2026-10-27 | Linked the successful Windows structured-tool stub probe and the next real Zetaris SELECT 1 milestone without claiming application completion. |
| 2026-10-27 | Synchronized the minimal SELECT-one implementation and standalone evidence before separately authorized live execution. |
| 2026-10-27 | Recorded report 0009 for the real reusable Nightshift/Zetaris application path while preserving untested domain and durability boundaries. |
