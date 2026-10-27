# 0006 - Check data validity before selective collection

- Status: Accepted
- Category: Functional
- Recorded on: 2026-10-26
- Approval evidence: Project owner's consolidation mission in this conversation.
- Supersedes: None
- Superseded by: None

## Context

Different runs may require overlapping observations.
Collecting everything for every request wastes resources and does not
guarantee that observations are sufficiently recent or complete.

Historical replay requires information available at the simulated time,
rather than everything available today.

## Decision

Before requesting collection, the Planner evaluates:
- Source and geographic scope.
- Requested period and actual coverage, including gaps.
- Latest available observation and last retrieval.
- Applicable freshness policy and analysis mode.
- Quality, usability, and dataset version.
- Parameters required by the analysis.
- Publication or availability time when relevant.

A recent retrieval does not prove recent observations.
Old historical observations may remain valid for historical analysis.

Permit deterministic decisions to:
- Reuse compatible valid data.
- Collect only missing intervals.
- Refresh expired or otherwise invalid data.
- Wait for a compatible collection already in progress.
- Report unavailable or insufficient data.
- Propose partial analysis only when the workflow permits it.

Record each decision, its reasons, and relevant dataset or collection
references in the operational history.

Persist collection metadata independently of individual run state.

## Shared collection operations

Provide a minimal mechanism to avoid duplicate compatible collections
already in progress.

The collection key must account for source, geographic scope, period, and
parameters affecting the collected result.

Sharing an operation must not merge run ownership, tasks, approvals,
or operational events.

A run waiting for shared work remains independently identifiable.
Its cancellation must not implicitly cancel work still needed by another run.

Exact-match deduplication is sufficient for the first prototype.
Overlapping-interval coalescing is not required initially.

## Alternatives considered

- Always collect: creates unnecessary requests and ignores reusable coverage.
- Use last retrieval time alone: confuses collection activity with data recency.
- Use one validity rule for all sources and modes: unsuitable for historical
  and current analysis.
- Use agent memory as the catalog: insufficient for deterministic validity
  and coverage checks.

## Rationale

Explicit validity checks make collection decisions reproducible and reduce
redundancy without compromising execution isolation.

## Responsibilities and capability boundaries

The data catalog supplies persistent metadata and dataset references.
The Planner evaluates policy.
The orchestrator coordinates authorized collection and waiting runs.
World Model records supported operational decisions and state.

Do not assume World Model provides a dataset catalog, collection lock,
freshness evaluator, or distributed deduplication service.

Use fictional collection for early increments and reproducible tests.
Final project validation additionally requires real observations accessed
through the application and Zetaris.

The accepted temporal and fixture-validity contract is documented in
../architecture/analysis-input-and-data-validity.md.

## Consequences and limitations

Coverage must represent gaps, not only minimum and maximum timestamps.

Collection metadata should distinguish:
- Observation time.
- Publication or availability time.
- Retrieval time.
- Dataset version.
- Coverage and quality information.
- Applicable validity or expiry information.

Missing availability history must be reported as a limitation for backtests,
not replaced silently by observation time.

Cache and collection identities are separate from task and attempt identities.

Coverage intervals use inclusive start and exclusive end.
The fictional freshness thresholds and strict historical-availability policy
are accepted for controlled tests, not for unverified use with real sources.

## Assumptions and open questions

- Source-specific validity policies and expiry calculation.
- Metadata schema and persistent storage.
- Geographic coverage matching and source-specific sampling cadence.
- Collection-key canonicalization.
- Coordination and recovery of abandoned in-progress collections.
- Verification that recorded coverage corresponds to usable stored data.
- Publication history and revision handling for historical replay.

No storage, lock, or collection-key implementation is selected here.

## Validation criteria

- Missing data triggers a simulated collection.
- An identical subsequent request reuses valid data without another collection.
- A partially uncovered period requests only missing coverage.
- Recent retrieval of stale observations is not treated as fresh data.
- Two runs needing the same compatible collection do not launch duplicate work.
- Collection decisions and reasons remain associated with each run.
- Simulated behavior is distinguished from actual data-source integration.

Tests have not yet been implemented or executed.

## References and approval history

- Project instructions: ../../AGENTS.md
- Related decisions:
  - 0002-execution-isolation.md
  - 0004-versioned-workflows.md
  - 0005-data-responsibilities.md
- Decision source: project owner's requirements on freshness, selective
  collection, shared collection operations, and historical availability.
- Approval evidence for exact-match deduplication and shared-cancellation
  boundaries: Ok.

## Record history

| Date | Change |
|---|---|
| 2026-10-26 | Recorded validity and selective-collection requirements; implementation mechanisms remain open. |
| 2026-10-26 | Consolidated selected design choices and retained only unresolved implementation questions. |
