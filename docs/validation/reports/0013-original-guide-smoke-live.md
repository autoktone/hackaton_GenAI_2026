# 0013 - Original Participant Setup Guide smoke passed

- Date recorded: 2026-10-27.
- Result: all three guide checks passed.
- Script process exit code: 0.
- Approval evidence: Ok.
- Execution context: Ubuntu WSL with the project's .venv Python.
- Launches by Codex for this check: one.
- Source unchanged during execution: yes.
- Source SHA-256: 295c5e8e8be4c9f518dddfdceb183bfb956fe88faf95e89227f8378552dea22c.
- Guide source: Participant Setup Guide.pdf, page 24, updated 21 October 2026.

## Context and source identity

The owner restored the original guide script to smoke_test.py and retained a
separate copy of the previous adaptation. Codex corrected indentation and
line layout only. A significant-token comparison, including comments,
confirmed that the formatting correction did not change code tokens.
Syntax was checked without executing the script at that stage.

The owner then reported the original script's three PASS lines after changing
Windows/WSL connectivity and private configuration. No firewall, forwarding or
network setting was changed or independently audited by Codex.

After separate approval, Codex independently launched the original restored
script from the project directory. It did not substitute the application
provider client, SQL adapter or former adapted web checker.

Reports 0010 to 0012 describe the earlier adaptation and its redirect refusal.
They remain historical evidence; they are not results from this original
script. The proposed redirect correction was not implemented.

## Preconditions

The project .venv and guide dependencies were already present. Codex installed
nothing for this execution. The original script loads the project .env through
python-dotenv, with any existing process variables retaining their usual
precedence. SDK and package versions were not collected.

A separate masked file inspection found the six required configuration names
present, the REST/model paths structurally appropriate, and a meterless/*
model-selection value. No secret values or IP addresses were displayed.

ZETARIS_BASE_URL was absent from the file. It is optional in the original
script, which can use an exported variable or its guide default. The successful
web check does not establish which value was effective, and no addition to
.env was needed or performed.

ZETARIS_BASE_URL refers to the Zetaris web interface. MODEL_BASE_URL identifies
the AI provider endpoint. They are different settings; this inspection did
not require changing either.

## Exact script invocation

Working directory: /home/info/flood-risk-intelligence.

The selected subprocess command was:

```bash
.venv/bin/python -B smoke_test.py
```

A standard-library parent captured stdout/stderr to protect secrets, extracted
only the three expected status labels, applied a 180-second process timeout
and compared the source hash before and after. It did not patch the script,
its dependencies, HTTP behavior or provider configuration.

### Exact approved execution guard

This is an execution record, not authorization to run it again.

```powershell
$officialSmokeCheck = @'
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

root = Path('/home/info/flood-risk-intelligence')
source = root / 'smoke_test.py'
venv_python = root / '.venv/bin/python'
selected = str(venv_python) if venv_python.is_file() and os.access(venv_python, os.X_OK) else sys.executable
interpreter_kind = 'project_venv' if selected == str(venv_python) else 'system_python'
before = hashlib.sha256(source.read_bytes()).hexdigest()
names = [
    'Data: Zetaris web interface',
    'Data: Zetaris runs SQL over its REST API',
    'Power: Nemotron replies',
]
result = {
    'script': 'smoke_test.py',
    'interpreter': interpreter_kind,
    'launches': 1,
    'timeoutSeconds': 180,
    'rawOutputSuppressed': True,
}
try:
    process = subprocess.run(
        [selected, '-B', 'smoke_test.py'],
        cwd=str(root), capture_output=True, text=True, encoding='utf-8',
        errors='replace', timeout=180, check=False,
    )
    lines = process.stdout.splitlines()
    checks = []
    for name in names:
        matching = []
        for line in lines:
            for status in ('PASS', 'FAIL'):
                prefix = status + ' ' + name
                if line == prefix or line.startswith(prefix + ' '):
                    matching.append(status)
        status = matching[0] if len(matching) == 1 else 'NOT_CONFIRMED'
        checks.append({'name': name, 'status': status})
    result['checks'] = checks
    result['processExitCode'] = process.returncode
    result['allThreePassed'] = (
        process.returncode == 0 and all(check['status'] == 'PASS' for check in checks))
    result['status'] = 'PASSED' if result['allThreePassed'] else 'FAILED'
    if not result['allThreePassed']:
        result['rawErrorDetailsWithheld'] = True
        missing = [name for name in ('requests', 'dotenv', 'openai')
                   if ("No module named '" + name + "'") in process.stderr]
        if missing:
            result['missingModules'] = missing
    for check in checks:
        print(check['status'] + ' ' + check['name'])
except subprocess.TimeoutExpired:
    result['status'] = 'OUTCOME_UNKNOWN'
    result['errorCode'] = 'ORIGINAL_SMOKE_TIMEOUT'
except Exception:
    result['status'] = 'FAILED'
    result['errorCode'] = 'ORIGINAL_SMOKE_EXECUTION_ERROR'
after = hashlib.sha256(source.read_bytes()).hexdigest()
result['scriptUnchanged'] = before == after
result['sourceSha256'] = after
if before != after:
    result['status'] = 'SOURCE_CHANGED_DURING_EXECUTION'
print(json.dumps(result, indent=2))
raise SystemExit(0 if result['status'] == 'PASSED' else 1)

'@
$officialSmokeCheck | wsl.exe -d Ubuntu --exec python3 -B -
```

## Expected and observed results

Expected: all three guide checks print PASS. The process exit code alone is
insufficient because the original script collects failures without explicitly
setting a nonzero exit code.

Observed filtered output:

```text
PASS Data: Zetaris web interface
PASS Data: Zetaris runs SQL over its REST API
PASS Power: Nemotron replies
```

Captured execution metadata:

```json
{
  "script": "smoke_test.py",
  "interpreter": "project_venv",
  "launches": 1,
  "timeoutSeconds": 180,
  "rawOutputSuppressed": true,
  "checks": [
    {
      "name": "Data: Zetaris web interface",
      "status": "PASS"
    },
    {
      "name": "Data: Zetaris runs SQL over its REST API",
      "status": "PASS"
    },
    {
      "name": "Power: Nemotron replies",
      "status": "PASS"
    }
  ],
  "processExitCode": 0,
  "allThreePassed": true,
  "status": "PASSED",
  "scriptUnchanged": true,
  "sourceSha256": "295c5e8e8be4c9f518dddfdceb183bfb956fe88faf95e89227f8378552dea22c"
}
```

No timeout occurred. The original SDK retained its settings and possible
internal retries; HTTP-attempt counts were not instrumented. One script
launch must not be reported as proof of exactly one provider HTTP request.

## Interpretation and limits

The original guide's three-check setup verification passed independently of
the owner's earlier manual result. The script source remained unchanged.

The original Power check asserts that reply.choices exists. It does not retain
the serving-model field or assert exact ready text. Therefore this report does
not independently establish the concrete serving model, exact answer, JUDGE
acceptance or full Runtime-contract compatibility. Earlier report 0009 retains
its own separate Nemotron model evidence and agentic application path.

The original web check follows requests' normal redirect behavior. The final
URL and redirect chain were not logged; the earlier 307 diagnostic remains
specific evidence from the former no-redirect checker. No security audit of
the owner's network changes is claimed.

This smoke does not execute World Model, workflow 1.2.0, hydrological collectors,
statistical analysis, durable tracing or the complete judging SAMPLE.
Passing it does not by itself establish complete hackathon eligibility or
scientific forecasting validity.

The original script runs checks at import time. The legacy isolated test file
tests/unit/test_smoke_test.py targets the former adaptation and must be
retargeted before reuse; importing the original during discovery can initiate
live checks. Those legacy tests were not rerun or modified for this record.

## Next work

Return to the business demonstration after separately approved planning:
World Model/workflow integration, controlled scenarios, owner-provided real
source verification, normalization and explainable hydrological analysis.
Any new operation still requires the project approval policy.

## References

- [Participant Setup Guide](../../Participant%20Setup%20Guide.pdf)
- [Project status](../../PROJECT_STATUS.md)
- [README](../../../README.md)
- [Validation register](../README.md)
- [Earlier adapted smoke](0011-guide-smoke-live.md)
- [Earlier web diagnostic](0012-zetaris-web-redirect-diagnostic.md)
- [Live agentic application probe](0009-select-one-live-application.md)

## Report history

| Date | Change |
|---|---|
| 2026-10-27 | Recorded the independent three-PASS run of the original guide smoke, unchanged source fingerprint, optional web setting and remaining application/test limits. |
