"""Standalone checks for bounded SQL attempts, provenance and human escalation."""
from __future__ import annotations

import json
from pathlib import Path
import unittest
import uuid
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from agent.hydro import HydroAnalyzer, SnapshotSqlExecutor, OBSERVATIONS_SQL
from agent.hydro_catalog import HydroQueryPolicy
from agent.llm import ProviderError
from agent.orchestrator import Orchestrator, OrchestrationError
from agent.tools_zetaris import (
    SqlError, ZetarisHttpTransport, ZetarisSettings, sql_http_error_code,
)


class OneReadProvider:
    kind = "standalone_stub"
    route = "standalone_stub"

    def __init__(self, sql=OBSERVATIONS_SQL):
        self.sql = sql
        self.calls = 0

    def complete(self, messages, **kwargs):
        self.calls += 1
        results = [json.loads(m["content"]) for m in messages if m["role"] == "tool"]
        if results:
            message = {"role": "assistant", "content":
                       "Scripted test response; conclusions remain unverified."}
        else:
            message = {"role": "assistant", "content": None, "tool_calls": [{
                "id": "call_incident_read", "type": "function",
                "function": {"name": "run_sql",
                             "arguments": json.dumps({"sql": self.sql})}}]}
        return {"model": "standalone_stub", "choices": [{"message": message}]}


class FailingSnapshot(SnapshotSqlExecutor):
    def __init__(self, snapshot, errors=(), on_execute=None):
        super().__init__(snapshot)
        self.errors = list(errors)
        self.calls = []
        self.on_execute = on_execute

    def execute(self, sql, *, operation_id):
        self.calls.append((sql, operation_id))
        if self.on_execute is not None:
            self.on_execute()
        if self.errors:
            error = self.errors.pop(0)
            if error:
                raise SqlError(error)
        return super().execute(sql, operation_id=operation_id)


class IncidentHandlingTests(unittest.TestCase):
    def setUp(self):
        fixture = Path(__file__).resolve().parents[2] / "data/snapshots/hubeau-givry-2026-10-27.json"
        self.snapshot = json.loads(fixture.read_text(encoding="utf-8"))
        self.enterContext(patch("socket.create_connection", side_effect=AssertionError("No network.")))
        self.enterContext(patch("subprocess.run", side_effect=AssertionError("No native process.")))
        self.enterContext(patch("pathlib.Path.read_text", side_effect=AssertionError("No private files.")))
        self.sleep = self.enterContext(patch("agent.orchestrator.time.sleep"))

    def run_case(self, errors=(), provider=None, **kwargs):
        provider = provider or OneReadProvider()
        executor = FailingSnapshot(self.snapshot, errors)
        result = Orchestrator(HydroAnalyzer(provider), executor, sql_attempts=2).run(
            "Read the available hydrometry and state limitations.", **kwargs)
        return result, provider, executor

    def test_transient_failure_retries_once_with_same_operation_and_distinct_attempts(self):
        result, provider, executor = self.run_case(["ZETARIS_TRANSIENT_HTTP_ERROR"])
        self.assertEqual(result["status"], "PASSED", result["errorCode"])
        self.assertEqual(result["workflowVersion"], "1.3.0")
        self.assertEqual(result["counts"],
                         {"inferenceDispatches": 2, "toolExecutions": 1, "sqlAttempts": 2})
        self.assertEqual(executor.calls[0][1], executor.calls[1][1])
        dispatched = [e for e in result["trace"] if e["eventType"] == "SQL_DISPATCHED"]
        self.assertEqual(dispatched[0]["taskId"], dispatched[1]["taskId"])
        self.assertNotEqual(dispatched[0]["attemptId"], dispatched[1]["attemptId"])
        self.assertIsNone(result["humanIntervention"])
        self.sleep.assert_called_once_with(0.25)

    def test_second_failure_suspends_without_another_model_request(self):
        result, provider, executor = self.run_case(
            ["ZETARIS_TRANSIENT_HTTP_ERROR", "ZETARIS_TRANSIENT_HTTP_ERROR"],
            user_id="USR-INCIDENT", request_id="REQ-INCIDENT", run_id="RUN-INCIDENT")
        self.assertEqual(result["status"], "WAITING_HUMAN")
        self.assertEqual(result["errorCode"], "HUMAN_INTERVENTION_REQUIRED")
        self.assertEqual(provider.calls, 1)
        self.assertEqual(len(executor.calls), 2)
        incident = result["humanIntervention"]
        self.assertEqual(incident["runId"], "RUN-INCIDENT")
        self.assertEqual(incident["userId"], "USR-INCIDENT")
        self.assertEqual(incident["operationId"], executor.calls[0][1])
        self.assertEqual(incident["action"], "CHECK_SOURCE_AND_RESTART_EXPLICITLY")
        self.assertIsNone(result["analysisResult"])
        self.assertFalse(any(e["eventType"] == "REPORT_PREPARED" for e in result["trace"]))
        self.assertEqual(result["trace"][-1]["payload"]["outcome"], "WAITING_HUMAN")

    def test_uncertain_read_can_be_repeated_but_original_uncertainty_is_traced(self):
        result, _, executor = self.run_case(["ZETARIS_OUTCOME_UNKNOWN"])
        self.assertEqual(result["status"], "PASSED", result["errorCode"])
        failure = next(e for e in result["trace"] if e["eventType"] == "SQL_ATTEMPT_FAILED")
        self.assertEqual(failure["payload"]["errorCode"], "ZETARIS_OUTCOME_UNKNOWN")
        self.assertEqual(len(executor.calls), 2)

    def test_nonretryable_failures_go_directly_to_human(self):
        for error in ["ZETARIS_UNAUTHORIZED", "ZETARIS_HTTP_ERROR",
                      "INVALID_ZETARIS_RESPONSE", "INVALID_SQL_RESULT"]:
            with self.subTest(error=error):
                result, provider, executor = self.run_case([error])
                self.assertEqual(result["status"], "WAITING_HUMAN")
                self.assertEqual(len(executor.calls), 1)
                self.assertEqual(provider.calls, 1)
                self.assertEqual(result["humanIntervention"]["reason"], error)

    def test_inference_is_never_retried_by_sql_policy(self):
        provider = Mock(kind="nightshift", route="meterless/auto")
        provider.complete.side_effect = ProviderError("PROVIDER_OUTCOME_UNKNOWN")
        result, _, executor = self.run_case(provider=provider)
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(provider.complete.call_count, 1)
        self.assertEqual(executor.calls, [])
        self.assertIsNone(result["humanIntervention"])

    def test_empty_successful_read_is_not_automatically_retried(self):
        provider = OneReadProvider(
            "SELECT * FROM flood_analysis.v_hydro_observations WHERE code_station = 'UNKNOWN' LIMIT 5")
        result, _, executor = self.run_case(provider=provider)
        self.assertEqual(result["status"], "PASSED", result["errorCode"])
        self.assertEqual(len(executor.calls), 1)
        self.assertEqual(result["analysisResult"]["data"]["rows"], [])
        self.sleep.assert_not_called()

    def test_insufficient_retry_budget_requests_human_without_second_dispatch(self):
        class Clock:
            now = 0
            def __call__(self):
                return self.now
        clock = Clock()
        executor = FailingSnapshot(self.snapshot, ["ZETARIS_TRANSIENT_HTTP_ERROR"],
                                   on_execute=lambda: setattr(clock, "now", 170))
        executor.timeout_seconds = 15
        provider = OneReadProvider()
        with patch("agent.orchestrator.time.monotonic", clock):
            result = Orchestrator(HydroAnalyzer(provider, clock=clock), executor,
                                  sql_attempts=2).run("Read one admitted source.")
        self.assertEqual(result["status"], "WAITING_HUMAN")
        self.assertEqual(result["humanIntervention"]["reason"], "INSUFFICIENT_RETRY_TIME_BUDGET")
        self.assertEqual(len(executor.calls), 1)
        self.assertEqual(provider.calls, 1)
        self.sleep.assert_not_called()

    def test_backend_provenance_does_not_claim_model_or_scientific_verification(self):
        result, _, _ = self.run_case()
        analysis = result["analysisResult"]
        self.assertEqual(analysis["answer"], "Scripted test response; conclusions remain unverified.")
        self.assertFalse(analysis["validation"]["toolResultReferenced"])
        self.assertTrue(analysis["validation"]["provenanceAttached"])
        self.assertFalse(analysis["validation"]["domainValidated"])
        self.assertEqual(analysis["validation"]["runtimeJudge"], "not_established")

    def test_intervention_identity_does_not_leak_between_same_user_runs(self):
        first, _, _ = self.run_case(["ZETARIS_HTTP_ERROR"], run_id="RUN-FIRST")
        second, _, _ = self.run_case(["ZETARIS_HTTP_ERROR"], run_id="RUN-SECOND")
        self.assertNotEqual(first["humanIntervention"]["operationId"],
                            second["humanIntervention"]["operationId"])
        self.assertNotEqual(first["humanIntervention"]["interventionId"],
                            second["humanIntervention"]["interventionId"])

    def test_retry_policy_must_match_an_explicit_new_workflow(self):
        executor = FailingSnapshot(self.snapshot)
        store = Mock(workflow_version="1.2.0")
        with self.assertRaises(OrchestrationError) as caught:
            Orchestrator(HydroAnalyzer(OneReadProvider()), executor,
                         execution_store=store, sql_attempts=2)
        self.assertEqual(caught.exception.code, "WORKFLOW_RETRY_POLICY_CONFLICT")
        store.begin.assert_not_called()
        for invalid in [True, 0, 3]:
            with self.subTest(invalid=invalid), self.assertRaises(OrchestrationError):
                Orchestrator(HydroAnalyzer(OneReadProvider()), executor, sql_attempts=invalid)

    def test_http_failure_classification_is_bounded_and_explicit(self):
        for status in [408, 500, 502, 503, 504]:
            self.assertEqual(sql_http_error_code(status), "ZETARIS_TRANSIENT_HTTP_ERROR")
        for status in [401, 403]:
            self.assertEqual(sql_http_error_code(status), "ZETARIS_UNAUTHORIZED")
        for status in [400, 404, 429]:
            self.assertEqual(sql_http_error_code(status), "ZETARIS_HTTP_ERROR")

    def test_physical_rest_query_id_differs_from_logical_operation(self):
        policy = HydroQueryPolicy()
        settings = ZetarisSettings("http://localhost:8888/api/v1.0", "1", "UNIT_TEST_TOKEN")
        transport = ZetarisHttpTransport(settings, sql_validator=policy.validate, query_limit=50)
        response = Mock(status=200)
        response.read.return_value = b'{"data":[]}'
        context = Mock()
        context.__enter__ = Mock(return_value=response)
        context.__exit__ = Mock(return_value=False)
        opener = Mock()
        opener.open.return_value = context
        operation = str(uuid.uuid4())
        attempts = [str(uuid.uuid4()), str(uuid.uuid4())]
        with patch("agent.tools_zetaris.build_opener", return_value=opener):
            for attempt in attempts:
                transport.post_query(OBSERVATIONS_SQL, operation_id=operation, query_id=attempt)
        bodies = [json.loads(call.args[0].data) for call in opener.open.call_args_list]
        self.assertEqual([body["queryId"] for body in bodies], attempts)
        self.assertTrue(all(body["queryId"] != operation for body in bodies))
        self.assertTrue(all(body["limit"] == 50 for body in bodies))

    def test_http_error_body_is_not_exposed_or_read(self):
        settings = ZetarisSettings("http://localhost:8888/api/v1.0", "1", "UNIT_TEST_TOKEN")
        error = HTTPError("http://localhost/", 503, "DO_NOT_LOG_PRIVATE_DIAGNOSTIC", {}, None)
        with patch("agent.tools_zetaris.build_opener") as factory:
            factory.return_value.open.side_effect = error
            with self.assertRaises(SqlError) as caught:
                ZetarisHttpTransport(settings).post_query(
                    "SELECT 1 AS one", operation_id=str(uuid.uuid4()))
        self.assertEqual(caught.exception.code, "ZETARIS_TRANSIENT_HTTP_ERROR")
        self.assertNotIn("DO_NOT_LOG", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
