# World Model integration review

Execution update (2026-10-26): the official reference passed 10 smoke tests
and 8 conformance checks; all 24 copied source fingerprints matched.
See [report 0004](../../../validation/reports/0004-world-model-reference-execution.md).
The E1 memory-only Python/TypeScript bridge is now implemented and tested; see
[report 0005](../../../validation/reports/0005-python-world-model-memory-bridge.md).
Durable publication, restart recovery, and application workflows remain unimplemented.
The original source-review findings below retain their original scope.


## Status

Source review only. No upstream tests or application integration have run.

Pinned revision:
1742dec56a66e58eef9dda2d2b865823758ca8cd

See provenance.json for selected upstream files and integrity metadata.

## Integration boundary

The official reference is TypeScript. Python integration remains undecided.

The reference provides generic records, an event log, projections, and optional
local JSON persistence. Workflow execution, authorization, task transitions,
blocker handling, and operation reconciliation remain application concerns.

## Findings requiring validation

| Area | Source-review finding | Integration consequence |
|---|---|---|
| Identity | External keys give deterministic record IDs. | Define application keys and execution scope explicitly. |
| Writes | Repeated entity upserts append events. | Stable identity alone does not prevent duplicate business events. |
| Ingestion | Checksums cover externalId, title, text, and observation time. | Mention or provenance changes alone may be skipped. |
| Isolation | Write serialization is per instance; sequences are per namespace. | Do not infer user isolation or interprocess coordination. |
| Relationships | A different target can close an existing edge with the same source, type, and context. | Preserve multiple dependencies and blockers through an explicitly tested representation. |
| Facts | Some materialization occurs outside the event fold. | Test reconstruction before using facts for operational status. |
| Persistence | Local JSON is rewritten directly; event and audit persistence are separate. | Do not claim atomic crash recovery or interprocess safety. |
| Views | Several documented methods are absent from the reference facade. | Use verified interfaces, not generic documentation snippets. |
| Projections | Custom views are recomputed on read. | Do not describe them as incrementally maintained in this reference. |

## Specification differences

- The ingest guide uses an automatic merge threshold of 0.92.
- The reference and conformance checks use 0.85.
- Generic documentation describes checkpointed queues, consistency helpers,
  and additional read/write methods not exposed by the reviewed facade.

Preserve upstream files unchanged. Record differences rather than silently
modifying the specifications to match the implementation.

## Official verification limits

The conformance runner contains eight checks covering stable IDs, merge bands,
provenance, ingestion idempotency and mutation, relationship supersession,
and audit ordering.

It does not establish application run isolation, restart persistence,
multiple blockers, scoped approvals, or external-effect recovery.

The canonical state comparison omits audit entries and score snapshots.
Passing that comparison does not prove that every stored structure is unchanged.

In scripts/idempotency-check.ts, --mutate returns zero when the expected
state difference is detected. This differs from its introductory comment.

## Next decision gate

Before selecting the integration mechanism:
- Complete documentation and reference consolidation.
- Inspect available runtime tooling after approval.
- Propose the Python boundary and operational representation.
- Define upstream and application verification separately.

No runtime, dependency installation, storage replacement, or adapter strategy
is approved by this document.

## Review history

| Date | Change |
|---|---|
| 2026-10-26 | Recorded source-review findings; runtime behavior remains unverified. |
| 2026-10-26 | Recorded successful official reference execution and linked report 0004 without claiming application integration. |
| 2026-10-26 | Linked the tested E1 application bridge and retained the limits of reference and workflow evidence. |
