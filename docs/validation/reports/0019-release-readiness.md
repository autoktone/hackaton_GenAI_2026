# Release readiness verification

Date: 2026-10-28 (Europe/Paris).
Scope: public Git packaging, credential-free SAMPLE and optional official
World Model installation. This does not publish or initialize the owner's
project repository.

## Observed checks

- The project root was not yet a Git repository.
- A separate local bare repository and clean clone were created under ignored
  .cache using the actual .gitignore rules.
- All required application, interface, snapshot, reference/provenance and
  installation files were present. README local link targets existed.
- No known secret from the project's private environment files and no checked
  high-confidence token/private-key pattern was found in candidate files.
  Values were never displayed. This is a bounded screening, not a universal
  guarantee about arbitrary future files or Git history.
- Git excluded private environment files, secrets, vendor, node_modules,
  caches and virtual environments. The empty .env.example, provenance,
  licenses and lockfiles remained eligible.
- All 15 targeted tests passed from the clean clone with site-packages
  disabled: 3.516 seconds reported by unittest.
- The documented SAMPLE CLI started in the clean clone. HTTP UI/config and
  streamed weather analysis passed; five captured rows were returned.
  Inference was explicitly scripted; portable World Model was disabled.
- The restore script verified all 24 pinned upstream hashes, made no changes
  in dry run, then reconstructed the official source tree in the clone.
- A fresh locked npm installation succeeded: 56 packages. The first offline
  attempt lacked cached dependencies; registry-backed npm ci then succeeded.
  A second clean short-path clone installed successfully from the warmed cache.
- SAMPLE with actual official World Model passed in that clean short-path
  clone: 16 native events. Inference remained scripted and no Zetaris or
  Nightshift credentials were used.

## Commands exercised

~~~bash
python3 -S -B -m unittest discover -s tests/unit -p test_demo.py -q
python3 -S -B -m agent.demo --port 0
python3 -S -B scripts/prepare_world_model.py
python3 -S -B scripts/prepare_world_model.py --apply
npm --prefix vendor/meterless/world-model/reference ci --include=dev --no-audit --no-fund
~~~

The CLI server test requested the displayed ephemeral localhost port, checked
GET / and GET /api/config, then POST /api/analyze with scenario weather.
It terminated only its own temporary test server.
The engine probe constructed DemoBackend(world_model="memory"), ran scenario
weather and checked PASSED, worldModelUsed=true, scripted inference and 16
native events. It closed the bridge afterwards.

For this host, npm was invoked using /usr/bin/node and the previously verified
Linux npm 10.9.2 CLI; the first clone used --prefer-offline after an --offline
cache miss. No package was installed globally or in the owner's existing vendor.

## Observed anomaly and limits

A deeply nested temporary clone failed on a tsx IPC Unix socket with EADDRINUSE.
Its socket pathname was too long for the usual Linux Unix-socket pathname
budget. The source/dependencies were unchanged; a shorter clone with a
98-character expected socket pathname passed. Keep optional-engine checkouts
short. No official source or application bridge was changed to mask the issue.

No new LIVE SQL/inference or original guide smoke was run during this audit.
The real Nightshift/Nemotron, Zetaris and World Model weather round trip remains
the evidence in [report 0018](0018-workflow-13-and-live-weather-analysis.md).
A clean LIVE bootstrap still requires operator-managed platforms, credentials,
source onboarding and the documented WSL/Windows transport.

The source snapshot carries real-data attribution, not a scientific-validation
claim. See [data sources](../../data-sources.md). The unused compressed weather
archive is excluded with its URL/hash retained; local data is preserved.
The requested guide PDF is retained and accounts for most upload size.
The final post-packaging check is recorded below after execution.

## Final packaging check

Passed after the packaging/documentation changes: all 15 targeted tests,
candidate secret/exclusion checks, local links and unchanged runtime/observation
rows. The optional extraction helper also passed an isolated synthetic-fixture
check for checkout-relative paths, the 2024 filter and refusing output overwrite.
No synthetic fixture was added to the application dataset. No archive was
downloaded and no full CSV was regenerated. No owner Git repository was created.


## History

- 2026-10-28: Recorded clean-clone SAMPLE tests, pinned engine reinstallation, real engine execution, secret screening and explicit delivery limits.
