"""Isolated smoke checks; no real network, native process or private configuration."""
from __future__ import annotations

import importlib
import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

import smoke_test
from agent.llm import ProviderError
from agent.tools_zetaris import SqlError, StubSqlExecutor, ZetarisSettings


def provider_response(model="nvidia/nemotron-test", text="ready"):
    return {"model": model, "choices": [{
        "message": {"role": "assistant", "content": text}}]}


class SmokeTests(unittest.TestCase):
    def setUp(self):
        self.network = self.enterContext(patch("socket.create_connection",
            side_effect=AssertionError("Live network forbidden.")))
        self.native = self.enterContext(patch("subprocess.run",
            side_effect=AssertionError("Native processes forbidden.")))
        self.private = self.enterContext(patch("pathlib.Path.read_text",
            side_effect=AssertionError("Private configuration reads forbidden.")))

    def run_checks(self, *, provider=None, executor=None, web_check=None):
        provider = provider or Mock(route="meterless/auto")
        if not provider.complete.side_effect and not isinstance(provider.complete.return_value, dict):
            provider.complete.return_value = provider_response()
        web_check = web_check or Mock()
        return smoke_test.run_checks(web_check=web_check,
            sql_executor=executor or StubSqlExecutor(), provider=provider)

    def test_three_independent_checks_pass_with_explicit_dependencies(self):
        provider = Mock(route="meterless/auto")
        provider.complete.return_value = provider_response()
        web = Mock()
        results, evidence = self.run_checks(provider=provider, web_check=web)
        self.assertEqual([r["status"] for r in results], ["PASS"] * 3)
        self.assertEqual([r["name"] for r in results], list(smoke_test.CHECK_NAMES))
        self.assertEqual(evidence["sql"]["rows"], [[1]])
        self.assertEqual(evidence["power"]["reportedModel"], "nvidia/nemotron-test")
        self.assertEqual(provider.complete.call_count, 1)
        self.assertEqual(provider.complete.call_args.kwargs["tools"], [])
        web.assert_called_once_with()
        self.native.assert_not_called()
        self.private.assert_not_called()

    def test_failed_web_check_does_not_hide_other_results_or_retry(self):
        provider = Mock(route="meterless/auto")
        provider.complete.return_value = provider_response()
        web = Mock(side_effect=SmokeErrorForTest())
        results, _ = self.run_checks(provider=provider, web_check=web)
        self.assertEqual([r["status"] for r in results], ["FAIL", "PASS", "PASS"])
        self.assertEqual(results[0]["errorCode"], "UNEXPECTED_SMOKE_ERROR")
        self.assertEqual(web.call_count, 1)

    def test_sql_failure_is_sanitized_and_does_not_activate_stub(self):
        executor = Mock(kind="zetaris_rest")
        executor.execute.side_effect = SqlError("ZETARIS_OUTCOME_UNKNOWN")
        results, evidence = self.run_checks(executor=executor)
        self.assertEqual(results[1]["errorCode"], "ZETARIS_OUTCOME_UNKNOWN")
        self.assertNotIn("sql", evidence)
        self.assertEqual(executor.execute.call_count, 1)

    def test_model_failure_is_sanitized_and_not_retried(self):
        provider = Mock(route="meterless/auto")
        provider.complete.side_effect = ProviderError("PROVIDER_OUTCOME_UNKNOWN")
        results, evidence = self.run_checks(provider=provider)
        self.assertEqual(results[2]["errorCode"], "PROVIDER_OUTCOME_UNKNOWN")
        self.assertEqual(provider.complete.call_count, 1)
        self.assertNotIn("power", evidence)

    def test_empty_or_tool_only_response_does_not_pass_power(self):
        cases = [
            {},
            {"model": "nemotron-test", "choices": []},
            provider_response(text=""),
            {"model": "nemotron-test", "choices": [{"message": {
                "role": "assistant", "content": None, "tool_calls": [{"id": "call"}]}}]},
        ]
        for response in cases:
            with self.subTest(response=response):
                provider = Mock(route="meterless/auto")
                provider.complete.return_value = response
                results, _ = self.run_checks(provider=provider)
                self.assertEqual(results[2]["status"], "FAIL")

    def test_power_does_not_claim_nemotron_without_reported_identity(self):
        for model in [None, "", "another-provider/model"]:
            with self.subTest(model=model):
                provider = Mock(route="meterless/auto")
                provider.complete.return_value = provider_response(model=model)
                results, _ = self.run_checks(provider=provider)
                self.assertEqual(results[2]["errorCode"], "NEMOTRON_IDENTITY_NOT_ESTABLISHED")

    def test_import_does_not_run_checks_or_read_configuration(self):
        importlib.reload(smoke_test)
        self.network.assert_not_called()
        self.native.assert_not_called()
        self.private.assert_not_called()

    def test_web_endpoint_is_explicit_and_rejects_secret_bearing_urls(self):
        for value in [None, "", "http://user:pass@localhost:3000",
                      "http://localhost:3000?token=example",
                      "http://localhost:8889", "http://example.org"]:
            with self.subTest(value=value), self.assertRaises(smoke_test.SmokeError):
                smoke_test.validate_web_url(value)
        self.assertEqual(smoke_test.validate_web_url("http://localhost:3000"),
                         "http://localhost:3000")

    def test_web_check_uses_one_bounded_get_without_reading_body(self):
        response = Mock(status=200)
        context = Mock()
        context.__enter__ = Mock(return_value=response)
        context.__exit__ = Mock(return_value=False)
        opener = Mock()
        opener.open.return_value = context
        with patch("smoke_test.build_opener", return_value=opener):
            smoke_test.check_zetaris_web("http://localhost:3000")
        self.assertEqual(opener.open.call_count, 1)
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 10)
        self.assertEqual(opener.open.call_args.args[0].get_method(), "GET")
        response.read.assert_not_called()

    def test_failures_produce_nonzero_exit_and_no_raw_exception_text(self):
        results, evidence = self.run_checks(web_check=Mock(
            side_effect=ValueError("PRIVATE_DIAGNOSTIC_DO_NOT_LOG")))
        output = io.StringIO()
        with redirect_stdout(output):
            code = smoke_test.print_results(results, evidence, details=True)
        self.assertEqual(code, 1)
        self.assertNotIn("PRIVATE_DIAGNOSTIC_DO_NOT_LOG", output.getvalue())
        self.assertIn("FAIL Data: Zetaris web interface UNEXPECTED_SMOKE_ERROR", output.getvalue())

    def test_configuration_loader_preserves_optional_web_url_and_env_precedence(self):
        text = ("ZETARIS_REST_URL=http://localhost:8888/api/v1.0\n"
                "ZETARIS_ORG_ID=1\nZETARIS_API_KEY=UNIT_TEST_TOKEN\n"
                "ZETARIS_BASE_URL=http://localhost:3000\n")
        with patch("pathlib.Path.read_text", return_value=text):
            settings = ZetarisSettings.from_env_file("/explicit/.env.local",
                environ={"ZETARIS_BASE_URL": "http://localhost:3001"})
        self.assertEqual(settings.web_url, "http://localhost:3001")
        self.assertNotIn("UNIT_TEST_TOKEN", repr(settings))

    def test_cli_requires_web_endpoint_without_guessing_or_live_calls(self):
        settings = ZetarisSettings("http://localhost:8888/api/v1.0", "1", "UNIT_TEST_TOKEN")
        output = io.StringIO()
        with patch("smoke_test.ZetarisSettings.from_env_file", return_value=settings):
            with redirect_stdout(output):
                code = smoke_test.main([
                    "--zetaris-env-file", "/explicit/.env.local",
                    "--nightshift-base-url", "http://127.0.0.1:8088/v1",
                    "--route", "meterless/auto", "--transport", "windows-loopback"])
        self.assertEqual(code, 1)
        self.assertEqual(output.getvalue().count("FAIL "), 3)
        self.assertIn("EXPLICIT_ZETARIS_WEB_URL_REQUIRED", output.getvalue())
        self.network.assert_not_called()
        self.native.assert_not_called()


class SmokeErrorForTest(Exception):
    pass


if __name__ == "__main__":
    unittest.main()
