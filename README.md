# Flood Risk Decision Intelligence

An exploratory Loire flood-analysis prototype for the Open Agent Hackathon.
It is not an official flood-warning or scientifically validated forecasting service.

## Submission snapshot and README clarification

The original submitted application is preserved at
[`hackathon-submission-2026`](https://github.com/autoktone/hackaton_GenAI_2026/tree/hackathon-submission-2026),
commit [9821503](https://github.com/autoktone/hackaton_GenAI_2026/commit/9821503e5abfb17b2fc40f4f6d96501c6599ea06).
This subsequent README-only clarification explains that existing submission.
It adds no application features and changes no code, tests, data or dependencies.

## What the sponsor technologies contribute

| Technology | Role in this application | Evidence and boundary |
|---|---|---|
| **Zetaris** | Makes the authorized hydrometry views and imported weather CSV queryable through one controlled REST SQL interface. Nemotron can request the data it needs through the backend's restricted run_sql tool. | Actual application reads were executed against Zetaris. Hub'Eau view coverage is partial; weather is an imported 2024 CSV, not a live Meteo-France API collector. |
| **Meterless Nightshift Runtime** | Provides the Analyzer's OpenAI-compatible inference endpoint and configurable routing. The backend sends the question, source catalog, permitted tools and previous tool results. | The recorded LIVE application run made two real Nightshift requests. The route was meterless/auto; the underlying model is configured in the Runtime, not hardcoded in application logic. |
| **NVIDIA Nemotron** | Within the Analyzer, selects an authorized data query through structured tool calling, receives its result and generates an explanation with stated limits. | Both responses in the recorded weather run reported nvidia/nemotron-3.5-lightning-30b-a3b. Generated text is not scientifically validated, and no positive Nightshift JUDGE verdict is claimed. |
| **Meterless World Model** | The actual official reference implementation records operational events/audits and supports the application-owned task/state projection. Python calls it through a small TypeScript bridge. | The recorded LIVE weather run produced 16 matching native events/audits. It is memory-only; World Model does not replace our orchestrator, grant permissions or provide durable recovery. |

The combined LIVE result is documented in
[report 0018](docs/validation/reports/0018-workflow-13-and-live-weather-analysis.md).
[Report 0019](docs/validation/reports/0019-release-readiness.md) separately records
clean-clone SAMPLE checks and actual official-engine installation/execution.
These are distinct tests, not claims that every mode executes every sponsor service.

## Two orchestration levels: the demonstrated agent loop

1. **User to application orchestrator:** the application receives the question,
   creates a scoped run and invokes the Analyzer with the authorized source
   catalog, context and execution limits.
2. **Analyzer to Nightshift/Nemotron:** the Analyzer submits the question and
   available tool descriptions. Nemotron requests a structured run_sql call;
   data acquisition is not a mandatory step completed before inference.
3. **Analyzer to application orchestrator:** the requested data operation goes
   through backend controls. Nemotron cannot change the global workflow,
   authorize itself or access arbitrary tables.
4. **Application orchestrator to Zetaris:** the backend validates the admitted
   read-only SQL, executes it within limits and records its outcome and
   provenance. A temporary SQL failure permits one bounded retry; an unresolved
   incident stops for human intervention.
5. **Tool result back to Nemotron:** the result returns through the Analyzer.
   The bounded loop can perform an additional authorized read when needed.
   Nemotron then generates its final response using the returned observations.
6. **Analyzer back to the application orchestrator:** the Analyzer returns a
   structured result with the answer, datasets, provenance, uncertainty,
   validation status and traces.
7. **Application orchestrator to interface and audit:** the application presents
   the conclusion separately from the evidence and scientific-validation
   status. With the official-engine profile selected, operational events and
   the task projection also go through World Model.

In the demonstrated LIVE weather run, this loop contained two model requests,
one actual Zetaris SQL read and five returned records. That query sample does
not represent the full source's coverage. No rainfall/discharge correlation,
validated flood prediction or automatic safety decision is claimed.

**SAMPLE and LIVE disclosure:** portable SAMPLE uses the same application
orchestrator, Analyzer and tool contracts with captured real observations and
explicitly scripted tool choices/responses. It requires no services or credentials
and does not execute World Model by default. The optional memory profile executes
the actual official World Model. LIVE uses real Zetaris and Nightshift calls.
A scripted SAMPLE response is never presented as live Nemotron inference.

## Original work, collaboration and reused third-party material

According to the project owner, no application code was developed before the
hackathon, and the application was not cloned or adapted from an existing
application project. Its original design and implementation were created during
the hackathon through collaboration between **one human and two AI assistants**.
The human directed the work, supplied and configured data/services, made decisions
and approved operations; the AI assistants supported design, implementation,
coherence review, debugging, testing, documentation and presentation preparation.
This describes the development process, not extra autonomous agents running
inside the delivered application.

Original project work includes the application orchestrator, bounded Analyzer
loop, controlled SQL adapters/catalog, Python-to-World-Model bridge and projection,
application-specific tests, SAMPLE scenarios, web interface and project documentation.

**Pre-existing third-party technologies and references were nevertheless reused:**
Zetaris, Nightshift, NVIDIA Nemotron, the unchanged official Meterless World Model
reference, its locked tooling dependencies, public datasets, onboarding material
and the Participant Setup Guide's original smoke script. These are acknowledged
integrations and reference material, not technologies authored by this team.
The originality statement above concerns our application, not ownership or
independent invention of these components or of general architectural concepts.

The original application code is MIT-licensed; third-party code, documents and
datasets retain their own terms. See [LICENSE](LICENSE), the
[World Model provenance](docs/references/meterless/world-model/provenance.json)
and [data attribution](docs/data-sources.md).

## Release verification - 2026-10-28

A clean local Git clone passed the 15 targeted tests and the credential-free
SAMPLE HTTP scenario. The optional official World Model was reinstalled from
pinned references/lockfile and executed successfully in a short-path clone
with 16 native events. Portable SAMPLE still leaves it disabled unless selected.

See [release evidence](docs/validation/reports/0019-release-readiness.md) and
[data attribution and raw-input restoration](docs/data-sources.md).
Keep optional World Model checkout paths short: deeply nested paths can exceed
tsx's Linux Unix-socket pathname limit. LIVE needs explicit service/data setup;
this audit did not repeat live platform inference or claim scientific validity.

## Project license and third-party materials

The project's original code is licensed under the [MIT License](LICENSE),
Copyright (c) 2026 Autoktone. Third-party components, reference documentation
and datasets retain their own licenses and attribution; the project MIT
license does not replace or relicense those materials.

The retained Meterless World Model reference is Apache-2.0; its upstream
license, pinned provenance and lockfile remain under
docs/references/meterless/world-model. See [data attribution](docs/data-sources.md)
for the public hydrometry/weather source licenses and processing provenance.

## Start here - judging and demo commands

### SAMPLE: no accounts, credentials or third-party dependencies

From the project root, with Python installed:

~~~bash
python3 -B -m agent.demo
~~~

Open **http://127.0.0.1:8765**. No pip install, .env file, Node, vendor directory,
Zetaris installation or Nightshift access is needed. Python's standard sqlite3
module is required. Tested with Python 3.14.4, including site-packages disabled;
the code uses Python 3.10+ syntax.

Choose weather, hydrometry, recovered incident or human-intervention scenario.
The interface streams real application events and validated tool results,
then displays the response, source receipts and downloadable run JSON.

SAMPLE uses captured real observations and explicitly scripted inference.
Portable SAMPLE does not execute World Model; its badge says so.
To exercise the actual engine without platform credentials, complete the optional
installation below, then run:

~~~bash
python3 -B -m agent.demo --world-model memory
~~~

### Optional official World Model installation - vendor is not in Git

Keep the provenance, license, pinned source references and package lock in
docs/references/meterless/world-model. Reconstruct the ignored runtime from
those verified files; do not substitute a homemade engine:

~~~bash
python3 -B scripts/prepare_world_model.py
python3 -B scripts/prepare_world_model.py --apply
npm --prefix vendor/meterless/world-model/reference ci --include=dev --no-audit --no-fund
~~~

The first command is a dry run. The second verifies all pinned SHA-256 values
before copying missing files; it refuses to overwrite local modifications.
It performs no download. npm ci installs the separately locked public packages
and may need registry access. No Meterless or Zetaris credentials are needed
for this installation.

The tested runtime is Linux Node 22.22.1 and npm 10.9.2. The current bridge
launches /usr/bin/node and the prepared tsx package. On WSL, ensure npm is the
Linux npm rather than an incompatible Windows executable:

~~~bash
node --version
npm --version
~~~

Upstream revision: 1742dec56a66e58eef9dda2d2b865823758ca8cd, Apache-2.0.
[Provenance](docs/references/meterless/world-model/provenance.json) and
[official repository](https://github.com/Meterless/Meterless) identify the source.
vendor/, node_modules/, environments and caches are excluded from Git.
No local files are removed by those ignore rules.

### LIVE: explicitly configured Zetaris + Nightshift + actual World Model

LIVE is optional for judges. It requires operator-managed services and private
credentials; the credential-free SAMPLE is the judging baseline.
No public gateway or shared demo password is shipped.

First complete the optional World Model installation above. Install/configure
Zetaris and Nightshift using the [participant guide](docs/Participant%20Setup%20Guide.pdf)
and the [LIVE data setup instructions](docs/setup/live-data.md). The tested
live transport runs from Ubuntu WSL to a Windows-hosted Nightshift Runtime.

If you do not already have a configured .env.local, copy .env.example to
.env.local using your editor and fill only your own Zetaris URL, organisation
and API key. Never overwrite an existing configured file. .env.example has
empty sensitive values and is intentionally versioned; real .env files are ignored.

Run with your actual Console URL, route and absolute private configuration path:

~~~bash
python3 -B -m agent.demo --mode live --world-model memory --port 8766 --nightshift-base-url http://127.0.0.1:8088/v1 --route meterless/auto --zetaris-env-file /absolute/path/to/.env.local
~~~

For the existing owner environment, the verified private configuration path is
/home/info/getting-started/.env.local. Open **http://127.0.0.1:8766** and choose
the weather scenario for the verified 2024 CSV. Click **Run live analysis** to
dispatch a real request; merely opening the UI performs no SQL or inference.

The provider route is configurable, not a hardcoded NVIDIA model. The server
reads the matching Windows Runtime token from its private proxy-token file.
It does not expose it to the browser. The Console URL must be reachable from
the chosen transport; 127.0.0.1 is not a portable address for another device.

The UI shows qualification, inference dispatch/response, model tool request,
effective SQL, typed rows, result return, report and trace. The actual engine's
task projection is shown when memory mode is selected. Race/Verify/Judge
internals are not invented; use the Nightshift Console as complementary evidence.

### Known delivery limits

- The web server binds only to 127.0.0.1. One active analysis is admitted at a
  time; LIVE starts have a two-second minimum interval. Per-run budgets are
  three inference requests, two logical SQL reads, at most four physical SQL
  attempts and 180 analysis seconds.
- Model access is not required for SAMPLE. Scripted SAMPLE text is not a new
  Nemotron response. Captured rows are not a new live collection.
- Verified weather data is a 2024 imported CSV: 5490 rows and 15 station codes.
  It is not a working Meteo-France API collector or verified 1950-2024 archive.
  RR units/accumulation and QRR meanings remain to confirm. No Python weather
  analysis was added.
- Hub'Eau reference/recent/history coverage is limited. Historical station
  overlap is unresolved and the latest earlier Givry live read was empty.
  Do not assume compatible locations or periods for rainfall/discharge analysis.
- Generated text is unverified. The live answer in report 0018 confused a
  five-row query sample with total source exposure. Backend source metadata
  and observed rows remain separate from generated claims.
- The JUDGE panel is not required for generation and no positive verdict is
  claimed. There is no scientifically validated forecast, flood threshold or
  causal correlation claim.
- World Model uses the actual official reference with an application-owned
  projection, not a native scheduler. Storage is memory-only. Full JSON-policy
  execution, durable restart/resume, production identity and public deployment
  are not implemented. Human intervention requires an explicit operator action;
  the prototype may start a new run rather than resume an old one.
- The tested LIVE topology is Ubuntu WSL + Windows Runtime and configured
  Docker Zetaris. Other live transports are not validated. Platform installation,
  private credentials and complete Hub'Eau source bootstrap are not bundled.
- Stop the server with Ctrl+C after the current run finishes. To avoid a port
  conflict, choose another explicit --port. No automatic fallback to a stub
  follows a LIVE failure.

### Original Participant Setup Guide smoke

The original smoke_test.py is preserved. It performs live checks on execution
and on import; do not import it for a generic test discovery.
It is not needed for the portable SAMPLE. If you elect to run it, use a virtual
environment, its required packages and a private .env with the exact guide keys:

~~~bash
python3 -m venv .venv
.venv/bin/python -m pip install openai python-dotenv requests
.venv/bin/python smoke_test.py
~~~

Required SQL keys: ZETARIS_REST_URL, ZETARIS_ORG_ID, ZETARIS_API_KEY.
Required Power keys: MODEL_BASE_URL, MODEL_API_KEY, NEMOTRON_MODEL.
ZETARIS_BASE_URL is only the optional web-interface check, defaulting to
http://localhost:3000. It is not the SQL or model endpoint.

The original SDK smoke runs in its Python environment. Its model URL must be
reachable there; the application's Windows-loopback transport is a separate,
explicit topology. Never mix an API key, model ID and base URL from different routes.

### Short recording sequence

1. Show the original three-PASS setup smoke if desired (prior evidence is in report 0013).
2. Run SAMPLE weather: disclose captured rows and scripted inference.
3. Show the recovery and human-intervention scenarios with visible events.
4. Run LIVE weather; show the SQL, returned rows, reported Nemotron model,
   actual World Model projection and the Nightshift Console with secrets hidden.
5. State the coverage, missing unit semantics and scientific limits; download
   the run JSON if needed.

[Project instructions](AGENTS.md), [current status](docs/PROJECT_STATUS.md) and
[validation register](docs/validation/README.md) provide deeper evidence.
Earlier milestones remain below as historical records.

## Current verified application checkpoint

The real catalog-aware weather application path passed in
[report 0018](docs/validation/reports/0018-workflow-13-and-live-weather-analysis.md):
two Nightshift calls, one real Zetaris SQL read, five returned weather rows,
and 16 matching World Model events/audits. Both responses reported
nvidia/nemotron-3.5-lightning-30b-a3b through the configured meterless/auto route.

Workflow 1.3.0 adds one bounded SQL-read retry and scoped human intervention.
Final recorded checks: 79 unit checks and 24 actual-engine checks, plus the
local SAMPLE CLI and the real weather run. Legacy workflows remain preserved.
One initial native acknowledgement anomaly was not reproduced in isolation;
its cause remains unestablished and is retained in the report.

Generated text is unverified. In the live answer, a statement confused the
five returned sample rows with the available source data. The verified source
contains 5490 rows and 15 stations for 2024. Backend provenance and source
coverage must remain visible; citation checks are not scientific validation.

The local replay command is:

~~~bash
python3 -B -m agent.main --analysis hydro --provider stub --sql-executor stub --world-model memory
~~~

This uses captured data, scripted inference and the actual prepared memory
engine. Node/locked bridge dependencies are prerequisites; a clean one-command
judging interface is still pending. The complete JSON workflow-policy executor,
durable recovery and production authorization are not claimed.

## Verified weather CSV access

The owner-supplied Meteo-France CSV is registered as
flood_hydro.meteo_precipitations_raw and included in the authorized model catalog.
Actual SQL and the application tool returned its rows: 5490 records, 15 station
codes, dates 20240101..20241231 and 5490 non-null RR values.

Verified coverage is 2024 only. No 1950-2024 completeness claim, Python weather
analysis, rainfall/discharge correlation or validated forecast is made.
RR units/accumulation semantics and QRR meaning need source confirmation.

No extra view is necessary. Example read:

~~~sql
SELECT * FROM flood_hydro.meteo_precipitations_raw LIMIT 5
~~~

Local import requires a file under the configured SQL root, not merely a file
visible in NDP's organisation file browser. The successful URI was
file:///home/zetaris/customer-data/shared/meteo_precipitations_44_2024.csv.
The existing setting is named ZETARIS_LOCAL_FILE_SYTEM_ROOT_PATH.
No Docker configuration was changed.

See [report 0017](docs/validation/reports/0017-meteo-csv-zetaris-import.md)
for the exact CREATE, path-validation diagnosis, schema, checks and limits.
This proves CSV/tool access, not a new Nightshift weather inference.

The workflow 1.3 bridge and current hydro CLI have since passed local and
real-weather checks in report 0018. Complete clean judging delivery and the
final interface remain pending.

## Earlier hydrological checkpoint (report 0016)

The hydrological Analyzer now receives the authorized three-view catalog,
verified station/site context, units, coverage caveats, tool policy, run context
and prior results on every inference request. Nemotron chooses useful reads;
the application orchestrator validates and executes them. Python adds
deterministic summaries. H-MEM remains a future option, not an implemented
catalog or permission authority.

Verified locally: 55 standalone checks, two actual World Model integration
checks and the final snapshot CLI. The CLI used captured real observations,
scripted inference and the actual official memory engine: two reads, three
scripted responses, five completed tasks and 23 native events/audit entries.

Run in the already prepared environment:

```bash
python3 -B -m agent.main --analysis hydro --provider stub --sql-executor stub --world-model memory
```

No platform credentials are required. Python with sqlite3, Linux Node and the
prepared locked World Model dependencies are prerequisites. Clean-setup judging
and the final user interface remain unverified; this is a CLI replay with
explicitly simulated inference, not a newly generated Nemotron analysis.

The latest live attempt made three Nightshift calls and two Zetaris reads.
The correct Givry observation query returned zero rows; station metadata
returned one row. A final Nemotron response was generated but failed the
exact receipt-citation check. The application reported FAILED; it must not
be presented as a successful hydrological demonstration or JUDGE validation.

The owner requires a bounded second attempt for transient SQL failures,
then orchestrator suspension and human intervention. This next mechanism
is not implemented yet and does not require another Nemotron call to manage
the infrastructure incident. Empty reads require distinct coverage checks;
a snapshot never silently replaces live data.

See the [hydrological contract](docs/architecture/hydrological-analysis.md)
and [report 0016](docs/validation/reports/0016-catalog-aware-hydro-analysis.md)
for exact commands, all observed failures, tests, limits and next work.
Earlier milestone sections are preserved below.

## Hub'Eau SQL qualification checkpoint

Actual read-only SQL confirmed all three hydrometry views:
- flood_analysis.v_hydro_stations: 103 distinct station codes, 68 sites,
  75 rows marked in service.
- flood_analysis.v_hydro_observations: exposed H/Q unit labels m and m3/s;
  1000 rows in the observed aggregate, with 12 H and 10 Q station codes
  matching the supplied reference.
- flood_analysis.v_hydro_history: exposed 1000 QmnJ rows on three station
  codes over 2024; none matched that reference by code_station.

See [report 0015](docs/validation/reports/0015-hubeau-sql-discovery.md) for actual
schemas, queries, errors, counts and the captured Givry series. These are view
results, not proof of exhaustive upstream API retrieval. Matching by code_site
and source pagination configuration were not independently checked.

A selected Givry sample, station K400001010, contains three H and three Q
points from 17:50 to 18:00 UTC on 2026-10-27: H=-1.46 m and Q=50.6 m3/s,
constant within that sample and labeled unqualified/raw (original labels are retained in the snapshot).
The short window and a height value alone cannot establish flood risk,
causality, forecasting skill or a rainfall-response lag.

Owner-reported public API endpoints:
- https://hubeau.eaufrance.fr/api/v2/hydrometrie/observations_tr
- https://hubeau.eaufrance.fr/api/v2/hydrometrie/obs_elab

The station-reference upstream URL and view-generator SQL were not inspected.
Unit labels/values were observed; upstream normalization and redistribution
conditions still require their own verification before publication claims.

The catalog-aware tool now accepts controlled reads across these three views.
A real recent-observation result (empty in the latest read) and station metadata
were returned to Nemotron; final receipt validation failed. Report 0016 preserves
the attempts and the existing orchestrator/Analyzer/World Model separation.

The weather CSV is now SQL-verified as flood_hydro.meteo_precipitations_raw
in report 0017. No v_meteo_precipitations view was required. Rainfall units and
accumulation semantics still need source confirmation. Current/incremental Q and historical daily QmnJ must not be mixed
without an explicit compatible period and aggregation rule.

## Earlier nominal-engine checkpoint (historical)

The original guide smoke passed all three checks; see
[report 0013](docs/validation/reports/0013-original-guide-smoke-live.md).
The nominal application now also uses the actual official World Model in
memory; see [report 0014](docs/validation/reports/0014-world-model-nominal-application.md).

Observed: 64 targeted tests passed, plus the actual CLI with selected provider
and SQL stubs. It produced 16 native events/audit entries and four completed
tasks with qualification, analysis, delegated data and report-preparation links.
Two simultaneous same-user runs were tested to remain isolated.

The executed local command is:

```bash
python3 -B -m agent.main --provider stub --sql-executor stub --world-model memory --trace
```

Prerequisites: Python and the already prepared official reference, Linux Node
and locked bridge dependencies described in report 0004. No live platform
credentials are needed for this command. Clean-install bootstrap is not yet
validated; this is a component demo, not the complete hydrological SAMPLE.

The output reports worldModelUsed=true and traceStatus=WORLD_MODEL_MEMORY.
It retains workflowExecuted=false and durableTrace=false: the implemented
nominal projection is not the full JSON policy executor or crash recovery.
Earlier real Nightshift/Zetaris evidence is separate; an all-real hydrological
run, source normalization, useful indicators, interface and final sample remain
to be delivered. Older milestone sections below are preserved as history.

## Earlier setup status (historical)

- Official Meterless World Model reference: 10 smoke tests and 8 conformance checks passed.
- Memory-only Python/TypeScript bridge: 9 standalone and 10 actual-engine integration tests passed.
- Nightshift live API smoke: authenticated discovery and one text inference passed from Python WSL using the explicit Windows-loopback transport.
- Complete workflows, durable recovery, the reusable Nightshift client,
  the Analyzer feature, and real-data Zetaris integration remain under development.

## Modes and delivery status

**Sample mode for judges — local replay implemented; clean setup pending.**
The required delivery is one documented command from a clean setup, without
accounts, credentials, sign-in, or live platform access.
The sample must use labeled fixtures or recorded outputs and must not
silently contact live services. It will not need a Nightshift URL.
The development checks below are not the complete judging sample.

**Live mode — partially tested.**
The live demo video must show real application requests through Zetaris and
Nightshift and use their results. Bounded application calls now reach both
platforms, but the latest hydrological attempt failed final receipt validation
and returned no Givry observations. Complete live business acceptance remains pending.

A live judge gateway is not implemented. If provided, its read-only scope,
rate limits, and access procedure must be documented and verified.
Personal access would be arranged through the organizers; reviewers must
not receive our Nightshift Runtime token or upstream provider keys.

## Development checks

Run from the project root in Ubuntu WSL. Commands are documented procedures;
agents must follow the approval policy in [AGENTS.md](AGENTS.md).

### Standalone World Model client tests

Verified with Python 3.14.4. These tests inject a stub and require no Node,
Nightshift, Zetaris, or platform credentials.

```bash
python3 -B -m unittest discover -s tests/unit -p test_world_model_client.py -v
```

Expected result: 9 tests pass.

### Actual World Model bridge tests

Prerequisites: the project files, Linux Node 22.22.1, and the prepared official
reference plus locked dependencies in vendor/meterless/world-model/reference.
First-time runtime-copy and dependency preparation is recorded in
[report 0004](docs/validation/reports/0004-world-model-reference-execution.md).
Preparation may require registry downloads; it is not an offline-bootstrap claim.
No Nightshift or Zetaris access is needed for these memory-only tests.

```bash
python3 -B -m unittest discover -s tests/integration -p test_world_model_bridge.py -v
```

Expected result: 10 tests pass.
[Report 0005](docs/validation/reports/0005-python-world-model-memory-bridge.md)
records the tested scope and limits.

## Verified live Nightshift smoke

### Prerequisites

- Windows with Nightshift installed, running, and configured with an available
  text-generation provider or lane. Provider keys are configured inside Nightshift.
- Windows PowerShell, the existing Windows System32 curl.exe, Ubuntu WSL,
  and Python 3; the recorded setup used Python 3.14.4.
- The matching Runtime token at the documented private Windows location:
  %LOCALAPPDATA%\ai.meterless.runtime\proxy-token.
- An explicitly approved inference, because it may consume provider credits.

This HTTP smoke uses Python standard-library modules and Windows curl.
Node and the Nightshift CLI are not prerequisites for this particular command.

### Endpoint and secret configuration

Copy the live base URL from the Nightshift Console into private local
configuration when the reusable configuration loader is implemented.
Do not treat http://127.0.0.1:8088/v1 as a universal project default.
The current smoke procedure is an explicit, recorded development command;
the environment-configured reusable client is still pending.

A loopback URL identifies the HTTP execution context:
- Native HTTP from Python WSL uses WSL loopback.
- The verified Windows-loopback procedure launches Windows curl from Python;
  its loopback reaches the Windows Runtime on the same host.
- Another machine requires a reachable, securely configured Runtime URL.
  Do not substitute another address, scan ports, or change networking automatically.

The recorded procedure is verified only for the operator-supplied Windows
loopback endpoint. Confirm that the Console URL matches before reusing it.
A different deployment needs explicit endpoint/transport selection and validation.
Do not reuse a token against an unrelated Runtime.

Runtime access tokens and upstream NVIDIA keys are different secrets.
Keep all credentials outside version control. Never paste tokens or secret-bearing
connect links into chat, source, examples, logs, or video.

### Complete procedure

1. Start Nightshift and finish provider/model setup. For this smoke, a text
   generation route must be available; an installed app or health response alone
   is insufficient. The sample judging mode will not require these steps.
2. Confirm the Console base URL and the HTTP execution context described above.
   In the recorded setup, Windows served port 8088 on its loopback only;
   native WSL access returned connection refused.
3. Keep the matching Runtime token in its existing private file. The command
   reads it at execution time and never displays it or writes it into the project.
4. Open Windows PowerShell and run the single complete command block in
   [report 0006, Exact successful smoke command](docs/validation/reports/0006-nightshift-live-api-smoke.md#exact-successful-smoke-command).
   It maps the existing executable/token paths into WSL, launches Python,
   and submits one POST through Windows curl. It works independently of the
   PowerShell working directory. No additional package installation is needed.
5. Inspect the filtered JSON result: httpStatus 200, finalTextReceived true,
   a final text, and finishReason stop are the recorded successful result.
   meterless/auto is the requested route; inspect reportedModel separately.
   The recorded model was nvidia/nemotron-3.5-lightning-30b-a3b.
6. Treat the output as generated, not application-verified. The command does
   not validate flood forecasts or the separate JUDGE panel.
7. Stop after an error. A timeout can leave inference completed or running;
   reconcile before another submission rather than retrying blindly.

### Troubleshooting boundaries

- No HTTP response or connection refused: check the configured endpoint and
  HTTP execution context; do not assume a credential failure.
- HTTP 401/403: the captured provider contract classifies unauthorized access.
  Correct the private credential/configuration; do not log it.
- HTTP 200 with empty final text or an unexpected body: preserve the response
  status and finish metadata; do not report a successful visible generation.
- An indeterminate JUDGE panel is separate from this text API smoke.
  A configured VERIFY lane alone is not evidence of successful verification.

No public gateway or authentication system was created by these tests.

## Documentation

- [Development instructions and project context](AGENTS.md)
- [Architecture and workflow](docs/architecture/workflow-and-planner.md)
- [Execution model and bridge](docs/architecture/execution-model.md)
- [Nightshift requirements](docs/architecture/nightshift-integration-requirements.md)
- [Decision register](docs/decisions/README.md)
- [Validation register](docs/validation/README.md)
- [Live Nightshift smoke evidence and exact command](docs/validation/reports/0006-nightshift-live-api-smoke.md)

## History

- 2026-10-27: Documented prerequisites, tested commands, endpoint contexts, secret handling, and the incomplete sample/live delivery scope.
- 2026-10-27: Clarified demand-driven Analyzer requests through the application orchestrator and linked decision 0011.
- 2026-10-27: Recorded report 0009 and the successful real Nightshift/Zetaris SELECT-one application path with scope limits.
- 2026-10-27: Recorded the guide page-24 smoke reference copy, syntax-only check and pending configuration/security adaptation.
- 2026-10-27: Documented the adapted three-check smoke, 12 isolated and 27 affected checks, explicit configuration and pending live run.
- 2026-10-27: Recorded the partial live guide smoke: SQL and Nemotron passed, web failed; no automatic retry or inferred cause.
- 2026-10-27: Recorded the HTTP 307 web diagnostic and kept redirect-target validation and correction pending.
- 2026-10-27: Recorded the original guide smoke's three PASS checks, unchanged source, optional web setting and legacy-test limitation.
- 2026-10-27: Linked the tested real-engine nominal path, 64 passing checks, local CLI and approved reduced delivery scope.
- 2026-10-27: Linked real Hub'Eau SQL schemas, coverage limits, Givry observations and pending hydrological tool integration.

- 2026-10-27: Added the delivery handover, nested Analyzer tool-loop requirements, pending source inventory, scientific limitations and deferred application storage.
- 2026-10-27: Added the minimal application probe, 27 standalone checks, explicit procedures and pending live/World Model boundaries.

## Delivery handover

See [Project status](docs/PROJECT_STATUS.md) for inspected implementation,
dependencies, open risks and next proposed work. Existing test evidence above
does not demonstrate the complete business pipeline.

The following sections record delivery requirements and planned integration,
not newly implemented or tested functionality. Accepted ADRs and existing
workflow versions remain unchanged.

## Application orchestration and the Analyzer tool loop

The application orchestrator retains control of the global workflow:
qualification, planning, dependencies, data validity, permitted dispatch,
run isolation, incidents, approvals and termination.

The Analyzer is a component invoked by that orchestrator. It receives the
question, geographical/time scope, relevant context, authorized source
descriptions and execution limits. Its required internal loop is:

```text
User question
  -> Application orchestrator
  -> Analyzer -> Nightshift / Nemotron
              <- Structured tool request
              -> Controlled backend -> Zetaris or deterministic Python calculation
              <- Tool result
              -> Nightshift / Nemotron
              <- Final analysis
  <- Structured Analyzer result
  -> Operational state, traceability and presentation
```

Nemotron selects useful analytical queries within the authorized scope.
It cannot change the global workflow, grant approval or directly update
World Model state. The Nightshift client handles provider transport; it is
not a second business orchestrator.

The backend must validate tool arguments and enforce read-only SQL access,
authorized tables/views, bounded results, deadlines and cumulative loop
budgets. Deterministic Python functions perform statistical calculations;
model-generated numbers are not a substitute for those computations.
The Analyzer returns conclusions, computed indicators, sources, uncertainties,
tool-call evidence, status and errors to the application orchestrator.

The Planner checks availability and collection needs; this does not require
every analytical query to be fixed before calling Nemotron. Subsequent reads
remain subject to the same source, time, freshness and authorization rules.
Any required refresh or action outside the Analyzer's scope returns to the
application orchestrator for an explicit decision.

Structured tool calling through the configured Runtime is not yet verified.
Text inference success alone is insufficient. Existing workflow 1.1.0 is the
deterministic intermediate baseline; a separately versioned final definition
must specify the Analyzer loop and its success/failure/trace requirements.

Record the requested Meterless route separately from available evidence of
the serving model. Present lane results only when actually returned or
observed. A generated response, a configured VERIFY lane and a successful
JUDGE verdict are distinct claims; the reported undecided panel is not
positive validation.

## External data inventory: pending connection verification

The project owner is preparing weather and hydrometry API access and objects
inside Zetaris. Application-side connection verification will follow receipt
of the source details. Do not interpret this setup activity as a completed
application integration.

| Data domain | API/source | Endpoints and Zetaris tables/views | Format and coverage |
|---|---|---|---|
| Weather | Awaiting owner-provided source | Awaiting sanitized endpoints and qualified object names | Not yet inspected |
| Hydrometry | Awaiting owner-provided source | Awaiting sanitized endpoints and qualified object names | Not yet inspected |

After approved connection checks, update this inventory with actual API names,
non-secret endpoint descriptions, qualified table/view names, schema/types,
units, timestamp/time-zone semantics, station identifiers, geographical/time
coverage, missing values and provenance. Document normalization and any
licensing or redistribution constraints before publishing a snapshot.
Never publish credentials, authorization headers or secret-bearing URLs.
Hub'Eau and Meteo-France remain candidates until the actual sources are confirmed.

Select a compatible real-data interval before freezing the business
demonstration. Preserve original measurements and document conversions and
derived values. Do not invent correlations, flood labels or favorable results.

LIVE and snapshot-backed execution should share normalization, calculations,
Analyzer tool contracts and reporting. A snapshot replays source data; it
does not itself prove a new model-generated response. Live-backed snapshot
analysis and credential-free offline judging must be identified separately.
Their final inference behavior remains to be agreed; a recorded or scripted
exchange must not be presented as a newly generated Nemotron tool decision.

The final live demonstration must show an actual application request through
Zetaris and Nightshift/Nemotron, with useful results and trace references.
Its evidence must distinguish live data, replayed real snapshots, synthetic
test fixtures, calculated values and model-generated interpretation.

## Scientific scope and limitations

The prototype explores precipitation, discharge and water-level observations
for a defined geographical area and period, optionally compared with documented
flood periods when suitable evidence is available.

This is a limited exploratory basis. The prototype does not comprehensively
model soil sealing or saturation, infiltration, catchment slopes and drainage
connectivity, channel conditions, hydraulic structures or other relevant
hydrological factors. It does not provide a calibrated and independently
validated hydrological, hydraulic or statistical forecasting system.

Only calculate time-lag relationships when sampling cadence, temporal coverage,
missing-data handling and geographical relevance support that calculation.
A correlation is not proof of causality. A generated explanation or confidence
statement is not a validated forecast or calibrated flood probability.
Historical analysis must disclose unavailable publication/revision history
and possible temporal contamination.

Results are intended for exploration and explanation, not operational warnings,
evacuation instructions or safety decisions. Forecast skill and uncertainty
would require separate scientific evaluation and suitable historical backtests.

## Deferred application storage

An additional application database for retained analytical results, comparisons
or a future internal predictive engine is outside the required hackathon scope.
H-MEM integration also remains deferred.

This deferral does not remove required operational traceability or the
separately designed event persistence, finalization and recovery mechanisms.
Those mechanisms must still be distinguished from what is actually implemented
and tested.

## Demand-driven workflow clarification

This clarification takes precedence over earlier descriptions implying
systematic data preparation before analysis.

The application orchestrator invokes the Analyzer with the question,
authorized source catalog and execution limits. Nemotron may request data;
the Analyzer forwards the request to the application orchestrator, which
checks authorization and data validity before coordinating Zetaris access.

Weather and Hydro operations are activated on demand, not as mandatory
pre-analysis stages. Results return through the Analyzer to Nemotron.
The application orchestrator retains global state, execution control,
traceability and termination.

This workflow is a validated design, not an implemented capability.
See [decision 0011](docs/decisions/0011-demand-driven-analysis.md) and
[Project status](docs/PROJECT_STATUS.md) for implementation status.

## SELECT-one application probe: standalone implementation

A minimal application orchestrator, bounded Analyzer, Nightshift client and
two SQL executors are now implemented. The shared run_sql tool accepts only
SELECT 1 AS one. Provider and SQL dependencies are selected independently;
a live failure never enables a stub automatically.

The 27 standalone checks passed; see
[report 0008](docs/validation/reports/0008-select-one-application-standalone.md).
They used injected transports, not real platform calls. The reusable Windows
worker and the application-to-Zetaris path have not yet been tested live.

Earlier sections describing the provider client as unimplemented or tool
calling as unverified predate these later milestones:
[report 0007](docs/validation/reports/0007-nightshift-structured-tool-round-trip.md)
verifies the Windows structured-tool stub probe; report 0008 verifies the
new application components with selected stubs. Neither establishes the
complete hydrological feature.

### Standalone procedure

From the project root in Ubuntu WSL with Python 3, no accounts, credentials,
packages, Node or platform access are required for this SELECT-one probe:

```bash
python3 -B -m agent.main --provider stub --sql-executor stub --trace
```

This procedure invokes the tested CLI function; the exact shell command
has not been separately executed in this increment. It emits scoped JSON
events to stderr and the structured result to stdout. The provider is scripted,
the SQL source is a stub, and no response is claimed as generated by Nemotron.

The available probe is not the complete judging SAMPLE application or a
hydrological scenario. The existing full sample/live delivery requirements
remain outstanding.

### Proposed real SELECT-one procedure: not executed

Prerequisites are the running Windows Nightshift Runtime and matching private
Runtime token, Windows PowerShell reachable from WSL, and the existing private
Zetaris .env.local with REST URL, organisation ID and API key.
The SQL identity should be read-only. This application additionally restricts
SQL to the single literal SELECT 1 AS one.

After separate approval, the currently prepared invocation is:

```bash
python3 -B -m agent.main --provider nightshift --sql-executor zetaris --transport windows-loopback --nightshift-base-url http://127.0.0.1:8088/v1 --route meterless/auto --zetaris-env-file /home/info/getting-started/.env.local --trace
```

The Runtime URL and configuration path above identify this operator's explicit
setup; they are not portable defaults. Another environment must supply its own
approved configuration. This increment implements only the explicitly selected
Windows-loopback Nightshift transport, not a general remote deployment client.

The backend reads credentials at execution time and does not copy them into
the project or output. The anticipated path uses at most two inference calls
and one real SQL call. It can consume provider credits and must not be retried
blindly after an uncertain outcome.

The Analyzer checks an elapsed-time budget of 180 seconds and the SQL HTTP
timeout is at most 15 seconds. The Windows worker has a bounded cleanup margin.
Client timeouts do not establish cancellation of server-side work.

The application result explicitly marks worldModelUsed=false,
workflowExecuted=false and durableTrace=false. Traces are in memory/stdout;
the official World Model integration, workflow executor and durable recovery
are not exercised by this probe.

## Verified live SELECT-one application milestone

The application command documented above subsequently passed on 2026-10-27.
Earlier "not executed" labels describe the preceding preparation stage;
this section records the later observed result.

The orchestrator invoked the Analyzer, Nemotron emitted run_sql, the backend
executed SELECT 1 AS one in Zetaris, and Nemotron used the returned value and
exact result receipt. The Analyzer returned its structured result to the
application orchestrator.

Observed evidence:
- Application status PASSED and Analyzer status SUCCEEDED.
- Normalized Zetaris result [[1]].
- Two Runtime completion dispatches, one SQL execution and 13 scoped events.
- Requested route meterless/auto; both responses reported
  nvidia/nemotron-3.5-lightning-30b-a3b.
- Approximately 20.95 seconds between the first and last trace timestamps.

See [report 0009](docs/validation/reports/0009-select-one-live-application.md)
for the exact executed command, captured result, traces and limitations.
This proves the tested application SELECT-one path, not a hydrological analysis.
The receipt is application correlation metadata, not a cryptographic source
attestation or a successful JUDGE verdict.

World Model, workflow 1.2.0 execution and durable traces were not exercised.
Weather/hydrometry source verification and the full judging SAMPLE remain
pending. The next proposed step is to inspect the exact Participant Setup
Guide smoke before authorizing its execution.

## Participant guide smoke copy: not executed

smoke_test.py now contains the Participant Setup Guide page-24 example, with
PDF indentation restored and source/history comments. Its Python syntax was
checked without importing the script or running any of its statements.

It is the guide reference copy, not yet adapted to this application's tested
configuration. The example requires requests, python-dotenv and openai and
loads .env; their availability was not checked and no package was installed.
Its top-level statements perform live web, SQL and inference checks when run.

Our Zetaris configuration remains in the existing private .env.local, and
Nightshift connectivity uses an explicit Windows transport. The example's
MODEL_BASE_URL/MODEL_API_KEY/NEMOTRON_MODEL setup is not presumed equivalent.
Do not copy real credentials into source or documentation to bridge that gap.

Before an approved execution, review the configuration/transport adaptation,
the fixed SELECT 1 versus our SELECT 1 AS one allowlist, SDK retry behavior,
required Runtime headers and sanitized failure output. The original example
prints exception text and a response excerpt; those paths must not expose
secrets. Its displayed PASS lines alone also do not set a failing process
exit code.

The three guide checks concern the web interface, SQL REST and model response.
They do not replace the already verified agentic application path in
[report 0009](docs/validation/reports/0009-select-one-live-application.md).
No guide-smoke result is claimed yet; current work is tracked in
[Project status](docs/PROJECT_STATUS.md).

## Adapted three-check guide smoke: standalone validated

The copied guide example has now been adapted to this project's existing
clients. Earlier reference-copy descriptions document the preceding stage.
The three live checks have not yet been run by this adapted script.

No third-party package is required. The script imports safely without
configuration reads or requests; live execution occurs only from its guarded
entry point. It reads the explicit Zetaris .env.local and uses the selected
Windows-loopback Nightshift transport.

The web endpoint comes from configured ZETARIS_BASE_URL, an exported variable
of that name, or an explicit --zetaris-web-url override. No URL is guessed.
Missing or invalid configuration fails before network calls.

After separate approval, the prepared invocation from the project root is:

```bash
python3 -B smoke_test.py --zetaris-env-file /home/info/getting-started/.env.local --nightshift-base-url http://127.0.0.1:8088/v1 --route meterless/auto --transport windows-loopback --details
```

The endpoint and private configuration path above describe the tested
operator's environment, not universal defaults. Credentials stay in their
existing private locations; do not copy values into this command or Git.

Expected successful output begins with:

```text
PASS Data: Zetaris web interface
PASS Data: Zetaris runs SQL over its REST API
PASS Power: Nemotron replies
```

The script attempts each configured check once, independently, as in the guide.
It makes at most one web GET, one SELECT 1 AS one and one Runtime text request.
It does not follow web redirects or retry a failed/uncertain request.
Client timeouts are 10 seconds for web, at most 15 for SQL and 180 for the
Runtime request, with the existing worker's bounded cleanup margin.
The checks are independent and do not constitute another agentic tool loop.

Compared with the guide, this version reuses the shared SELECT-one allowlist,
checks a nonempty text response and a Runtime-reported Nemotron model name,
sanitizes failure messages and returns exit code 1 if a check fails.
A configured route alone is not serving-model evidence; unavailable identity
fails the Power check. No successful JUDGE or scientific validation is inferred.

Twelve isolated smoke tests and 27 affected application checks passed; see
[report 0010](docs/validation/reports/0010-guide-smoke-adaptation-standalone.md).
These are standalone results, not the three live PASS lines. World Model,
full workflow execution, source collectors and complete judging SAMPLE remain
outside this smoke's scope.

## Three-check live smoke: partial result

The adapted guide smoke ran once on 2026-10-27 and exited with code 1:

```text
FAIL Data: Zetaris web interface ZETARIS_WEB_HTTP_ERROR
PASS Data: Zetaris runs SQL over its REST API
PASS Power: Nemotron replies
```

Zetaris returned the normalized SELECT-one row [[1]]. Nightshift returned ready
and reported nvidia/nemotron-3.5-lightning-30b-a3b through meterless/auto.

See [report 0011](docs/validation/reports/0011-guide-smoke-live.md) for the exact
command, captured output and limits. Earlier pending-live descriptions refer
to the preceding stage; this is a partial result, not three successful checks.

The web checker did not retain its numeric HTTP status. Its redirect-refusal
policy differs from the original guide example; a redirect is a hypothesis,
not a confirmed cause. No new diagnostic, retry, endpoint change or code
modification was performed after this result.

The next proposed action is a separately approved status-only diagnostic of
the same configured web endpoint. Do not log raw headers, response bodies,
secret-bearing URLs or Location values, and do not weaken the check without
reviewing the cause.

## Web smoke diagnostic: HTTP 307

A separately approved single GET confirmed HTTP 307 with a Location header;
see [report 0012](docs/validation/reports/0012-zetaris-web-redirect-diagnostic.md).

The adapted web check refuses redirects, whereas the guide's requests.get
follows them. This explains the immediate check failure. The redirect target
and final response were not inspected, and no redirected request was sent.

The live smoke remains partial. A bounded web-only same-origin redirect policy
is proposed for review; SQL and Nightshift redirect restrictions remain
unchanged. No correction or smoke retry has been executed.

## Original guide smoke: three PASS checks verified

This is the current setup-verification result. The owner restored the original
page-24 script and configured Windows/WSL connectivity. Codex corrected only
indentation/line layout, then independently ran the original from Ubuntu WSL
with the project .venv Python.

```text
PASS Data: Zetaris web interface
PASS Data: Zetaris runs SQL over its REST API
PASS Power: Nemotron replies
```

Exit code was 0 and the script fingerprint remained identical before and after.
See [report 0013](docs/validation/reports/0013-original-guide-smoke-live.md)
for the exact invocation, guarded output and evidence limits.

For an operator-approved run from the project directory:

```bash
.venv/bin/python -B smoke_test.py
```

The original uses the guide's dependencies and private project .env, rather
than the former adapted CLI. No CLI flags from that adaptation apply to the
original. Earlier adaptation descriptions and partial results remain preserved
above as history; no web-redirect patch was applied.

ZETARIS_BASE_URL is the optional Zetaris web-interface setting. It was absent
from the inspected .env; the original can use an exported value or its guide
default. No addition is needed solely because the file omits it.
MODEL_BASE_URL is the separate AI provider endpoint and remains required.
Do not commit or display tokens, keys, passwords or secret-bearing URLs.

This passes the original setup smoke, not the complete hydrological application
or all hackathon requirements. Its Power check only asserts reply.choices;
actual-model evidence and the agentic path remain separately recorded in
[report 0009](docs/validation/reports/0009-select-one-live-application.md).

The original executes its checks on import. Do not run the legacy
tests/unit/test_smoke_test.py suite against it: that file targets the earlier
adaptation and needs approved retargeting before reuse. No such test or source
change was performed in this documentation update.

The next project work remains the controlled and real-data business scenarios,
with source provenance, actual World Model integration and application traces.
The original smoke must not be repurposed or modified to implement them.

- 2026-10-27: Recorded catalog-aware hydro tests, failed live outcomes and the pending bounded retry/human-intervention requirement.

- 2026-10-27: Recorded verified 2024 weather CSV access and catalog scope without Python precipitation analysis; kept workflow 1.3 in progress.

- 2026-10-27: Recorded completed workflow 1.3 checks and the real weather inference with explicit generation, coverage and durability limits.

- 2026-10-27: Added credential-free SAMPLE, explicit LIVE commands, optional vendor restoration, service/data setup and known judging limitations.

- 2026-10-28: Added clean-clone release evidence, official-engine installation results, data credits and the short-checkout requirement.

- 2026-10-28: Linked the project MIT license with copyright Autoktone and preserved third-party licensing boundaries for GitHub publication.

- 2026-10-28: Clarified sponsor contributions, the demonstrated bounded agent loop, original application authorship and reused references in a post-submission README-only commit; preserved the original tagged snapshot.
