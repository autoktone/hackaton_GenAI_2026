# Operational execution model

## Status

Design direction accepted by the project owner.
Approval: Ok.

The detailed contract was approved for documentation.
Implementation operations require separate approval.
The E1 memory-only bridge and RUN_CREATED projection are implemented and tested.
Operational persistence, restart reconstruction, and workflow scenarios remain
unimplemented; see report 0005 in the validation register.

## Memory bridge increment E1

Implemented and tested in memory only; see
[report 0005](../validation/reports/0005-python-world-model-memory-bridge.md).
The durable publication design below remains the selected next increment.

The application-owned bridge imports the unchanged official WorldModel.
It uses upsertEntity for immutable-by-convention operation-event records,
registerView/view for the RUN_CREATED projection, and native event/audit reads.
It does not reimplement the engine.

Protocol version 1 uses one JSON object per line with protocolVersion,
messageId, principalId, command, and params.
messageId is transport correlation, not requestId, runId, or eventId.
principalId is trusted caller context supplied by the local application;
checks are simulated and do not authenticate an external user.

Supported commands:
- ping: engine metadata and the explicit profile, without creating a run.
- create_run: eventId, runId, request, occurredAt, recordedAt, expectedRevision.
- get_run: runId, subject to the simulated owner check.
- shutdown: application-owned bridge lifecycle control.

The memory profile must be selected explicitly; local persistence is refused.
Inputs follow the structural [request contract](analysis-input-and-data-validity.md),
with LOIRE-DEMO as the only accepted fixture zone.
Freshness evaluation, collection, and workflow task execution are not performed.
The bridge reads the fixed flood-analysis 1.1.0 definition from the project,
records its content fingerprint and definition in the creation event, and
returns status CREATED. It does not execute that workflow.

Run identifiers become run_ plus SHA-256 of runId.
Identifiers use one to 64 ASCII letters, digits, underscores, or hyphens,
starting with a letter or digit.
Requests are limited to 4096 encoded bytes including their newline.
The Python client bounds response lines to 65536 bytes.
Default transport timeout is ten seconds; explicit values must be positive
and at most sixty seconds.

Creation records RUN_CREATED as an operation-event entity with the documented
external key and full envelope in attrs.event.
attrs.command retains canonical normalized original command content.
An exact duplicate returns its original in-memory receipt before revision
validation; conflicting reuse is rejected. New creation requires revision zero.
The caller provides captured UTC occurrence and recording timestamps, which
are normalized and preserved. The reducer uses event data, not wall-clock time
or the currently available workflow definition.

One Python transport permits one in-flight exchange. The bridge processes
commands serially across its per-run WorldModel instances.
Multiple application requests can coexist without sharing run state.
Two overlapping same-user creation calls were tested, not parallel analyses.

Standalone tests explicitly inject StubTransport; actual integration tests
explicitly select SubprocessTransport(profile="memory").
A failed live dependency never activates a stub or another provider.
Timeout, transport loss, or invalid acknowledgement of creation produces an
uncertain-outcome error and disables the client until explicitly replaced.
No automatic mutation retry occurs. Owned subprocesses are closed or stopped.

Only run creation and reads are implemented. Tasks, blockers, approvals,
planning decisions, finalization, durable receipts, rejected-command tracing,
and restart reconstruction remain future application work.
Native mutation audit does not establish those application capabilities.

## Scope and ownership

Use one World Model namespace per run for the initial prototype.

A single bridge process owns all World Model instances and writes.
Application code must not open competing writers for the same namespace.

Derive namespace names from validated run identifiers using a deterministic,
path-safe mapping. Do not accept arbitrary storage paths from protocol input.

Namespaces provide storage separation, not authentication or authorization.
The application checks ownership before accessing a run.

Shared datasets, collection metadata, and collection coordination remain
outside per-run operational state.

## Identity

Preserve application identifiers independently of native World Model IDs.

Every business event has a stable eventId and belongs to one runId.
One user may own multiple simultaneous requests and runs, including matching
zones and periods. Scope state by run, not by user or data-selection values.
Native event identifiers are qualified by namespace when referenced globally.

Keep requestId, runId, taskId, attemptId, agentId, actorId, blockerId,
workflowId, workflowVersion, and protocol correlation identifiers distinct.

A logical operation identifier remains stable across attempts when they
refer to the same protected operation.

## Business event representation

Store each accepted business event as an externally keyed World Model entity:

- type: operation-event
- externalKey.system: flood-risk-intelligence
- externalKey.id: the validated business eventId
- attrs.event: the complete validated business event envelope and payload

The application treats these entities as immutable, although the upstream
primitive is an upsert.

Do not update or delete an accepted business event through the bridge.
Corrections use new events referencing the previous event.

This application convention is not an upstream immutability guarantee.

## Event envelope

Required common fields:
- eventId, eventType, schemaVersion.
- userId, requestId, runId.
- workflowId, workflowVersion.
- actorId.
- occurredAt, recordedAt.
- payload.

Include stepId, taskId, attemptId, agentId, blockerId, causationId, and
correlationId where applicable.

Use normalized UTC timestamps.
occurredAt describes the reported occurrence.
recordedAt describes initial application acceptance.

Use native append sequence for operational replay order within the namespace.
Do not reorder replay using producer timestamps.

Keep historical simulation time separate from operational recording time.
Exact timestamp fields and event-specific schemas require further definition.

## Provenance

Map accepted business events to upstream provenance:
- kind: agent or another explicitly permitted application origin.
- by: actorId.
- at: recordedAt.
- runId: the owning application run.

Preserve occurredAt and historical simulation time in application attributes.
Do not interpret the provenance runId field as an access-control boundary.

## Duplicate handling

Before writing, inspect the existing event entity by its deterministic key.

- Same eventId and identical canonical business content: return the existing
  event without another write.
- Same eventId and different business content: reject the command.
- Unknown eventId: validate the proposed transition before appending.

Assign recordedAt once on first acceptance. A retry must reuse the stored
envelope rather than generate a new acceptance timestamp.

Protocol correlation identifiers do not replace business event identifiers.
The application must define canonical comparison and retry handling precisely
before implementation.

Duplicate checks and writes must run through the same serialized bridge
command path. This does not protect against an independently launched writer.

## Lost acknowledgements and duplicate command order

The application checks caller authorization and run scope before returning
any recorded result.
For an authorized retry, look up the stable logical command or event identity
before rejecting it against the current run revision.
If its immutable original envelope matches an already committed command,
return that command's recorded outcome and accepted revision without a new
mutation or external dispatch. Do not substitute a later run outcome.
Reuse of the identity with different original fields is a conflict.
New commands must pass expected-revision and transition validation.
Recording timestamps assigned by the trusted application are retained,
not regenerated on retry.
The publication adapter must make the reconciliation evidence recoverable.
This is an application contract, not a native World Model guarantee.
Tests for lost acknowledgement, conflicting reuse, and unauthorized access
remain unimplemented.

## State projection

Register an application-owned custom view using the official registerView
interface. Read its result through view().get().

The reducer handles native upsertEntity events containing operation-event
entities and ignores unrelated records.

Reconstruct tasks, attempts, blockers, approvals, planning decisions, and run
state from accepted business events in native append order.

The reducer must be deterministic and perform no network calls, dispatches,
filesystem writes, or wall-clock reads.

Re-register the projection after opening the official store in a new process.
The reference recomputes custom views on read.

The projection is derived state, not a second independently editable store.

## Tasks, dependencies, and blockers

Task-creation events contain explicit dependency references.
Do not encode multiple dependencies using upstream relationship patterns
that close earlier edges.

Blockers have independent identities and lifecycle events.
Resolving one blocker leaves other blockers unchanged.

Preserve attempt history independently from task and operation identity.

Eligibility and transitions are application rules governed by the pinned
workflow. A projection alone does not dispatch work.

## Approvals and tracing

Approval decisions bind to an exact run, task or operation, and requested
action. Technical resolution does not grant approval.

The Tracer verifies required evidence and causal references.
Native mutation audit and business traceability remain distinct.

Rejected commands must not apply their requested transition.
Record their disposition through a defined application event when the run
scope is valid and authorized.

Malformed or unauthorized requests must not create records in a victim run.
Diagnostic handling must avoid secrets and unnecessary personal data.

## Nightshift invocation state

The Analyzer's final demonstration includes an actual Nightshift-backed
analytical operation, as required by decision 0010.

Represent invocation identity, task and attempt linkage, dispatch intent,
response references, validation outcome, and failure or uncertain outcome
through application events.

Keep provider execution separate from event projection.
Reconstruction must not automatically repeat inference.

A response received without recorded completion requires reconciliation.
Do not assume the Runtime provides an idempotency mechanism or permits
retrieval of an earlier response without verifying its contract.

Record requested routing configuration separately from evidence of the
actual serving model. Never include credentials in events.

Exact invocation event schemas remain to be defined.

## Command acceptance and finalization

Serialize commands and check the expected run revision before accepting
a state transition. Record the disposition of obsolete commands without
applying their requested transition.

An accepted cancellation prevents new dispatches.
Late results remain evidence and do not reactivate the run.

Use FINALIZING while reconciling active or uncertain operations.
Finalization does not depend on a business report.

The Tracer checks available evidence and records missing items.
Publish one logical finalization event containing the outcome, traceStatus,
summary references, and reconciliation findings.

COMPLETED requires complete mandatory evidence.
FAILED and CANCELLED may carry traceStatus INCOMPLETE with explicit reasons.
Unresolved external-operation outcomes prevent terminal confirmation.

A finalization identity is stable across retries.
Closed runs cannot be reactivated through ordinary commands.

## Staged publication adapter

Keep official World Model source files unchanged.

For each accepted command:
1. Prepare an isolated working copy from the last committed snapshot.
2. Load and mutate it through the official implementation.
3. Validate the complete candidate, event identity, and expected projection.
4. Preserve a recoverable previous committed snapshot.
5. Synchronize the candidate and atomically replace the committed file on
   the same filesystem.
6. Synchronize publication metadata as required by the target filesystem.
7. Return success only after the commit boundary is confirmed.

Intermediate upstream writes must not modify the committed snapshot.
After an error, discard the working instance and reconcile committed storage
before accepting another mutation.

An error after replacement may leave publication uncertain; do not assume
that an unsuccessful response means no commit occurred.

A restart loads committed storage, not an unverified working copy.
Fail explicitly on invalid committed data rather than silently resetting it.

The adapter's filesystem assumptions, recovery checks, and single-writer
enforcement require implementation and fault-injection tests.

## Recovery boundaries

Opening the official local store replays its recorded native events.
The application then registers its operational projection.

Verify the pinned workflow and ownership context before allowing resume.
Reconstruction must not automatically dispatch pending work.

If an operation result exists without recorded completion, reconcile it before
retrying. This requires separate operation evidence.

The upstream store alone does not establish atomic crash recovery.
The selected staged-publication adapter is intended to protect the committed
snapshot against interrupted working writes; this remains untested.

No distributed locking, exactly-once external execution, or universal
hardware-failure protection is claimed.

## Validation criteria

- Two namespaces reconstruct independent run states.
- Duplicate business events produce no additional native event.
- Conflicting reuse of eventId is rejected.
- Multiple dependencies and blockers survive process restart.
- Resolving one blocker does not resolve another.
- Pending approval remains pending after reconstruction.
- Replay does not invoke agents or external operations.
- Invalid ownership does not expose or modify another run.
- The runtime imports the unchanged official WorldModel implementation.

Memory-only creation/read, duplicates, conflicts, simulated ownership,
protocol correlation, and local closure are tested in report 0005.
Task/blocker/approval workflows, persistent reconstruction, and durable recovery
remain unimplemented and untested.

## Open implementation details

- Durable-store namespace ownership and path validation.
- Exact event catalog and payload schemas.
- Canonical comparison for the remaining event catalog.
- Command validation and projection transition rules.
- Durable protocol recovery and additional fault-injection coverage.
- Operation-result reconciliation storage.
- Maintenance of the verified runtime copy and dependency versions.

## Analyzer request lifecycle

The application records the causal chain from model invocation and tool
request to authorization, data operation, returned result and analysis outcome.

Use the existing business-event envelope. Preserve run, task, attempt and
operation identities; carry invocation, tool-call and data-request references
in the applicable payload. Exact event schemas remain to be implemented.

Only the application command path changes operational state.
The Analyzer cannot bypass authorization or mutate World Model directly.

A waiting Analyzer must not hold an execution lock that prevents the
orchestrator from servicing its data requests. Event projection performs
no collection, inference or dispatch.

Pending and uncertain operations remain subject to the existing reconciliation
and finalization rules. Reconstructing events never reissues tool calls.

See [decision 0011](../decisions/0011-demand-driven-analysis.md).
This lifecycle remains application work, not a native World Model guarantee.
The documented durable-publication design remains pending; immediate delivery
priorities are tracked in [Project status](../PROJECT_STATUS.md).

## Implemented nominal application integration

Report 0014 records the application-owned create_execution and append_event
commands, the Python per-run adapter, nominal task projection and actual CLI.
The commands call the unchanged official World Model, not a replacement engine.
See [report 0014](../validation/reports/0014-world-model-nominal-application.md).

create_execution binds run/user/request, question, explicit provider/source
profile, bounded context and pinned workflow 1.2.0 plus fingerprint.
Legacy create_run remains unchanged and bound to workflow 1.1.0.

append_event validates scope and expected revision. Exact duplicate commands
return their original receipt; conflicting identities and stale new commands
are rejected before mutation. Invalid or lost mutation acknowledgements stop
the client/recorder without automatic resubmission.

Qualification, analysis, delegated SQL and report preparation have distinct
tasks/attempts. Event intents are recorded before protected dispatch. The
official custom view derives current state/history and parent/dependency links.
Uncertain operations remain explicit and cannot be projected as success.

This profile remains memory-only, with 4096-byte frames, 65536-byte responses,
bounded context/payload fields, 512-byte questions and 32 history entries.
These are application limits. A SUCCEEDED nominal projection is not durable
finalization or execution of every JSON workflow policy. Snapshot/restart
recovery and full incident machinery remain unimplemented.

## References

- Nightshift requirements: nightshift-integration-requirements.md
- Project instructions: ../../AGENTS.md
- Workflow design: workflow-and-planner.md
- Decision register: ../decisions/README.md
- World Model review:
  ../references/meterless/world-model/integration-notes.md

## Document history

| Date | Change |
|---|---|
| 2026-10-26 | Defined the proposed per-run event representation, projection, ownership, and recovery boundaries. |
| 2026-10-26 | Clarified documented-contract approval and retained separate implementation approval. |
| 2026-10-26 | Added Nightshift invocation-state and reconstruction boundaries for the Analyzer. |
| 2026-10-26 | Specified report-independent finalization and staged publication with explicit verification limits. |
| 2026-10-26 | Clarified authorized duplicate reconciliation before revision checks and preserved command outcomes. |
| 2026-10-26 | Recorded the implemented E1 protocol and tests while preserving pending durable and workflow requirements. |
| 2026-10-27 | Added the Analyzer request lifecycle, causal trace requirements and prevention of circular waits. |
| 2026-10-27 | Linked the implemented nominal memory-engine path and retained explicit full-workflow and durability limits. |
