# 0005 - Separate data, collection metadata, operational state, and knowledge

- Status: Accepted
- Category: Architecture
- Recorded on: 2026-10-26
- Approval evidence: Project owner's consolidation mission in this conversation.
- Supersedes: None
- Superseded by: None

## Context

Analysis runs need business observations, availability information,
operational records, and potentially reusable knowledge.

These categories have different ownership, retention, access, and
reconstruction requirements.

## Decision

Separate four categories:

1. Business data: weather and hydrological observations, historical series,
   and dataset versions.
2. Collection metadata and technical cache: coverage, observation and retrieval
   times, availability, quality, freshness policies, and reusable result references.
3. Operational state: tasks, dependencies, attempts, blockers, approvals,
   Planner decisions, events, and execution result references.
4. Reusable knowledge: conclusions, hypotheses, corrections, and experience
   selected for reuse across analyses.

Use Zetaris as the planned access layer for business data and collection
metadata. Determine the underlying writable storage after technical verification.

Use World Model for operational representation and reconstruction within its
verified contracts.

Defer H-MEM and reusable-knowledge integration.

Do not copy complete measurement series or calculation outputs into agent
memory merely to make them available to agents.

Reference datasets and result artifacts by stable identity and version.
Record the versions actually used by each run.

## Alternatives considered

- Store every category in World Model: duplicates business data and conflates
  operational history with dataset management.
- Use H-MEM for freshness and calculation reuse: confuses knowledge retrieval
  with deterministic cache validity.
- Keep availability metadata only in process memory: prevents reliable reuse
  across sessions.
- Duplicate datasets per run: unnecessary when references and access boundaries
  can preserve reproducibility and isolation.

## Rationale

Separate responsibilities reduce duplication and make data reuse, operational
reconstruction, and future knowledge capitalisation independently testable.

## Responsibilities and capability boundaries

The data layer exposes observations and persistent collection metadata.

The Planner evaluates availability and validity using explicit policies.
The orchestrator performs authorized collection and analysis operations.

World Model records operational decisions and references. It is not assumed
to be the authoritative dataset catalog or a replacement for Zetaris.

Zetaris connectivity verified from getting-started does not establish data
storage, metadata persistence, or application integration in this project.

Use a fictional local catalog for early increments and controlled tests.
Retain fictional fixtures for repeatable incident demonstrations.

Final project validation requires application access to real external
observations through Zetaris. A fictional catalog does not satisfy it.

Hub'Eau and Meteo-France are candidates, not selected integrations.
See ../architecture/analysis-input-and-data-validity.md.

## Consequences and limitations

Dataset availability and execution ownership are separate.
Sharing data or cached results must not expose another user's analysis.

Freshness must distinguish observation time, publication or availability time,
and retrieval time. A recent retrieval does not prove recent observations.

Historical replay must use only information available at the simulated time,
including the applicable dataset revisions.

Cache validity requires compatible inputs, dataset versions, algorithm
versions, and other parameters that affect the result.

Collection metadata and operational decisions may reference the same resource,
but must not become competing independently editable sources of truth.

## Assumptions and open questions

- Persistent metadata storage exposed through Zetaris.
- Dataset version and artifact-reference formats.
- Physical representation and verification of the accepted coverage segments,
  gaps, geographic scope, and observation cadence.
- Source-specific freshness and quality policies.
- Cache keys, invalidation, retention, and access rules.
- Representation of in-progress shared collection operations.
- Reconciliation when data persistence succeeds before operational completion
  is recorded.

No physical storage schema or cache implementation is selected here.

## Validation criteria

- A run records the dataset versions and result references it actually uses.
- A second compatible request reuses valid data without another collection.
- Missing coverage triggers only the necessary complementary collection.
- Planner decisions include their reasons and relevant metadata references.
- Operational records do not duplicate full measurement series.
- Simulated catalogs are clearly distinguished from real Zetaris integration.
- Shared data does not grant access to another run's private results.

Tests have not yet been implemented or executed.

## References and approval history

- Project instructions: ../../AGENTS.md
- Related decisions:
  - 0001-meterless-world-model.md
  - 0002-execution-isolation.md
  - 0004-versioned-workflows.md
- Decision source: project owner's requirements on data separation,
  freshness, selective collection, reuse, reproducibility, and confidentiality.

## Record history

| Date | Change |
|---|---|
| 2026-10-26 | Recorded accepted data responsibility boundaries; storage and cache mechanisms remain open. |
| 2026-10-26 | Consolidated selected design choices and retained only unresolved implementation questions. |
