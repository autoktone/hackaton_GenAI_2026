"""Standalone behavioral checks; network, native processes and private files are blocked."""
from __future__ import annotations

import copy
import io
import json
import subprocess
import unittest
import uuid
from contextlib import redirect_stdout
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from agent.analyzer import Analyzer
from agent.llm import NightshiftClient, ProviderError, StubProvider, WindowsRuntimeTransport, normalize_runtime_url
from agent.main import main
from agent.orchestrator import Orchestrator
from agent.tools_zetaris import ALLOWED_SQL, SqlError, StubSqlExecutor, ZetarisHttpTransport, ZetarisSettings, ZetarisSqlExecutor

OPERATION_ID = "00000000-0000-4000-8000-000000000001"
QUESTION = "Run the SELECT-one integration probe."


class ChangedProvider(StubProvider):
    def __init__(self, *, first=None, final=None):
        self._first = first
        self._final = final

    def complete(self, messages, **kwargs):
        response = super().complete(messages, **kwargs)
        change = self._final if messages[-1]["role"] == "tool" else self._first
        if change is not None:
            change(response["choices"][0]["message"])
        return response


class StandaloneTests(unittest.TestCase):
    def setUp(self):
        # Any accidental real I/O fails the test immediately.
        self.network = self.enterContext(patch("socket.create_connection",
            side_effect=AssertionError("Network is forbidden in standalone tests.")))
        self.native = self.enterContext(patch("subprocess.run",
            side_effect=AssertionError("Native processes are forbidden in standalone tests.")))
        self.private_files = self.enterContext(patch("pathlib.Path.read_text",
            side_effect=AssertionError("Private file reads are forbidden in standalone tests.")))

    def run_probe(self, provider=None, executor=None, **kwargs):
        return Orchestrator(Analyzer(provider or StubProvider()),
                            executor or StubSqlExecutor()).run(QUESTION, **kwargs)

    def test_complete_stub_path_and_causal_trace(self):
        result = self.run_probe()
        self.assertEqual(result["status"], "PASSED")
        self.assertEqual(result["counts"], {"inferenceDispatches": 2, "toolExecutions": 1})
        self.assertEqual(result["profile"], {"providerKind": "standalone_stub", "sourceKind": "standalone_stub"})
        self.assertFalse(result["worldModelUsed"])
        self.assertFalse(result["workflowExecuted"])
        self.assertFalse(result["durableTrace"])
        self.assertFalse(result["analysisResult"]["validation"]["domainValidated"])
        events = result["trace"]
        kinds = [event["eventType"] for event in events]
        self.assertLess(kinds.index("TOOL_REQUEST_RECEIVED"), kinds.index("SQL_DISPATCHED"))
        self.assertLess(kinds.index("DATA_OPERATION_COMPLETED"), kinds.index("TOOL_RESULT_PREPARED"))
        self.assertEqual(kinds[-1], "PROBE_FINISHED")
        self.assertTrue(all(e["runId"] == result["runId"] for e in events))
        self.assertIn(result["analysisResult"]["data"]["evidenceId"], result["analysisResult"]["answer"])
        self.native.assert_not_called()
        self.private_files.assert_not_called()

    def test_two_same_user_requests_keep_contexts_and_receipts_separate(self):
        orchestrator = Orchestrator(Analyzer(StubProvider()), StubSqlExecutor())
        first = orchestrator.run(QUESTION, user_id="USR-DEMO")
        second = orchestrator.run(QUESTION, user_id="USR-DEMO")
        for name in ["runId", "requestId", "taskId", "attemptId"]:
            self.assertNotEqual(first[name], second[name])
        self.assertNotEqual(first["analysisResult"]["data"]["operationId"],
                            second["analysisResult"]["data"]["operationId"])
        self.assertTrue(all(e["runId"] == second["runId"] for e in second["trace"]))

    def test_stub_and_injected_rest_executor_share_result_contract(self):
        fake_http = Mock(timeout_seconds=15)
        for raw in ["1", "1.0", "1E+0", 1]:
            with self.subTest(raw=raw):
                fake_http.post_query.return_value = {"data": [[raw]]}
                real_adapter = ZetarisSqlExecutor(fake_http)
                actual = real_adapter.execute(ALLOWED_SQL, operation_id=OPERATION_ID)
                stub = StubSqlExecutor().execute(ALLOWED_SQL, operation_id=OPERATION_ID)
                self.assertEqual(set(actual), set(stub))
                self.assertEqual(actual["rows"], [[1]])
                self.assertIs(type(actual["rows"][0][0]), int)
                self.assertEqual(actual["sourceKind"], "zetaris_rest")
                self.assertEqual(actual["operationId"], OPERATION_ID)

    def test_disallowed_sql_rejected_before_transport(self):
        transport = Mock(timeout_seconds=15)
        executor = ZetarisSqlExecutor(transport)
        for sql in ["SELECT 2 AS one", "SELECT 1 AS one;", "DROP TABLE x",
                    " SELECT 1 AS one", "SELECT 1 AS one -- comment", None]:
            with self.subTest(sql=sql):
                with self.assertRaises(SqlError) as error:
                    executor.execute(sql, operation_id=OPERATION_ID)
                self.assertEqual(error.exception.code, "SQL_NOT_ALLOWED")
        transport.post_query.assert_not_called()

    def test_invalid_or_ambiguous_rest_values_are_rejected(self):
        transport = Mock(timeout_seconds=15)
        executor = ZetarisSqlExecutor(transport)
        for rows in [[], [["1"], ["1"]], [[True]], [[None]], [["NaN"]],
                     [["2"]], [["1.000000000000000000000001"]], [[1, 2]], "1"]:
            with self.subTest(rows=rows):
                transport.post_query.return_value = {"data": rows}
                with self.assertRaises(SqlError):
                    executor.execute(ALLOWED_SQL, operation_id=OPERATION_ID)

    def test_no_structured_call_means_no_sql_execution(self):
        def remove(message):
            message.pop("tool_calls")
            message["content"] = "one is 1"
        result = self.run_probe(ChangedProvider(first=remove))
        self.assertEqual(result["errorCode"], "EXPECTED_ONE_STRUCTURED_TOOL_CALL")
        self.assertEqual(result["counts"]["toolExecutions"], 0)

    def test_unknown_tool_and_malformed_arguments_are_rejected(self):
        def change_name(message):
            message["tool_calls"][0]["function"]["name"] = "shell"
        def invalid_json(message):
            message["tool_calls"][0]["function"]["arguments"] = "not JSON"
        def extra_arguments(message):
            message["tool_calls"][0]["function"]["arguments"] = json.dumps(
                {"sql": ALLOWED_SQL, "runId": "another-run"})
        def forbidden_sql(message):
            message["tool_calls"][0]["function"]["arguments"] = json.dumps(
                {"sql": "DROP TABLE example"})
        for change, code in [(change_name, "TOOL_NOT_ALLOWED"),
                             (invalid_json, "INVALID_TOOL_ARGUMENTS"),
                             (extra_arguments, "INVALID_TOOL_ARGUMENTS"),
                             (forbidden_sql, "SQL_NOT_ALLOWED")]:
            with self.subTest(code=code):
                result = self.run_probe(ChangedProvider(first=change))
                self.assertEqual(result["errorCode"], code)
                self.assertEqual(result["counts"]["toolExecutions"], 0)
                self.assertEqual(result["trace"][-1]["payload"]["outcome"], "FAILED")

    def test_multiple_initial_calls_are_not_dispatched(self):
        def duplicate(message):
            message["tool_calls"].append(copy.deepcopy(message["tool_calls"][0]))
        result = self.run_probe(ChangedProvider(first=duplicate))
        self.assertEqual(result["errorCode"], "EXPECTED_ONE_STRUCTURED_TOOL_CALL")
        self.assertEqual(result["counts"]["toolExecutions"], 0)

    def test_additional_call_after_result_is_rejected_without_reexecution(self):
        def call_again(message):
            message["tool_calls"] = [{"id": "extra"}]
        result = self.run_probe(ChangedProvider(final=call_again))
        self.assertEqual(result["errorCode"], "ADDITIONAL_TOOL_CALL_NOT_ALLOWED")
        self.assertEqual(result["counts"]["toolExecutions"], 1)

    def test_answer_must_reference_the_returned_result(self):
        def omit_receipt(message):
            message["content"] = "one is 1"
        result = self.run_probe(ChangedProvider(final=omit_receipt))
        self.assertEqual(result["errorCode"], "FINAL_RESULT_NOT_REFERENCED")

    def test_executor_cannot_return_another_operations_result(self):
        class WrongOperation(StubSqlExecutor):
            def execute(self, sql, *, operation_id):
                return super().execute(sql, operation_id=str(uuid.uuid4()))
        result = self.run_probe(executor=WrongOperation())
        self.assertEqual(result["errorCode"], "INVALID_SQL_RESULT")
        self.assertNotIn("TOOL_RESULT_PREPARED", [e["eventType"] for e in result["trace"]])

    def test_sql_failure_keeps_failure_evidence_and_does_not_fall_back(self):
        class FailedSql(StubSqlExecutor):
            def execute(self, sql, *, operation_id):
                raise SqlError("ZETARIS_OUTCOME_UNKNOWN")
        result = self.run_probe(executor=FailedSql())
        self.assertEqual(result["errorCode"], "ZETARIS_OUTCOME_UNKNOWN")
        self.assertIsNone(result["analysisResult"])
        self.assertEqual(result["counts"]["inferenceDispatches"], 1)
        self.assertIn("DATA_OPERATION_FAILED", [e["eventType"] for e in result["trace"]])

    def test_provider_failure_is_not_retried(self):
        provider = Mock(kind="nightshift", route="meterless/auto")
        provider.complete.side_effect = ProviderError("PROVIDER_OUTCOME_UNKNOWN")
        result = self.run_probe(provider)
        self.assertEqual(result["errorCode"], "PROVIDER_OUTCOME_UNKNOWN")
        self.assertEqual(provider.complete.call_count, 1)
        self.assertEqual(result["counts"]["toolExecutions"], 0)

    def test_budget_exhaustion_prevents_sql(self):
        clock = Mock(side_effect=[0, 0, 181])
        result = Orchestrator(Analyzer(StubProvider(), clock=clock), StubSqlExecutor()).run(QUESTION)
        self.assertEqual(result["errorCode"], "ANALYSIS_BUDGET_EXHAUSTED")
        self.assertEqual(result["counts"]["toolExecutions"], 0)

    def test_insufficient_sql_budget_prevents_dispatch(self):
        transport = Mock(timeout_seconds=15)
        clock = Mock(side_effect=[0, 0, 170, 170])
        result = Orchestrator(Analyzer(StubProvider(), clock=clock),
                              ZetarisSqlExecutor(transport)).run(QUESTION)
        self.assertEqual(result["errorCode"], "INSUFFICIENT_SQL_TIME_BUDGET")
        transport.post_query.assert_not_called()

    def test_trace_sink_failure_prevents_protected_dispatch(self):
        provider = Mock(kind="nightshift", route="meterless/auto")
        def failed_sink(event):
            raise RuntimeError("DO_NOT_LOG_PRIVATE_DIAGNOSTIC")
        result = self.run_probe(provider, event_sink=failed_sink)
        self.assertEqual(result["errorCode"], "TRACE_SINK_FAILED")
        self.assertEqual(result["traceStatus"], "INCOMPLETE")
        self.assertNotIn("DO_NOT_LOG_PRIVATE_DIAGNOSTIC", json.dumps(result))
        provider.complete.assert_not_called()

    def test_unexpected_exception_is_sanitized(self):
        provider = Mock(kind="nightshift", route="meterless/auto")
        provider.complete.side_effect = ValueError("DO_NOT_LOG_PRIVATE_DIAGNOSTIC")
        result = self.run_probe(provider)
        self.assertEqual(result["errorCode"], "UNEXPECTED_APPLICATION_ERROR")
        self.assertNotIn("DO_NOT_LOG_PRIVATE_DIAGNOSTIC", json.dumps(result))

    def test_rest_request_uses_verified_body_and_fresh_request_uuid(self):
        settings = ZetarisSettings("http://localhost:8888/api/v1.0", "1", "UNIT_TEST_TOKEN")
        transport = ZetarisHttpTransport(settings)
        response = Mock(status=200)
        response.read.return_value = b'{"data":[["1"]]}'
        context = Mock()
        context.__enter__ = Mock(return_value=response)
        context.__exit__ = Mock(return_value=False)
        opener = Mock()
        opener.open.return_value = context
        with patch("agent.tools_zetaris.build_opener", return_value=opener):
            transport.post_query(ALLOWED_SQL, operation_id=OPERATION_ID)
        request = opener.open.call_args.args[0]
        self.assertEqual(json.loads(request.data),
            {"queryId": OPERATION_ID, "sql": ALLOWED_SQL, "source": "SqlEditor", "limit": 1})
        self.assertEqual(request.full_url,
                         "http://localhost:8888/api/v1.0/sql-editor/sqls/run")
        headers = {key.lower(): value for key, value in request.header_items()}
        self.assertEqual(headers["authorization"], "Bearer UNIT_TEST_TOKEN")
        self.assertEqual(headers["x-org-id"], "1")
        self.assertNotEqual(str(uuid.UUID(headers["x-request-id"])), OPERATION_ID)
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 15)
        self.assertNotIn("UNIT_TEST_TOKEN", repr(settings))

    def test_rest_unauthorized_does_not_read_or_expose_error_body(self):
        settings = ZetarisSettings("http://localhost:8888/api/v1.0", "1", "UNIT_TEST_TOKEN")
        error = HTTPError("http://localhost/", 401, "PRIVATE_DIAGNOSTIC", {}, None)
        with patch("agent.tools_zetaris.build_opener") as factory:
            factory.return_value.open.side_effect = error
            with self.assertRaises(SqlError) as caught:
                ZetarisHttpTransport(settings).post_query(ALLOWED_SQL, operation_id=OPERATION_ID)
        self.assertEqual(str(caught.exception), "ZETARIS_UNAUTHORIZED")

    def test_private_configuration_is_explicit_and_never_executed(self):
        text = ("ZETARIS_REST_URL=http://localhost:8888/api/v1.0\n"
                "ZETARIS_ORG_ID=1\nZETARIS_API_KEY='UNIT_TEST_TOKEN'\n"
                "UNRELATED=PRIVATE_DIAGNOSTIC\n")
        with patch("pathlib.Path.read_text", return_value=text):
            settings = ZetarisSettings.from_env_file("/explicit/.env.local", environ={})
        self.assertEqual(settings.org_id, "1")
        self.assertNotIn("UNIT_TEST_TOKEN", repr(settings))
        with self.assertRaises(SqlError):
            ZetarisSettings.from_env_file("/explicit/.env", environ={})
        self.native.assert_not_called()

    def test_configuration_never_guesses_endpoint_or_org(self):
        with patch("pathlib.Path.read_text", return_value="ZETARIS_API_KEY=UNIT_TEST_TOKEN"):
            with self.assertRaises(SqlError) as caught:
                ZetarisSettings.from_env_file("/explicit/.env.local", environ={})
        self.assertEqual(caught.exception.code, "MISSING_ZETARIS_CONFIGURATION")
        for url in ["http://example.org/api/v1.0", "http://localhost:8889/api/v1.0",
                    "http://user:pass@localhost:8888/api/v1.0",
                    "http://localhost:8888/api/v1.0?token=example"]:
            with self.subTest(url=url), self.assertRaises(SqlError):
                ZetarisSettings(url, "1", "UNIT_TEST_TOKEN")

    def test_runtime_url_normalization_and_unknown_meterless_route(self):
        for value in ["127.0.0.1:8088", "http://127.0.0.1:8088/v1",
                      "http://127.0.0.1:8088/v1/chat/completions",
                      "http://127.0.0.1:8088/v1/models",
                      "http://127.0.0.1:8088/healthz"]:
            self.assertEqual(normalize_runtime_url(value), "http://127.0.0.1:8088/v1")
        client = NightshiftClient(Mock(), route="meterless/new-class.deep")
        self.assertEqual(client.route, "meterless/new-class.deep")

    def test_runtime_transport_rejects_nonlocal_and_secret_bearing_urls(self):
        for value in ["http://example.org/v1", "http://user:pass@localhost:8088/v1",
                      "http://localhost:8088/connect#k=example"]:
            with self.subTest(value=value), self.assertRaises(ProviderError):
                WindowsRuntimeTransport(value)
        self.native.assert_not_called()

    def test_windows_worker_receives_payload_as_data_not_command_text(self):
        dangerous = "User text: $(must-not-run); 'quoted' \u00e9"
        process = Mock(returncode=0, stdout=json.dumps({"ok": True, "body": {"choices": []}}))
        transport = WindowsRuntimeTransport("http://127.0.0.1:8088/v1")
        with patch("agent.llm.subprocess.run", return_value=process) as launch:
            response = transport.post({"messages": [{"content": dangerous}]}, timeout_seconds=20)
        self.assertEqual(response, {"choices": []})
        self.assertNotIn(dangerous, " ".join(launch.call_args.args[0]))
        sent = json.loads(launch.call_args.kwargs["input"])
        self.assertEqual(sent["payload"]["messages"][0]["content"], dangerous)
        self.assertEqual(sent["url"], "http://127.0.0.1:8088/v1/chat/completions")
        self.assertEqual(launch.call_count, 1)

    def test_windows_transport_classifies_failure_without_retry(self):
        transport = WindowsRuntimeTransport("http://127.0.0.1:8088/v1")
        for code in ["PROVIDER_UNAUTHORIZED", "PROVIDER_OUTCOME_UNKNOWN"]:
            process = Mock(returncode=0, stdout=json.dumps({"ok": False, "code": code}))
            with self.subTest(code=code):
                with patch("agent.llm.subprocess.run", return_value=process) as launch:
                    with self.assertRaises(ProviderError) as caught:
                        transport.post({}, timeout_seconds=10)
                self.assertEqual(caught.exception.code, code)
                self.assertEqual(launch.call_count, 1)
        with patch("agent.llm.subprocess.run",
                   side_effect=subprocess.TimeoutExpired("worker", 10)) as launch:
            with self.assertRaises(ProviderError) as caught:
                transport.post({}, timeout_seconds=10)
        self.assertEqual(caught.exception.code, "PROVIDER_OUTCOME_UNKNOWN")
        self.assertEqual(launch.call_count, 1)

    def test_cli_stub_profile_does_not_read_private_configuration(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = main(["--provider", "stub", "--sql-executor", "stub",
                         "--zetaris-env-file", "/must-not-read/.env.local",
                         "--nightshift-base-url", "http://must-not-contact/v1"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout.getvalue())["status"], "PASSED")
        self.private_files.assert_not_called()
        self.native.assert_not_called()

    def test_cli_requires_explicit_live_configuration(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = main(["--provider", "nightshift", "--sql-executor", "stub"])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(stdout.getvalue())["errorCode"],
                         "EXPLICIT_NIGHTSHIFT_CONFIGURATION_REQUIRED")
        self.private_files.assert_not_called()
        self.native.assert_not_called()


if __name__ == "__main__":
    unittest.main()
