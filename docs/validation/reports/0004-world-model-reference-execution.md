# 0004 - Official World Model reference execution

- Date: 2026-10-26.
- Result: Passed for the official reference suites.
- Application Git reference: Not recorded.
- Upstream repository: https://github.com/Meterless/Meterless
- Upstream commit: 1742dec56a66e58eef9dda2d2b865823758ca8cd.
- Reference package: @meterless/world-model-reference 0.1.0.

## Preconditions and scope

The project owner approved the working copy, dependency installation, and
official test execution. The selected upstream reference files were copied to
vendor/meterless/world-model without modifying the documentary originals.
Node dependencies and local caches are excluded by .gitignore.
This report verifies the official reference, not the Python application adapter.

## Attempts and environment correction

1. Bare npm invoked through WSL resolved to Windows npm 12.2.1 with Windows
   Node 24.19.0. Installation failed with Maximum call stack size exceeded.
   No reference or conformance tests ran in this attempt.
2. Explicit Linux Node 22.22.1 with the existing Windows npm JavaScript CLI
   failed the package's declared Node compatibility check.
   Installation and suites were not attempted after that rejection.
3. npm 10.9.2 was downloaded into the project cache from the official npm
   registry. The archive matched its published SHA-512 integrity value.
   Its declared Node compatibility check passed on Linux Node 22.22.1.
   Installation and both official suites then passed.

## Successful command sequence

The bootstrap portion is first-time setup and deliberately stops if its
destination exists. For subsequent checks with the prepared cache, start
with the dependency or test commands as appropriate.

```powershell
$bootstrapNpm = @'
import base64
import hashlib
import io
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

root = Path("/home/info/flood-risk-intelligence")
target = root / ".cache/tools/npm-10.9.2"
if not root.is_dir() or target.exists():
    raise SystemExit("Destination unavailable; no files changed.")
metadata_url = "https://registry.npmjs.org/npm/10.9.2"
archive_url = "https://registry.npmjs.org/npm/-/npm-10.9.2.tgz"
with urlopen(metadata_url, timeout=30) as response:
    metadata = json.load(response)
if metadata["version"] != "10.9.2" or metadata["dist"]["tarball"] != archive_url:
    raise SystemExit("Unexpected package metadata.")
with urlopen(archive_url, timeout=30) as response:
    archive = response.read()
integrity = "sha512-" + base64.b64encode(
    hashlib.sha512(archive).digest()).decode()
if integrity != metadata["dist"]["integrity"]:
    raise SystemExit("Package integrity mismatch.")
target.mkdir(parents=True)
with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as package:
    package.extractall(target, filter="data")
(target / "provenance.json").write_text(json.dumps({
    "version": metadata["version"],
    "metadata_url": metadata_url,
    "archive_url": archive_url,
    "integrity": integrity,
    "engines": metadata.get("engines"),
    "retrieved_at": datetime.now(timezone.utc).isoformat()
}, indent=2) + "\n", encoding="utf-8")
print("PASS: Project-local npm downloaded and integrity verified.")
'@
$bootstrapNpm | wsl.exe -d Ubuntu -- python3 -
if ($LASTEXITCODE -ne 0) { throw "npm preparation failed." }

$checkNpm = @'
const base = "/home/info/flood-risk-intelligence/.cache/tools/npm-10.9.2/package";
const pkg = require(base + "/package.json");
const semver = require(base + "/node_modules/semver");
if (process.platform !== "linux" ||
    !semver.satisfies(process.version, pkg.engines.node))
    throw new Error("Incompatible runtime.");
console.log("PASS:", process.platform, process.version, "npm", pkg.version);
'@
$checkNpm | wsl.exe -d Ubuntu -- /usr/bin/node -
if ($LASTEXITCODE -ne 0) { throw "Compatibility check failed." }

wsl.exe -d Ubuntu -- /usr/bin/node /home/info/flood-risk-intelligence/.cache/tools/npm-10.9.2/package/bin/npm-cli.js --cache /home/info/flood-risk-intelligence/.cache/npm --prefix /home/info/flood-risk-intelligence/vendor/meterless/world-model/reference ci --ignore-scripts --no-audit --no-fund
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }

wsl.exe -d Ubuntu -- /usr/bin/node /home/info/flood-risk-intelligence/.cache/tools/npm-10.9.2/package/bin/npm-cli.js --cache /home/info/flood-risk-intelligence/.cache/npm --prefix /home/info/flood-risk-intelligence/vendor/meterless/world-model/reference test
if ($LASTEXITCODE -ne 0) { throw "Reference tests failed." }

wsl.exe -d Ubuntu --cd /home/info/flood-risk-intelligence/vendor/meterless/world-model/reference -- ./node_modules/.bin/tsx ../conformance/runner.ts
if ($LASTEXITCODE -ne 0) { throw "Conformance checks failed." }
```

## Expected and observed results

| Check | Expected | Observed |
|---|---|---|
| npm archive | Published integrity matches | Passed |
| Tool compatibility | Linux Node satisfies npm engines | Linux v22.22.1, npm 10.9.2 |
| Dependency installation | Successful locked install without lifecycle scripts | Exit 0; 56 packages added in 14 seconds |
| Official reference suite | All smoke tests pass | 10/10 passed; Vitest 3.2.7; duration 3.69 seconds |
| Official conformance suite | All checks pass | 8/8 passed; exit 0 |

Conformance cases passed: sid-001, sid-002, band-001, prov-001, idem-001,
idem-002, bitemp-001, and audit-001.
They cover the suite's stable IDs, merge boundaries, required provenance,
ingest idempotency and mutation sensitivity, temporal edges, and ordered audit.

## Source preservation

After the successful suites, 24/24 copied source files matched the SHA-256
fingerprints in the preserved upstream provenance manifest.

## npm bootstrap provenance

Version: 10.9.2

Metadata: https://registry.npmjs.org/npm/10.9.2

Archive: https://registry.npmjs.org/npm/-/npm-10.9.2.tgz

Verified integrity: sha512-iriPEPIkoMYUy3F6f3wwSZAU93E0Eg6cHwIR6jzzOXWSy+SD/rOODEs74cVONHKSx2obXtuUoyidVEhISrisgQ==

## Limits

No Python-to-World-Model adapter or application workflow has been implemented
by this verification. Application run isolation, multiple blockers, scoped
approvals, reconstruction after restart, staged publication, crash recovery,
and exactly-once external effects are not established by these suites.
Ingest idempotency does not establish business-operation idempotency.
No Nightshift or Zetaris request was performed in this sequence.
The final real-data and Nightshift-backed demonstration remains outstanding.

## History

- 2026-10-26: Recorded failed tooling attempts, the working Linux toolchain, official suite results, and source-integrity evidence.
