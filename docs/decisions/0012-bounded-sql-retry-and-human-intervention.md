# 0012 - Bound read-only SQL retries and request human intervention

- Status: Accepted
- Category: Application reliability
- Recorded on: 2026-10-27
- Approval evidence: Ok; explicit owner approval of workflow 1.3, two SQL attempts, human intervention and backend provenance.
- Supersedes: None; refines ADR 0007 for controlled read-only result acquisition.
- Superseded by: None

## Context

Workflow 1.2.0 prohibits automatic retries. The owner observes intermittent
Zetaris availability and requires a second bounded attempt before human
intervention. This must not create inconsistent task identities or cause
additional inference solely to manage an infrastructure incident.

## Decision

Preserve workflows 1.1.0 and 1.2.0. Add explicit workflow 1.3.0 for the
hydrological CLI. Legacy callers default to 1.2.0.

The application orchestrator may repeat one admitted read-only SQL operation
once after a transient HTTP error or an uncertain transport outcome.
Each attempt has a distinct attemptId and, for the live adapter, REST queryId.
The logical operationId and taskId remain stable. Record failed attempts,
retry intent, dispatched SQL and selected result provenance.

This narrow uncertain-outcome exception applies only to the existing
side-effect-free SELECT grammar on authorized tables/views. It does not
authorize replaying writes, inference, collection side effects or arbitrary
SQL. It records the uncertainty before a fresh read; it does not establish
that the previous server query was cancelled or completed exactly once.

Use a fixed 0.25-second backoff within the remaining analysis time.
At most two logical tool reads and four physical SQL attempts are permitted
by the current hydrological Analyzer limits.

Do not retry authentication/authorization failures, generic non-transient
HTTP errors or invalid result shapes blindly. Request human intervention
when a dispatched read cannot be completed under the policy or time budget.

An empty successful result is not a transport failure and does not trigger
an automatic retry. Its coverage must be evaluated separately.

On unresolved failure, stop the Analyzer before another inference dispatch
and return WAITING_HUMAN with the owning user/request/run/task/operation,
attempt, reason, requested action and intervention identity.
No extra Nemotron call is required for infrastructure escalation.

The actual World Model reference stores the application-owned records and
projection. Retry decisions, classification, timing and human escalation
belong to the application, not to a native Meterless scheduler.

## Generated results and evidence

Preserve a nonempty generated hydrological answer even if it omits exact
receipt strings. Attach the actual tool datasets/provenance in the structured
result. Flag toolResultReferenced=false when citations are incomplete.
provenanceAttached=true does not establish scientific or factual validation.
Keep domainValidated=false and runtimeJudge=not_established.

The original SELECT-one probe retains its stricter protocol check.

## Alternatives and rationale

- Abort on the first technical error: rejected for transient availability.
- Unlimited retries: rejected because of time, resource and duplicate-operation risk.
- Ask Nemotron to manage infrastructure incidents: rejected; the application owns them.
- Require generated text to repeat every UUID: rejected as the sole acceptance
  condition for useful text; backend provenance is a separate explicit artifact.

## Limits and deferred work

The supported World Model profile remains in memory. WAITING_HUMAN returns
an actionable request and prevents new dispatches; durable restart/resume,
interactive approval UI and production authorization are not implemented here.
An operator may check the source and explicitly start another run.
Do not claim automatic continuation, write idempotency or full JSON-policy execution.

## Validation

Implementation checks must cover first-failure recovery, exhausted retries,
non-retryable errors, bounded time, distinct attempts under one operation,
same-user run isolation, blocked post-intervention dispatch and preservation
of earlier workflow contracts. Record executed results in the validation register.

## References

- [Recovery and operation idempotency](0007-recovery-idempotency-and-concurrency.md)
- [Scoped approvals](0008-human-approval-and-authorization.md)
- [Demand-driven analysis](0011-demand-driven-analysis.md)
- [Project status](../PROJECT_STATUS.md)

## History

- 2026-10-27: Accepted the owner-approved bounded SQL-read policy and backend provenance behavior while preserving legacy workflow versions.
