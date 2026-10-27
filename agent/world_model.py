"""Explicit local transports for the official World Model memory bridge.

The memory profile is an integration increment, not durable application storage.
No transport selection, retry, or provider fallback happens automatically.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import queue
import re
import signal
import subprocess
import threading
from typing import Any, Protocol
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
MAX_REQUEST_BYTES = 4096
MAX_RESPONSE_BYTES = 65536
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")
MUTATING_COMMANDS = {"create_run", "create_execution", "append_event"}


class BridgeProtocolError(RuntimeError):
    """The bridge boundary is no longer safe to use."""


class BridgeOutcomeUnknown(BridgeProtocolError):
    """A mutating command may have been accepted before its reply was lost."""


class BridgeCommandError(RuntimeError):
    """A known command was rejected without the requested mutation."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class Transport(Protocol):
    def exchange(self, frame: dict[str, Any]) -> dict[str, Any]: ...
    def close(self) -> None: ...


def encode_frame(frame: dict[str, Any]) -> bytes:
    try:
        encoded = (json.dumps(frame, allow_nan=False, separators=(",", ":")) + "\n").encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError("Request must contain finite JSON data.") from error
    if len(encoded) > MAX_REQUEST_BYTES:
        raise ValueError("Request exceeds the protocol limit.")
    return encoded


class SubprocessTransport:
    """One persistent Linux subprocess, with serialized bounded exchanges."""

    def __init__(self, *, profile: str, timeout: float = 10):
        if profile != "memory":
            raise ValueError("Only the explicit memory profile is implemented.")
        if not 0 < timeout <= 60:
            raise ValueError("Timeout must be between zero and sixty seconds.")
        self.timeout = timeout
        self._lock = threading.Lock()
        self._failed = False
        self._closed = False
        self._responses: queue.Queue[Any] = queue.Queue()
        cache = ROOT / ".cache/world-model-bridge"
        cache.mkdir(parents=True, exist_ok=True)
        launcher = ROOT / "vendor/meterless/world-model/reference/node_modules/tsx/dist/cli.mjs"
        bridge = ROOT / "bridge/world-model.mts"
        if not launcher.is_file() or not bridge.is_file():
            raise BridgeProtocolError("The prepared bridge runtime is unavailable.")
        self.process = subprocess.Popen(
            ["/usr/bin/node", str(launcher), str(bridge), "--memory"],
            cwd=ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
            bufsize=-1,
            start_new_session=True,
            env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "TMPDIR": str(cache)},
        )
        self._reader = threading.Thread(target=self._read_responses, daemon=True)
        self._reader.start()

    def _read_responses(self) -> None:
        stream = self.process.stdout
        assert stream is not None
        try:
            while True:
                line = stream.readline(MAX_RESPONSE_BYTES + 1)
                if not line:
                    self._responses.put(BridgeProtocolError("Bridge closed its output."))
                    return
                if len(line) > MAX_RESPONSE_BYTES or not line.endswith(b"\n"):
                    self._responses.put(BridgeProtocolError("Invalid bridge response framing."))
                    return
                try:
                    value = json.loads(line)
                except (ValueError, UnicodeError):
                    self._responses.put(BridgeProtocolError("Bridge returned invalid JSON."))
                    return
                self._responses.put(value)
        except (OSError, ValueError):
            self._responses.put(BridgeProtocolError("Bridge output became unavailable."))

    def _stop_owned_group(self) -> None:
        try:
            os.killpg(self.process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        self.process.wait(timeout=5)

    def _invalidate(self) -> None:
        self._failed = True
        self._stop_owned_group()

    def exchange(self, frame: dict[str, Any]) -> dict[str, Any]:
        data = encode_frame(frame)
        with self._lock:
            if self._closed or self._failed:
                raise BridgeProtocolError("Bridge transport is unavailable.")
            if self.process.poll() is not None:
                self._failed = True
                raise BridgeProtocolError("Bridge process has stopped.")
            try:
                assert self.process.stdin is not None
                # One in-flight request, bounded to PIPE_BUF-sized framing.
                remaining = memoryview(data)
                while remaining:
                    written = os.write(self.process.stdin.fileno(), remaining)
                    if written <= 0:
                        raise OSError("Bridge input closed.")
                    remaining = remaining[written:]
                response = self._responses.get(timeout=self.timeout)
            except queue.Empty as error:
                self._invalidate()
                raise TimeoutError("Bridge response deadline exceeded.") from error
            except OSError as error:
                self._invalidate()
                raise TimeoutError("Bridge exchange failed after dispatch.") from error
            if isinstance(response, BaseException):
                self._invalidate()
                raise response
            return response

    def close(self) -> None:
        if self._closed:
            return
        try:
            if not self._failed and self.process.poll() is None:
                try:
                    self.exchange({
                        "protocolVersion": 1, "messageId": uuid4().hex,
                        "principalId": "SYSTEM", "command": "shutdown", "params": {},
                    })
                except (BridgeProtocolError, TimeoutError, OSError):
                    pass
        finally:
            self._closed = True
            if self.process.stdin is not None:
                self.process.stdin.close()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._stop_owned_group()
            self._reader.join(timeout=1)
            if self.process.stdout is not None:
                self.process.stdout.close()


class WorldModelClient:
    """Application protocol client; callers explicitly supply their transport."""

    def __init__(self, transport: Transport):
        self.transport = transport
        self._usable = True

    def _request(self, command: str, params: dict[str, Any], principal_id: str) -> dict[str, Any]:
        if not self._usable:
            raise BridgeProtocolError("Client requires explicit replacement.")
        if not isinstance(principal_id, str) or not IDENTIFIER.fullmatch(principal_id):
            raise ValueError("Invalid principal identifier.")
        frame = {
            "protocolVersion": 1, "messageId": uuid4().hex,
            "principalId": principal_id, "command": command, "params": params,
        }
        encode_frame(frame)
        try:
            response = self.transport.exchange(frame)
        except TimeoutError as error:
            self._usable = False
            if command in MUTATING_COMMANDS:
                raise BridgeOutcomeUnknown("Mutation outcome is unknown; do not retry blindly.") from error
            raise BridgeProtocolError("Bridge read timed out.") from error
        except BridgeProtocolError as error:
            self._usable = False
            if command in MUTATING_COMMANDS:
                raise BridgeOutcomeUnknown("Mutation outcome is unknown after transport failure.") from error
            raise
        error_type = BridgeOutcomeUnknown if command in MUTATING_COMMANDS else BridgeProtocolError
        if not isinstance(response, dict) or type(response.get("protocolVersion")) is not int or \
                response.get("protocolVersion") != 1 or response.get("messageId") != frame["messageId"] or \
                type(response.get("ok")) is not bool:
            self._usable = False
            raise error_type("Bridge response correlation or shape is invalid.")
        if response["ok"]:
            if not isinstance(response.get("result"), dict):
                self._usable = False
                raise error_type("Bridge result must be an object.")
            return response["result"]
        error = response.get("error")
        if not isinstance(error, dict) or not isinstance(error.get("code"), str) or \
                not isinstance(error.get("message"), str):
            self._usable = False
            raise error_type("Bridge error response is invalid.")
        if command in MUTATING_COMMANDS and error["code"] == "INTERNAL_ERROR":
            self._usable = False
            raise BridgeOutcomeUnknown("Mutation outcome requires reconciliation.")
        raise BridgeCommandError(error["code"], error["message"])

    def ping(self, *, principal_id: str) -> dict[str, Any]:
        return self._request("ping", {}, principal_id)

    def create_run(self, *, principal_id: str, **params: Any) -> dict[str, Any]:
        return self._request("create_run", params, principal_id)

    def create_execution(self, *, principal_id: str, **params: Any) -> dict[str, Any]:
        return self._request("create_execution", params, principal_id)

    def append_event(self, *, principal_id: str, run_id: str, event: dict,
                     expected_revision: int) -> dict[str, Any]:
        return self._request("append_event", {
            "runId": run_id, "event": event, "expectedRevision": expected_revision,
        }, principal_id)

    def get_run(self, run_id: str, *, principal_id: str) -> dict[str, Any]:
        return self._request("get_run", {"runId": run_id}, principal_id)

    def close(self) -> None:
        if self._usable:
            self._usable = False
        self.transport.close()

    def __enter__(self) -> WorldModelClient:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

# History: 2026-10-27: Added explicit execution/event commands and uncertain-outcome handling for all mutations.
