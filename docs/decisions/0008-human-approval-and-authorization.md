# 0008 - Scope human approval to explicit operations

- Status: Accepted
- Category: Security
- Recorded on: 2026-10-26
- Approval evidence: Project owner's consolidation mission in this conversation.
- Supersedes: None
- Superseded by: None

## Context

The project requires human control over development operations and explicit
approval gates within application workflows.

These are separate authorization boundaries.

## Decision

### Development operations

Codex must obtain explicit approval before every command, file read, network
request, installation, file change, Git operation, program execution, or test.

Before acting, present the purpose, exact command or proposed changes,
expected effects, risks, and acceptance criteria.

Approval covers only the stated operation. Do not infer authorization for
subsequent actions or use permanent command permissions as human approval.

Do not begin the next project stage without validation.

Do not modify getting-started or zetaris-platform.
Consulting either directory also requires prior approval.

### Application workflow approvals

Associate each approval request and decision with:
- The owning run.
- The affected task or logical operation.
- The precise requested action.
- The authorized decision-maker.
- The decision and its timestamp.

Use actorId to identify the decision-maker. Record the relevant execution
context and action parameters so that approval cannot authorize a different
operation implicitly.

Approval for one run does not authorize the same action in another run.

Resolving a technical blocker does not grant human approval.
Refusal or missing approval must not permit the protected action.

The prototype may use a fictional user and simulated authorization checks.
Do not present these checks as production authentication or authorization.

## Alternatives considered

- Blanket approval for an entire development stage: incompatible with the
  required operation-by-operation policy.
- One approval flag per user or agent: insufficiently scoped.
- Treating incident resolution as approval: confuses technical readiness
  with permission.
- Assuming World Model contexts provide authorization: unsupported.

## Rationale

Explicit scope prevents accidental reuse of permission across operations,
tasks, or executions and preserves an understandable decision trail.

## Responsibilities and capability boundaries

Project instructions govern Codex development operations.

The application validates workflow permissions before dispatching protected
actions and records decisions through verified persistence mechanisms.

World Model may represent approval records and events. It is not assumed
to identify users, authenticate actors, enforce access policies, or provide
tamper-proof approval evidence.

Zetaris permissions govern access through Zetaris credentials. They do not
replace application permissions for requests, runs, or result ownership.

## Consequences and limitations

An approval recorded in the prototype does not change Codex's development
permissions. Conversational approval does not automatically satisfy an
application workflow approval.

Reconstruction must preserve pending decisions and their scope.
Recovery must not treat an unresolved approval as granted.

Changes to a protected action require checking whether existing approval
still covers the exact operation. The binding mechanism remains open.

Store technical identifiers required for traceability without unnecessary
personal data. Do not store IP addresses or secrets in World Model events.

## Assumptions and open questions

- Approval request and decision schema.
- Allowed decision vocabulary.
- Authorization policy for fictional actors.
- Binding approval to operation parameters and versions.
- Expiry, revocation, and conflicting decisions.
- Persistence and reconstruction of approval history.

No production identity provider or authorization framework is selected.

## Validation criteria

- A task remains blocked when approval is absent.
- A refusal does not trigger the protected operation.
- Approval is restricted to the specified run and operation.
- Resolving another blocker does not clear the approval requirement.
- Restart preserves pending approval and recorded decisions.
- Shared agents cannot reuse an approval from another run.
- Logs contain decision identifiers and reasons without credentials or IP
  addresses.

Tests have not yet been implemented or executed.

## References and approval history

- Project instructions: ../../AGENTS.md
- Related decisions:
  - 0002-execution-isolation.md
  - 0003-tasks-attempts-and-blockers.md
  - 0004-versioned-workflows.md
  - 0007-recovery-idempotency-and-concurrency.md
- Decision source: project owner's requirements on operation-by-operation
  approval, workflow authorization, traceability, and confidentiality.

## Record history

| Date | Change |
|---|---|
| 2026-10-26 | Recorded development and workflow approval boundaries; implementation mechanisms remain open. |
