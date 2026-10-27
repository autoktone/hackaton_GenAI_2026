# 0001 - Prioritize Meterless World Model

- Status: Accepted
- Category: Architecture
- Recorded on: 2026-10-26
- Approval evidence: Project owner's consolidation mission in this conversation.
- Supersedes: None
- Superseded by: Decision 0010 only regarding deferred Nightshift integration.

## Context

The first demonstration needs independent analysis runs, identifiable tasks,
multiple blockers, human approval, and reconstruction after restart.

The hackathon schedule requires a limited, verifiable integration.

## Decision

Prioritize Meterless World Model for the first integration, subject to
verification of its technical feasibility.

Defer H-MEM, Markovian, and Scout Intent integration.

Nightshift is required as the primary AI provider under decision 0010.
The Analyzer must make an identifiable analytical contribution through it.
World Model remains responsible for operational representation.

This decision selects the engine. It does not select a Python implementation,
bridge protocol, persistence design, or orchestration framework.

## Alternatives considered

- H-MEM: useful later for reusable knowledge, conclusions, and provenance.
- Markovian: potentially useful for bounded reasoning context in long runs.
- Scout Intent: potentially useful for intent routing and action controls.
- Combining engines immediately: deferred to limit integration and validation
  scope.

Data freshness and calculation reuse primarily require collection metadata
and technical caching, rather than agent memory.

## Rationale

Operational state is the immediate demonstration priority.
World Model provides a relevant representation architecture and an executable
reference that must be evaluated against our requirements.

## Responsibilities and capability boundaries

- World Model represents supported operational records and projections.
- Workflow definitions specify permitted procedures and versions.
- The Planner determines necessary actions using explicit rules.
- The orchestrator executes, supervises, and applies incident policies.
- Durable storage preserves information required for reconstruction.
- Zetaris is planned for business data and collection metadata.

Do not attribute scheduling, authorization, timeout monitoring, or safe
external-effect recovery to World Model without verified support.

The initial demonstration uses fictional data and deterministic behavior.
It does not demonstrate hydrological forecasting validity.

## Consequences and limitations

An effective Meterless integration must call the official reference or
demonstrate conformity of an alternative implementation.

Source review has identified specification/reference differences and
persistence limitations. No official or application tests have been executed.

Passing upstream conformance alone will not prove run isolation, recovery,
or application correctness.

Current consolidation update: decision 0009 selects the Python bridge to
the official TypeScript reference. The operational representation is
documented in ../architecture/execution-model.md.
These selections are not implemented or runtime-validated.

## Assumptions and open questions

- Runtime suitability of the selected official reference.
- Detailed bridge protocol and event validation.
- Remaining transition and terminal tracing rules.
- Persistence and recovery guarantees demonstrated by actual tests.

## Validation criteria

- Identify the upstream revision and preserve reference provenance.
- Document specification, implementation, application, and simulation boundaries.
- Verify an actual runtime path through the selected Meterless implementation.
- Execute applicable upstream and application tests after separate approval.

## References and approval history

- Project instructions: ../../AGENTS.md
- Upstream revision:
  https://github.com/Meterless/Meterless/tree/1742dec56a66e58eef9dda2d2b865823758ca8cd/engines/world-model
- Decision source: project owner's mission explicitly prioritizing World Model.
- The bridge direction and operational representation are selected;
  detailed implementation and execution still require approval.

## Record history

| Date | Change |
|---|---|
| 2026-10-26 | Recorded the initial World Model selection and deferred integrations. |
| 2026-10-26 | Linked decision 0010, which replaces only the Nightshift deferral. |
| 2026-10-26 | Linked subsequent bridge and operational-model selections while preserving their implementation limits. |
| 2026-10-26 | Consolidated selected design choices and retained only unresolved implementation questions. |
