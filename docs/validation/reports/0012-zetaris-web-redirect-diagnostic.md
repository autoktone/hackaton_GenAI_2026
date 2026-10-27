# 0012 - Zetaris web smoke redirect diagnostic

- Date: 2026-10-27.
- Result: HTTP 307 and a Location header observed.
- Approval evidence: Ok.
- Scope: one GET to the same configured web URL, without following redirects.
- SQL and Nightshift calls: none.
- Source code changed: none.

## Context

Report 0011 recorded ZETARIS_WEB_HTTP_ERROR without retaining the numeric
status. The separately approved diagnostic retained only safe metadata.

## Exact executed command

This retained command is not authorization to repeat the request.

```powershell
$webDiagnostic = @'
import json
from urllib.error import HTTPError
from urllib.request import Request, ProxyHandler, build_opener
from agent.tools_zetaris import ZetarisSettings, _NoRedirect
from smoke_test import validate_web_url

result = {}
try:
    settings = ZetarisSettings.from_env_file(
        "/home/info/getting-started/.env.local")
    url = validate_web_url(settings.web_url)
    opener = build_opener(ProxyHandler({}), _NoRedirect())
    with opener.open(Request(url, method="GET"), timeout=10) as response:
        result = {"httpStatus": response.status}
except HTTPError as error:
    result = {
        "httpStatus": error.code,
        "hasRedirectLocation": bool(error.headers.get("Location"))
    }
    error.close()
except Exception:
    result = {"errorCode": "WEB_DIAGNOSTIC_FAILED"}
print(json.dumps(result))
'@
$webDiagnostic | wsl.exe -d Ubuntu --cd /home/info/flood-risk-intelligence --exec python3 -B -
```

## Expected and observed result

Expected: numeric HTTP status and a boolean indicating a redirect header,
without logging a body, credential, URL or raw Location.

Observed, process exit 0:

```json
{
  "httpStatus": 307,
  "hasRedirectLocation": true
}
```

The configured endpoint returned a redirect. The adapted smoke's refusal to
follow it explains this immediate check failure. The original guide example
uses requests.get, which follows redirects by default.

The target URL, origin, scheme, path and final HTTP result were not inspected.
No redirected request was sent. This does not establish that the target is
reachable, safe or an HTTP 200 page. It does not turn report 0011 into a pass.

## Proposed correction, not implemented

Consider a bounded web-only redirect policy: preserve the configured origin,
scheme and effective port, reject credentials in URLs, never forward secrets,
bound requests and elapsed time, and require a final HTTP 200.

The direct SQL and Nightshift transports must retain their existing
no-redirect policy. A permissive global redirect handler is not proposed.

Exact handling, isolated tests and any follow-up live request require
separate approval. No smoke retry, endpoint change or dependency install
occurred in this diagnostic.

## References

- [Failed live smoke](0011-guide-smoke-live.md)
- [Project status](../../PROJECT_STATUS.md)
- [Validation register](../README.md)
- [README](../../../README.md)

## Report history

| Date | Change |
|---|---|
| 2026-10-27 | Recorded one HTTP 307 response and Location-header presence; target validation and a bounded web-only correction remain pending. |

## Checked implementation fingerprint

- smoke_test.py: 076b47809b95e2df74a327dc73afcc92418711c86122e8f8d0d3ea86c95eee7e
