# 0006 - Nightshift live API smoke

- Recorded on: 2026-10-27.
- Result: Passed for authenticated discovery and one text inference through the explicit Windows-loopback transport.
- Application Git reference: Not recorded.
- Runtime installed version: Not recorded; do not infer it from the target provider contract.
- Target contract: Runtime 1.4 / provider contract v4.
- Reusable project provider client and Analyzer feature: Not implemented.

## Scope and prerequisites

The project owner approved each diagnostic and the single inference separately.
The development host runs Nightshift on Windows and Python inside Ubuntu WSL.
The test uses Python standard-library modules and the existing Windows curl.exe.
No additional packages, Runtime changes, listener changes, firewall rules,
or Windows/WSL network configuration changes were made.

Nightshift was started and configured by the owner with NVIDIA-backed lanes.
The existing Runtime token was read locally without printing or storing its value.
Provider credentials remained in Nightshift. No credentials appear in this report.
The official World Model integration is separate from this provider smoke.

## Connection sequence and observed results

| Check | Observed | Interpretation |
|---|---|---|
| Initial Windows health probe | No HTTP response before the owner confirmed startup | Not evidence of a credential failure |
| Owner's later health check | HTTP 200, status ok, engine meterless | Owner-supplied evidence that the Runtime was running |
| Windows authenticated GET /v1/models | HTTP 200; 18 meterless routes; meterless/auto present | Catalog request with the local token succeeded |
| Native Python WSL GET /v1/models | ConnectionRefusedError, errno 111, no HTTP response | Native WSL loopback could not reach that listener |
| Windows listener inspection | Port 8088 bound to Windows loopback only | Do not assume Windows and WSL share localhost |
| WSL caller using Windows curl GET /v1/models | HTTP 200; 18 routes; auto present | Explicit Windows-network transport reached the Runtime |
| Same transport POST /v1/chat/completions | HTTP 200; nonempty final text; finish reason stop | One real text generation succeeded |

Only the supplied endpoint was tested. No port scan, automatic host fallback,
or automatic retry was performed. The observed Windows-loopback method is a
verified development transport, not an implemented general-purpose client.

## Inference request and response

The request selected meterless/auto, stream false, temperature 0.1,
and requested max_tokens 512. It asked for two English sentences explaining
why heavy rainfall can cause a delayed river flood.
The route is a routing choice, not a fixed model identity.

Observed filtered response:

```json
{
  "callerContext": "wsl",
  "transport": "windows-loopback",
  "requestedRoute": "meterless/auto",
  "curlExitCode": 0,
  "applicationVerification": "not_performed",
  "httpStatus": 200,
  "finalTextReceived": true,
  "finalText": "Heavy rainfall initially saturates the soil and generates surface runoff, which flows into tributaries and streams. This water eventually reaches the main river channel, causing water levels to rise several hours after the precipitation ends.",
  "reportedModel": "nvidia/nemotron-3.5-lightning-30b-a3b",
  "responseId": "chatcmpl-5009d09d-78ac-4795-94e5-31a12b7aa080",
  "finishReason": "stop",
  "usage": {
    "prompt_tokens": 64,
    "completion_tokens": 357,
    "total_tokens": 421
  }
}
```

The Runtime reported nvidia/nemotron-3.5-lightning-30b-a3b.
That is returned model evidence, not independent provider-side verification.
Usage values are Runtime-reported counters, not an independent billing check.
No application verification, panel validation, calibrated uncertainty,
or hydrological forecasting performance was established.

## Exact successful smoke command

This is the executed development command for the operator-supplied Windows
endpoint http://127.0.0.1:8088/v1. It is not a universal deployment address.
The token remains in memory; headers and request body reach curl by stdin.
The HTTP deadline is 180 seconds and the parent deadline is 190 seconds.
A timeout is an uncertain outcome and must not trigger blind resubmission.
Running this command sends one inference and may consume provider credits.
Do not run it automatically merely because it is documented.

```powershell
$windowsCurlPath = Join-Path $env:SystemRoot "System32\curl.exe"
$linuxCurlPath = & wsl.exe -d Ubuntu --exec wslpath -u $windowsCurlPath
if ($LASTEXITCODE -ne 0) { throw "Executable path mapping failed." }
$linuxCurlPath = $linuxCurlPath.Trim()
$windowsTokenPath = Join-Path $env:LOCALAPPDATA "ai.meterless.runtime\proxy-token"
$linuxTokenPath = & wsl.exe -d Ubuntu --exec wslpath -u $windowsTokenPath
if ($LASTEXITCODE -ne 0) { throw "Token path mapping failed." }
$linuxTokenPath = $linuxTokenPath.Trim()

$inferNightshift = @'
import json
import re
import subprocess
import sys
from pathlib import Path

curl = Path(sys.argv[1])
if not curl.is_file():
    raise SystemExit("Windows curl executable unavailable.")
token = Path(sys.argv[2]).read_text(encoding="utf-8").strip()
if not token or token == "rt-local" or "\r" in token or "\n" in token:
    raise SystemExit("Runtime token unavailable or invalid.")

payload = {
    "model": "meterless/auto",
    "stream": False,
    "temperature": 0.1,
    "max_tokens": 512,
    "messages": [{
        "role": "user",
        "content": "Explain in two English sentences why heavy rainfall can cause river flooding several hours later."
    }],
}

def quoted(value):
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'

configuration = "\n".join([
    "url = " + quoted("http://127.0.0.1:8088/v1/chat/completions"),
    'request = "POST"',
    "header = " + quoted("Authorization: Bearer " + token),
    "header = " + quoted("meterless-app: flood-risk-intelligence"),
    "header = " + quoted("meterless-scope: user"),
    'header = "Content-Type: application/json"',
    "data-binary = " + quoted(json.dumps(payload, separators=(",", ":"))),
]) + "\n"
try:
    result = subprocess.run(
        [str(curl), "--disable", "--silent", "--show-error",
         "--noproxy", "*", "--max-time", "180",
         "--write-out", r"\n%{http_code}", "--config", "-"],
        input=configuration.encode("utf-8"),
        capture_output=True, timeout=190, check=False,
    )
    output = {
        "callerContext": "wsl",
        "transport": "windows-loopback",
        "requestedRoute": "meterless/auto",
        "curlExitCode": result.returncode,
        "applicationVerification": "not_performed",
    }
    if result.returncode == 0:
        body, status = result.stdout.rsplit(b"\n", 1)
        output["httpStatus"] = int(status)
        if output["httpStatus"] == 200:
            response = json.loads(body)
            choices = response.get("choices", [])
            choice = choices[0] if isinstance(choices, list) and choices and isinstance(choices[0], dict) else {}
            message = choice.get("message", {})
            content = message.get("content") if isinstance(message, dict) else None
            if isinstance(content, list):
                content = "\n".join(
                    part["text"] for part in content
                    if isinstance(part, dict) and isinstance(part.get("text"), str)
                    and part.get("type") in ("text", "output_text")
                )
            if isinstance(content, str):
                if re.search(r"<(?:think|analysis)>", content, re.I):
                    closing = list(re.finditer(r"</(?:think|analysis)>", content, re.I))
                    content = content[closing[-1].end():].strip() if closing else ""
                    output["reasoningMarkupExcluded"] = True
                output["finalTextReceived"] = bool(content.strip())
                output["finalText"] = content.strip()[:1600]
            else:
                output["finalTextReceived"] = False
                output["contentType"] = type(content).__name__
            for source, target in (("model", "reportedModel"), ("id", "responseId")):
                value = response.get(source)
                output[target] = value if isinstance(value, str) else None
            reason = choice.get("finish_reason")
            output["finishReason"] = reason if isinstance(reason, str) else None
            usage = response.get("usage")
            if isinstance(usage, dict):
                output["usage"] = {
                    key: value for key, value in usage.items()
                    if key in ("prompt_tokens", "completion_tokens", "total_tokens")
                    and isinstance(value, (int, float)) and not isinstance(value, bool)
                }
    elif result.returncode == 28:
        output["state"] = "outcome_unknown_timeout"
    print(json.dumps(output, ensure_ascii=True))
except subprocess.TimeoutExpired:
    print(json.dumps({
        "transport": "windows-loopback",
        "state": "outcome_unknown_timeout",
        "applicationVerification": "not_performed",
    }))
except (ValueError, UnicodeError, TypeError):
    print(json.dumps({
        "transport": "windows-loopback",
        "state": "unexpected_response",
        "applicationVerification": "not_performed",
    }))
finally:
    token = None
    configuration = None
'@
$inferNightshift | wsl.exe -d Ubuntu --exec python3 -B - $linuxCurlPath $linuxTokenPath
```

## Separate panel issue

The owner reported job job_mvqdodfh02 with two generated candidates, a distinct
JUDGE model, no timeout, an unparseable panel, zero scored candidates, and two
abstentions. A configured VERIFY lane does not prove its checks ran or passed.
Local references do not publish the exact internal judge-output parser schema
or establish a specific NVIDIA incompatibility.
The successful text request here is a different path and does not resolve
that job's missing judge verdict.

## Delivery and configuration boundaries

The clean-setup one-command sample remains to be implemented. It must not need
Nightshift, platform accounts, credentials, sign-in, or a live endpoint.
Live mode needs an operator-supplied reachable URL and an explicit transport.
Loopback means the host/network context executing HTTP, not necessarily the
context of the calling Python process.
The reusable provider configuration loader remains to be implemented.
No public judge gateway, access token distribution, or rate limiting was built.
The live application feature and video evidence remain outstanding.

## History

- 2026-10-27: Recorded connection diagnostics, the successful real inference, endpoint-context constraints, and generated-versus-verified evidence.
