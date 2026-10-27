# 0014 - Nominal application integration with official World Model

- Date recorded: 2026-10-27.
- Result: 64 targeted tests passed; actual local CLI passed.
- Approval evidence: Ok.
- Engine: unchanged official TypeScript World Model reference, package 0.1.0,
  pinned source 1742dec56a66e58eef9dda2d2b865823758ca8cd.
- Storage: explicit memory profile; no durable recovery claim.
- Provider and SQL: explicitly selected stubs for this increment.
- External platform requests or package installations: none.

## Increment and boundaries

The application orchestrator now records scoped intents and outcomes through
the official engine before protected dispatch. A per-run adapter calls the
local Python/TypeScript bridge; the reducer derives the nominal state and tasks
from stored operation-event entities. It does not replace the upstream engine.

Legacy create_run behavior remains pinned to workflow 1.1.0. New
create_execution contexts bind workflow 1.2.0, its source fingerprint and the
explicit dependency profile. append_event checks ownership, scope, identity,
expected revision and the implemented nominal transition conditions.

Commands remain serialized by the bridge. Recorder locks scope local revision
updates by run. Identical event retries return their original receipt before
stale-revision rejection; conflicting identity reuse is refused. This is an
application contract, not a native exactly-once guarantee.

The projection represents qualification, analysis, delegated SQL and report
preparation with distinct tasks and attempts. It retains parent/dependency
links and event history. Uncertain provider outcomes remain OUTCOME_UNKNOWN
with requiresReconciliation=true instead of being reported as success.

This is a nominal application projection, not an interpreter of every JSON
workflow policy, full finalization, approval/blocker machinery or restart
recovery. The output deliberately retains workflowExecuted=false and
durableTrace=false. SUCCEEDED describes the tested nominal projection only.

## Source changes

- bridge/world-model.mts: application execution/event commands and projection.
- agent/world_model.py: commands and uncertain mutation acknowledgement handling.
- agent/execution_state.py: explicit per-run adapter and validated receipts.
- agent/orchestrator.py: record-before-dispatch and distinct nominal/data tasks.
- agent/main.py: explicit --world-model memory selection and owned lifecycle.
- tests/unit/test_execution_state.py: ten isolated adapter checks.
- tests/integration/test_world_model_bridge.py: preserved ten E1 checks and
  added eight actual-reference nominal application checks.

No upstream source, existing workflow definition, accepted ADR, original
smoke script, user copy or private configuration was modified.

## Exact test commands

```bash
python3 -B -m unittest discover -s tests/unit -p test_world_model_client.py -v
python3 -B -m unittest discover -s tests/unit -p test_execution_state.py -v
python3 -B -m unittest discover -s tests/unit -p test_analysis_round_trip.py -v
python3 -B -m unittest discover -s tests/integration -p test_world_model_bridge.py -v
```

Executed from /home/info/flood-risk-intelligence through wsl.exe -d Ubuntu
--cd /home/info/flood-risk-intelligence --exec, with the prepared Linux Node
runtime and installed locked reference dependencies. No bootstrap download
was performed. Integration tests may use the existing ignored bridge cache.

## Expected and observed test results

Expected: preserve E1 behavior, protect event scope and mutation receipts,
stop external dispatch when state recording fails, project the nominal
application through the real engine, and isolate simultaneous same-user runs.

Observed:
- Client suite: 9 tests, 0.010 seconds, exit 0.
- State adapter suite: 10 tests, 0.036 seconds, exit 0.
- Application suite: 27 tests, 0.125 seconds, exit 0.
- Actual-engine suite: 18 tests, 63.039 seconds, exit 0.
- Total: 64 targeted tests. Official upstream smoke/conformance checks were
  not repeated because this increment did not change upstream source.

### Actual-engine test output

```text
test_close_terminates_owned_process (test_world_model_bridge.BridgeIntegrationTests.test_close_terminates_owned_process) ... ok
test_conflicting_identity_cannot_overwrite_event (test_world_model_bridge.BridgeIntegrationTests.test_conflicting_identity_cannot_overwrite_event) ... ok
test_create_and_read_reach_actual_engine_projection (test_world_model_bridge.BridgeIntegrationTests.test_create_and_read_reach_actual_engine_projection) ... ok
test_identical_retry_precedes_now_newer_revision (test_world_model_bridge.BridgeIntegrationTests.test_identical_retry_precedes_now_newer_revision) ... ok
test_independent_runs_allow_same_event_id_and_data_parameters (test_world_model_bridge.BridgeIntegrationTests.test_independent_runs_allow_same_event_id_and_data_parameters) ... ok
test_invalid_request_does_not_allocate_namespace (test_world_model_bridge.BridgeIntegrationTests.test_invalid_request_does_not_allocate_namespace) ... ok
test_overlapping_calls_receive_their_own_correlated_results (test_world_model_bridge.BridgeIntegrationTests.test_overlapping_calls_receive_their_own_correlated_results) ... ok
test_owner_checks_protect_reads_and_duplicate_results (test_world_model_bridge.BridgeIntegrationTests.test_owner_checks_protect_reads_and_duplicate_results) ... ok
test_unimplemented_persistence_profile_is_refused (test_world_model_bridge.BridgeIntegrationTests.test_unimplemented_persistence_profile_is_refused) ... ok
test_unsupported_protocol_commands_leave_state_unchanged (test_world_model_bridge.BridgeIntegrationTests.test_unsupported_protocol_commands_leave_state_unchanged) ... ok
test_closed_execution_rejects_new_events (test_world_model_bridge.NominalApplicationIntegrationTests.test_closed_execution_rejects_new_events) ... ok
test_duplicate_event_receipt_precedes_stale_revision_and_conflicts (test_world_model_bridge.NominalApplicationIntegrationTests.test_duplicate_event_receipt_precedes_stale_revision_and_conflicts) ... ok
test_intent_recording_failure_stops_before_provider_dispatch (test_world_model_bridge.NominalApplicationIntegrationTests.test_intent_recording_failure_stops_before_provider_dispatch) ... ok
test_orchestrator_projects_nominal_tasks_through_actual_engine (test_world_model_bridge.NominalApplicationIntegrationTests.test_orchestrator_projects_nominal_tasks_through_actual_engine) ... ok
test_overlapping_same_user_runs_keep_event_histories_separate (test_world_model_bridge.NominalApplicationIntegrationTests.test_overlapping_same_user_runs_keep_event_histories_separate) ... ok
test_owner_and_event_scope_rejections_leave_engine_unchanged (test_world_model_bridge.NominalApplicationIntegrationTests.test_owner_and_event_scope_rejections_leave_engine_unchanged) ... ok
test_uncertain_provider_outcome_remains_explicit_in_real_projection (test_world_model_bridge.NominalApplicationIntegrationTests.test_uncertain_provider_outcome_remains_explicit_in_real_projection) ... ok
test_unqualified_analysis_and_premature_success_are_refused (test_world_model_bridge.NominalApplicationIntegrationTests.test_unqualified_analysis_and_premature_success_are_refused) ... ok

----------------------------------------------------------------------
Ran 18 tests in 63.039s

OK
```

The unit suites explicitly block platform networking/native process use.
Actual-engine tests intentionally start the local Node bridge and retain
selected provider/SQL stubs. They do not import the original live smoke.

## Exact observed CLI command

This record is not authorization for another execution.

```powershell
wsl.exe -d Ubuntu --cd /home/info/flood-risk-intelligence --exec python3 -B -m agent.main --provider stub --sql-executor stub --world-model memory --trace
```

Expected: the selected real engine returns a derived successful nominal
projection while provider and SQL are explicitly simulated.

Observed, process exit 0:

```json
{
  "status": "PASSED",
  "profile": {
    "providerKind": "standalone_stub",
    "sourceKind": "standalone_stub"
  },
  "worldModelUsed": true,
  "traceStatus": "WORLD_MODEL_MEMORY",
  "nativeEventCount": 16,
  "nativeAuditCount": 16,
  "revision": 16,
  "workflowVersion": "1.2.0",
  "projectedStatus": "SUCCEEDED",
  "namespace": "run_df094ab4c907b154c91fb82f123b50c9cd13b3c3f3d400d1dc55b41e11ed7d9a",
  "tasks": [
    {
      "taskId": "0eaf07e3-0de5-4159-b19b-5e48dd696acf",
      "attemptId": "f42dab7e-b857-4ee4-81aa-7b787e4acbf5",
      "stepId": "qualify-request",
      "agentId": "planner",
      "status": "COMPLETED",
      "dependsOn": []
    },
    {
      "taskId": "542d9586-36e2-4a5f-9127-fb885543b229",
      "attemptId": "108498c5-b111-494a-b26b-d79c8af48471",
      "stepId": "analyze",
      "agentId": "analyzer",
      "status": "COMPLETED",
      "dependsOn": [
        "0eaf07e3-0de5-4159-b19b-5e48dd696acf"
      ]
    },
    {
      "taskId": "62ebb85a-ddf4-48ae-942c-b60c47b58e1e",
      "attemptId": "3d90c50d-3aaa-460a-8f7a-0bc66c8208ac",
      "stepId": "analyze",
      "agentId": "zetaris",
      "status": "COMPLETED",
      "dependsOn": [],
      "parentTaskId": "542d9586-36e2-4a5f-9127-fb885543b229"
    },
    {
      "taskId": "93e6371a-d481-4868-9b6b-4ba683b78df0",
      "attemptId": "88c42290-38a3-44d3-aae0-eb16725eece3",
      "stepId": "report",
      "agentId": "reporter",
      "status": "COMPLETED",
      "dependsOn": [
        "542d9586-36e2-4a5f-9127-fb885543b229"
      ]
    }
  ],
  "counts": {
    "inferenceDispatches": 2,
    "toolExecutions": 1
  },
  "workflowExecuted": false,
  "durableTrace": false
}
```

The 16 engine events/audit entries correspond to execution creation and
15 application events. Four tasks completed: qualification, analysis,
delegated data operation and report preparation. The observed data task has
its own task/attempt identity and an Analyzer parent; operation identity is
separate.

Two overlapping same-user requests were also verified in the integration
suite to retain separate namespaces and disjoint histories. This is a bounded
concurrency check, not a load or production multi-tenant authorization claim.

## Limits and next work

- Memory only. No persistence, process restart or reliable external-effect
  recovery is demonstrated.
- Simulated provider/SQL in this increment; earlier real platform evidence
  remains separately recorded in reports 0009 and 0013.
- No single hydrological run combining all real components has been executed.
- The bridge keeps 4096-byte request and 65536-byte response limits. Application
  events have bounded payloads and a 32-event history budget. Questions through
  this adapter are limited to 512 UTF-8 bytes; context and payload fields are
  constrained. These are application limits, not Meterless specifications.
- Namespace ownership checks are prototype caller-context checks, not identity
  authentication.
- The CLI requires the prepared reference/runtime dependencies; a clean judging
  installation and a meaningful credential-free hydrological SAMPLE remain
  to be delivered.
- The owner is preparing real Zetaris sources. Inspect schemas, units, periods,
  stations, provenance and actual compatibility before fixing the real scenario.
- The approved shortened delivery scope prioritizes a nominal business demo,
  real-data access, meaningful Nemotron use, controlled SAMPLE and submission
  artifacts. Advanced crash recovery, production auth, a public gateway, JUDGE
  improvements and other Meterless engines remain outside this delivery cut.
- The original guide smoke and its legacy-test migration are not changed here.

## References

- [Project status](../../PROJECT_STATUS.md)
- [README](../../../README.md)
- [Validation register](../README.md)
- [Execution model](../../architecture/execution-model.md)
- [Workflow design](../../architecture/workflow-and-planner.md)
- [Demand-driven decision](../../decisions/0011-demand-driven-analysis.md)
- [Original guide smoke](0013-original-guide-smoke-live.md)
- [Earlier live agentic probe](0009-select-one-live-application.md)

## Report history

| Date | Change |
|---|---|
| 2026-10-27 | Recorded the real-engine nominal integration, 64 passing targeted tests, isolated concurrent runs, actual CLI projection and delivery limits. |

## Source fingerprints

- bridge/world-model.mts: 0dc9bf562d1a1c5007fa080d17d2f1cb75e52248b00bf5c67ceb2a3e03cf9290
- agent/world_model.py: bb74e827575be3cf7f240c15f85bf920ea272b679ca292ab955dfbb231d809b7
- agent/execution_state.py: 84eceb1580a2058155a716c5d030df56282c7a4c41f011bfb77152bd1a5b9b23
- agent/orchestrator.py: 960df1a887680f9545df43673ce17d22fcf011e6ee5627402d28ab2191d383a8
- agent/main.py: 5b67e7de1764521cfd2d683a1e494f0030e814a55c3b980af08ee60ccaac3775
- tests/unit/test_execution_state.py: fe6bcc2d20d0be1816de6ac07b72aadda884860fb36d1a9dbb3c1a071544050c
- tests/integration/test_world_model_bridge.py: 38fc1f866dcce386e78ae5cb1dc40be28bf5ec9b0a614a63fb9c8d6203dd9bb4
