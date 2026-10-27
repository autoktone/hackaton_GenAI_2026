# Workflow, planning, and operational traceability

## Status

Functional design accepted by the project owner.
Approval: Ok.

The nominal application path is now integrated with the real memory engine;
see report 0014. Full workflow policy execution and hydrological demonstration
remain pending, with implementation changes subject to separate approval.

## Scope

Development proceeds incrementally. Fictional fixtures support initial
specifications, repeatable tests, and controlled demonstration scenarios.

A subsequent increment integrates real external observations through Zetaris.
Final project validation requires working application access to real data
through Zetaris and an identifiable Nightshift-backed analytical contribution
from the Analyzer.

Keep fictional scenarios for reproducible incident, approval, isolation,
and recovery demonstrations. Label their data and simulated operations
explicitly; do not present them as live source integration.

It is not an official flood-warning service or a validated safety system.

World Model is the selected operational-state engine. The accepted integration
direction uses the unchanged official TypeScript reference through a local
Python subprocess bridge.

Nightshift is required as the primary AI provider for the final demonstration.
The deterministic no-LLM workflow remains an intermediate verification baseline.

The Nightshift client is separate from the World Model bridge.
Model selection and the exact AI-powered feature remain open.

AI-generated proposals must respect workflow rules and human approval gates.
Record invocation references, input and output artifact references, requested
routing configuration, and available evidence of the actual serving model.
Never record Runtime tokens or provider credentials.

An actual Nightshift-backed application feature must be demonstrated.
Simulated responses and health checks alone do not satisfy this requirement.
New AI-dependent workflow rules require an explicitly versioned definition;
do not silently change existing runs or either preserved deterministic
workflow version, 1.0.0 or 1.1.0.

## Responsibilities

- Workflow definition: versioned steps, dependencies, permitted adaptations,
  incident policies, approval gates, and termination conditions.
- Planner: determines necessary actions from explicit rules and available data.
- Orchestrator: dispatches authorized actions and supervises progression,
  interruptions, retries, and escalation.
- Weather and Hydro: obtain or reuse observations.
- Analyzer: performs calculations, uses Nightshift for an identifiable
  analytical contribution in the final demonstration, and records assumptions,
  validation results, and uncertainty limitations.
- Reporter: prepares results and their presentation.
- Tracer/Audit: structures evidence, checks trace completeness, and explains
  execution history.
- World Model: stores supported operational representations and events and
  reconstructs projections within verified implementation limits.
- Data layer: preserves observations, dataset versions, collection metadata,
  and reusable result references.

These responsibilities may share a process in the prototype.
The Tracer is deterministic and requires no LLM.

## Workflow outline

1. Create the run and capture its fixed inputs and workflow version.
2. Check data availability, coverage, quality, and applicable freshness.
3. Execute or reuse Weather and Hydro work independently when permitted.
4. Analyze after required dependencies and approvals are satisfied.
5. Prepare the report with evidence references.
6. Verify trace completeness before normal closure.

The deterministic workflow definition is recorded in
../../workflows/flood-analysis/1.1.0.json.
The operational representation is documented in execution-model.md.
Detailed event schemas, status transitions, and the final Nightshift-enabled
workflow version remain to be defined.

The event-envelope requirements in execution-model.md refine the general
field inventory below and define which common fields are mandatory.

Workflow 1.1.0 defines finalization independently of report production.
After normal work, definitive failure, or cancellation, the orchestrator
stops new dispatches and reconciles outstanding operations.

The Tracer performs the terminal evidence review even when no report exists.
The run remains FINALIZING until uncertain operations are reconciled and
the finalization event is durably published.

COMPLETED requires complete mandatory evidence. FAILED or CANCELLED may
record incomplete evidence with explicit missing items.

See execution-model.md for command ordering and staged publication.
Workflow 1.0.0 remains preserved as the earlier verification baseline.
Neither version has an implemented executor.

## Tracer participation

Tracing is part of the workflow throughout execution, not only a final step.

| Checkpoint | Required trace |
|---|---|
| Run creation | Request, fixed inputs, owner, workflow identity and version |
| Planning | Metadata examined, policies applied, selected actions and reasons |
| Task preparation | Dependencies, preconditions, assignment, intended operation |
| Task execution | Start, attempt, sources, result references, outcome |
| Modification | Affected object, change, reason, relevant state references |
| Incident | Cause, affected task, impact, related events |
| Blocker creation | Blocker identity, cause, scope, resolution conditions |
| Approval | Requested action, bound parameters, authorized actor, decision |
| Resolution | Resolved condition, remaining blockers, evidence |
| Resume | Reconstructed position, reconciliation, new attempt if applicable |
| Analysis | Input versions, method, assumptions, result references, uncertainty |
| Reporting | Evidence supporting the presented conclusions |
| Closure | Trace-completeness findings and execution summary |

The Tracer does not grant authorization or silently change other components'
decisions. Missing or inconsistent evidence produces a traceability incident.

## Event context

Application events have a common envelope with applicable fields:

- eventId, eventType, schemaVersion.
- userId, requestId, runId.
- workflowId, workflowVersion.
- stepId, taskId, attemptId.
- actorId, agentId.
- occurredAt, recordedAt.
- causationId, correlationId.

Omit fields that do not apply. Define precise identity, timestamp, ordering,
and correlation semantics before implementation.

Event-specific payloads identify changes, blockers, approvals, dataset
versions, operation results, and the reasons for decisions.

Keep large artifacts and measurement series in their dedicated storage.
Trace records reference them without embedding credentials or IP addresses.

## Operational evidence and native audit

The application command path records required operational evidence.
It must not depend on a later agent inferring missing events from logs.

The Tracer consumes this evidence to explain decisions and check completeness.

World Model's native mutation audit is separate from business traceability.
It does not by itself explain why a collection was avoided or an approval
was required.

No atomic transaction across application operations, engine events, and
native audit is assumed.

## Traceability failure policy

- Do not dispatch a protected action if its required intent cannot be recorded.
- If a result exists without recorded completion, report an uncertain outcome
  and reconcile before retrying.
- Missing mandatory evidence prevents normal closure and must be reported.
- Never fabricate historical evidence to hide a gap.

Enforcement belongs to the application and requires dedicated tests.

## Data validity and selective collection

The Planner distinguishes observation time, publication or availability time,
and retrieval time.

Evaluate source, zone, requested coverage, gaps, quality, dataset version,
parameters, and applicable policy before collecting.

Decisions may reuse valid data, collect missing coverage, refresh invalid
data, wait for compatible shared collection, or report insufficiency.

Record the decision and supporting metadata references for each run.
Sharing data or collection work does not share private execution state.

## Historical replay

Historical data replay and operational event replay are distinct:

- Historical data replay evaluates a past situation using information
  available at the simulated time.
- Operational event replay reconstructs execution state from recorded events.

Historical runs preserve the simulated time, requested horizon, input
parameters, workflow version, dataset versions, and relevant method versions.

The Tracer explains which information was included or excluded and why.
Observation time alone does not prove historical availability.

Unavailable publication or revision history must be disclosed as a limitation.
A fictional replay scenario does not establish hydrological forecast accuracy.

## Concurrent requests and execution scope

One user may submit multiple concurrent requests. Each request and run retains
its own operational context, regardless of shared geography, time period, or
underlying datasets. User identity and data-selection parameters are not
execution-state keys.

The same rule applies across users, whether zones and periods overlap or not.
Keep userId, requestId, and runId distinct; a request may be replayed through
more than one run. Do not silently merge independently submitted requests
because their business parameters match.

Share only permitted datasets, valid cached calculations, and compatible
collection operations. Retain per-run references, ownership checks, tasks,
events, blockers, approvals, and results.
Shared collection deduplication is not request or run deduplication.

The E1 bridge tests overlapping same-user creation calls with the same fixture
zone and period. Its state writes are serialized.
Multi-user workflow execution, other-zone scenarios, task parallelism, and
higher-load behavior remain to be implemented and verified.

## Execution profiles and demonstration modes

Bind each run to an explicit data-source and dependency profile.
Changing the profile creates a new run rather than silently changing a
resumed execution.
Standalone unit tests use selected dependency stubs. Controlled demonstration
scenarios use fictional data and deterministic incidents; record which
components actually execute, including World Model and Nightshift.
A real-data demonstration uses external observations through Zetaris and
an actual Nightshift-backed analytical contribution.
Both fictional and real inputs may support historical analysis where their
availability at the simulated time is established.
Operational event replay restores recorded state and artifacts without
repeating collection or inference.
The current deterministic workflow remains an intermediate verification
baseline, not the final Nightshift and real-data workflow.

## Demonstration evidence

The operational scenario includes:
1. RUN-001 creation and planning decisions.
2. Weather completion.
3. Separate Hydro network and approval blockers.
4. Network resolution while approval remains outstanding.
5. Process restart and state reconstruction.
6. Scoped human approval and authorized resume.
7. Hydro completion and Analyzer eligibility.
8. A traceability summary.
9. Verification that RUN-002 remains independent.

A separate data scenario demonstrates initial simulated collection,
subsequent valid-data reuse, and collection of missing coverage only.

Final integration evidence must also show real external observations accessed
through the application's Zetaris connection, with source and dataset
references linked to the analysis.

A controlled fictional scenario can demonstrate workflow behavior, but cannot
alone establish real-data integration.

Additional verification should exercise missing evidence using a separate
fictional fixture, without altering preserved demonstration records.

Record preconditions, exact commands, expected and observed results, versions,
dates, and limitations. Distinguish planned, implemented, tested, and
demonstrated behavior.

These scenarios provide evidence of prototype behavior. They do not alone
prove scientific validity or compliance with an external participant guide.

## Deferred work

- Retention and purge policies.
- Assessment and implementation of applicable personal-data obligations,
  including GDPR/RGPD.
- Production identity and authorization infrastructure.
- Full historical backtesting and hydrological validation.
- H-MEM, Markovian, and Scout Intent integration.

Retention and GDPR compliance are not implemented or claimed for the
hackathon prototype. Existing secret-protection and data-minimization rules
remain applicable.

The local Participant Setup Guide, dated 21 October 2026, has been reviewed
for the Power requirement on pages 16 to 24. Decision 0010 records the findings.
A complete requirement-to-evidence mapping remains pending.

## Demand-driven execution

Decision 0011 governs the final workflow.

The application orchestrator qualifies the request and invokes the Analyzer
with an authorized source catalog and execution limits. Weather and Hydro
are not mandatory predecessors of analysis.

The Analyzer forwards Nemotron data requests to the application orchestrator.
The Planner evaluates validity and reuse for the requested scope. The
orchestrator coordinates permitted Zetaris operations and returns a correlated
result to the Analyzer.

The orchestrator must remain responsive while the Analyzer is active.
Collector requests do not recursively start another analysis workflow.
Only permitted data-operation templates may be instantiated.

Analysis cannot complete while its required tool results remain pending.
Cancellation prevents new dispatches; late results remain trace evidence.

This section takes precedence over the earlier pre-analysis collection outline
for the final application. Existing deterministic definitions remain preserved.
See [decision 0011](../decisions/0011-demand-driven-analysis.md) and the
[documentary workflow 1.2.0](../../workflows/flood-analysis/1.2.0.json).
The new definition has no implemented executor; E1 remains bound to 1.1.0.

## Nominal executable checkpoint

The application now records its nominal qualification, analysis, delegated
SQL and report-preparation path through the actual official World Model.
See [report 0014](../validation/reports/0014-world-model-nominal-application.md).

The tested path binds definition 1.2.0 and derives task state in memory.
It does not interpret every JSON policy, execute general collectors, provide
durable finalization or recover after process restart. Legacy E1 is preserved.

The local CLI passed with explicit provider/data stubs. Earlier real
Nightshift/Zetaris evidence is separate. A useful all-real hydrological run,
source normalization and meaningful SAMPLE remain to be delivered.

## References

- Project instructions: ../../AGENTS.md
- Decision register: ../decisions/README.md
- Nightshift requirement: ../decisions/0010-nightshift-required-integration.md
- Participant guide: ../Participant%20Setup%20Guide.pdf
- Bridge decision: ../decisions/0009-python-world-model-bridge.md
- World Model review:
  ../references/meterless/world-model/integration-notes.md
- Zetaris reference: ../references/zetaris/integration-notes.md

## Document history

| Date | Change |
|---|---|
| 2026-10-26 | Recorded the accepted workflow design, transversal tracing, replay boundaries, demonstration evidence, and deferred work. |
| 2026-10-26 | Added required Nightshift integration, preserved the deterministic baseline, and updated guide-review status. |
| 2026-10-26 | Reconciled contracts and responsibilities, clarified progression to real-data integration, and identified the terminal tracing gap. |
| 2026-10-26 | Specified report-independent finalization and staged publication with explicit verification limits. |
| 2026-10-26 | Aligned the current deterministic workflow reference with version 1.1.0 and preserved version 1.0.0. |
| 2026-10-26 | Separated standalone tests, controlled demonstrations, real-data analysis, and operational replay. |
| 2026-10-26 | Clarified concurrent requests per user, independent execution scopes, and the limits of E1 concurrency evidence. |
| 2026-10-27 | Documented demand-driven Analyzer requests and linked workflow 1.2.0 while preserving the deterministic baseline. |
| 2026-10-27 | Linked the implemented nominal memory-engine path and retained explicit full-workflow and durability limits. |
