# 0005 - Python to World Model memory bridge

- Date: 2026-10-26.
- Result: Passed within the memory-only integration scope.
- Application Git reference: Not recorded.
- Official reference: @meterless/world-model-reference 0.1.0.
- Upstream commit: 1742dec56a66e58eef9dda2d2b865823758ca8cd.

## Preconditions and files

The owner approved four new source files and both test commands.
The official runtime and its local dependencies were already prepared; see
[report 0004](0004-world-model-reference-execution.md).

New files:
- bridge/world-model.mts: application-owned NDJSON boundary importing the
  unchanged official WorldModel class.
- agent/world_model.py: explicit client, transport selection, framing,
  deadlines, correlation, and owned-process lifecycle.
- tests/unit/test_world_model_client.py: injected standalone wire stubs.
- tests/integration/test_world_model_bridge.py: actual local TypeScript engine.

The application entry point, official source, configuration, and neighboring
repositories were not modified. No packages were installed in this increment.

## Commands

Standalone client tests, without a Node subprocess or network:

```powershell
wsl.exe -d Ubuntu --cd /home/info/flood-risk-intelligence -- python3 -B -m unittest discover -s tests/unit -p test_world_model_client.py -v
```

Actual-reference integration tests, without external services:

```powershell
wsl.exe -d Ubuntu --cd /home/info/flood-risk-intelligence -- python3 -B -m unittest discover -s tests/integration -p test_world_model_bridge.py -v
```

## Expected and observed results

| Suite | Expected | Observed |
|---|---|---|
| Standalone client | Explicit stubs exercise client success and failure boundaries | 9/9 passed, 0.009 seconds |
| Actual bridge | Python commands reach the official engine and custom projection | 10/10 passed, 23.080 seconds |

Both commands completed successfully; the enclosing sequence exited with 0.
Python source syntax and creation fingerprints were checked before execution.

Standalone evidence covers context separation, command rejection without
retry, response correlation, request size, finite JSON, cleanup after caller
failure, and uncertain write outcomes after timeout, transport loss, or
malformed acknowledgement.

Actual-engine evidence covers:
- A native operation-event entity and RUN_CREATED projection.
- One native event and native audit entry after creation.
- Original workflow version and a recorded definition fingerprint.
- Identical retries without another native event, despite revision zero
  in the original command and revision one in the existing run.
- Conflicting identity reuse rejected without overwriting the accepted event.
- Simulated owner checks on reads and duplicate receipts.
- Invalid request rejection before namespace allocation.
- Independent runs sharing a user, event identifier, and data-selection values.
- Two overlapping Python calls returning their own correlated run receipts.
- Unsupported protocol commands and versions leaving run state unchanged.
- Graceful owned-process closure and refusal of an unimplemented local profile.

## Implementation and simulation boundaries

The official implementation supplies WorldModel, externally keyed entities,
native events and audit, and registerView/view projection primitives.
Application code supplies validation, simulated principal checks, per-run
namespace selection, duplicate rules, receipt handling, and the protocol.

StubTransport exists in the unit tests and is explicitly injected.
Integration tests instead launch Linux Node and the prepared local tsx runtime.
The profile is explicitly memory/fixture/inference-disabled, with LOIRE-DEMO
as its only accepted zone. The fixed fixture timestamps are application inputs.

Caller-supplied principalId is trusted local application context.
This is not external authentication or production multi-tenant security.

## Concurrency scope

The test demonstrates overlapping calls for two distinct requests from the
same fictional user with identical zone and time-window values.
One transport and one bridge serialize exchanges and native mutations.
This is not parallel hydrological analysis or a load benchmark.

A user may have several simultaneous requests, and a request may have several
runs. Shared data-selection values do not identify an execution or transfer
ownership. Different-user, different-zone, and full-workflow concurrency
remain requirements to exercise in later increments.

## Limits and next increment

Memory state is lost when the process stops. No persistence, restart
reconstruction, staged publication, task dependency execution, multiple-blocker
workflow, approval workflow, selective collection, freshness checks, real-data
Zetaris access, or Nightshift analytical feature is implemented by this increment.
Rejected commands return protocol errors; durable rejection tracing is pending.
The duplicate test is not a forced crash after commit and before acknowledgement.
Schema and failure tests cover selected paths, not every input combination.
The application entry point remains a placeholder.
No hydrological forecast or scientific performance result is established.

## History

- 2026-10-26: Recorded the first real Python-to-reference integration, standalone and engine-backed results, concurrent request scope, and remaining work.
