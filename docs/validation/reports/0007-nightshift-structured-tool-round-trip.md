# 0007 - Nightshift structured tool round trip

- Date: 2026-10-27.
- Result: Passed within the tested protocol scope.
- Execution context: Windows PowerShell and .NET HTTP, not the Python WSL application.
- Approval evidence: Ok.
- Runtime version: not established by this check.
- Requested route: meterless/auto.
- Tool implementation: explicitly selected standalone stub.
- Zetaris access: none.

## Scenario and preconditions

Verify that the configured Runtime carries a structured Nemotron tool call,
accepts the corresponding tool result and returns a final answer using it.

The existing Windows Runtime must be running at the owner-supplied endpoint
http://127.0.0.1:8088/v1, with its matching token in the existing private
Windows token file. The command uses Windows PowerShell, .NET HTTP and no
additional package. Provider credentials remain in Nightshift.

This is a live inference test and can consume credits. Its command is retained
for reproducibility, not as authorization to execute it again.

## Expected behavior

1. Declare run_sql with a single permitted SQL argument, SELECT 1 AS one.
2. Receive exactly one structured function call and validate its arguments.
3. Execute the explicit local stub, not a database query.
4. Return one=1 and a fresh marker under the matching tool_call_id.
5. Receive final text containing the exact marker, supplied only in the result.

The request has a two-HTTP-call limit and a total 180-second budget.
Redirects and proxy use are disabled. Responses are bounded to 1 MiB;
requested completion limits are 1024 and 512 tokens respectively.
There is no automatic retry, provider fallback or live-to-stub fallback.

## Exact executed command

The token is read privately at execution time. The command contains its
documented file location, never its value. No project file is written.

```powershell
$ErrorActionPreference = 'Stop'
$probeState = [ordered]@{
    test = 'nightshift-structured-tool-round-trip'
    transport = 'windows-loopback-http'
    requestedRoute = 'meterless/auto'
    toolExecution = 'explicit-standalone-stub'
    zetarisContacted = $false
    structuredToolCallReceived = $false
    toolResultReturned = $false
    finalMarkerMatched = $false
    httpRequests = 0
    lastHttpStatus = $null
    firstReportedModel = $null
    finalReportedModel = $null
    phase = 'setup'
    status = 'not_started'
}
$script:probeFailure = 'SETUP_FAILED'
$probeClient = $null
$probeHandler = $null
$probeToken = $null
$probeClock = [Diagnostics.Stopwatch]::StartNew()
$probeFailed = $false
try {
    Add-Type -AssemblyName System.Net.Http
    $probeTokenPath = Join-Path $env:LOCALAPPDATA 'ai.meterless.runtime\proxy-token'
    $probeToken = [IO.File]::ReadAllText($probeTokenPath).Trim()
    if ([string]::IsNullOrWhiteSpace($probeToken) -or $probeToken -eq 'rt-local') {
        $script:probeFailure = 'INVALID_RUNTIME_TOKEN'
        throw 'Controlled probe failure.'
    }
    $probeHandler = New-Object System.Net.Http.HttpClientHandler
    $probeHandler.UseProxy = $false
    $probeHandler.AllowAutoRedirect = $false
    $probeClient = New-Object System.Net.Http.HttpClient($probeHandler)
    $probeClient.Timeout = [TimeSpan]::FromSeconds(180)
    $probeClient.MaxResponseContentBufferSize = 1048576
    $probeClient.DefaultRequestHeaders.Authorization = New-Object System.Net.Http.Headers.AuthenticationHeaderValue('Bearer', $probeToken)
    $probeClient.DefaultRequestHeaders.Add('meterless-app', 'flood-risk-intelligence')
    $probeClient.DefaultRequestHeaders.Add('meterless-scope', 'user')

    function Send-ProbeCompletion {
        param($Payload)
        $remaining = 180 - $probeClock.Elapsed.TotalSeconds
        if ($remaining -le 0 -or $probeState.httpRequests -ge 2) {
            $script:probeFailure = 'PROBE_BUDGET_EXHAUSTED'
            throw 'Controlled probe failure.'
        }
        $cancellation = New-Object System.Threading.CancellationTokenSource
        $cancellation.CancelAfter([TimeSpan]::FromSeconds($remaining))
        $requestContent = $null
        $response = $null
        try {
            $body = ConvertTo-Json -InputObject $Payload -Depth 20 -Compress
            $requestContent = New-Object System.Net.Http.StringContent($body, [Text.Encoding]::UTF8, 'application/json')
            $probeState.httpRequests = $probeState.httpRequests + 1
            $script:probeFailure = 'TRANSPORT_FAILED_OR_OUTCOME_UNKNOWN'
            $response = $probeClient.PostAsync(
                'http://127.0.0.1:8088/v1/chat/completions',
                $requestContent,
                $cancellation.Token
            ).GetAwaiter().GetResult()
            $probeState.lastHttpStatus = [int]$response.StatusCode
            if ([int]$response.StatusCode -ne 200) {
                $script:probeFailure = 'HTTP_' + [int]$response.StatusCode
                throw 'Controlled probe failure.'
            }
            $script:probeFailure = 'INVALID_RESPONSE_JSON'
            $responseText = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
            return (ConvertFrom-Json -InputObject $responseText)
        } finally {
            if ($null -ne $response) { $response.Dispose() }
            if ($null -ne $requestContent) { $requestContent.Dispose() }
            $cancellation.Dispose()
        }
    }

    $probeTool = @{
        type = 'function'
        function = @{
            name = 'run_sql'
            description = 'Standalone protocol probe only. No database connection. Only SELECT 1 AS one is allowed. Returns one and a probeMarker.'
            parameters = @{
                type = 'object'
                properties = @{
                    sql = @{
                        type = 'string'
                        enum = @('SELECT 1 AS one')
                    }
                }
                required = @('sql')
                additionalProperties = $false
            }
        }
    }
    $probeMessages = @(
        @{
            role = 'user'
            content = 'Protocol test: call run_sql exactly once with SQL SELECT 1 AS one. After receiving its result, return the value of one and the exact probeMarker from that result. Do not guess the marker. Do not request any other tool.'
        }
    )
    $probeState.phase = 'request_tool_call'
    $firstReply = Send-ProbeCompletion @{
        model = 'meterless/auto'
        stream = $false
        temperature = 0.1
        max_tokens = 1024
        tools = @($probeTool)
        tool_choice = 'auto'
        messages = $probeMessages
    }
    $probeState.firstReportedModel = $firstReply.model
    $firstChoices = @($firstReply.choices)
    $script:probeFailure = 'MISSING_ASSISTANT_MESSAGE'
    if ($firstChoices.Count -ne 1 -or $null -eq $firstChoices[0].message) {
        throw 'Controlled probe failure.'
    }
    $assistantMessage = $firstChoices[0].message
    $toolCalls = @($assistantMessage.tool_calls)
    $script:probeFailure = 'EXPECTED_ONE_STRUCTURED_TOOL_CALL'
    if ($toolCalls.Count -ne 1 -or $null -eq $toolCalls[0]) {
        throw 'Controlled probe failure.'
    }
    $toolCall = $toolCalls[0]
    $script:probeFailure = 'INVALID_TOOL_CALL'
    if ($toolCall.type -ne 'function' -or $toolCall.function.name -ne 'run_sql' -or
        [string]::IsNullOrWhiteSpace([string]$toolCall.id) -or
        $toolCall.function.arguments -isnot [string]) {
        throw 'Controlled probe failure.'
    }
    $script:probeFailure = 'INVALID_TOOL_ARGUMENTS'
    $toolArguments = ConvertFrom-Json -InputObject $toolCall.function.arguments
    $argumentNames = @($toolArguments.PSObject.Properties.Name)
    if ($argumentNames.Count -ne 1 -or $argumentNames[0] -ne 'sql' -or
        $toolArguments.sql -isnot [string] -or
        $toolArguments.sql -cne 'SELECT 1 AS one') {
        throw 'Controlled probe failure.'
    }
    $probeState.structuredToolCallReceived = $true
    $probeMarker = 'FRDI_TOOL_' + [Guid]::NewGuid().ToString('N')
    $toolResult = @{
        one = 1
        probeMarker = $probeMarker
        source = 'standalone_stub'
        databaseAccess = $false
    }
    $probeMessages += @{
        role = 'assistant'
        content = $assistantMessage.content
        tool_calls = @(@{
            id = $toolCall.id
            type = 'function'
            function = @{
                name = 'run_sql'
                arguments = $toolCall.function.arguments
            }
        })
    }
    $probeMessages += @{
        role = 'tool'
        tool_call_id = $toolCall.id
        content = (ConvertTo-Json -InputObject $toolResult -Compress)
    }
    $probeState.phase = 'return_tool_result'
    $probeState.toolResultReturned = $true
    $finalReply = Send-ProbeCompletion @{
        model = 'meterless/auto'
        stream = $false
        temperature = 0.1
        max_tokens = 512
        tools = @($probeTool)
        messages = $probeMessages
    }
    $probeState.finalReportedModel = $finalReply.model
    $script:probeFailure = 'INVALID_FINAL_RESPONSE'
    $finalChoices = @($finalReply.choices)
    if ($finalChoices.Count -ne 1 -or $null -eq $finalChoices[0].message) {
        throw 'Controlled probe failure.'
    }
    $finalMessage = $finalChoices[0].message
    if (@($finalMessage.tool_calls).Where({ $null -ne $_ }).Count -ne 0 -or
        $finalMessage.content -isnot [string] -or
        [string]::IsNullOrWhiteSpace($finalMessage.content)) {
        throw 'Controlled probe failure.'
    }
    $probeState.finalMarkerMatched = $finalMessage.content.Contains($probeMarker)
    $script:probeFailure = 'FINAL_RESULT_NOT_USED'
    if (-not $probeState.finalMarkerMatched) {
        throw 'Controlled probe failure.'
    }
    $probeState.finalText = $finalMessage.content
    $probeState.status = 'passed'
    $probeState.phase = 'completed'
} catch {
    $probeFailed = $true
    $probeState.status = 'failed'
    $probeState.failureCode = $script:probeFailure
} finally {
    $probeState.elapsedSeconds = [Math]::Round($probeClock.Elapsed.TotalSeconds, 2)
    if ($null -ne $probeClient) { $probeClient.Dispose() }
    if ($null -ne $probeHandler) { $probeHandler.Dispose() }
    $probeToken = $null
    ConvertTo-Json -InputObject $probeState -Depth 5
}
if ($probeFailed) { exit 1 }
```

## Observed result

The process exited with code 0. The instrumented probe took 6.23 seconds;
the command runner reported approximately 8.93 seconds.

```json
{
  "test": "nightshift-structured-tool-round-trip",
  "transport": "windows-loopback-http",
  "requestedRoute": "meterless/auto",
  "toolExecution": "explicit-standalone-stub",
  "zetarisContacted": false,
  "structuredToolCallReceived": true,
  "toolResultReturned": true,
  "finalMarkerMatched": true,
  "httpRequests": 2,
  "lastHttpStatus": 200,
  "firstReportedModel": "nvidia/nemotron-3.5-lightning-30b-a3b",
  "finalReportedModel": "nvidia/nemotron-3.5-lightning-30b-a3b",
  "phase": "completed",
  "status": "passed",
  "finalText": "one: 1  \nprobeMarker: FRDI_TOOL_2613e43792f840a0aad1303893cf12f3",
  "elapsedSeconds": 6.23
}
```

Both HTTP calls returned 200; the command stops on any non-200 response.
The returned serving-model field identified Nemotron Lightning for both calls.
This is Runtime-reported model evidence, not an independent provider audit.

The exact marker in the final answer establishes consumption of the stub
result in this tested exchange. No hydrological content was validated.

## Limits

- This is a Windows protocol probe, not a reusable Python provider client.
- No Zetaris query, application orchestrator, Analyzer workflow, World Model
  tool-event lifecycle or application-level run correlation was executed.
- No JUDGE acceptance, VERIFY success or hydrological accuracy is established.
- This does not prove every tool-calling option, routing mode, parallel tool
  behavior or Runtime/provider-contract feature.
- Provider usage, billing and response identifiers were not captured.
- The measured result does not remove the need for timeout, malformed-call,
  authorization, cancellation and failure tests.
- Historical accepted ADRs retain their context at acceptance; this report
  supplies later execution evidence rather than rewriting their decisions.

## Next increment

The owner requested an intermediate real SELECT 1 path before the guide
smoke and hydrological queries:

Application orchestrator -> Analyzer -> Nightshift/Nemotron -> run_sql
-> application-controlled Zetaris executor -> tool result -> Nemotron
-> structured Analyzer result -> application orchestrator.

Preserve the same tool name and SQL argument contract across explicitly
selected stub and Zetaris executors. Keep dispatch validation and tool-result
correlation unchanged. The probe's marker is test evidence, not a required
field for every production SQL result.

The existing entry-point, model and Zetaris files were placeholders at last
inspection. A controlled HTTP probe alone must not be reported as this
completed application path. Source-specific weather/hydrometry queries follow
only after this increment and owner-provided object verification.

## References

- [Project status](../../PROJECT_STATUS.md)
- [Validation register](../README.md)
- [Nightshift requirements](../../architecture/nightshift-integration-requirements.md)
- [Decision 0011](../../decisions/0011-demand-driven-analysis.md)
- [Earlier text API smoke](0006-nightshift-live-api-smoke.md)

## Report history

| Date | Change |
|---|---|
| 2026-10-27 | Recorded the successful structured-tool probe, exact command, observed marker round trip and owner-requested real Zetaris SELECT 1 next step. |
