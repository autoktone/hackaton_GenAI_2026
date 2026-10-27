# 0002 - Isolate operational state by execution

- Status: Accepted
- Category: Architecture
- Recorded on: 2026-10-26
- Approval evidence: Project owner's consolidation mission in this conversation.
- Supersedes: None
- Superseded by: None

## Context

Multiple requests and executions may use the same agents, datasets,
collection results, and cached calculations.

Sharing resources must not mix operational state or expose another user's
analysis results.

## Decision

Each run has independent operational state.

One user may submit multiple simultaneous requests, each with independent
runs. This also applies across users and across matching or different zones
and periods. userId and data-selection parameters are not execution-state keys.
A request may have multiple runs; shared data does not merge their state.

Associate tasks, attempts, blockers, approvals, decisions, operational events,
and result references unambiguously with their owning run.

Keep the following conceptual identities distinct:
- userId: request owner.
- requestId: logical business request.
- runId: a particular execution of a request.
- workflowId and workflowVersion: governing workflow definition.
- workflowInstanceId: workflow instance; equivalence with runId remains open.
- stepId: step in a workflow definition.
- taskId: concrete task in a run.
- attemptId: execution attempt for a task.
- agentId: agent type or instance; its precise representation remains open.
- eventId: recorded event.
- actorId: author of an action or decision.
- blockerId: individually tracked blocker.

An agent may serve multiple tasks and runs. Agent identity is not task
identity, and step identity is not task identity.

Resource reuse does not grant access to another run's operational information
or results.

Use one fictional user for the initial demonstration. Defer production
identity management and multi-tenant authentication.

## Alternatives considered

- One global mutable agent status: insufficient for concurrent tasks and runs.
- One status row per run: insufficient for multiple tasks and blockers.
- Fully separate deployments per run: unnecessary for the initial prototype.

## Rationale

Explicit ownership makes independent execution, audit, reconstruction, and
future access controls possible without requiring separate agent processes.

## Responsibilities and capability boundaries

The application validates ownership and permitted access before invoking
World Model.

Use one namespace per run, as documented in
../architecture/execution-model.md.

Namespace separation does not provide authentication or authorization.
The application validates ownership before accessing a run.

The upstream reference orders events within a namespace and serializes writes
per instance. This does not establish isolation across users or safe concurrent
writers in separate processes.

Shared data and collection operations require references back to each
requesting run without transferring ownership of operational state.

## Consequences and limitations

All operational reads and writes need an explicit execution scope.

Qualify native event identifiers by namespace when referenced globally.
Keep business event identities distinct from native event identities.

The first demonstration will not establish production security or distributed
concurrency guarantees.

## Assumptions and open questions

- Mapping application identities to upstream entities, contexts, and keys.
- Validation of namespace names and storage paths.
- Agent type versus agent instance representation.
- Ownership enforcement and scope of shared collection metadata.
- Exact identity and deduplication rules for business and native events.

The per-run namespace boundary is selected. Detailed identity validation,
authorization enforcement, and event schemas remain open.

## Validation criteria

- RUN-001 and RUN-002 retain independent tasks, events, blockers, and approvals.
- Resolving or approving an action in one run does not change the other.
- Reconstruction preserves ownership and execution scope.
- Shared agents and datasets do not merge operational records.
- Requests outside the permitted owner scope are rejected in the prototype's
  simulated access checks.

Memory-only run separation, overlapping same-user creation calls, and simulated
owner checks passed in [report 0005](../validation/reports/0005-python-world-model-memory-bridge.md).
Task/blocker/approval isolation, persistent reconstruction, and multi-user
workflow concurrency remain unimplemented and untested.

## References and approval history

- Project instructions: ../../AGENTS.md
- Related decision: 0001-meterless-world-model.md
- Upstream candidate revision:
  https://github.com/Meterless/Meterless/tree/1742dec56a66e58eef9dda2d2b865823758ca8cd/engines/world-model
- Decision source: project owner's requirements on identification, isolation,
  resource sharing, and authorization boundaries.
- Selected representation: ../architecture/execution-model.md
- Detailed mechanisms and implementation operations require separate approval.

## Record history

| Date | Change |
|---|---|
| 2026-10-26 | Recorded accepted execution-isolation requirements; implementation choices remain open. |
| 2026-10-26 | Consolidated selected design choices and retained only unresolved implementation questions. |
| 2026-10-26 | Clarified multiple concurrent requests per user and recorded the bounded E1 isolation evidence. |
