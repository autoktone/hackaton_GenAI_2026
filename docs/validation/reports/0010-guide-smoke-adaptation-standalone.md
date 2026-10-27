# 0010 - Adapted guide smoke standalone validation

- Date: 2026-10-27.
- Result: Passed within standalone scope.
- Approval evidence: Ok.
- Source: Participant Setup Guide, page 24, updated 21 October 2026.
- Live web/SQL/Runtime calls: none.
- Actual private configuration/token reads: none.
- Packages installed: none.
- Git reference: not collected.

## Adaptation

Replace the copied example in smoke_test.py with three equivalent layer checks
using the standard library and existing application clients.

Retain the guide's three PASS names. Use explicit .env.local settings and
Windows-loopback Runtime transport, without copying credentials.
The selected configuration loader now retains optional ZETARIS_BASE_URL in
a repr-hidden web_url field; SQL execution and existing constructor calls
remain compatible.

Differences are recorded in the source and README:
- Import-safe main guard instead of top-level network checks.
- No openai, requests or python-dotenv dependency.
- No guessed web or Runtime endpoint.
- Existing SELECT 1 AS one allowlist instead of the guide's SELECT 1 spelling.
- Bounded non-retrying project clients; no redirects or proxy discovery.
- Sanitized errors rather than exception/body excerpts.
- Nonempty text plus Runtime-reported Nemotron identity for Power.
- Nonzero process exit on any failed check.
- Dependency injection for isolated tests.

The three configured checks remain independent. A web failure does not
suppress SQL or model checks. Invalid initial configuration prevents all
network work. A client timeout does not prove remote cancellation.

## Files

- smoke_test.py: adapted guide check with source/history.
- agent/tools_zetaris.py: optional selected web setting and history.
- tests/unit/test_smoke_test.py: new isolated behavioral tests.
- README, project status, permanent instructions and validation register:
  scope, procedures, evidence and histories.

## Exact executed commands

```powershell
wsl.exe -d Ubuntu --cd /home/info/flood-risk-intelligence --exec python3 -B -m unittest discover -s tests/unit -p test_smoke_test.py -v
```

```powershell
wsl.exe -d Ubuntu --cd /home/info/flood-risk-intelligence --exec python3 -B -m unittest discover -s tests/unit -p test_analysis_round_trip.py -v
```

## Expected and observed results

Expected: isolated checks pass, failures remain visible and sanitized, imports
do not perform I/O, and the configuration extension preserves the application
round-trip behavior.

Observed:
- Smoke suite: exit 0; 12 tests in 0.157 seconds, OK.
- Affected application suite: exit 0; 27 tests in 0.222 seconds, OK.
- Command-runner wall times were approximately 13.37 and 3.08 seconds.
  These include invocation overhead and are distinct from unittest timings.

### Smoke output

```text
test_cli_requires_web_endpoint_without_guessing_or_live_calls (test_smoke_test.SmokeTests.test_cli_requires_web_endpoint_without_guessing_or_live_calls) ... ok
test_configuration_loader_preserves_optional_web_url_and_env_precedence (test_smoke_test.SmokeTests.test_configuration_loader_preserves_optional_web_url_and_env_precedence) ... ok
test_empty_or_tool_only_response_does_not_pass_power (test_smoke_test.SmokeTests.test_empty_or_tool_only_response_does_not_pass_power) ... ok
test_failed_web_check_does_not_hide_other_results_or_retry (test_smoke_test.SmokeTests.test_failed_web_check_does_not_hide_other_results_or_retry) ... ok
test_failures_produce_nonzero_exit_and_no_raw_exception_text (test_smoke_test.SmokeTests.test_failures_produce_nonzero_exit_and_no_raw_exception_text) ... ok
test_import_does_not_run_checks_or_read_configuration (test_smoke_test.SmokeTests.test_import_does_not_run_checks_or_read_configuration) ... ok
test_model_failure_is_sanitized_and_not_retried (test_smoke_test.SmokeTests.test_model_failure_is_sanitized_and_not_retried) ... ok
test_power_does_not_claim_nemotron_without_reported_identity (test_smoke_test.SmokeTests.test_power_does_not_claim_nemotron_without_reported_identity) ... ok
test_sql_failure_is_sanitized_and_does_not_activate_stub (test_smoke_test.SmokeTests.test_sql_failure_is_sanitized_and_does_not_activate_stub) ... ok
test_three_independent_checks_pass_with_explicit_dependencies (test_smoke_test.SmokeTests.test_three_independent_checks_pass_with_explicit_dependencies) ... ok
test_web_check_uses_one_bounded_get_without_reading_body (test_smoke_test.SmokeTests.test_web_check_uses_one_bounded_get_without_reading_body) ... ok
test_web_endpoint_is_explicit_and_rejects_secret_bearing_urls (test_smoke_test.SmokeTests.test_web_endpoint_is_explicit_and_rejects_secret_bearing_urls) ... ok

----------------------------------------------------------------------
Ran 12 tests in 0.157s

OK
```

### Affected application output

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
Ran 27 tests in 0.222s

OK
```

## Verification scope

The tests explicitly replace network connections, native processes and
private-file reads. Mocks return synthetic data; no result here is a live
platform result.

Covered behaviors include three independent checks, failure exit status,
secret-safe errors, no fallback/retry, refusal of empty/tool-only model output,
unestablished model identity, import safety, explicit web configuration,
bounded web GET construction and environment precedence.

The earlier live application SELECT-one evidence remains in report 0009.
Its historical fingerprints are not rewritten after the configuration change.

## Pending live validation

The adapted smoke itself has not run. A separately approved run will attempt
one web GET, one real SQL query and one Runtime text request. Do not infer its
three PASS lines from these unit tests or from the earlier application probe.

UI reachability, present ZETARIS_BASE_URL configuration and the Runtime's
ready-prompt response remain to be observed. The web check establishes an
HTTP 200 response, not complete UI functionality. It deliberately does not
follow redirects, unlike the original requests example.

No World Model execution, hydrological analysis, JUDGE acceptance, durable
trace or complete hackathon compliance is claimed.

## References

- [Participant Setup Guide](../../Participant%20Setup%20Guide.pdf)
- [Project status](../../PROJECT_STATUS.md)
- [README procedure](../../../README.md)
- [Validation register](../README.md)
- [Earlier live application probe](0009-select-one-live-application.md)
- [Earlier standalone application checks](0008-select-one-application-standalone.md)

## Report history

| Date | Change |
|---|---|
| 2026-10-27 | Recorded the guide-smoke adaptation, 12 isolated and 27 affected passing checks, explicit differences and pending live execution. |

## Source fingerprints

- smoke_test.py: 076b47809b95e2df74a327dc73afcc92418711c86122e8f8d0d3ea86c95eee7e
- agent/tools_zetaris.py: 7628f0fd633818081f4f4c033968b7e846b92cbd14cc55d6c37e42dc162d59c0
- tests/unit/test_smoke_test.py: b39b6ea8538cd7070f4fa5189eebecdc43a18fd048ce5326d366bb28a46cb550
