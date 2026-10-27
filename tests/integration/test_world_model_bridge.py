"""Local integration tests: actual unchanged TypeScript reference, memory only."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import unittest

from agent.world_model import BridgeCommandError, SubprocessTransport, WorldModelClient

TIME = "2026-10-25T12:00:00Z"


def parameters(run_id="RUN-001", request_id="REQ-001"):
    return {
        "eventId": "EVT-001", "runId": run_id,
        "occurredAt": TIME, "recordedAt": TIME, "expectedRevision": 0,
        "request": {
            "userId": "USR-001", "requestId": request_id, "zoneId": "LOIRE-DEMO",
            "analysisTime": TIME, "forecastHorizonHours": 24,
            "mode": "historical_replay",
            "dataWindowStart": "2026-10-24T12:00:00Z",
            "dataWindowEnd": TIME,
        },
    }


class BridgeIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.transport = SubprocessTransport(profile="memory", timeout=10)
        self.client = WorldModelClient(self.transport)
        self.addCleanup(self.client.close)

    def test_create_and_read_reach_actual_engine_projection(self):
        ping = self.client.ping(principal_id="USR-001")
        self.assertEqual(ping["engine"]["package"], "@meterless/world-model-reference")
        created = self.client.create_run(principal_id="USR-001", **parameters())
        observed = self.client.get_run("RUN-001", principal_id="USR-001")
        self.assertEqual(created["nativeEntityId"], "operation-event:flood-risk-intelligence:EVT-001")
        self.assertEqual(observed["nativeEventCount"], 1)
        self.assertEqual(observed["nativeAuditCount"], 1)
        self.assertEqual(observed["state"]["revision"], 1)
        run = observed["state"]["run"]
        self.assertEqual(run["status"], "CREATED")
        self.assertEqual(run["workflowVersion"], "1.1.0")
        self.assertEqual(len(run["workflowSha256"]), 64)
        self.assertEqual(run["profile"], {"storage": "memory", "dataSource": "fixture", "inference": "disabled"})

    def test_identical_retry_precedes_now_newer_revision(self):
        params = parameters()
        first = self.client.create_run(principal_id="USR-001", **params)
        repeated = self.client.create_run(principal_id="USR-001", **params)
        self.assertFalse(first["duplicate"])
        self.assertTrue(repeated["duplicate"])
        self.assertEqual(first["nativeEventId"], repeated["nativeEventId"])
        self.assertEqual(repeated["acceptedRevision"], 1)
        self.assertEqual(repeated["nativeEventCount"], 1)
        self.assertEqual(self.client.get_run("RUN-001", principal_id="USR-001")["nativeEventCount"], 1)

    def test_conflicting_identity_cannot_overwrite_event(self):
        params = parameters()
        self.client.create_run(principal_id="USR-001", **params)
        changed = deepcopy(params)
        changed["request"]["forecastHorizonHours"] = 48
        with self.assertRaises(BridgeCommandError) as caught:
            self.client.create_run(principal_id="USR-001", **changed)
        self.assertEqual(caught.exception.code, "EVENT_CONFLICT")
        observed = self.client.get_run("RUN-001", principal_id="USR-001")
        self.assertEqual(observed["nativeEventCount"], 1)
        self.assertEqual(observed["state"]["run"]["request"]["forecastHorizonHours"], 24)

    def test_owner_checks_protect_reads_and_duplicate_results(self):
        self.client.create_run(principal_id="USR-001", **parameters())
        with self.assertRaises(BridgeCommandError) as read_error:
            self.client.get_run("RUN-001", principal_id="USR-002")
        self.assertEqual(read_error.exception.code, "FORBIDDEN")
        with self.assertRaises(BridgeCommandError) as retry_error:
            self.client.create_run(principal_id="USR-002", **parameters())
        self.assertEqual(retry_error.exception.code, "FORBIDDEN")
        self.assertEqual(self.client.get_run("RUN-001", principal_id="USR-001")["nativeEventCount"], 1)

    def test_invalid_request_does_not_allocate_namespace(self):
        params = parameters()
        params["request"]["forecastHorizonHours"] = True
        with self.assertRaises(BridgeCommandError) as caught:
            self.client.create_run(principal_id="USR-001", **params)
        self.assertEqual(caught.exception.code, "INVALID_REQUEST")
        self.assertEqual(self.client.ping(principal_id="USR-001")["namespaces"], 0)

    def test_independent_runs_allow_same_event_id_and_data_parameters(self):
        self.client.create_run(principal_id="USR-001", **parameters())
        self.client.create_run(principal_id="USR-001", **parameters("RUN-002", "REQ-002"))
        first = self.client.get_run("RUN-001", principal_id="USR-001")
        second = self.client.get_run("RUN-002", principal_id="USR-001")
        self.assertNotEqual(first["namespace"], second["namespace"])
        self.assertEqual(first["state"]["run"]["requestId"], "REQ-001")
        self.assertEqual(second["state"]["run"]["requestId"], "REQ-002")
        first["state"]["run"]["status"] = "ALTERED-CLIENT-COPY"
        self.assertEqual(self.client.get_run("RUN-001", principal_id="USR-001")["state"]["run"]["status"], "CREATED")
        self.assertEqual(second["nativeEventCount"], 1)

    def test_overlapping_calls_receive_their_own_correlated_results(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(self.client.create_run, principal_id="USR-001", **parameters("RUN-001", "REQ-001")),
                pool.submit(self.client.create_run, principal_id="USR-001", **parameters("RUN-002", "REQ-002")),
            ]
            receipts = [future.result(timeout=20) for future in futures]
        self.assertEqual({receipt["runId"] for receipt in receipts}, {"RUN-001", "RUN-002"})
        for receipt in receipts:
            self.assertEqual(receipt["nativeEventCount"], 1)
        self.assertEqual(self.client.ping(principal_id="USR-001")["namespaces"], 2)

    def test_unsupported_protocol_commands_leave_state_unchanged(self):
        response = self.transport.exchange({
            "protocolVersion": 1, "messageId": "MSG-INVALID",
            "principalId": "USR-001", "command": "erase_everything", "params": {},
        })
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "UNKNOWN_COMMAND")
        response = self.transport.exchange({
            "protocolVersion": 2, "messageId": "MSG-VERSION",
            "principalId": "USR-001", "command": "ping", "params": {},
        })
        self.assertEqual(response["error"]["code"], "INVALID_REQUEST")
        self.assertEqual(self.client.ping(principal_id="USR-001")["namespaces"], 0)

    def test_close_terminates_owned_process(self):
        self.client.ping(principal_id="USR-001")
        self.client.close()
        self.assertEqual(self.transport.process.poll(), 0)

    def test_unimplemented_persistence_profile_is_refused(self):
        with self.assertRaises(ValueError):
            SubprocessTransport(profile="local")


# Nominal application checks use the real official engine and selected stubs.
from unittest.mock import patch
from agent.analyzer import Analyzer
from agent.execution_state import ExecutionStateError, ExecutionStateStore
from agent.llm import ProviderError, StubProvider
from agent.orchestrator import Orchestrator
from agent.tools_zetaris import StubSqlExecutor


def application_parameters():
    return {
        "eventId": "APP-CREATED", "runId": "APP-001",
        "userId": "USR-001", "requestId": "REQ-001",
        "question": "SELECT-one test", "context": {},
        "profile": {"providerKind": "standalone_stub", "sourceKind": "standalone_stub"},
        "occurredAt": TIME, "recordedAt": TIME, "expectedRevision": 0,
    }


def application_event(event_id="APP-EVENT", **changes):
    result = {
        "eventId": event_id, "eventType": "PROBE_CONTEXT_CREATED", "schemaVersion": 1,
        "runId": "APP-001", "userId": "USR-001", "requestId": "REQ-001",
        "workflowId": "flood-analysis", "workflowVersion": "1.2.0",
        "actorId": "orchestrator", "occurredAt": TIME, "recordedAt": TIME,
        "stepId": "qualify-request", "taskId": "TASK-001",
        "attemptId": "ATTEMPT-001", "agentId": "planner", "payload": {},
    }
    result.update(changes)
    return result


class NominalApplicationIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.transport = SubprocessTransport(profile="memory", timeout=10)
        self.client = WorldModelClient(self.transport)
        self.addCleanup(self.client.close)
        self.store = ExecutionStateStore(self.client)
        self.enterContext(patch("socket.create_connection",
            side_effect=AssertionError("Platform network forbidden in local integration tests.")))

    def test_orchestrator_projects_nominal_tasks_through_actual_engine(self):
        result = Orchestrator(Analyzer(StubProvider()), StubSqlExecutor(),
                              execution_store=self.store).run("Run SELECT-one test")
        self.assertEqual(result["status"], "PASSED", result["errorCode"])
        self.assertTrue(result["worldModelUsed"])
        self.assertEqual(result["traceStatus"], "WORLD_MODEL_MEMORY")
        self.assertFalse(result["durableTrace"])
        self.assertFalse(result["workflowExecuted"])
        snapshot = result["worldModel"]
        run = snapshot["state"]["run"]
        self.assertEqual(run["status"], "SUCCEEDED")
        self.assertEqual(run["workflowVersion"], "1.2.0")
        self.assertEqual(run["profile"]["storage"], "memory")
        self.assertEqual(snapshot["nativeEventCount"], len(result["trace"]) + 1)
        self.assertEqual(snapshot["nativeAuditCount"], snapshot["nativeEventCount"])
        self.assertEqual(len(run["history"]), snapshot["nativeEventCount"])
        tasks = list(run["tasks"].values())
        self.assertEqual(len(tasks), 4)
        self.assertTrue(all(t["status"] == "COMPLETED" for t in tasks))
        parent = next(t for t in tasks if t["stepId"] == "analyze" and not t.get("parentTaskId"))
        child = next(t for t in tasks if t.get("parentTaskId"))
        self.assertEqual(child["parentTaskId"], parent["taskId"])
        self.assertNotEqual(child["taskId"], result["analysisResult"]["data"]["operationId"])
        self.assertNotEqual(child["attemptId"], parent["attemptId"])
        self.assertEqual(self.client.ping(principal_id="USR-DEMO")["engine"]["package"],
                         "@meterless/world-model-reference")

    def test_overlapping_same_user_runs_keep_event_histories_separate(self):
        orchestrator = Orchestrator(Analyzer(StubProvider()), StubSqlExecutor(),
                                   execution_store=self.store)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(orchestrator.run, "Run SELECT-one test", run_id="APP-A", request_id="REQ-A"),
                pool.submit(orchestrator.run, "Run SELECT-one test", run_id="APP-B", request_id="REQ-B"),
            ]
            first, second = [future.result(timeout=45) for future in futures]
        self.assertEqual(first["status"], "PASSED", first["errorCode"])
        self.assertEqual(second["status"], "PASSED", second["errorCode"])
        self.assertNotEqual(first["worldModel"]["namespace"], second["worldModel"]["namespace"])
        first_ids = {e["eventId"] for e in first["worldModel"]["state"]["run"]["history"]}
        second_ids = {e["eventId"] for e in second["worldModel"]["state"]["run"]["history"]}
        self.assertTrue(first_ids.isdisjoint(second_ids))
        self.assertEqual(self.client.get_run("APP-A", principal_id="USR-DEMO")["state"]["run"]["requestId"], "REQ-A")

    def test_duplicate_event_receipt_precedes_stale_revision_and_conflicts(self):
        params = application_parameters()
        self.client.create_execution(principal_id="USR-001", **params)
        event = application_event()
        first = self.client.append_event(principal_id="USR-001",
            run_id="APP-001", event=event, expected_revision=1)
        repeated = self.client.append_event(principal_id="USR-001",
            run_id="APP-001", event=event, expected_revision=1)
        self.assertEqual(first["nativeEventId"], repeated["nativeEventId"])
        self.assertTrue(repeated["duplicate"])
        self.assertEqual(repeated["acceptedRevision"], 2)
        changed = deepcopy(event)
        changed["payload"] = {"question": "changed"}
        with self.assertRaises(BridgeCommandError) as caught:
            self.client.append_event(principal_id="USR-001",
                run_id="APP-001", event=changed, expected_revision=1)
        self.assertEqual(caught.exception.code, "EVENT_CONFLICT")
        with self.assertRaises(BridgeCommandError) as stale:
            self.client.append_event(principal_id="USR-001",
                run_id="APP-001", event=application_event("APP-NEW"), expected_revision=1)
        self.assertEqual(stale.exception.code, "REVISION_CONFLICT")
        self.assertEqual(self.client.get_run("APP-001", principal_id="USR-001")["nativeEventCount"], 2)

    def test_owner_and_event_scope_rejections_leave_engine_unchanged(self):
        self.client.create_execution(principal_id="USR-001", **application_parameters())
        with self.assertRaises(BridgeCommandError) as wrong_owner:
            self.client.append_event(principal_id="USR-002",
                run_id="APP-001", event=application_event(), expected_revision=1)
        self.assertEqual(wrong_owner.exception.code, "FORBIDDEN")
        for changes in [{"runId": "OTHER-RUN"}, {"workflowVersion": "1.1.0"}]:
            with self.subTest(changes=changes):
                with self.assertRaises(BridgeCommandError) as caught:
                    self.client.append_event(principal_id="USR-001", run_id="APP-001",
                        event=application_event(**changes), expected_revision=1)
                self.assertEqual(caught.exception.code, "SCOPE_CONFLICT")
        self.assertEqual(self.client.get_run("APP-001", principal_id="USR-001")["nativeEventCount"], 1)

    def test_unqualified_analysis_and_premature_success_are_refused(self):
        params = application_parameters()
        created = self.client.create_execution(principal_id="USR-001", **params)
        duplicate = self.client.create_execution(principal_id="USR-001", **params)
        self.assertTrue(duplicate["duplicate"])
        self.assertEqual(created["nativeEventId"], duplicate["nativeEventId"])
        invalid = [
            application_event(eventType="INFERENCE_DISPATCHED", stepId="analyze"),
            application_event(eventType="PROBE_FINISHED", payload={"outcome": "PASSED", "errorCode": None}),
        ]
        for event in invalid:
            with self.assertRaises(BridgeCommandError) as caught:
                self.client.append_event(principal_id="USR-001", run_id="APP-001",
                    event=event, expected_revision=1)
            self.assertEqual(caught.exception.code, "DEPENDENCY_CONFLICT")
        self.assertEqual(self.client.get_run("APP-001", principal_id="USR-001")["nativeEventCount"], 1)

    def test_closed_execution_rejects_new_events(self):
        result = Orchestrator(Analyzer(StubProvider()), StubSqlExecutor(),
                              execution_store=self.store).run(
                                  "Run SELECT-one test", user_id="USR-001",
                                  run_id="APP-001", request_id="REQ-001")
        self.assertEqual(result["status"], "PASSED", result["errorCode"])
        revision = result["worldModel"]["state"]["revision"]
        with self.assertRaises(BridgeCommandError) as caught:
            self.client.append_event(principal_id="USR-001", run_id="APP-001",
                event=application_event("APP-LATE"), expected_revision=revision)
        self.assertEqual(caught.exception.code, "TERMINAL_STATE")

    def test_uncertain_provider_outcome_remains_explicit_in_real_projection(self):
        class UncertainProvider(StubProvider):
            kind = "nightshift"
            route = "meterless/auto"
            def complete(self, *args, **kwargs):
                raise ProviderError("PROVIDER_OUTCOME_UNKNOWN")
        result = Orchestrator(Analyzer(UncertainProvider()), StubSqlExecutor(),
                              execution_store=self.store).run("Run SELECT-one test")
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["errorCode"], "PROVIDER_OUTCOME_UNKNOWN")
        projected = result["worldModel"]["state"]["run"]
        self.assertEqual(projected["status"], "OUTCOME_UNKNOWN")
        self.assertTrue(projected["requiresReconciliation"])
        self.assertEqual(result["counts"]["toolExecutions"], 0)

    def test_intent_recording_failure_stops_before_provider_dispatch(self):
        provider = StubProvider()
        original_begin = self.store.begin
        def begin(**kwargs):
            ledger = original_begin(**kwargs)
            original_append = ledger.append
            def append(event):
                if event["eventType"] == "INFERENCE_DISPATCHED":
                    raise ExecutionStateError("WORLD_MODEL_UNAVAILABLE")
                return original_append(event)
            ledger.append = append
            return ledger
        with patch.object(self.store, "begin", side_effect=begin):
            with patch.object(provider, "complete", wraps=provider.complete) as invoke:
                result = Orchestrator(Analyzer(provider), StubSqlExecutor(),
                                      execution_store=self.store).run("Run SELECT-one test")
        invoke.assert_not_called()
        self.assertEqual(result["counts"]["toolExecutions"], 0)
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["worldModel"]["state"]["run"]["status"], "FAILED")


# History: 2026-10-27: Added nominal application projection, concurrent isolation, duplicate/revision and fail-closed tests against the real reference.
