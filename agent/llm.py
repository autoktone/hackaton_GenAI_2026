"""Explicit Nightshift Windows transport and an isolated scripted provider."""
from __future__ import annotations

import json
import math
import subprocess
from urllib.parse import urlsplit, urlunsplit


class ProviderError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def normalize_runtime_url(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProviderError("INVALID_RUNTIME_URL")
    value = value.strip()
    if "://" not in value:
        value = "http://" + value
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        raise ProviderError("INVALID_RUNTIME_URL") from None
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.query or parsed.fragment or port == 8889
            or any(ord(c) < 33 or ord(c) == 127 for c in value)
            or parsed.path.rstrip("/") not in
            {"", "/v1", "/v1/chat/completions", "/v1/models", "/healthz"}):
        raise ProviderError("INVALID_RUNTIME_URL")
    return urlunsplit((parsed.scheme, parsed.netloc, "/v1", "", ""))


# The command is constant. Untrusted request data enters only through stdin JSON.
# Credentials are read inside the Windows backend and never sent to Python.
_WINDOWS_HTTP_WORKER = r"""
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::InputEncoding = New-Object Text.UTF8Encoding($false)
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$workerClient = $null
$workerHandler = $null
$workerContent = $null
$workerResponse = $null
$workerCancellation = $null
$workerToken = $null
$workerCode = 'PROVIDER_TRANSPORT_FAILED'
$workerOutput = $null
try {
    Add-Type -AssemblyName System.Net.Http
    $workerRequest = ConvertFrom-Json -InputObject ([Console]::In.ReadToEnd())
    $workerUri = [Uri]$workerRequest.url
    if ($workerUri.Host -notin @('localhost', '127.0.0.1', '[::1]', '::1') -or
        $workerUri.Scheme -notin @('http', 'https') -or
        $workerUri.AbsolutePath -ne '/v1/chat/completions' -or
        $workerUri.UserInfo -or $workerUri.Query -or $workerUri.Fragment -or
        $workerUri.Port -eq 8889) {
        $workerCode = 'INVALID_RUNTIME_URL'
        throw 'Controlled transport failure.'
    }
    $workerTokenPath = Join-Path $env:LOCALAPPDATA 'ai.meterless.runtime\proxy-token'
    $workerToken = [IO.File]::ReadAllText($workerTokenPath).Trim()
    if ([string]::IsNullOrWhiteSpace($workerToken) -or $workerToken -eq 'rt-local') {
        $workerCode = 'INVALID_RUNTIME_TOKEN'
        throw 'Controlled transport failure.'
    }
    $workerHandler = New-Object Net.Http.HttpClientHandler
    $workerHandler.UseProxy = $false
    $workerHandler.AllowAutoRedirect = $false
    $workerClient = New-Object Net.Http.HttpClient($workerHandler)
    $workerClient.MaxResponseContentBufferSize = 1048576
    $workerClient.Timeout = [TimeSpan]::FromSeconds([double]$workerRequest.timeoutSeconds)
    $workerClient.DefaultRequestHeaders.Authorization = New-Object Net.Http.Headers.AuthenticationHeaderValue('Bearer', $workerToken)
    $workerClient.DefaultRequestHeaders.Add('meterless-app', 'flood-risk-intelligence')
    $workerClient.DefaultRequestHeaders.Add('meterless-scope', 'user')
    $workerBody = ConvertTo-Json -InputObject $workerRequest.payload -Depth 30 -Compress
    $workerContent = New-Object Net.Http.StringContent($workerBody, [Text.Encoding]::UTF8, 'application/json')
    $workerCancellation = New-Object Threading.CancellationTokenSource
    $workerCancellation.CancelAfter([TimeSpan]::FromSeconds([double]$workerRequest.timeoutSeconds))
    $workerCode = 'PROVIDER_OUTCOME_UNKNOWN'
    $workerResponse = $workerClient.PostAsync(
        $workerUri, $workerContent, $workerCancellation.Token
    ).GetAwaiter().GetResult()
    $workerStatus = [int]$workerResponse.StatusCode
    if ($workerStatus -ne 200) {
        if ($workerStatus -in @(401, 403)) {
            $workerCode = 'PROVIDER_UNAUTHORIZED'
        } else {
            $workerCode = 'PROVIDER_HTTP_ERROR'
        }
        throw 'Controlled transport failure.'
    }
    $workerCode = 'INVALID_PROVIDER_RESPONSE'
    $workerBody = $workerResponse.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    $workerParsed = ConvertFrom-Json -InputObject $workerBody
    $workerOutput = @{ok=$true; body=$workerParsed}
} catch {
    $workerOutput = @{ok=$false; code=$workerCode}
} finally {
    if ($null -ne $workerResponse) { $workerResponse.Dispose() }
    if ($null -ne $workerContent) { $workerContent.Dispose() }
    if ($null -ne $workerCancellation) { $workerCancellation.Dispose() }
    if ($null -ne $workerClient) { $workerClient.Dispose() }
    if ($null -ne $workerHandler) { $workerHandler.Dispose() }
    $workerToken = $null
}
ConvertTo-Json -InputObject $workerOutput -Depth 40 -Compress
"""


class WindowsRuntimeTransport:
    """Selected Windows-loopback transport, without proxy, scan or retry."""

    def __init__(self, base_url: str, *, executable: str = "powershell.exe"):
        self.base_url = normalize_runtime_url(base_url)
        if urlsplit(self.base_url).hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ProviderError("WINDOWS_LOOPBACK_REQUIRED")
        self._executable = executable

    def post(self, payload: dict, *, timeout_seconds: float) -> dict:
        if (isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float))
                or not math.isfinite(timeout_seconds) or not 0 < timeout_seconds <= 180):
            raise ProviderError("INVALID_PROVIDER_TIMEOUT")
        request = json.dumps({"url": self.base_url + "/chat/completions",
                              "timeoutSeconds": timeout_seconds, "payload": payload})
        if len(request.encode("utf-8")) > 65536:
            raise ProviderError("PROVIDER_REQUEST_TOO_LARGE")
        try:
            process = subprocess.run(
                [self._executable, "-NoProfile", "-NonInteractive", "-Command", _WINDOWS_HTTP_WORKER],
                input=request, text=True, encoding="utf-8", capture_output=True,
                timeout=timeout_seconds + 5, check=False,
            )
        except subprocess.TimeoutExpired:
            raise ProviderError("PROVIDER_OUTCOME_UNKNOWN") from None
        except (OSError, UnicodeError):
            raise ProviderError("PROVIDER_TRANSPORT_FAILED") from None
        # Never include subprocess stderr, credentials or raw error bodies in errors.
        if process.returncode != 0:
            raise ProviderError("PROVIDER_TRANSPORT_FAILED")
        if len(process.stdout.encode("utf-8")) > 2097152:
            raise ProviderError("PROVIDER_RESPONSE_TOO_LARGE")
        try:
            envelope = json.loads(process.stdout.lstrip("\ufeff"))
        except (ValueError, UnicodeError):
            raise ProviderError("INVALID_PROVIDER_RESPONSE") from None
        if not isinstance(envelope, dict) or type(envelope.get("ok")) is not bool:
            raise ProviderError("INVALID_PROVIDER_RESPONSE")
        if not envelope["ok"]:
            allowed = {"PROVIDER_UNAUTHORIZED", "PROVIDER_HTTP_ERROR",
                       "PROVIDER_OUTCOME_UNKNOWN", "PROVIDER_TRANSPORT_FAILED",
                       "INVALID_RUNTIME_TOKEN", "INVALID_RUNTIME_URL",
                       "INVALID_PROVIDER_RESPONSE"}
            code = envelope.get("code")
            raise ProviderError(code if code in allowed else "PROVIDER_TRANSPORT_FAILED")
        if not isinstance(envelope.get("body"), dict):
            raise ProviderError("INVALID_PROVIDER_RESPONSE")
        return envelope["body"]


class NightshiftClient:
    kind = "nightshift"

    def __init__(self, transport, *, route: str):
        if (not isinstance(route, str) or not route.startswith("meterless/")
                or not 10 < len(route) <= 200
                or any(ord(c) < 33 or ord(c) > 126 for c in route)):
            raise ProviderError("INVALID_METERLESS_ROUTE")
        self.route = route
        self._transport = transport

    def complete(self, messages: list, *, tools: list,
                 timeout_seconds: float, max_tokens: int) -> dict:
        return self._transport.post(
            {"model": self.route, "messages": messages, "tools": tools,
             "stream": False, "temperature": 0.1, "max_tokens": max_tokens},
            timeout_seconds=timeout_seconds,
        )


class StubProvider:
    """Scripted unit/probe dependency; never presented as generated inference."""

    kind = "standalone_stub"
    route = "standalone_stub"

    def complete(self, messages: list, *, tools: list,
                 timeout_seconds: float, max_tokens: int) -> dict:
        if messages[-1]["role"] == "tool":
            result = json.loads(messages[-1]["content"])
            message = {"role": "assistant",
                       "content": "one: " + str(result["rows"][0][0])
                       + "; evidenceId: " + result["evidenceId"]}
        else:
            message = {"role": "assistant", "content": None, "tool_calls": [{
                "id": "call_select_one", "type": "function",
                "function": {"name": "run_sql",
                             "arguments": json.dumps({"sql": "SELECT 1 AS one"})}
            }]}
        return {"model": "standalone_stub", "choices": [{"message": message}]}


# History: 2026-10-27: Replaced the placeholder with an explicit Windows Runtime client and a separately selected scripted provider.
