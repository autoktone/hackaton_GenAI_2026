# 0007 - Separate reconstruction, recovery, and operation idempotency

- Status: Accepted
- Category: Architecture
- Recorded on: 2026-10-26
- Approval evidence: Project owner's consolidation mission in this conversation.
- Supersedes: None
- Superseded by: None

## Context

A process may stop after an operation produces a result but before task
completion is recorded.

Reconstructing operational state alone cannot determine whether every
external effect occurred or whether repeating an operation is safe.

Completion, timeout, cancellation, and approval events may also compete.

## Decision

Distinguish:
- Logical state reconstruction.
- Durable preservation of events and required metadata.
- Recovery of interrupted orchestration.
- Reconciliation of operations and results already produced.

Keep task identity, attempt identity, and logical operation identity separate.
Changing attemptId does not make an operation idempotent.

Before retrying work with an uncertain outcome, reconcile available operation
and result evidence. Do not repeat the operation blindly.

Define explicit transition rules and a deterministic policy for competing
events. Record the disposition and reason for obsolete or rejected signals
without applying invalid state transitions.

Preserve the run's original inputs and workflow version during recovery.

Do not claim exactly-once external execution merely because state writes or
ingestion are deduplicated.

## Alternatives considered

- Restart every task: may duplicate completed work and external effects.
- Trust reconstructed task status alone: misses results committed before
  completion was recorded.
- Use attemptId as the deduplication key: treats retries as distinct operations.
- Resolve races using producer timestamps alone: does not establish a reliable
  total order or enforce workflow semantics.

## Rationale

Reliable recovery requires evidence about both operational history and
performed operations.

Explicit concurrency policies prevent invalid transitions from depending on
arrival timing or incidental implementation behavior.

## Responsibilities and capability boundaries

World Model supplies only the event, projection, ordering, and persistence
mechanisms verified in the selected implementation.

The application defines transition validation, operation identities,
reconciliation, retry policies, and dispatch recovery.

Source review of the official reference found:
- A write queue per WorldModel instance.
- Event sequence numbers within a namespace.
- Direct JSON-file persistence without an interprocess lock.
- Separate persistence of an event and its audit entry.
- Fact materialization requiring dedicated reconstruction tests.

These findings are not runtime test results.

Do not infer atomic transactions across World Model, dataset storage, result
artifacts, and external services.

## Finalization and durable publication

Use a FINALIZING phase independent of report production.

Stop new dispatches, reconcile outstanding operations, and have the Tracer
produce an execution summary before confirming a terminal outcome.

Keep outcome and traceStatus separate:
- outcome: COMPLETED, FAILED, or CANCELLED.
- traceStatus: COMPLETE or INCOMPLETE.

COMPLETED requires complete mandatory evidence.
FAILED or CANCELLED may retain incomplete evidence with explicit missing items.
Unresolved external-operation outcomes prevent confirmed finalization.

Give finalization a stable logical identity. Repetition returns the recorded
result instead of producing another logical closure.

Serialize commands and validate their expected run revision.
Accepted cancellation prevents new dispatches. Preserve late results as
evidence without reactivating the run.

Apply official World Model writes to an isolated working copy.
Validate the completed candidate snapshot, synchronize it, and publish it
through atomic replacement on the same filesystem.
Preserve a recoverable previously committed snapshot.

Acknowledge success only after publication and required synchronization.
If publication may have occurred without acknowledgement, reconcile the
logical event identity before retrying.

These are application-adapter requirements, not upstream durability guarantees.
They do not establish exactly-once external effects or protection against
every filesystem or hardware failure.

## Consequences and limitations

Operation evidence must identify the logical operation and the relevant input,
dataset, workflow, or algorithm versions affecting its result.

An unresolved outcome may require a blocker or human review rather than an
automatic retry.

Order and scope must be explicit when comparing native events from different
namespaces. No global native sequence is assumed.

Crash recovery, graceful restart, and reconstruction are different guarantees.
Demonstrating one does not establish the others.

The selected prototype uses one bridge process owning all World Model writes,
with one namespace per run. This is an application ownership constraint,
not a verified interprocess lock.

Reconstruction does not automatically dispatch work or repeat inference.
See ../architecture/execution-model.md.

## Assumptions and open questions

- Logical operation-key construction.
- Durable operation and result evidence.
- Reconciliation procedure and uncertain-outcome handling.
- Transition precedence for completion, timeout, cancellation, and approval.
- Enforcement of selected single-writer ownership and rejection of competing
  processes.
- Storage atomicity, corruption detection, and backup strategy.
- Representation of rejected or obsolete signals.
- Recovery of pending dispatches.

Single-writer ownership and staged atomic publication are selected.
These application mechanisms are not implemented or runtime-verified.
The official World Model source remains unchanged.

## Validation criteria

Minimum demonstration:
- Reconstruct operational state in a new process.
- Preserve unresolved blockers, approval requirements, and workflow version.
- Avoid duplicating an already recorded logical event when replayed through
  the application adapter.
- Keep recovered state isolated by run.

Additional validation before claiming stronger recovery:
- Stop after result persistence but before completion recording.
- Reconcile the result without repeating the protected operation.
- Exercise competing completion and timeout signals.
- Verify deterministic transition outcomes under the declared ordering policy.
- Document behavior when persistence is interrupted or corrupted.

Tests have not yet been implemented or executed.
Untested guarantees must remain explicitly unverified.

## References and approval history

- Project instructions: ../../AGENTS.md
- Related decisions:
  - 0002-execution-isolation.md
  - 0003-tasks-attempts-and-blockers.md
  - 0004-versioned-workflows.md
  - 0005-data-responsibilities.md
  - 0006-data-freshness-and-selective-collection.md
- Decision source: project owner's requirements on interruption, uncertain
  outcomes, idempotency, concurrent events, persistence, and reproducibility.
- Concrete mechanisms require separate approval.

## Record history

| Date | Change |
|---|---|
| 2026-10-26 | Recorded recovery, idempotency, and concurrency requirements; technical mechanisms remain open. |
| 2026-10-26 | Consolidated selected design choices and retained only unresolved implementation questions. |
| 2026-10-26 | Specified report-independent finalization and staged publication with explicit verification limits. |
