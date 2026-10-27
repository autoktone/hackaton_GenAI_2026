# Decision register

This register records architectural, functional, and technical decisions.

## Status

- Proposed: awaiting explicit human validation.
- Accepted: explicitly validated by the project owner.
- Deferred: intentionally postponed.
- Superseded: replaced by another decision, linked in both records.

Documenting an accepted requirement does not authorize its implementation.
Approval of an operation does not accept unrelated design proposals.

## Naming and maintenance

Use sequential identifiers and English kebab-case filenames:
0001-meterless-world-model.md

Use template.md for new records. Keep one primary decision per record.
Separate accepted decisions from assumptions and open implementation choices.

Do not silently rewrite an accepted decision. Record amendments explicitly.
For a substantive replacement, create a new record and link the predecessor.

## Evidence

Record the source of approval and relevant technical references.
Do not invent dates, approvals, guarantees, or test results.

Distinguish:
- Requirements accepted by the project owner.
- Contracts stated in upstream specifications.
- Behavior found in the upstream implementation.
- Application responsibilities.
- Simulated behavior.
- Deferred capabilities.

Track execution evidence separately in ../validation/.
Passing upstream conformance does not establish application reliability.

## Decision index

| ID | Decision | Status |
|---|---|---|
| [0001](0001-meterless-world-model.md) | Prioritize Meterless World Model | Accepted |
| [0002](0002-execution-isolation.md) | Isolate operational state by execution | Accepted |
| [0003](0003-tasks-attempts-and-blockers.md) | Track tasks, attempts, and blockers independently | Accepted |
| [0004](0004-versioned-workflows.md) | Use explicit versioned workflows | Accepted |
| [0005](0005-data-responsibilities.md) | Separate data, collection metadata, operational state, and knowledge | Accepted |
| [0006](0006-data-freshness-and-selective-collection.md) | Check data validity before selective collection | Accepted |
| [0007](0007-recovery-idempotency-and-concurrency.md) | Separate reconstruction, recovery, and operation idempotency | Accepted |
| [0008](0008-human-approval-and-authorization.md) | Scope human approval to explicit operations | Accepted |
| [0009](0009-python-world-model-bridge.md) | Bridge Python to the official World Model reference | Accepted |
| [0010](0010-nightshift-required-integration.md) | Require Nightshift as the primary AI provider | Accepted |
| [0011](0011-demand-driven-analysis.md) | Use demand-driven data operations inside analysis | Accepted |
| [0012](0012-bounded-sql-retry-and-human-intervention.md) | Bound SQL-read retries and request human intervention | Accepted |

Further decision records require separate content approval and creation approval.

## Register history

| Date | Change |
|---|---|
| 2026-10-26 | Created the register conventions and reusable template. |
| 2026-10-26 | Added accepted decision 0001 to the index. |
| 2026-10-26 | Added accepted decision 0002 to the index. |
| 2026-10-26 | Added accepted decision 0003 to the index. |
| 2026-10-26 | Added accepted decision 0004 to the index. |
| 2026-10-26 | Added accepted decision 0005 to the index. |
| 2026-10-26 | Added accepted decision 0006 to the index. |
| 2026-10-26 | Added accepted decision 0007 to the index. |
| 2026-10-26 | Added accepted decision 0008 to the index. |
| 2026-10-26 | Added proposed decision 0009 to the index. |
| 2026-10-26 | Updated decision 0009 from Proposed to Accepted following explicit owner approval. |
| 2026-10-26 | Indexed accepted decision 0010 and linked its partial replacement of decision 0001. |
| 2026-10-27 | Indexed accepted decision 0011 for demand-driven Analyzer requests without changing previous ADRs. |

| 2026-10-27 | Indexed the explicitly approved workflow 1.3 read-retry and human-intervention policy without rewriting prior ADRs. |
