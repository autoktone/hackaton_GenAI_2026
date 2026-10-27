# LIVE services and data setup

SAMPLE does not need any of this setup. It runs from the repository with Python
and captured data. LIVE requires explicitly configured external services.
This document is an operator checklist, not a claim of automated full bootstrap.

## 1. Install the platforms

Use the included Participant Setup Guide and your own Zetaris installation
bundle/registry access. Install Zetaris and create your own account and REST
API key. The tested installation is Docker Zetaris 2.4.3.1.

Install/configure Meterless Nightshift and a working route in its Console.
The successful route was meterless/auto; response metadata reported
nvidia/nemotron-3.5-lightning-30b-a3b. Do not replace the configurable route
with that model ID in application code.

The current application LIVE transport is Windows-loopback from Python WSL.
Its private Runtime token stays in the Windows state directory:
LOCALAPPDATA/ai.meterless.runtime/proxy-token. The browser never receives it.
The application's server configuration remains private.

Restore the optional official World Model using the commands at the top of
README.md. This runtime is deliberately excluded from Git; its source and lock
are recreated from the retained pinned references before npm ci.

## 2. Configure your private REST access

Copy .env.example to .env.local only if you have no existing configured file.
Set ZETARIS_REST_URL to your API base ending in /api/v1.0, the correct
ZETARIS_ORG_ID (1 on the tested local installation), and your ZETARIS_API_KEY.
Username/password are not needed by this application's bearer REST calls.

The demo consumes those Zetaris fields from the explicit --zetaris-env-file
argument. MODEL_BASE_URL, MODEL_API_KEY and NEMOTRON_MODEL in the example are
for the optional original guide smoke; the web demo's Runtime URL and route
are explicit CLI arguments. Do not assume it automatically reads a .env file.

Backend SQL is restricted to admitted read-only grammar and authorized sources.
Use least-privilege read credentials after administrator onboarding. The
prototype does not establish or audit your database account grants.

## 3. Required objects and actual sources

| Object | Source | Verified scope and limitation |
|---|---|---|
| flood_hydro | Existing Lightning database | Reused for the CSV, not a newly deployed database server |
| flood_analysis.v_hydro_stations | Hub'Eau hydrometry station reference | 103 station codes / 68 sites at inspection; exact original registration URL/filter was not exported |
| flood_analysis.v_hydro_observations | https://hubeau.eaufrance.fr/api/v2/hydrometrie/observations_tr | 1000 exposed rows at inspection, partial overlap; H in m / Q in m3/s in the normalized view |
| flood_analysis.v_hydro_history | https://hubeau.eaufrance.fr/api/v2/hydrometrie/obs_elab | 1000 QmnJ rows on three station codes, 2024 bounds; no verified match to the reference by station code |
| flood_hydro.meteo_precipitations_raw | Owner-supplied Meteo-France CSV | 5490 rows, 15 station codes, 2024; static file, not a weather REST collector |

The exact hydrometry columns/types are preserved in
[report 0015](../validation/reports/0015-hubeau-sql-discovery.md) and the
application catalog in agent/hydro_catalog.py. The model receives that catalog
on each inference request.

The source endpoints above were supplied by the owner and the SQL views were
actually queried. Do not assume all pages, stations, dates or revisions were
collected. The complete original Hub'Eau REST registrations and view-creation
SQL are not shipped as a tested fresh-instance bootstrap. To reproduce them,
configure your own sources in Zetaris and expose the documented contracts,
or use an existing configured instance. This is a known LIVE setup limitation,
not a requirement for judging the SAMPLE.

The operator must supply the original weather CSV or another explicitly
qualified dataset. The repository snapshot contains only five weather rows;
it is not the full 5490-row CSV. The official weather resource URL and licensing were subsequently verified;
see [data attribution and raw-input restoration](../data-sources.md).
Source unit/quality semantics remain unverified in the application. If you use a different file,
reverify its schema/coverage and update the catalog rather than claim the
original metadata applies.

## 4. Register the CSV under the configured local SQL root

A readable shared Docker file is not automatically an allowed SQL path.
The installed driver checks the configured local filesystem root.

The tested API and driver both contained:

~~~text
ZETARIS_LOCAL_FILE_SYTEM_ROOT_PATH=/home/zetaris/customer-data/shared
~~~

The spelling SYTEM is the actual installed setting. Inspect your own
configuration; do not disable path validation.

NDP's virtual /file-store maps to an organisation-specific directory and is
separate from this SQL root. Merely uploading/browsing there did not make the
path acceptable to the tested driver.

Place your CSV under the configured root and ensure the driver can read it.
In the owner setup, the successful file was:

~~~text
/home/zetaris/customer-data/shared/meteo_precipitations_44_2024.csv
~~~

Source and copied file matched SHA-256:
5fbffc154a7b04fbed8c696abbeb6bb2fc32dae8bb8f3d39c9239d8deb36ceaf.

Use the SQL Workspace as an authorized administrator for registration.
First inspect existing objects and reuse a matching table. Do not drop or
overwrite existing resources merely to repeat this setup.

Only if the logical database does not already exist, create it:

~~~sql
CREATE LIGHTNING DATABASE flood_hydro DESCRIBE BY 'Flood data'
~~~

Register the file using your actual allowed path:

~~~sql
CREATE LIGHTNING FILESTORE TABLE meteo_precipitations_raw
FROM flood_hydro FORMAT CSV
OPTIONS (
  path 'file:///home/zetaris/customer-data/shared/meteo_precipitations_44_2024.csv',
  header 'true',
  delimiter ',',
  inferSchema 'true'
)
~~~

Verify by actual reads; CREATE success alone is insufficient:

~~~sql
DESCRIBE flood_hydro.meteo_precipitations_raw
~~~

~~~sql
SELECT * FROM flood_hydro.meteo_precipitations_raw LIMIT 5
~~~

~~~sql
SELECT COUNT(*) AS row_count, COUNT(DISTINCT NUM_POSTE) AS station_count,
       MIN(AAAAMMJJ) AS first_day, MAX(AAAAMMJJ) AS last_day,
       COUNT(RR) AS nonnull_rr
FROM flood_hydro.meteo_precipitations_raw
~~~

Actual inferred columns: NUM_POSTE int, NOM_USUEL string, LAT double, LON double,
AAAAMMJJ int, RR double, QRR int. Dates are integer YYYYMMDD values.
Do not interpret RR units/accumulation or QRR quality meanings without source
documentation. No Python weather calculation is part of this integration.

[Report 0017](../validation/reports/0017-meteo-csv-zetaris-import.md) records
the actual diagnosis, failed virtual path, successful CREATE/SELECT and values.

## 5. Start LIVE

After restoring World Model and configuring the two services:

~~~bash
python3 -B -m agent.demo --mode live --world-model memory --port 8766 --nightshift-base-url http://127.0.0.1:8088/v1 --route meterless/auto --zetaris-env-file /absolute/path/to/.env.local
~~~

In the owner environment, use /home/info/getting-started/.env.local as that
explicit configuration path. Open http://127.0.0.1:8766 and start an analysis.
The weather question matches the source path verified in report 0018.

The application uses POST <ZETARIS_REST_URL>/sql-editor/sqls/run and Nightshift
POST /v1/chat/completions. Preflight also used GET /datasource/datasources.
Nightshift /healthz proves only process availability; authenticated /v1/models
is the readiness/model-route discovery check.

Only explicitly admitted run_sql reads are executed. The model cannot create
tables, rewrite global workflow state or grant permissions.

## Troubleshooting and delivery boundaries

- Invalid file path to access: check the driver's configured SQL root, not only
  permissions or the NDP browser. No Docker change was needed in this setup.
- Empty hydrometry: verify source filters/pagination and station/site identity.
  A successful empty SELECT is not a transport error.
- Temporary SQL failure: workflow 1.3 allows one bounded read retry, then human
  intervention. It does not silently substitute SAMPLE data.
- 401/403: verify the matching server-side credentials; do not switch accounts
  or reuse a different provider's key automatically.
- Runtime unavailable: check the chosen Windows Console endpoint and token;
  other device/WSL addresses need their own reachable configuration.
- World Model missing: run the verified-source restore script and npm ci.
  Do not advertise the portable trace as the actual engine.
- Missing UUID citations: the structured result preserves backend provenance
  and flags incomplete generated citations; it is not a JUDGE approval.
- There is no deployed public judge gateway, production identity system or
  durable restart/resume. Access to an operator's live installation would need
  a separately arranged personal channel; no shared password/token is in Git.

## History

- 2026-10-27: Added exact optional runtime/service setup, verified CSV registration, source inventory and explicit LIVE bootstrap limits.

- 2026-10-28: Linked the verified official weather archive, attribution and optional restoration while retaining unresolved scientific semantics.
