"""Explicit per-run ledger backed by the official World Model bridge."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import threading
from uuid import uuid4

from agent.world_model import (
    BridgeCommandError, BridgeOutcomeUnknown, BridgeProtocolError, WorldModelClient,
)


class ExecutionStateError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _time() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _translate(action):
    try:
        return action()
    except BridgeOutcomeUnknown:
        raise ExecutionStateError("WORLD_MODEL_OUTCOME_UNKNOWN") from None
    except BridgeCommandError as error:
        raise ExecutionStateError("WORLD_MODEL_" + error.code) from None
    except (BridgeProtocolError, OSError):
        raise ExecutionStateError("WORLD_MODEL_UNAVAILABLE") from None
    except (ValueError, TypeError):
        raise ExecutionStateError("WORLD_MODEL_INVALID_EVENT") from None


class ExecutionRecorder:
    def __init__(self, client: WorldModelClient, *, user_id: str,
                 request_id: str, run_id: str, receipt: dict, workflow_version: str = "1.2.0"):
        self.client = client
        self.user_id = user_id
        self.request_id = request_id
        self.run_id = run_id
        self.workflow_version = workflow_version
        self._lock = threading.Lock()
        self._usable = True
        try:
            self._last = self._checked(receipt, 1)
        except ExecutionStateError:
            self._usable = False
            raise ExecutionStateError("WORLD_MODEL_OUTCOME_UNKNOWN") from None

    def _checked(self, result: dict, revision: int) -> dict:
        try:
            run = result["state"]["run"]
            valid = (
                result["runId"] == self.run_id
                and type(result["state"]["revision"]) is int
                and result["state"]["revision"] == revision
                and run["runId"] == self.run_id
                and run["userId"] == self.user_id
                and run["requestId"] == self.request_id
                and run["workflowVersion"] == self.workflow_version
                and run["executionKind"] == "application-execution"
                and result["nativeEventCount"] == revision
                and result["nativeAuditCount"] == revision
            )
        except (KeyError, TypeError):
            valid = False
        if not valid:
            raise ExecutionStateError("WORLD_MODEL_INVALID_RECEIPT")
        return deepcopy(result)

    def append(self, event: dict) -> dict:
        if (not isinstance(event, dict) or event.get("runId") != self.run_id or event.get("userId") != self.user_id
                or event.get("requestId") != self.request_id):
            raise ExecutionStateError("WORLD_MODEL_SCOPE_CONFLICT")
        envelope = {
            **deepcopy(event), "schemaVersion": 1,
            "workflowId": "flood-analysis", "workflowVersion": self.workflow_version,
            "actorId": "orchestrator", "occurredAt": event["recordedAt"],
        }
        with self._lock:
            if not self._usable:
                raise ExecutionStateError("WORLD_MODEL_OUTCOME_UNKNOWN")
            revision = self._last["state"]["revision"]
            try:
                receipt = _translate(lambda: self.client.append_event(
                    principal_id=self.user_id, run_id=self.run_id,
                    event=envelope, expected_revision=revision))
            except ExecutionStateError as error:
                if error.code in {"WORLD_MODEL_OUTCOME_UNKNOWN", "WORLD_MODEL_UNAVAILABLE"}:
                    self._usable = False
                raise
            try:
                self._last = self._checked(receipt, revision + 1)
            except ExecutionStateError:
                self._usable = False
                raise ExecutionStateError("WORLD_MODEL_OUTCOME_UNKNOWN") from None
            return deepcopy(self._last)

    def snapshot(self) -> dict:
        with self._lock:
            if not self._usable:
                raise ExecutionStateError("WORLD_MODEL_OUTCOME_UNKNOWN")
            result = _translate(lambda: self.client.get_run(
                self.run_id, principal_id=self.user_id))
            self._last = self._checked(result, self._last["state"]["revision"])
            return deepcopy(self._last)


class ExecutionStateStore:
    """The caller selects and owns the client; no process or fallback is implicit."""

    def __init__(self, client: WorldModelClient, *, workflow_version: str = "1.2.0"):
        if workflow_version not in {"1.2.0", "1.3.0"}:
            raise ExecutionStateError("WORLD_MODEL_UNSUPPORTED_WORKFLOW")
        self.client = client
        self.workflow_version = workflow_version

    def begin(self, *, user_id: str, request_id: str, run_id: str,
              question: str, provider_kind: str, source_kind: str,
              context: dict | None = None) -> ExecutionRecorder:
        if not isinstance(question, str) or len(question.encode("utf-8")) > 512:
            raise ExecutionStateError("WORLD_MODEL_QUESTION_TOO_LARGE")
        now = _time()
        receipt = _translate(lambda: self.client.create_execution(
            principal_id=user_id, eventId=str(uuid4()), runId=run_id,
            userId=user_id, requestId=request_id, question=question,
            context={} if context is None else deepcopy(context),
            profile={"providerKind": provider_kind, "sourceKind": source_kind},
            occurredAt=now, recordedAt=now, expectedRevision=0,
            **({"workflowVersion": self.workflow_version} if self.workflow_version != "1.2.0" else {})))
        return ExecutionRecorder(self.client, user_id=user_id,
                                 request_id=request_id, run_id=run_id, receipt=receipt,
                                 workflow_version=self.workflow_version)

# History: 2026-10-27: Added explicit workflow 1.3 read attempts, scoped human escalation and backend-linked generated results.
