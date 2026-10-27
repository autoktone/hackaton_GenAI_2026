# 0008 - SELECT-one application standalone checks

- Date: 2026-10-27.
- Result: Passed within standalone scope.
- Approval evidence: Ok.
- Profile: explicitly injected provider, SQL and transport dependencies.
- Live Nightshift calls: none.
- Live Zetaris queries: none.
- Packages installed: none.
- Git revision: not collected.

## Scenario

Exercise the implemented application orchestrator -> Analyzer -> structured
run_sql request -> controlled executor -> tool result -> provider -> structured
Analyzer result path, using standalone dependencies.

The same SQL method and result structure serve StubSqlExecutor and
ZetarisSqlExecutor. The latter was tested with injected HTTP responses;
its sourceKind describes the adapter and is not proof of a live connection.

## Files

- agent/main.py: explicit CLI and sanitized failure output.
- agent/llm.py: Nightshift client, constant Windows HTTP worker and selected stub.
- agent/tools_zetaris.py: strict SELECT-one executors, settings and direct REST.
- agent/analyzer.py: bounded internal tool-result loop.
- agent/orchestrator.py: scoped dispatch control and in-memory trace.
- tests/unit/test_analysis_round_trip.py: standalone behavioral checks.

The three modified placeholders carry concise dated source-history comments.
No official World Model code, existing bridge, earlier test file or workflow
definition was changed.

## Preconditions and exact command

Python 3 is sufficient; tests guard against native-process execution, network
connections and private configuration reads. Particular tests replace those
dependencies with selected in-memory mocks.

```powershell
wsl.exe -d Ubuntu --cd /home/info/flood-risk-intelligence --exec python3 -B -m unittest discover -s tests/unit -p test_analysis_round_trip.py -v
```

## Expected result

The application path returns the SELECT-one value and its evidence receipt;
invalid calls or results fail before an unauthorized follow-up action.
No dependency failure activates a fallback or retries an uncertain operation.

## Observed result

Exit code: 0.
Unittest reported 27 tests in 0.207 seconds, OK.
The command runner reported approximately 3.44 seconds.

```text
test_additional_call_after_result_is_rejected_without_reexecution (test_analysis_round_trip.StandaloneTests.test_additional_call_after_result_is_rejected_without_reexecution) ... ok
test_answer_must_reference_the_returned_result (test_analysis_round_trip.StandaloneTests.test_answer_must_reference_the_returned_result) ... ok
test_budget_exhaustion_prevents_sql (test_analysis_round_trip.StandaloneTests.test_budget_exhaustion_prevents_sql) ... ok
test_cli_requires_explicit_live_configuration (test_analysis_round_trip.StandaloneTests.test_cli_requires_explicit_live_configuration) ... ok
test_cli_stub_profile_does_not_read_private_configuration (test_analysis_round_trip.StandaloneTests.test_cli_stub_profile_does_not_read_private_configuration) ... ok
test_complete_stub_path_and_causal_trace (test_analysis_round_trip.StandaloneTests.test_complete_stub_path_and_causal_trace) ... ok
test_configuration_never_guesses_endpoint_or_org (test_analysis_round_trip.StandaloneTests.test_configuration_never_guesses_endpoint_or_org) ... ok
test_disallowed_sql_rejected_before_transport (test_analysis_round_trip.StandaloneTests.test_disallowed_sql_rejected_before_transport) ... ok
test_executor_cannot_return_another_operations_result (test_analysis_round_trip.StandaloneTests.test_executor_cannot_return_another_operations_result) ... ok
test_insufficient_sql_budget_prevents_dispatch (test_analysis_round_trip.StandaloneTests.test_insufficient_sql_budget_prevents_dispatch) ... ok
test_invalid_or_ambiguous_rest_values_are_rejected (test_analysis_round_trip.StandaloneTests.test_invalid_or_ambiguous_rest_values_are_rejected) ... ok
test_multiple_initial_calls_are_not_dispatched (test_analysis_round_trip.StandaloneTests.test_multiple_initial_calls_are_not_dispatched) ... ok
test_no_structured_call_means_no_sql_execution (test_analysis_round_trip.StandaloneTests.test_no_structured_call_means_no_sql_execution) ... ok
test_private_configuration_is_explicit_and_never_executed (test_analysis_round_trip.StandaloneTests.test_private_configuration_is_explicit_and_never_executed) ... ok
test_provider_failure_is_not_retried (test_analysis_round_trip.StandaloneTests.test_provider_failure_is_not_retried) ... ok
test_rest_request_uses_verified_body_and_fresh_request_uuid (test_analysis_round_trip.StandaloneTests.test_rest_request_uses_verified_body_and_fresh_request_uuid) ... ok
test_rest_unauthorized_does_not_read_or_expose_error_body (test_analysis_round_trip.StandaloneTests.test_rest_unauthorized_does_not_read_or_expose_error_body) ... ok
test_runtime_transport_rejects_nonlocal_and_secret_bearing_urls (test_analysis_round_trip.StandaloneTests.test_runtime_transport_rejects_nonlocal_and_secret_bearing_urls) ... ok
test_runtime_url_normalization_and_unknown_meterless_route (test_analysis_round_trip.StandaloneTests.test_runtime_url_normalization_and_unknown_meterless_route) ... ok
test_sql_failure_keeps_failure_evidence_and_does_not_fall_back (test_analysis_round_trip.StandaloneTests.test_sql_failure_keeps_failure_evidence_and_does_not_fall_back) ... ok
test_stub_and_injected_rest_executor_share_result_contract (test_analysis_round_trip.StandaloneTests.test_stub_and_injected_rest_executor_share_result_contract) ... ok
test_trace_sink_failure_prevents_protected_dispatch (test_analysis_round_trip.StandaloneTests.test_trace_sink_failure_prevents_protected_dispatch) ... ok
test_two_same_user_requests_keep_contexts_and_receipts_separate (test_analysis_round_trip.StandaloneTests.test_two_same_user_requests_keep_contexts_and_receipts_separate) ... ok
test_unexpected_exception_is_sanitized (test_analysis_round_trip.StandaloneTests.test_unexpected_exception_is_sanitized) ... ok
test_unknown_tool_and_malformed_arguments_are_rejected (test_analysis_round_trip.StandaloneTests.test_unknown_tool_and_malformed_arguments_are_rejected) ... ok
test_windows_transport_classifies_failure_without_retry (test_analysis_round_trip.StandaloneTests.test_windows_transport_classifies_failure_without_retry) ... ok
test_windows_worker_receives_payload_as_data_not_command_text (test_analysis_round_trip.StandaloneTests.test_windows_worker_receives_payload_as_data_not_command_text) ... ok

----------------------------------------------------------------------
Ran 27 tests in 0.207s

OK
```

## Verified behaviors

- Complete standalone component path with two provider dispatches and one SQL.
- Same normalized result keys across both executor implementations.
- String/decimal/exponent SELECT-one values normalized; invalid data rejected.
- Other SQL, tool names, extra arguments and multiple tool calls rejected.
- Returned operation identity and final result receipt checked.
- Two sequential same-user requests retain distinct contexts and receipts.
- Provider/SQL failures and budget exhaustion stop progression without retry.
- Trace-sink failure prevents protected dispatch.
- REST payload, headers and request UUID construction checked with mocked I/O.
- Configuration remains explicit; credential-bearing URLs and disallowed
  endpoints are rejected. Unit-test credential strings are synthetic fixtures.
- Model request text crosses the Windows boundary as stdin JSON, not executable
  command text. The native worker itself was not executed in these tests.
- Stub CLI selection ignores live configuration and private files.

## Limits and pending work

This is a SELECT-one integration probe, not the full workflow 1.2.0 executor.
It does not run World Model, persist/reconstruct events or prove concurrency,
full identity authorization, collector deduplication or hydrological validity.

The live reusable Windows transport and real Zetaris executor still require
an authorized application round trip. Earlier report 0007 tested a different
direct Windows probe and cannot substitute for that check.

Timeouts are client controls, not proof that remote work stopped. There is no
exactly-once or durable-recovery claim. An uncertain result must not be retried
automatically.

Provider-contract discovery/Auto Detect/connect-link support and a general
remote transport remain outside this minimal implementation.
The scripted dependency is labeled as a stub, not a generated model response.
A SELECT-one probe is not the complete one-command judging sample.

The permanent instructions and technical milestone summaries still require
a targeted synchronization with this newly implemented scope; their earlier
baseline descriptions must not be treated as current implementation proof.

## Next step

After separate approval, execute the same application path with the real
Nightshift provider and Zetaris executor. SELECT 1 does not require the
owner's new weather/hydrometry sources. Then identify and authorize the exact
Participant Setup Guide smoke before source-specific hydrological scenarios.

## References

- [Project status](../../PROJECT_STATUS.md)
- [README procedures](../../../README.md)
- [Validation register](../README.md)
- [Structured-tool protocol evidence](0007-nightshift-structured-tool-round-trip.md)
- [Demand-driven decision](../../decisions/0011-demand-driven-analysis.md)

## Report history

| Date | Change |
|---|---|
| 2026-10-27 | Recorded 27 passing standalone application checks, exact command, source fingerprints and pending live/World Model scope. |

## Source fingerprints

- agent/tools_zetaris.py: 660536fc9ef9a0d13c2bee855880982cf0b0280259b8d7eebb284beb0d01b9f2
- agent/llm.py: dd093b7d54b653e136bf02902e352e8299a276b60479a4d7293b0897dfef132a
- agent/analyzer.py: f30070b8589f9c2908dcfad59d2d0231a24534b36620d2d3bcfbd4e994b1c957
- agent/orchestrator.py: d72d08d52deda0a1fef0cd87d6dc8e3105a459e199c909ae22dfbc4eac6e1e8a
- agent/main.py: 003b456442509492b755b75a70a0cbfd0fb8df5cb389688dcfe46c5797f21d69
- tests/unit/test_analysis_round_trip.py: dc32918a10e1b2e1d8a37baef4dc741771ae91df4a2441b8421bc4861804af50
