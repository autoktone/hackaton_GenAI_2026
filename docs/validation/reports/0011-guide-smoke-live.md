# 0011 - Adapted guide smoke live run

- Date: 2026-10-27.
- Result: Partial; two checks passed and the web check failed.
- Process exit code: 1.
- Approval evidence: Ok.
- Execution context: Python Ubuntu WSL, native Zetaris web/REST requests and
  explicitly selected Windows-loopback Nightshift transport.
- Retries: none.
- Resources created or changed by SQL: none; the only SQL was SELECT 1 AS one.

## Scenario and preconditions

Run the three Participant Setup Guide page-24 checks through the adapted
smoke_test.py. The existing private .env.local supplies Zetaris settings and
ZETARIS_BASE_URL. Nightshift uses the owner-supplied Runtime URL and matching
private Windows token. No credentials were displayed or copied.

Standalone adaptation evidence is in report 0010. This live run does not
replace the separate agentic application evidence in report 0009.

## Exact executed command

This retained command is not authorization for another execution.

```powershell
wsl.exe -d Ubuntu --cd /home/info/flood-risk-intelligence --exec python3 -B smoke_test.py --zetaris-env-file /home/info/getting-started/.env.local --nightshift-base-url http://127.0.0.1:8088/v1 --route meterless/auto --transport windows-loopback --details
```

## Expected result

All three configured checks print PASS and the process exits 0.
Each check is attempted once independently, as documented for this adaptation.

## Observed result

```text
FAIL Data: Zetaris web interface ZETARIS_WEB_HTTP_ERROR
PASS Data: Zetaris runs SQL over its REST API
PASS Power: Nemotron replies
{
  "checks": [
    {
      "status": "FAIL",
      "name": "Data: Zetaris web interface",
      "errorCode": "ZETARIS_WEB_HTTP_ERROR"
    },
    {
      "status": "PASS",
      "name": "Data: Zetaris runs SQL over its REST API",
      "errorCode": null
    },
    {
      "status": "PASS",
      "name": "Power: Nemotron replies",
      "errorCode": null
    }
  ],
  "evidence": {
    "sql": {
      "columns": [
        "one"
      ],
      "rows": [
        [
          1
        ]
      ],
      "rowCount": 1,
      "truncated": false,
      "sourceKind": "zetaris_rest",
      "operationId": "6f3fa5d4-0a73-4c6f-9e2e-641be224d868",
      "evidenceId": "5b114c1b-0df9-404a-8907-2759fa8ef149"
    },
    "power": {
      "requestedRoute": "meterless/auto",
      "reportedModel": "nvidia/nemotron-3.5-lightning-30b-a3b",
      "text": "ready",
      "contentValidation": "nonempty_text_only",
      "runtimeJudge": "not_established"
    }
  }
}
```

The SQL adapter returned normalized rows [[1]] from real Zetaris.
Its operationId is also the submitted queryId; evidenceId is an application
receipt, not an independent source attestation.

Nightshift returned ready and reported
nvidia/nemotron-3.5-lightning-30b-a3b for meterless/auto.
This establishes response and reported model identity for this invocation,
not a successful JUDGE/VERIFY outcome.

The web check returned ZETARIS_WEB_HTTP_ERROR. The checker does not retain
the numeric HTTP status or response headers. The observed failure therefore
does not establish a particular HTTP code, endpoint mismatch, authentication
failure, redirect or platform outage.

Total smoke duration was not instrumented. No additional network diagnostic
was run and the smoke was not repeated.

## Interpretation and open issue

The overall smoke failed; do not present it as three PASS lines or a completed
guide smoke.

The adaptation deliberately refuses redirects, unlike the original guide's
requests.get behavior. A legitimate UI redirect is a hypothesis only and must
be verified before changing the check. The successful SQL check confirms that
this web result did not prevent the direct REST SELECT operation.

Proposed next diagnostic, requiring separate approval:
one GET to the same configured web endpoint, retaining numeric HTTP status
and safe redirect metadata only. No raw response body, credentials, URL query
or Location value should be logged. Do not change the endpoint, follow an
unreviewed redirect or weaken the checker automatically.

## Limits

- Web availability remains unresolved.
- No source-specific weather/hydrometry data, station joins or hydrological
  analysis was performed.
- No World Model, workflow executor or durable tracing was exercised.
- No full hackathon compliance, forecast accuracy or JUDGE acceptance is claimed.
- Existing configured checks are independent; two PASS results do not turn the
  overall failed process into a success.
- Client timeouts do not prove remote work stopped.

## References

- [Project status](../../PROJECT_STATUS.md)
- [README](../../../README.md)
- [Validation register](../README.md)
- [Guide adaptation standalone checks](0010-guide-smoke-adaptation-standalone.md)
- [Successful agentic application path](0009-select-one-live-application.md)
- [Participant Setup Guide](../../Participant%20Setup%20Guide.pdf)

## Report history

| Date | Change |
|---|---|
| 2026-10-27 | Recorded the single live smoke attempt: SQL and Nemotron passed, web check failed, exit 1; cause remains unverified and no retry was run. |

## Source fingerprints

- smoke_test.py: 076b47809b95e2df74a327dc73afcc92418711c86122e8f8d0d3ea86c95eee7e
- agent/tools_zetaris.py: 7628f0fd633818081f4f4c033968b7e846b92cbd14cc55d6c37e42dc162d59c0
- agent/llm.py: dd093b7d54b653e136bf02902e352e8299a276b60479a4d7293b0897dfef132a
