# 0011 - Use demand-driven data operations inside analysis

- Status: Accepted
- Category: Architecture
- Recorded on: 2026-10-27
- Approval evidence: Ok.
- Supersedes: None; refines decisions 0004 and 0006 for the final workflow.
- Superseded by: None

## Context

The earlier deterministic verification workflow requires Weather and Hydro
tasks before the Analyzer can start. The owner has clarified that the final
application must let Nemotron identify analytical data needs inside the
Analyzer, while preserving the application orchestrator's global control.

This decision replaces that mandatory pre-analysis sequencing for the final
workflow. It does not rewrite accepted ADRs or alter preserved workflows
1.0.0 and 1.1.0.

## Decision

Keep the application orchestrator in control of the global workflow.

The Analyzer orchestrates a bounded internal Nemotron analysis loop.
It receives the question, authorized source catalog, context and limits.

Weather and Hydro collection are not mandatory prerequisites for analysis.
Data operations are activated only in response to permitted Analyzer requests.

The Analyzer forwards structured data requests to the application
orchestrator. The Planner evaluates coverage, freshness, quality and reuse
for the requested scope. The application orchestrator authorizes and
coordinates the necessary Zetaris operations, then returns their results.

Nemotron may request additional information within the approved analysis
scope. It cannot change the global workflow, grant authorization or dispatch
collectors directly.

Preserve per-run ownership, tool-call correlation, traceability, bounded
execution and controlled termination.

## Alternatives considered

- Mandatory collection before every analysis: retains the earlier sequencing,
  creates unnecessary work and prevents demand-driven acquisition.
- Nemotron controlling the global workflow or directly dispatching collectors:
  bypasses application authorization and execution responsibilities.
- One bounded Analyzer loop under the application orchestrator: selected;
  permits analytical tool decisions without replacing global orchestration.

## Rationale

The model identifies the information needed to answer the question.
The application retains deterministic validation, collection coordination,
resource limits and evidence. This separates analytical decisions from the
authority to perform operations.

## Responsibilities and capability boundaries

- Application: global workflow, request validation, authorization, data
  validity, collector dispatch, deduplication, deadlines and termination.
- Analyzer: internal Nemotron/tool-result loop and structured analytical output.
- Nightshift client: provider transport and protocol handling.
- Zetaris: authorized access to configured weather and hydrometry data.
- Python functions: deterministic normalization and calculations.
- World Model: supported operational records and projections through the
  unchanged official reference; no native scheduler or authorization claim.
- Sample and unit fixtures: explicitly selected source/model substitutions.
  Simulated requests are not evidence of actual Nemotron tool calling.
- Future work: additional result storage, H-MEM and scientific validation.

Structured tool calling through the installed Runtime is not verified.
Text completion success does not establish support for that protocol.

## Consequences and limitations

The application orchestrator must remain able to process Analyzer requests
while analysis is active. Waiting for the final analysis result must not
prevent servicing its pending data requests.

Reuse valid data where possible; a data request does not necessarily require
a new external collection. Temporal admissibility, quality and coverage rules
from decision 0006 continue to apply when a request is processed.

Trace the causal chain from model tool request through application validation,
any collection/read operation and the result returned to the Analyzer.
Shared collection never merges run state or approvals.

Pending or uncertain data operations must be reconciled before terminal
confirmation. Resolving one blocker must not resolve unrelated blockers.
No automatic retry or authorization bypass is introduced.

A new workflow definition must describe demand-driven data operations.
The E1 bridge remains pinned to workflow 1.1.0; this decision does not migrate
existing runs, change code or establish an executable final workflow.

## Assumptions and open questions

- Analysis and data-request/result payload schemas and correlation fields.
- Supported Nightshift structured tool-call behavior and controlled fallback
  proposals if that behavior is unavailable.
- Callback or command-processing implementation avoiding circular waits.
- Exact tool permissions, iteration/time/volume budgets and failure mapping.
- Final workflow version and source contracts after collector verification.
- Credential-free sample inference behavior versus live-backed execution.

These implementation choices require separate review and authorization.

## Validation criteria

- No Weather/Hydro collection is dispatched without an admitted Analyzer request.
- The Analyzer receives the authorized source catalog before requesting data.
- Requests outside allowed sources, scope or budgets are rejected.
- Existing valid data can satisfy a request without another collection.
- A data result returns to the correct run and tool request.
- The orchestrator can service requests while the Analyzer is active.
- Tool results are fed back to Nemotron before the final analysis is produced.
- Run isolation, scoped approvals and bounded termination remain enforced.
- Failure, cancellation and uncertain outcomes retain trace evidence.
- Sample simulations are distinguished from real generated tool calls.

These criteria are planned; no new functional tests have been run.
Prior evidence remains in the [validation register](../validation/README.md).

## References and approval history

- [Project instructions](../../AGENTS.md)
- [Project status](../PROJECT_STATUS.md)
- [Versioned workflows](0004-versioned-workflows.md)
- [Data validity and selective collection](0006-data-freshness-and-selective-collection.md)
- [Nightshift integration](0010-nightshift-required-integration.md)
- [Workflow design](../architecture/workflow-and-planner.md)
- [Data-validity contract](../architecture/analysis-input-and-data-validity.md)
- Approval evidence: Ok. The owner approved demand-driven orchestration and
  this five-file documentation batch in the current conversation.
- Detailed technical-document and JSON-workflow alignment remains pending.

## Record history

| Date | Change |
|---|---|
| 2026-10-27 | Recorded the accepted demand-driven Analyzer/application orchestration split while preserving earlier decisions and workflow versions. |
