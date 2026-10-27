# 0009 - Live Nightshift and Zetaris SELECT-one application path

- Date: 2026-10-27.
- Result: Passed within the SELECT-one application scope.
- Approval evidence: Ok.
- Execution context: Python Ubuntu WSL, Windows-loopback Nightshift transport,
  and native Python direct REST to configured Zetaris.
- Requested route: meterless/auto.
- Reported serving model, both calls: nvidia/nemotron-3.5-lightning-30b-a3b.
- Git revision and exact installed Runtime version: not collected.

## Scenario

Execute the real minimal application path:

Application orchestrator -> Analyzer -> Nightshift/Nemotron -> structured
run_sql request -> orchestrator-controlled Zetaris executor -> tool result
-> Nightshift/Nemotron -> structured Analyzer result -> application orchestrator.

Only SELECT 1 AS one is permitted. Unlike report 0007, this execution uses the
reusable Python application components and a real Zetaris REST operation.
Unlike report 0008, provider and SQL transports are not injected stubs.

## Preconditions and security

The operator's Windows Runtime is running at the explicitly supplied loopback
URL. Its matching token remains in the existing private Windows token file.

Zetaris settings come from the explicitly supplied getting-started .env.local,
with exported matching environment variables taking precedence. Only required
configuration names are used. No credentials were copied into this repository
or displayed. The neighboring repositories and configured resources were not
modified. Previously successful preflights and Pok?API access were retained
as prior evidence; this increment did not repeat their onboarding or run new
preflight/listing checks.

The application permits at most two Runtime completion dispatches and one
SQL execution. No automatic retries, proxy discovery or redirects are enabled.
Inference can consume credits; Runtime lanes may perform multiple underlying
provider operations per completion request.

## Exact executed command

This is a reproducibility record, not authorization to execute it again.

```powershell
wsl.exe -d Ubuntu --cd /home/info/flood-risk-intelligence --exec python3 -B -m agent.main --provider nightshift --sql-executor zetaris --transport windows-loopback --nightshift-base-url http://127.0.0.1:8088/v1 --route meterless/auto --zetaris-env-file /home/info/getting-started/.env.local --trace
```

## Expected result

1. The application creates a scoped probe context and invokes the Analyzer.
2. Nemotron returns exactly one admitted structured run_sql call.
3. The application sends SELECT 1 AS one through Zetaris direct REST.
4. The executor validates and normalizes the one-row result.
5. The Analyzer returns the result under the matching tool_call_id.
6. Nemotron returns final text containing one=1 and the exact evidence receipt.
7. The application receives the structured result and records probe closure.

## Observed result

- Process exit code: 0.
- Application status: PASSED.
- Analyzer status: SUCCEEDED.
- Normalized Zetaris rows: [[1]].
- Runtime completion dispatches: 2.
- SQL executions recorded: 1.
- Scoped events: 13.
- Interval between first and last application trace timestamps: 20.946 seconds.
  This is a trace-derived interval, not an independently instrumented benchmark.
- Run: 1c545ff6-c5bd-479f-a319-35d6319942ab.
- SQL queryId / operationId: 02c65b32-201b-4a8c-b806-1bb489055c50.
- Result receipt: 38b90827-5e48-40f0-95e3-ee75e007801b.
- Both responses reported the configured Nemotron Lightning serving model.

The live transport implementations accept only HTTP 200 before returning
success. Raw HTTP bodies/status headers and server-side audit logs were not
separately retained. The result and event sequence below are the application
evidence, not an independent database audit or exactly-once guarantee.

## Captured structured output

The CLI also emitted the same events as JSON lines to stderr during execution.
The final object retains them under trace; it is reproduced without duplicating
the event stream.

```json
{
  "scope": "select_one_application_probe",
  "status": "PASSED",
  "userId": "USR-DEMO",
  "requestId": "ede06947-37a1-4893-b8ad-dbae52291397",
  "runId": "1c545ff6-c5bd-479f-a319-35d6319942ab",
  "taskId": "430757c6-cbc1-45c1-ba9a-b4ce1c1fd3fd",
  "attemptId": "6d409b3a-3c13-4473-9db6-4357533efec8",
  "profile": {
    "providerKind": "nightshift",
    "sourceKind": "zetaris_rest"
  },
  "analysisResult": {
    "status": "SUCCEEDED",
    "answer": "**Result**\n\n- **Value of `one`:** `1`\n- **Evidence ID:** `38b90827-5e48-40f0-95e3-ee75e007801b`\n\nThe `run_sql` probe executed the allowed `SELECT 1 AS one` statement and returned a single row with the column `one` set to `1`. The accompanying receipt includes the `evidenceId` shown above, confirming the operation's provenance.",
    "indicators": {
      "one": 1
    },
    "data": {
      "columns": [
        "one"
      ],
      "rows": [
        [
          1
        ]
      ],
      "rowCount": 1,
      "truncated": false,
      "sourceKind": "zetaris_rest",
      "operationId": "02c65b32-201b-4a8c-b806-1bb489055c50",
      "evidenceId": "38b90827-5e48-40f0-95e3-ee75e007801b"
    },
    "requestedRoute": "meterless/auto",
    "reportedModels": [
      "nvidia/nemotron-3.5-lightning-30b-a3b",
      "nvidia/nemotron-3.5-lightning-30b-a3b"
    ],
    "invocationIds": [
      "f701f311-c905-475d-adb9-60fd0c7c4e6b",
      "eb842228-0a7b-4558-95bd-b4aaf0336134"
    ],
    "toolCalls": [
      {
        "toolName": "run_sql",
        "toolCallId": "call-39f56f48-ce79-40bb-97b9-0c81a243d118",
        "sql": "SELECT 1 AS one",
        "operationId": "02c65b32-201b-4a8c-b806-1bb489055c50",
        "evidenceId": "38b90827-5e48-40f0-95e3-ee75e007801b"
      }
    ],
    "validation": {
      "toolResultReferenced": true,
      "domainValidated": false,
      "runtimeJudge": "not_established"
    },
    "uncertainties": [
      "This verifies a SELECT-one protocol path, not hydrological conclusions."
    ]
  },
  "errorCode": null,
  "counts": {
    "inferenceDispatches": 2,
    "toolExecutions": 1
  },
  "traceStatus": "IN_MEMORY",
  "trace": [
    {
      "eventId": "62aceb3f-06e7-4555-a763-96bda72a4f5a",
      "eventType": "PROBE_CONTEXT_CREATED",
      "userId": "USR-DEMO",
      "requestId": "ede06947-37a1-4893-b8ad-dbae52291397",
      "runId": "1c545ff6-c5bd-479f-a319-35d6319942ab",
      "taskId": "430757c6-cbc1-45c1-ba9a-b4ce1c1fd3fd",
      "attemptId": "6d409b3a-3c13-4473-9db6-4357533efec8",
      "recordedAt": "2026-10-27T12:33:40.471353Z",
      "payload": {
        "question": "Run SELECT 1 AS one and report its value and result receipt.",
        "providerKind": "nightshift",
        "sourceKind": "zetaris_rest",
        "maxInferenceCalls": 2,
        "maxToolExecutions": 1,
        "maxElapsedSeconds": 180
      }
    },
    {
      "eventId": "592eb043-f502-4d78-aabd-6a15e475ca79",
      "eventType": "INFERENCE_DISPATCHED",
      "userId": "USR-DEMO",
      "requestId": "ede06947-37a1-4893-b8ad-dbae52291397",
      "runId": "1c545ff6-c5bd-479f-a319-35d6319942ab",
      "taskId": "430757c6-cbc1-45c1-ba9a-b4ce1c1fd3fd",
      "attemptId": "6d409b3a-3c13-4473-9db6-4357533efec8",
      "recordedAt": "2026-10-27T12:33:40.472737Z",
      "payload": {
        "invocationId": "f701f311-c905-475d-adb9-60fd0c7c4e6b",
        "requestedRoute": "meterless/auto",
        "providerKind": "nightshift"
      }
    },
    {
      "eventId": "fd5c22b2-478e-4b47-898b-e86beaf5a9cf",
      "eventType": "INFERENCE_RESPONSE_RECEIVED",
      "userId": "USR-DEMO",
      "requestId": "ede06947-37a1-4893-b8ad-dbae52291397",
      "runId": "1c545ff6-c5bd-479f-a319-35d6319942ab",
      "taskId": "430757c6-cbc1-45c1-ba9a-b4ce1c1fd3fd",
      "attemptId": "6d409b3a-3c13-4473-9db6-4357533efec8",
      "recordedAt": "2026-10-27T12:33:50.939404Z",
      "payload": {
        "invocationId": "f701f311-c905-475d-adb9-60fd0c7c4e6b",
        "reportedModel": "nvidia/nemotron-3.5-lightning-30b-a3b",
        "verification": "not_established"
      }
    },
    {
      "eventId": "92cc4977-7f57-4b8f-b7cd-44747ac6c539",
      "eventType": "TOOL_REQUEST_RECEIVED",
      "userId": "USR-DEMO",
      "requestId": "ede06947-37a1-4893-b8ad-dbae52291397",
      "runId": "1c545ff6-c5bd-479f-a319-35d6319942ab",
      "taskId": "430757c6-cbc1-45c1-ba9a-b4ce1c1fd3fd",
      "attemptId": "6d409b3a-3c13-4473-9db6-4357533efec8",
      "recordedAt": "2026-10-27T12:33:50.940504Z",
      "payload": {
        "invocationId": "f701f311-c905-475d-adb9-60fd0c7c4e6b",
        "toolCallId": "call-39f56f48-ce79-40bb-97b9-0c81a243d118",
        "toolName": "run_sql",
        "sql": "SELECT 1 AS one"
      }
    },
    {
      "eventId": "81b166cc-2a88-4cba-8489-0146d03bf22d",
      "eventType": "DATA_REQUEST_ACCEPTED",
      "userId": "USR-DEMO",
      "requestId": "ede06947-37a1-4893-b8ad-dbae52291397",
      "runId": "1c545ff6-c5bd-479f-a319-35d6319942ab",
      "taskId": "430757c6-cbc1-45c1-ba9a-b4ce1c1fd3fd",
      "attemptId": "6d409b3a-3c13-4473-9db6-4357533efec8",
      "recordedAt": "2026-10-27T12:33:50.941771Z",
      "payload": {
        "toolCallId": "call-39f56f48-ce79-40bb-97b9-0c81a243d118",
        "invocationId": "f701f311-c905-475d-adb9-60fd0c7c4e6b",
        "operationId": "02c65b32-201b-4a8c-b806-1bb489055c50",
        "sql": "SELECT 1 AS one",
        "sourceKind": "zetaris_rest"
      }
    },
    {
      "eventId": "96c8d4f8-fbe9-4eff-b561-ba6ed61a1113",
      "eventType": "SQL_DISPATCHED",
      "userId": "USR-DEMO",
      "requestId": "ede06947-37a1-4893-b8ad-dbae52291397",
      "runId": "1c545ff6-c5bd-479f-a319-35d6319942ab",
      "taskId": "430757c6-cbc1-45c1-ba9a-b4ce1c1fd3fd",
      "attemptId": "6d409b3a-3c13-4473-9db6-4357533efec8",
      "recordedAt": "2026-10-27T12:33:50.942522Z",
      "payload": {
        "operationId": "02c65b32-201b-4a8c-b806-1bb489055c50",
        "toolCallId": "call-39f56f48-ce79-40bb-97b9-0c81a243d118",
        "sourceKind": "zetaris_rest"
      }
    },
    {
      "eventId": "c9be9778-519b-4df1-adad-0eaf76d7c71b",
      "eventType": "DATA_OPERATION_COMPLETED",
      "userId": "USR-DEMO",
      "requestId": "ede06947-37a1-4893-b8ad-dbae52291397",
      "runId": "1c545ff6-c5bd-479f-a319-35d6319942ab",
      "taskId": "430757c6-cbc1-45c1-ba9a-b4ce1c1fd3fd",
      "attemptId": "6d409b3a-3c13-4473-9db6-4357533efec8",
      "recordedAt": "2026-10-27T12:33:52.809849Z",
      "payload": {
        "operationId": "02c65b32-201b-4a8c-b806-1bb489055c50",
        "toolCallId": "call-39f56f48-ce79-40bb-97b9-0c81a243d118",
        "evidenceId": "38b90827-5e48-40f0-95e3-ee75e007801b",
        "rowCount": 1,
        "sourceKind": "zetaris_rest"
      }
    },
    {
      "eventId": "29db405a-95ca-4a19-b1be-dc4644e32390",
      "eventType": "TOOL_RESULT_PREPARED",
      "userId": "USR-DEMO",
      "requestId": "ede06947-37a1-4893-b8ad-dbae52291397",
      "runId": "1c545ff6-c5bd-479f-a319-35d6319942ab",
      "taskId": "430757c6-cbc1-45c1-ba9a-b4ce1c1fd3fd",
      "attemptId": "6d409b3a-3c13-4473-9db6-4357533efec8",
      "recordedAt": "2026-10-27T12:33:52.810292Z",
      "payload": {
        "toolCallId": "call-39f56f48-ce79-40bb-97b9-0c81a243d118",
        "evidenceId": "38b90827-5e48-40f0-95e3-ee75e007801b",
        "operationId": "02c65b32-201b-4a8c-b806-1bb489055c50"
      }
    },
    {
      "eventId": "f6cda27c-4765-4ed0-ae04-7b85287728cc",
      "eventType": "INFERENCE_DISPATCHED",
      "userId": "USR-DEMO",
      "requestId": "ede06947-37a1-4893-b8ad-dbae52291397",
      "runId": "1c545ff6-c5bd-479f-a319-35d6319942ab",
      "taskId": "430757c6-cbc1-45c1-ba9a-b4ce1c1fd3fd",
      "attemptId": "6d409b3a-3c13-4473-9db6-4357533efec8",
      "recordedAt": "2026-10-27T12:33:52.810495Z",
      "payload": {
        "invocationId": "eb842228-0a7b-4558-95bd-b4aaf0336134",
        "requestedRoute": "meterless/auto",
        "providerKind": "nightshift"
      }
    },
    {
      "eventId": "e5380726-46f2-4db6-bba5-70b4ad0a760d",
      "eventType": "INFERENCE_RESPONSE_RECEIVED",
      "userId": "USR-DEMO",
      "requestId": "ede06947-37a1-4893-b8ad-dbae52291397",
      "runId": "1c545ff6-c5bd-479f-a319-35d6319942ab",
      "taskId": "430757c6-cbc1-45c1-ba9a-b4ce1c1fd3fd",
      "attemptId": "6d409b3a-3c13-4473-9db6-4357533efec8",
      "recordedAt": "2026-10-27T12:34:01.413443Z",
      "payload": {
        "invocationId": "eb842228-0a7b-4558-95bd-b4aaf0336134",
        "reportedModel": "nvidia/nemotron-3.5-lightning-30b-a3b",
        "verification": "not_established"
      }
    },
    {
      "eventId": "6d2e2de2-3b1f-4fc9-9b30-c9e89c43561a",
      "eventType": "ANALYSIS_RESULT_CHECKED",
      "userId": "USR-DEMO",
      "requestId": "ede06947-37a1-4893-b8ad-dbae52291397",
      "runId": "1c545ff6-c5bd-479f-a319-35d6319942ab",
      "taskId": "430757c6-cbc1-45c1-ba9a-b4ce1c1fd3fd",
      "attemptId": "6d409b3a-3c13-4473-9db6-4357533efec8",
      "recordedAt": "2026-10-27T12:34:01.414642Z",
      "payload": {
        "evidenceId": "38b90827-5e48-40f0-95e3-ee75e007801b",
        "check": "select_one_value_and_receipt_present",
        "domainValidated": false
      }
    },
    {
      "eventId": "64101236-ca75-4b73-849e-0d532a91f64e",
      "eventType": "ANALYZER_RESULT_RECEIVED",
      "userId": "USR-DEMO",
      "requestId": "ede06947-37a1-4893-b8ad-dbae52291397",
      "runId": "1c545ff6-c5bd-479f-a319-35d6319942ab",
      "taskId": "430757c6-cbc1-45c1-ba9a-b4ce1c1fd3fd",
      "attemptId": "6d409b3a-3c13-4473-9db6-4357533efec8",
      "recordedAt": "2026-10-27T12:34:01.415334Z",
      "payload": {
        "analysisStatus": "SUCCEEDED",
        "evidenceId": "38b90827-5e48-40f0-95e3-ee75e007801b"
      }
    },
    {
      "eventId": "5a323c31-8408-47d3-998e-c073c67cf693",
      "eventType": "PROBE_FINISHED",
      "userId": "USR-DEMO",
      "requestId": "ede06947-37a1-4893-b8ad-dbae52291397",
      "runId": "1c545ff6-c5bd-479f-a319-35d6319942ab",
      "taskId": "430757c6-cbc1-45c1-ba9a-b4ce1c1fd3fd",
      "attemptId": "6d409b3a-3c13-4473-9db6-4357533efec8",
      "recordedAt": "2026-10-27T12:34:01.417393Z",
      "payload": {
        "outcome": "PASSED",
        "errorCode": null
      }
    }
  ],
  "worldModelUsed": false,
  "workflowExecuted": false,
  "durableTrace": false
}
```

## Interpretation and limits

The returned receipt is application-generated correlation metadata. Its exact
appearance in final text demonstrates use of the tool result in this exchange;
it is not a cryptographic source attestation. The model's prose must not
extend that evidence into unsupported guarantees.

This verifies the SELECT-one path through the application and both live
platforms. It does not verify weather/hydrometry collectors, table schemas,
station joins, correlations, forecasting, scientific accuracy or the complete
judging SAMPLE.

The application explicitly reports worldModelUsed=false,
workflowExecuted=false and durableTrace=false. Its trace remains in memory
and stdout/stderr; it is preserved here as a validation artifact, not a
runtime event store. The official World Model bridge is tested separately.

No successful JUDGE verdict, VERIFY outcome, production authentication,
concurrent workflow execution, restart recovery or full provider-contract
conformance is established.

A client timeout does not prove remote work stopped. Any uncertain future
outcome requires reconciliation, not an automatic retry. Numerical budgets
and behavior for the final hydrological workflow still require review.

## Next step

Identify the exact smoke procedure in the local Participant Setup Guide
before changing or executing smoke_test.py. That existing file is the earlier
hello baseline. The guide smoke is not assumed to be identical or to add
new coverage without inspection.

Then use the owner-provided weather/hydrometry objects to inspect real source
contracts and extend the controlled query scope before hydrological scenarios.
The current literal-query allowlist intentionally rejects station queries.

## References

- [Project status](../../PROJECT_STATUS.md)
- [README](../../../README.md)
- [Validation register](../README.md)
- [Standalone application checks](0008-select-one-application-standalone.md)
- [Earlier tool-protocol check](0007-nightshift-structured-tool-round-trip.md)
- [Nightshift requirements](../../architecture/nightshift-integration-requirements.md)
- [Demand-driven decision](../../decisions/0011-demand-driven-analysis.md)

## Report history

| Date | Change |
|---|---|
| 2026-10-27 | Recorded the successful live application SELECT-one path, full structured trace, exact command and unverified boundaries. |

## Source fingerprints

- agent/tools_zetaris.py: 660536fc9ef9a0d13c2bee855880982cf0b0280259b8d7eebb284beb0d01b9f2
- agent/llm.py: dd093b7d54b653e136bf02902e352e8299a276b60479a4d7293b0897dfef132a
- agent/analyzer.py: f30070b8589f9c2908dcfad59d2d0231a24534b36620d2d3bcfbd4e994b1c957
- agent/orchestrator.py: d72d08d52deda0a1fef0cd87d6dc8e3105a459e199c909ae22dfbc4eac6e1e8a
- agent/main.py: 003b456442509492b755b75a70a0cbfd0fb8df5cb389688dcfe46c5797f21d69
- tests/unit/test_analysis_round_trip.py: dc32918a10e1b2e1d8a37baef4dc741771ae91df4a2441b8421bc4861804af50
