"""Bounded internal analysis loop for the SELECT-one application probe."""
from __future__ import annotations

import copy
import json
import math
import re
import time
import uuid
from typing import Callable

from agent.llm import ProviderError
from agent.tools_zetaris import ALLOWED_SQL, SqlError, validate_sql

RUN_SQL_TOOL = {
    "type": "function",
    "function": {
        "name": "run_sql",
        "description": "Read-only SELECT-one integration probe. Only SELECT 1 AS one is allowed. Returns normalized rows and an application evidenceId.",
        "parameters": {
            "type": "object",
            "properties": {"sql": {"type": "string", "enum": [ALLOWED_SQL]}},
            "required": ["sql"],
            "additionalProperties": False,
        },
    },
}


class AnalyzerError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def parse_tool_call(call: dict, *, sql_validator=validate_sql) -> tuple[str, str]:
    if not isinstance(call, dict) or call.get("type") != "function":
        raise AnalyzerError("INVALID_TOOL_CALL")
    tool_id = call.get("id")
    if (not isinstance(tool_id, str) or not 1 <= len(tool_id) <= 200
            or any(ord(c) < 33 or ord(c) > 126 for c in tool_id)):
        raise AnalyzerError("INVALID_TOOL_CALL")
    function = call.get("function")
    if not isinstance(function, dict) or function.get("name") != "run_sql":
        raise AnalyzerError("TOOL_NOT_ALLOWED")
    raw = function.get("arguments")
    if not isinstance(raw, str) or len(raw.encode("utf-8")) > 4096:
        raise AnalyzerError("INVALID_TOOL_ARGUMENTS")
    try:
        arguments = json.loads(raw)
    except (ValueError, UnicodeError):
        raise AnalyzerError("INVALID_TOOL_ARGUMENTS") from None
    if not isinstance(arguments, dict) or set(arguments) != {"sql"}:
        raise AnalyzerError("INVALID_TOOL_ARGUMENTS")
    sql_validator(arguments["sql"])
    return tool_id, arguments["sql"]


def _assistant_message(response: dict) -> dict:
    if not isinstance(response, dict):
        raise AnalyzerError("INVALID_PROVIDER_RESPONSE")
    choices = response.get("choices")
    if (not isinstance(choices, list) or len(choices) != 1
            or not isinstance(choices[0], dict)
            or not isinstance(choices[0].get("message"), dict)):
        raise AnalyzerError("INVALID_PROVIDER_RESPONSE")
    message = choices[0]["message"]
    if message.get("role") != "assistant":
        raise AnalyzerError("INVALID_PROVIDER_RESPONSE")
    return message


def _model_name(response: dict) -> str | None:
    model = response.get("model")
    if isinstance(model, str) and re.fullmatch(r"[A-Za-z0-9_./:-]{1,200}", model):
        return model
    return None


class Analyzer:
    def __init__(self, provider, *, max_elapsed_seconds: float = 180,
                 clock: Callable[[], float] = time.monotonic):
        if (isinstance(max_elapsed_seconds, bool)
                or not isinstance(max_elapsed_seconds, (int, float))
                or not math.isfinite(max_elapsed_seconds)
                or not 0 < max_elapsed_seconds <= 180):
            raise AnalyzerError("INVALID_ANALYSIS_BUDGET")
        self.provider = provider
        self.max_elapsed_seconds = float(max_elapsed_seconds)
        self._clock = clock

    def analyze(self, question: str, *, request_data: Callable,
                record_event: Callable, context: dict | None = None) -> dict:
        deadline = self._clock() + self.max_elapsed_seconds

        def remaining() -> float:
            seconds = deadline - self._clock()
            if seconds <= 0:
                raise AnalyzerError("ANALYSIS_BUDGET_EXHAUSTED")
            return seconds

        def invoke(messages: list, max_tokens: int) -> tuple[dict, str, str | None]:
            invocation_id = str(uuid.uuid4())
            timeout = remaining()
            record_event("INFERENCE_DISPATCHED", {
                "invocationId": invocation_id, "requestedRoute": self.provider.route,
                "providerKind": self.provider.kind,
            })
            try:
                response = self.provider.complete(
                    messages, tools=[copy.deepcopy(RUN_SQL_TOOL)],
                    timeout_seconds=timeout, max_tokens=max_tokens)
            except ProviderError as error:
                record_event("INFERENCE_FAILED", {
                    "invocationId": invocation_id, "errorCode": error.code})
                raise
            remaining()
            message = _assistant_message(response)
            model = _model_name(response)
            record_event("INFERENCE_RESPONSE_RECEIVED", {
                "invocationId": invocation_id, "reportedModel": model,
                "verification": "not_established"})
            return message, invocation_id, model

        messages = [
            {"role": "system", "content":
             "You are running a SELECT-one application integration probe, not a hydrological analysis. "
             "Call run_sql exactly once with SELECT 1 AS one. Wait for the tool result, "
             "then state the value of one and its exact evidenceId. Never invent a receipt "
             "or call another tool. The source may be an explicitly selected stub or real Zetaris."},
            {"role": "user", "content": question},
        ]
        first, first_invocation, first_model = invoke(messages, 1024)
        calls = first.get("tool_calls")
        if not isinstance(calls, list) or len(calls) != 1:
            raise AnalyzerError("EXPECTED_ONE_STRUCTURED_TOOL_CALL")
        tool_id, sql = parse_tool_call(calls[0])
        record_event("TOOL_REQUEST_RECEIVED", {
            "invocationId": first_invocation, "toolCallId": tool_id,
            "toolName": "run_sql", "sql": sql})
        data_result = request_data(calls[0], invocation_id=first_invocation,
                                   remaining_seconds=remaining())
        remaining()
        messages.append({"role": "assistant",
                         "content": first.get("content") if isinstance(first.get("content"), str) else None,
                         "tool_calls": [{"id": tool_id, "type": "function",
                                         "function": {"name": "run_sql",
                                                      "arguments": json.dumps({"sql": sql})}}]})
        messages.append({"role": "tool", "tool_call_id": tool_id,
                         "content": json.dumps(data_result)})
        record_event("TOOL_RESULT_PREPARED", {
            "toolCallId": tool_id, "evidenceId": data_result["evidenceId"],
            "operationId": data_result["operationId"]})
        final, final_invocation, final_model = invoke(messages, 512)
        final_calls = final.get("tool_calls")
        if final_calls not in (None, []):
            raise AnalyzerError("ADDITIONAL_TOOL_CALL_NOT_ALLOWED")
        text = final.get("content")
        if not isinstance(text, str) or not text.strip() or len(text.encode("utf-8")) > 32768:
            raise AnalyzerError("INVALID_FINAL_RESPONSE")
        if data_result["evidenceId"] not in text or not re.search(r"\b1\b", text):
            raise AnalyzerError("FINAL_RESULT_NOT_REFERENCED")
        record_event("ANALYSIS_RESULT_CHECKED", {
            "evidenceId": data_result["evidenceId"],
            "check": "select_one_value_and_receipt_present",
            "domainValidated": False})
        return {
            "status": "SUCCEEDED", "answer": text,
            "indicators": {"one": 1}, "data": data_result,
            "requestedRoute": self.provider.route,
            "reportedModels": [first_model, final_model],
            "invocationIds": [first_invocation, final_invocation],
            "toolCalls": [{"toolName": "run_sql", "toolCallId": tool_id,
                           "sql": sql, "operationId": data_result["operationId"],
                           "evidenceId": data_result["evidenceId"]}],
            "validation": {"toolResultReferenced": True,
                           "domainValidated": False, "runtimeJudge": "not_established"},
            "uncertainties": ["This verifies a SELECT-one protocol path, not hydrological conclusions."],
        }

# History: 2026-10-27: Added scoped catalog-aware hydro analysis while retaining the SELECT-one baseline and explicit dependency profiles.
