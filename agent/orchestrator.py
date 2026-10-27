"""Application control and optional official World Model nominal projection."""
from __future__ import annotations

import re
import time
import uuid
from datetime import datetime, timezone
from typing import Callable

from agent.analyzer import Analyzer, AnalyzerError, parse_tool_call
from agent.execution_state import ExecutionStateError
from agent.llm import ProviderError
from agent.tools_zetaris import SqlError, validate_result, validate_sql


class OrchestrationError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _identifier(value: str) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value) is not None


class Orchestrator:
    """Nominal application probe; not the complete JSON policy executor."""

    def __init__(self, analyzer: Analyzer, executor, *, execution_store=None,
                 sql_attempts: int = 1):
        if type(sql_attempts) is not int or sql_attempts not in {1, 2}:
            raise OrchestrationError("INVALID_SQL_RETRY_POLICY")
        if (sql_attempts == 2 and execution_store is not None
                and execution_store.workflow_version != "1.3.0"):
            raise OrchestrationError("WORKFLOW_RETRY_POLICY_CONFLICT")
        self.analyzer = analyzer
        self.executor = executor
        self.execution_store = execution_store
        self.sql_attempts = sql_attempts

    def run(self, question: str, *, user_id: str = "USR-DEMO",
            request_id: str | None = None, run_id: str | None = None,
            event_sink: Callable | None = None, context: dict | None = None) -> dict:
        request_id = str(uuid.uuid4()) if request_id is None else request_id
        run_id = str(uuid.uuid4()) if run_id is None else run_id
        task_id = str(uuid.uuid4())
        attempt_id = str(uuid.uuid4())
        scope = {"stepId": "qualify-request", "taskId": str(uuid.uuid4()),
                 "attemptId": str(uuid.uuid4()), "agentId": "planner"}
        events = []
        executions = 0
        physical_attempts = 0
        intervention = None
        recorder = None

        def record(event_type: str, payload: dict, *, event_scope=None):
            active = scope if event_scope is None else event_scope
            event = {"eventId": str(uuid.uuid4()), "eventType": event_type,
                     "userId": user_id, "requestId": request_id, "runId": run_id,
                     **active,
                     "recordedAt": datetime.now(timezone.utc).isoformat(
                         timespec="milliseconds").replace("+00:00", "Z"),
                     "payload": payload}
            # The selected state adapter must accept intent before external dispatch.
            if recorder is not None:
                recorder.append(event)
            events.append(event)
            if event_sink is not None:
                try:
                    event_sink(event)
                except Exception:
                    raise OrchestrationError("TRACE_SINK_FAILED") from None

        def request_data(call: dict, *, invocation_id: str,
                         remaining_seconds: float) -> dict:
            nonlocal executions, physical_attempts, intervention
            tool_id, sql = parse_tool_call(
                call, sql_validator=getattr(self.analyzer, "validate_sql", validate_sql))
            if executions >= getattr(self.analyzer, "max_tool_executions", 1):
                raise OrchestrationError("DATA_OPERATION_BUDGET_EXHAUSTED")
            deadline = time.monotonic() + remaining_seconds
            if remaining_seconds <= self.executor.timeout_seconds:
                raise OrchestrationError("INSUFFICIENT_SQL_TIME_BUDGET")
            effective_sql = self.executor.prepare_sql(sql) if hasattr(self.executor, "prepare_sql") else sql
            operation_id = str(uuid.uuid4())
            data_scope = {"stepId": "analyze", "taskId": str(uuid.uuid4()),
                          "attemptId": str(uuid.uuid4()), "agentId": "zetaris"}
            record("DATA_REQUEST_ACCEPTED", {
                "toolCallId": tool_id, "invocationId": invocation_id,
                "operationId": operation_id, "sql": sql,
                "sourceKind": self.executor.kind, "parentTaskId": task_id,
            }, event_scope=data_scope)
            executions += 1

            def require_human(reason: str):
                nonlocal intervention
                intervention = {
                    "interventionId": str(uuid.uuid4()), "userId": user_id,
                    "requestId": request_id, "runId": run_id,
                    "taskId": data_scope["taskId"], "attemptId": data_scope["attemptId"],
                    "operationId": operation_id, "reason": reason,
                    "action": "CHECK_SOURCE_AND_RESTART_EXPLICITLY",
                    "requestedAt": datetime.now(timezone.utc).isoformat(
                        timespec="milliseconds").replace("+00:00", "Z"),
                }
                record("HUMAN_INTERVENTION_REQUIRED", {
                    "interventionId": intervention["interventionId"],
                    "operationId": operation_id, "errorCode": reason,
                    "action": intervention["action"]}, event_scope=data_scope)
                raise OrchestrationError("HUMAN_INTERVENTION_REQUIRED")

            for attempt_number in range(1, self.sql_attempts + 1):
                record("SQL_DISPATCHED", {
                    "operationId": operation_id, "toolCallId": tool_id,
                    "sql": effective_sql, "sourceKind": self.executor.kind,
                    **({"attemptNumber": attempt_number,
                        "queryId": data_scope["attemptId"] if hasattr(
                            self.executor, "execute_attempt") else operation_id}
                       if self.sql_attempts == 2 else {})}, event_scope=data_scope)
                physical_attempts += 1
                try:
                    if self.sql_attempts == 2 and hasattr(self.executor, "execute_attempt"):
                        result = self.executor.execute_attempt(
                            effective_sql, operation_id=operation_id,
                            attempt_id=data_scope["attemptId"])
                    else:
                        result = self.executor.execute(effective_sql, operation_id=operation_id)
                    if hasattr(self.executor, "validate_result"):
                        self.executor.validate_result(
                            result, sql=effective_sql, operation_id=operation_id)
                    else:
                        validate_result(result, operation_id=operation_id, source_kind=self.executor.kind)
                except SqlError as error:
                    retryable = error.code in {
                        "ZETARIS_TRANSIENT_HTTP_ERROR", "ZETARIS_OUTCOME_UNKNOWN"}
                    if self.sql_attempts == 2 and retryable and attempt_number == 1:
                        record("SQL_ATTEMPT_FAILED", {
                            "operationId": operation_id, "errorCode": error.code,
                            "attemptNumber": attempt_number, "retryable": True},
                            event_scope=data_scope)
                        if deadline - time.monotonic() > self.executor.timeout_seconds + 0.25:
                            next_attempt = str(uuid.uuid4())
                            record("SQL_RETRY_SCHEDULED", {
                                "operationId": operation_id, "nextAttemptId": next_attempt,
                                "attemptNumber": 2, "action": "REPEAT_VALIDATED_READ_ONLY_SELECT"},
                                event_scope=data_scope)
                            time.sleep(0.25)
                            # Recheck after tracing/backoff; never dispatch outside the budget.
                            if deadline - time.monotonic() > self.executor.timeout_seconds:
                                data_scope = {**data_scope, "attemptId": next_attempt}
                                continue
                        record("DATA_OPERATION_FAILED", {
                            "operationId": operation_id,
                            "errorCode": "INSUFFICIENT_RETRY_TIME_BUDGET"}, event_scope=data_scope)
                        require_human("INSUFFICIENT_RETRY_TIME_BUDGET")
                    record("DATA_OPERATION_FAILED", {
                        "operationId": operation_id, "errorCode": error.code},
                        event_scope=data_scope)
                    if self.sql_attempts == 2:
                        require_human(error.code)
                    raise
                record("DATA_OPERATION_COMPLETED", {
                    "operationId": operation_id, "toolCallId": tool_id,
                    "evidenceId": result["evidenceId"], "rowCount": result["rowCount"],
                    "sourceKind": result["sourceKind"]}, event_scope=data_scope)
                return result
            raise OrchestrationError("DATA_OPERATION_BUDGET_EXHAUSTED")

        analysis_result = None
        error_code = None
        try:
            if not all(_identifier(v) for v in [user_id, request_id, run_id]):
                raise OrchestrationError("INVALID_CONTEXT_IDENTIFIER")
            if not isinstance(question, str) or not question.strip() or len(question.encode("utf-8")) > 4096:
                raise OrchestrationError("INVALID_QUESTION")
            if self.execution_store is not None:
                recorder = self.execution_store.begin(
                    user_id=user_id, request_id=request_id, run_id=run_id,
                    question=question, provider_kind=self.analyzer.provider.kind,
                    source_kind=self.executor.kind, context=context)
            record("PROBE_CONTEXT_CREATED", {
                "question": question,
                "providerKind": self.analyzer.provider.kind,
                "sourceKind": self.executor.kind,
                "maxInferenceCalls": getattr(self.analyzer, "max_inference_calls", 2),
                "maxToolExecutions": getattr(self.analyzer, "max_tool_executions", 1),
                "maxElapsedSeconds": self.analyzer.max_elapsed_seconds})
            record("QUALIFICATION_COMPLETED", {})
            scope = {"stepId": "analyze", "taskId": task_id,
                     "attemptId": attempt_id, "agentId": "analyzer"}
            analysis_result = self.analyzer.analyze(
                question, request_data=request_data, record_event=record,
                context={**({} if context is None else context),
                         "userId": user_id, "requestId": request_id, "runId": run_id,
                         "sourceKind": self.executor.kind,
                         "providerKind": self.analyzer.provider.kind})
            record("ANALYZER_RESULT_RECEIVED", {
                "analysisStatus": analysis_result["status"],
                "evidenceId": analysis_result["data"]["evidenceId"]})
            scope = {"stepId": "report", "taskId": str(uuid.uuid4()),
                     "attemptId": str(uuid.uuid4()), "agentId": "reporter"}
            record("REPORT_PREPARED", {"resultRef": analysis_result["data"]["evidenceId"]})
        except (AnalyzerError, ProviderError, SqlError, OrchestrationError,
                ExecutionStateError) as error:
            error_code = error.code
        except Exception:
            error_code = "UNEXPECTED_APPLICATION_ERROR"

        trace_status = "WORLD_MODEL_MEMORY" if recorder is not None else "IN_MEMORY"
        if self.execution_store is not None and recorder is None:
            trace_status = "INCOMPLETE"
        try:
            record("PROBE_FINISHED", {
                "outcome": ("WAITING_HUMAN" if intervention is not None else
                            "PASSED" if error_code is None else "FAILED"),
                "errorCode": error_code})
        except (OrchestrationError, ExecutionStateError) as error:
            error_code = error.code
            trace_status = "INCOMPLETE"
        snapshot = None
        if recorder is not None:
            try:
                snapshot = recorder.snapshot()
            except ExecutionStateError as error:
                error_code = error.code
                trace_status = "INCOMPLETE"

        return {
            "scope": getattr(self.analyzer, "scope", "select_one_application_probe"),
            "status": ("WAITING_HUMAN" if intervention is not None and trace_status != "INCOMPLETE"
                       else "PASSED" if error_code is None else "FAILED"),
            "humanIntervention": intervention,
            "workflowVersion": "1.3.0" if self.sql_attempts == 2 else "1.2.0",
            "userId": user_id, "requestId": request_id, "runId": run_id,
            "taskId": task_id, "attemptId": attempt_id,
            "profile": {"providerKind": self.analyzer.provider.kind,
                        "sourceKind": self.executor.kind},
            "analysisResult": analysis_result, "errorCode": error_code,
            "counts": {"inferenceDispatches": sum(
                e["eventType"] == "INFERENCE_DISPATCHED" for e in events),
                "toolExecutions": executions,
                **({"sqlAttempts": physical_attempts} if self.sql_attempts == 2 else {})},
            "traceStatus": trace_status, "trace": events,
            "worldModelUsed": recorder is not None, "worldModel": snapshot,
            "workflowExecuted": False, "durableTrace": False,
        }


# History: 2026-10-27: Routed scoped intents through the explicit World Model store and represented nominal tasks and data delegation.

# History: 2026-10-27: Added scoped catalog-aware hydro analysis while retaining the SELECT-one baseline and explicit dependency profiles.

# History: 2026-10-27: Enforced a backend default row cap for admitted SELECTs and traced proposed versus executed SQL.

# History: 2026-10-27: Added explicit workflow 1.3 read attempts, scoped human escalation and backend-linked generated results.
