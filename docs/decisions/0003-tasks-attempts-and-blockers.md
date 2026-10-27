# 0003 - Track tasks, attempts, and blockers independently

- Status: Accepted
- Category: Functional
- Recorded on: 2026-10-26
- Approval evidence: Project owner's consolidation mission in this conversation.
- Supersedes: None
- Superseded by: None

## Context

A run may contain multiple active tasks. A shared agent may execute several
tasks across different runs.

A task may encounter multiple blockers, require human approval, produce a
partial result, or need several execution attempts.

One global status per agent or run cannot represent these situations.

## Decision

Represent tasks, attempts, and blockers as distinct concepts, each associated
unambiguously with its owning run.

A task represents concrete work associated with a workflow step.
An attempt represents one execution attempt for that task.
A blocker represents an individually identifiable condition preventing progress.

Keep task identity, attempt identity, and logical operation identity distinct.
A new attempt must not automatically repeat an operation already performed.

A blocker records at least:
- Its identity and affected task.
- Its cause and appearance time.
- Its resolution status.
- Its resolution action or procedure when applicable.

Resolving one blocker must not resolve other blockers implicitly.

Task eligibility depends on all applicable conditions:
- Workflow dependencies.
- Active blockers.
- Required human authorization.
- Permitted task and run lifecycle transitions.

Distinguish a blocked task, an unmet dependency, an unavailable agent, and
an action awaiting approval.

Agent availability is separate from the status of its assigned tasks.

Derive run status from its tasks and workflow rules. Do not treat a run as
a single independently editable status.

## Alternatives considered

- One status per agent: confuses resource availability with task progress.
- One blocker field per task: loses simultaneous incidents and approvals.
- Treating retries as new unrelated tasks: loses execution lineage.
- Automatically resuming after any blocker resolution: unsafe while other
  preconditions remain unsatisfied.

## Rationale

Independent records support explainable progress, targeted resolution,
controlled retries, and reconstruction after interruption.

## Responsibilities and capability boundaries

The application defines task transitions, dependency checks, blocker handling,
attempt policies, and approval requirements.

World Model provides generic records and events through its verified
interfaces. It is not assumed to provide native task, blocker, or workflow
semantics.

The reference implementation supersedes some relationships sharing the same
origin, type, and context. Do not encode multiple dependencies or blockers
using a relationship pattern that silently closes earlier links.

Represent business events as externally keyed operation-event entities and
derive operational state through an application-owned World Model projection.

Task dependencies are explicit references in task-creation events.
Blocker lifecycle events preserve independent blocker identities.
See ../architecture/execution-model.md.

## Consequences and limitations

Several simultaneous blockers must remain visible after reconstruction.

Resolving a technical incident must not constitute human authorization.
An approval applies only to its specified run, task or operation, and action.

The prototype may simulate agents and incidents. Simulation does not prove
production scheduling, timeout monitoring, or recovery of external effects.

## Assumptions and open questions

- Task and attempt status vocabulary and permitted transitions.
- Blocker lifecycle and resolution evidence.
- Ordering of competing completion, timeout, cancellation, and approval events.
- Handling of partial results and terminal runs.
- Logical operation keys and reconciliation after interruption.

The event-based representation is selected. Exact payload schemas and
transition algorithms remain to be defined and tested.

## Validation criteria

- Hydro retains two distinct active blockers.
- Resolving its network blocker leaves its approval blocker active.
- Restart preserves tasks, attempts, and unresolved blockers.
- No task resumes while a required blocker or authorization remains unresolved.
- A blocked task does not make its agent unavailable for unrelated work.
- Changes remain isolated to the owning run.
- Attempt history remains associated with the original task.

Tests have not yet been implemented or executed.

## References and approval history

- Project instructions: ../../AGENTS.md
- Related decision: 0001-meterless-world-model.md
- Related decision: 0002-execution-isolation.md
- Decision source: project owner's requirements on multiple tasks, blockers,
  attempts, human approvals, and recovery.
- Detailed event schemas and implementation operations require separate approval.

## Record history

| Date | Change |
|---|---|
| 2026-10-26 | Recorded accepted task, attempt, and blocker requirements; technical representation remains open. |
| 2026-10-26 | Consolidated selected design choices and retained only unresolved implementation questions. |
