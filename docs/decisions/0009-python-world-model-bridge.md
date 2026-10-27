# 0009 - Bridge Python to the official World Model reference

- Status: Accepted
- Category: Technical
- Recorded on: 2026-10-26
- Approval evidence: Ok (explicit project-owner approval in this conversation).
- Supersedes: None
- Superseded by: None

## Context

The application uses Python. The selected upstream World Model reference
uses TypeScript and exposes no verified Python interface.

Source review identified useful event and projection primitives, together
with persistence limitations and specification differences.

Available tooling:
- Python 3.14.4
- Node.js 22.22.1 on Linux
- npm 10.9.2 in the project cache

The locked installation and official suites passed; see [report 0004](../validation/reports/0004-world-model-reference-execution.md).
The E1 memory bridge passed 9 standalone and 10 actual-engine integration tests;
see [report 0005](../validation/reports/0005-python-world-model-memory-bridge.md).
These results do not establish durable recovery or application workflows.

## Decision

Use the official TypeScript reference at revision:
1742dec56a66e58eef9dda2d2b865823758ca8cd

Preserve upstream implementation files unchanged.

Create a separate runtime copy rather than installing dependencies into
the documentation reference collection.

Add an application-owned TypeScript bridge that imports the upstream
WorldModel class.

Call the bridge from Python through a local subprocess using newline-delimited
JSON messages over standard input and standard output.

Do not add an HTTP server or rewrite the engine in Python for the first
demonstration.

The operational representation is defined in
../architecture/execution-model.md.
Dependency installation and implementation operations require separate approval.

## Alternatives considered

- A custom Python implementation: requires reproducing upstream behavior
  and demonstrating conformity through an additional compatibility boundary.
- An HTTP service: introduces network configuration and service lifecycle
  management without an immediate demonstration requirement.
- A new subprocess for every write: increases overhead and complicates
  ownership of concurrent writes.
- Installing directly in the documentation copy: mixes immutable references
  with runtime artifacts.

## Rationale

A narrow subprocess boundary allows Python application logic to invoke
the actual reference implementation.

Keeping the upstream source unchanged makes integration provenance and
comparison with official tests easier to demonstrate.

## Responsibilities and capability boundaries

The upstream reference handles only its implemented records, events,
projections, and persistence mechanisms.

The application bridge validates its protocol and exposes a restricted set
of supported operations.

Python application components implement workflow rules, planning, scoped
approval, transition validation, operation reconciliation, and data reuse.

Subprocess communication does not itself establish authorization,
idempotency, transactionality, or safe recovery.

## Process and protocol boundaries

For the initial demonstration, use one application process and one bridge
process owning all World Model writes.

The bridge may manage separate WorldModel instances where justified by the
subsequent execution-isolation design.

Do not permit independently launched writers to share a local namespace file.
This ownership rule is an application constraint, not an upstream lock.

Protocol messages should include a correlation identifier.
Distinguish protocol correlation from requestId, runId, and eventId.

Reserve standard output for protocol responses.
Use standard error for diagnostics without secrets or unnecessary personal data.

Use explicit commands and structured arguments, not shell-generated commands
containing user input.

Keep the bridge command surface restricted. Do not expose arbitrary code
execution or unrestricted filesystem paths.

## Persistence and recovery limitations

The upstream local store writes JSON directly and has no verified
interprocess locking or atomic replacement mechanism.

Do not claim resilience to interrupted file writes or exactly-once external
operations.

Test reconstruction in a new process using the selected representation.
Handle uncertain subprocess outcomes explicitly rather than retrying writes
blindly.

Pending protocol requests and external effects require application recovery
rules beyond the engine's state reconstruction.

## Consequences and costs

The prototype requires a Node runtime alongside Python.

A separate dependency installation and official test execution need approval.
The runtime copy and its provenance need explicit maintenance.

The bridge adds protocol validation, error handling, lifecycle management,
and integration tests, but avoids reimplementing the engine.

No additional orchestration framework is selected.

Current consolidation update: ../architecture/execution-model.md selects
one namespace per run and application-owned business-event projections.
Namespace validation, exact event schemas, and protocol behavior remain open.

## Assumptions and open questions

- Maintenance of the recorded runtime copy and pinned provenance.
- Compatibility of future toolchain changes beyond the verified locked baseline.
- Extension of the verified memory protocol to operational task events and durable recovery.
- Namespace ownership and validation for the future durable store.
- Remaining task, blocker, approval, and finalization event schemas.
- Restart reconciliation and handling of incomplete responses.
- Implementation and fault-injection testing of the selected staged-publication design.

## Validation criteria

- Verify runtime source fingerprints against the pinned reference collection.
- Run applicable official tests against the actual runtime implementation.
- Demonstrate Python requests reaching the imported WorldModel class.
- Reconstruct operational state after restarting the bridge process.
- Preserve independent execution state and multiple blockers.
- Reject malformed or unsupported protocol operations without state changes.
- Keep diagnostics separate from protocol output.
- Report untested persistence and concurrency guarantees explicitly.

The official runtime and E1 memory bridge are installed and tested.
The runtime copy is vendor/meterless/world-model and the recorded file set
contains 24 unchanged reference files, plus separately installed dependencies.
Durable storage, reconstruction after restart, and application workflows
remain unimplemented and untested.

## References and approval history

- Project instructions: ../../AGENTS.md
- Related decisions:
  - 0001-meterless-world-model.md
  - 0002-execution-isolation.md
  - 0007-recovery-idempotency-and-concurrency.md
  - 0008-human-approval-and-authorization.md
- Source review:
  ../references/meterless/world-model/integration-notes.md
- Provenance:
  ../references/meterless/world-model/provenance.json
- Strategy accepted by the project owner; implementation operations require separate approval.

## Record history

| Date | Change |
|---|---|
| 2026-10-26 | Proposed a local Python-to-TypeScript bridge using the unchanged official reference. |
| 2026-10-26 | Accepted the bridge strategy; installation and implementation remain subject to separate approval. |
| 2026-10-26 | Linked the selected execution model and narrowed the remaining integration questions. |
| 2026-10-26 | Consolidated selected design choices and retained only unresolved implementation questions. |
| 2026-10-26 | Updated verified Linux tooling and memory-bridge status without changing the accepted bridge architecture. |
