"""Real official-engine checks for workflow 1.3 attempt and intervention projection."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest
import uuid
from unittest.mock import patch

from agent.hydro import HydroAnalyzer, HydroStubProvider, SnapshotSqlExecutor, OBSERVATIONS_SQL
from agent.execution_state import ExecutionStateStore
from agent.orchestrator import Orchestrator
from agent.tools_zetaris import SqlError
from agent.world_model import BridgeCommandError, SubprocessTransport, WorldModelClient


class OneReadProvider:
    kind = "standalone_stub"
    route = "standalone_stub"

    def __init__(self):
        self.calls = 0

    def complete(self, messages, **kwargs):
        self.calls += 1
        results = [json.loads(m["content"]) for m in messages if m["role"] == "tool"]
        if results:
            message = {"role": "assistant", "content": "Scripted response; backend evidence is attached."}
        else:
            message = {"role": "assistant", "content": None, "tool_calls": [{
                "id": "call_native_incident", "type": "function", "function": {
                    "name": "run_sql", "arguments": json.dumps({"sql": OBSERVATIONS_SQL})}}]}
        return {"model": "standalone_stub", "choices": [{"message": message}]}


class PerOperationFailure(SnapshotSqlExecutor):
    def __init__(self, snapshot, *, persistent=False, code="ZETARIS_TRANSIENT_HTTP_ERROR"):
        super().__init__(snapshot)
        self.calls = {}
        self.persistent = persistent
        self.code = code

    def execute(self, sql, *, operation_id):
        self.calls[operation_id] = self.calls.get(operation_id, 0) + 1
        if self.persistent or self.calls[operation_id] == 1:
            raise SqlError(self.code)
        return super().execute(sql, operation_id=operation_id)


class IncidentWorldModelTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[2] / "data/snapshots/hubeau-givry-2026-10-27.json"
        self.snapshot = json.loads(path.read_text(encoding="utf-8"))
        self.client = WorldModelClient(SubprocessTransport(profile="memory", timeout=10))
        self.addCleanup(self.client.close)
        self.store = ExecutionStateStore(self.client, workflow_version="1.3.0")
        self.enterContext(patch("socket.create_connection", side_effect=AssertionError("No platform network.")))

    def test_both_data_reads_recover_with_two_attempts_and_one_logical_operation_each(self):
        executor = PerOperationFailure(self.snapshot)
        result = Orchestrator(HydroAnalyzer(HydroStubProvider()), executor,
            execution_store=self.store, sql_attempts=2).run("Read hydrometry and station context.")
        self.assertEqual(result["status"], "PASSED", result["errorCode"])
        self.assertEqual(result["counts"], {"inferenceDispatches": 3, "toolExecutions": 2, "sqlAttempts": 4})
        state = result["worldModel"]
        run = state["state"]["run"]
        self.assertEqual(run["workflowVersion"], "1.3.0")
        self.assertEqual(run["status"], "SUCCEEDED")
        children = [task for task in run["tasks"].values() if task.get("parentTaskId")]
        self.assertEqual(len(children), 2)
        for child in children:
            self.assertEqual(child["status"], "COMPLETED")
            self.assertEqual(len(child["attempts"]), 2)
            attempts = list(child["attempts"].values())
            self.assertEqual([a["number"] for a in attempts], [1, 2])
            self.assertEqual([a["status"] for a in attempts], ["FAILED", "COMPLETED"])
            self.assertEqual(attempts[0]["supersededByReadAttempt"], attempts[1]["attemptId"])
        self.assertEqual(state["nativeEventCount"], len(result["trace"]) + 1)
        self.assertEqual(state["nativeAuditCount"], state["nativeEventCount"])
        self.assertLessEqual(state["nativeEventCount"], 32)

    def test_persistent_failure_projects_scoped_human_wait_and_refuses_more_dispatch(self):
        executor = PerOperationFailure(self.snapshot, persistent=True)
        provider = OneReadProvider()
        result = Orchestrator(HydroAnalyzer(provider), executor,
            execution_store=self.store, sql_attempts=2).run(
                "Read current hydrometry.", run_id="RUN-HUMAN", request_id="REQ-HUMAN")
        self.assertEqual(result["status"], "WAITING_HUMAN", result["errorCode"])
        self.assertEqual(provider.calls, 1)
        state = result["worldModel"]
        run = state["state"]["run"]
        self.assertEqual(run["status"], "WAITING_HUMAN")
        self.assertTrue(run["suspensionRecorded"])
        self.assertEqual(run["humanIntervention"]["operationId"],
                         result["humanIntervention"]["operationId"])
        child = next(t for t in run["tasks"].values() if t.get("parentTaskId"))
        self.assertEqual(child["status"], "WAITING_HUMAN")
        self.assertEqual(len(child["attempts"]), 2)
        event = copy.deepcopy(next(e for e in reversed(result["trace"])
                                   if e["eventType"] == "SQL_DISPATCHED"))
        event.update(eventId=str(uuid.uuid4()), schemaVersion=1,
                     workflowId="flood-analysis", workflowVersion="1.3.0",
                     actorId="orchestrator", occurredAt=event["recordedAt"])
        with self.assertRaises(BridgeCommandError) as caught:
            self.client.append_event(principal_id="USR-DEMO", run_id="RUN-HUMAN",
                event=event, expected_revision=state["state"]["revision"])
        self.assertEqual(caught.exception.code, "HUMAN_INTERVENTION_REQUIRED")
        unchanged = self.client.get_run("RUN-HUMAN", principal_id="USR-DEMO")
        self.assertEqual(unchanged["nativeEventCount"], state["nativeEventCount"])

    def test_uncertain_first_read_keeps_attempt_evidence_without_claiming_write_recovery(self):
        result = Orchestrator(HydroAnalyzer(OneReadProvider()),
            PerOperationFailure(self.snapshot, code="ZETARIS_OUTCOME_UNKNOWN"),
            execution_store=self.store, sql_attempts=2).run("Read available observations.")
        self.assertEqual(result["status"], "PASSED", result["errorCode"])
        run = result["worldModel"]["state"]["run"]
        child = next(t for t in run["tasks"].values() if t.get("parentTaskId"))
        attempts = list(child["attempts"].values())
        self.assertEqual(attempts[0]["status"], "OUTCOME_UNKNOWN")
        self.assertEqual(attempts[1]["status"], "COMPLETED")
        self.assertFalse(result["durableTrace"])

    def test_old_workflow_rejects_new_retry_events_without_mutating_state(self):
        now = "2026-10-27T12:00:00Z"
        self.client.create_execution(principal_id="USR-DEMO", eventId="OLD-CREATE",
            runId="OLD-RUN", userId="USR-DEMO", requestId="OLD-REQUEST",
            question="Legacy policy", context={},
            profile={"providerKind":"standalone_stub","sourceKind":"standalone_stub"},
            occurredAt=now, recordedAt=now, expectedRevision=0)
        event = {"eventId":"OLD-RETRY", "eventType":"SQL_ATTEMPT_FAILED", "schemaVersion":1,
                 "runId":"OLD-RUN", "userId":"USR-DEMO", "requestId":"OLD-REQUEST",
                 "workflowId":"flood-analysis", "workflowVersion":"1.2.0",
                 "actorId":"orchestrator", "occurredAt":now, "recordedAt":now,
                 "stepId":"analyze", "taskId":"OLD-TASK", "attemptId":"OLD-ATTEMPT",
                 "agentId":"zetaris", "payload":{"errorCode":"ZETARIS_TRANSIENT_HTTP_ERROR"}}
        with self.assertRaises(BridgeCommandError) as caught:
            self.client.append_event(principal_id="USR-DEMO",run_id="OLD-RUN",
                                     event=event,expected_revision=1)
        self.assertEqual(caught.exception.code, "WORKFLOW_POLICY_CONFLICT")
        self.assertEqual(self.client.get_run("OLD-RUN",principal_id="USR-DEMO")["nativeEventCount"],1)


if __name__ == "__main__":
    unittest.main()
