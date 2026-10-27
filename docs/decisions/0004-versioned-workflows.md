# 0004 - Use explicit versioned workflows

- Status: Accepted
- Category: Architecture
- Recorded on: 2026-10-26
- Approval evidence: Project owner's consolidation mission in this conversation.
- Supersedes: None
- Superseded by: None

## Context

Analysis runs require explicit dependencies, permitted adaptations, incident
procedures, and reproducible execution rules.

Workflow definitions, planning decisions, execution control, and operational
state are separate responsibilities.

## Decision

Use the predefined deterministic JSON workflow flood-analysis version 1.1.0
as the current intermediate verification baseline.

The definition is stored in ../../workflows/flood-analysis/1.1.0.json.
Preserve version 1.0.0 as the previous baseline.
Version 1.1.0 adds report-independent finalization and terminal trace review.
It disables automatic retries and partial completion, requires explicit resume,
and permits at most two collection attempts per task.

A separately versioned final workflow must include the Analyzer's required
Nightshift contribution and real-data access through Zetaris.

Each run references a workflow definition and its version. Preserve that
version during reconstruction and resume. A later definition change must not
silently change an existing run.

Workflow definitions describe:
- Steps, dependencies, and permitted parallelism.
- Required inputs and activation conditions.
- Success criteria and permitted partial results.
- Alternative paths and termination conditions.
- Retry, failure, cancellation, and human-approval policies.

The Planner determines necessary actions using explicit permitted rules.
It may reuse valid data, request missing coverage, or wait for an existing
collection operation. Record its decisions and their reasons.

The orchestrator interprets the workflow, checks preconditions, dispatches
authorized actions, and applies progression and incident policies.

World Model represents supported operational records and reconstructs state
within verified contracts. Do not assume it supplies a workflow engine.

Planner and orchestrator may share one component in the initial prototype.

Defer LLM-generated workflows and workflow-version migrations.

## Alternatives considered

- Implicit procedure distributed across agents: difficult to inspect and replay.
- State transitions alone: insufficient to describe the governing procedure.
- Dynamic LLM workflow composition: unnecessary for the initial scenario.
- A full BPMN engine or additional orchestration framework: not selected;
  any introduction requires separate justification and approval.

## Rationale

Explicit versioned procedures make planning adaptations inspectable and
prevent silent behavior changes when interrupted runs resume.

## Responsibilities and capability boundaries

Workflow semantics, dependency evaluation, dispatch, timeouts, escalation,
and approval enforcement belong to the application unless upstream support
is specifically verified.

The upstream reference's write serialization is not a task scheduler.
Serializing state writes does not require all business tasks to run serially.

The demonstration may simulate task execution and incident signals.
It must identify which workflow and state mechanisms execute for real.

## Consequences and limitations

Record the workflow identity and version with each run.

Retain the exact definition, or an immutable retrievable reference plus an
integrity identifier, needed to reproduce the run.

Adaptations must remain within workflow rules and be traceable.
An incident cannot authorize an otherwise prohibited action.

Historical replay also requires appropriate input and dataset versions;
workflow versioning alone is insufficient.

## Assumptions and open questions

- Workflow schema, validation, and integrity identifier.
- Mapping step definitions to concrete tasks and attempts.
- Deadline handling and policies beyond the recorded baseline.
- Terminal tracing after failure or cancellation without a completed report.
- Exact AI-powered analysis step and final workflow version.
- Handling obsolete concurrent events and terminal-state transitions.
- Persistence and reconstruction of pending dispatch decisions.

The JSON baseline and its declared policies are selected.
Semantic validation, execution, and remaining policies are not implemented.

## Validation criteria

- An analysis waits for its required dependencies.
- Planner adaptations are permitted, justified, and recorded.
- Human approval gates remain enforced during resume.
- Restart retains the workflow identity and original version.
- Changing the available workflow definition does not silently alter a
  previously started run.
- Workflow rules determine whether partial completion is permitted.

Tests have not yet been implemented or executed.

## References and approval history

- Project instructions: ../../AGENTS.md
- Related decisions:
  - 0001-meterless-world-model.md
  - 0002-execution-isolation.md
  - 0003-tasks-attempts-and-blockers.md
- Decision source: project owner's requirements on workflow definition,
  planning, orchestration, versioning, incidents, and resume.

## Record history

| Date | Change |
|---|---|
| 2026-10-26 | Recorded accepted workflow and responsibility boundaries; implementation mechanisms remain open. |
| 2026-10-26 | Consolidated selected design choices and retained only unresolved implementation questions. |
| 2026-10-26 | Aligned the current deterministic workflow reference with version 1.1.0 and preserved version 1.0.0. |
