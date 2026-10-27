"""Isolated execution-ledger safety checks; no native processes or platform I/O."""
from copy import deepcopy
from unittest.mock import Mock, patch
import unittest

from agent.analyzer import Analyzer
from agent.execution_state import ExecutionStateError, ExecutionStateStore
from agent.llm import StubProvider
from agent.orchestrator import Orchestrator
from agent.tools_zetaris import StubSqlExecutor
from agent.world_model import BridgeOutcomeUnknown, BridgeProtocolError, WorldModelClient

TIME = "2026-10-27T12:00:00.000Z"


def receipt(revision=1):
    return {"runId": "RUN-001", "nativeEventCount": revision,
            "nativeAuditCount": revision, "state": {
                "revision": revision, "run": {
                    "runId": "RUN-001", "userId": "USR-001", "requestId": "REQ-001",
                    "workflowVersion": "1.2.0", "executionKind": "application-execution"}}}


def event():
    return {"eventId": "EVT-002", "eventType": "PROBE_CONTEXT_CREATED",
            "userId": "USR-001", "requestId": "REQ-001", "runId": "RUN-001",
            "stepId": "qualify-request", "taskId": "TASK-001",
            "attemptId": "ATTEMPT-001", "agentId": "planner",
            "recordedAt": TIME, "payload": {}}


class ExecutionStateTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("socket.create_connection",
            side_effect=AssertionError("Network forbidden in isolated tests.")))
        self.enterContext(patch("subprocess.Popen",
            side_effect=AssertionError("Native processes forbidden in isolated tests.")))

    def recorder(self):
        client = Mock()
        client.create_execution.return_value = receipt()
        store = ExecutionStateStore(client)
        ledger = store.begin(user_id="USR-001", request_id="REQ-001",
            run_id="RUN-001", question="SELECT-one test",
            provider_kind="standalone_stub", source_kind="standalone_stub")
        return client, ledger

    def test_creation_binds_explicit_profile_and_scope(self):
        client, ledger = self.recorder()
        params = client.create_execution.call_args.kwargs
        self.assertEqual(params["principal_id"], "USR-001")
        self.assertEqual(params["expectedRevision"], 0)
        self.assertEqual(params["profile"], {
            "providerKind": "standalone_stub", "sourceKind": "standalone_stub"})
        self.assertEqual(params["context"], {})

    def test_append_enriches_envelope_and_uses_current_revision(self):
        client, ledger = self.recorder()
        client.append_event.return_value = receipt(2)
        ledger.append(event())
        params = client.append_event.call_args.kwargs
        self.assertEqual(params["expected_revision"], 1)
        self.assertEqual(params["event"]["schemaVersion"], 1)
        self.assertEqual(params["event"]["workflowVersion"], "1.2.0")
        self.assertEqual(params["event"]["actorId"], "orchestrator")
        self.assertEqual(params["event"]["occurredAt"], TIME)
        self.assertNotIn("schemaVersion", event())

    def test_cross_run_event_never_reaches_client(self):
        client, ledger = self.recorder()
        wrong = event()
        wrong["runId"] = "RUN-OTHER"
        with self.assertRaises(ExecutionStateError) as caught:
            ledger.append(wrong)
        self.assertEqual(caught.exception.code, "WORLD_MODEL_SCOPE_CONFLICT")
        client.append_event.assert_not_called()

    def test_malformed_mutation_receipt_disables_further_appends(self):
        client, ledger = self.recorder()
        client.append_event.return_value = receipt(99)
        with self.assertRaises(ExecutionStateError) as caught:
            ledger.append(event())
        self.assertEqual(caught.exception.code, "WORLD_MODEL_OUTCOME_UNKNOWN")
        with self.assertRaises(ExecutionStateError):
            ledger.append(event())
        self.assertEqual(client.append_event.call_count, 1)

    def test_uncertain_mutation_is_not_retried(self):
        client, ledger = self.recorder()
        client.append_event.side_effect = BridgeOutcomeUnknown("not logged")
        with self.assertRaises(ExecutionStateError) as caught:
            ledger.append(event())
        self.assertEqual(caught.exception.code, "WORLD_MODEL_OUTCOME_UNKNOWN")
        with self.assertRaises(ExecutionStateError):
            ledger.snapshot()
        self.assertEqual(client.append_event.call_count, 1)
        client.get_run.assert_not_called()

    def test_mutating_protocol_command_invalidates_client_on_timeout(self):
        transport = Mock()
        transport.exchange.side_effect = TimeoutError()
        client = WorldModelClient(transport)
        with self.assertRaises(BridgeOutcomeUnknown):
            client.append_event(principal_id="USR-001", run_id="RUN-001",
                                event=event(), expected_revision=1)
        with self.assertRaises(BridgeProtocolError):
            client.ping(principal_id="USR-001")
        self.assertEqual(transport.exchange.call_count, 1)

    def test_snapshot_checks_scope_and_returns_an_independent_copy(self):
        client, ledger = self.recorder()
        client.get_run.return_value = receipt()
        first = ledger.snapshot()
        first["state"]["run"]["userId"] = "ALTERED"
        self.assertEqual(ledger.snapshot()["state"]["run"]["userId"], "USR-001")

    def test_unrecordable_intent_prevents_provider_and_sql(self):
        store = Mock()
        store.begin.side_effect = ExecutionStateError("WORLD_MODEL_UNAVAILABLE")
        provider = StubProvider()
        executor = StubSqlExecutor()
        with patch.object(provider, "complete", wraps=provider.complete) as model:
            with patch.object(executor, "execute", wraps=executor.execute) as sql:
                result = Orchestrator(Analyzer(provider), executor,
                                      execution_store=store).run("SELECT-one test")
        self.assertEqual(result["errorCode"], "WORLD_MODEL_UNAVAILABLE")
        self.assertEqual(result["traceStatus"], "INCOMPLETE")
        model.assert_not_called()
        sql.assert_not_called()

    def test_lost_creation_receipt_is_not_reported_as_known_failure(self):
        client = Mock()
        client.create_execution.return_value = {}
        with self.assertRaises(ExecutionStateError) as caught:
            ExecutionStateStore(client).begin(
                user_id="USR-001", request_id="REQ-001", run_id="RUN-001",
                question="SELECT-one test", provider_kind="standalone_stub",
                source_kind="standalone_stub")
        self.assertEqual(caught.exception.code, "WORLD_MODEL_OUTCOME_UNKNOWN")

    def test_question_bound_precedes_any_mutation(self):
        client = Mock()
        with self.assertRaises(ExecutionStateError):
            ExecutionStateStore(client).begin(
                user_id="USR-001", request_id="REQ-001", run_id="RUN-001",
                question="x" * 513, provider_kind="standalone_stub",
                source_kind="standalone_stub")
        client.create_execution.assert_not_called()
