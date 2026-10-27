# 0017 - Verified Meteo-France CSV registration and application tool access

- Date: 2026-10-27.
- Approval evidence: Ok; urgent owner request and individual operation approvals.
- Result: actual table creation and SELECT verification passed.
- Nightshift was not called in this increment.
- No Python precipitation analysis was added.

## Exact cause

Installed Zetaris SQL library version: 2.4.3.1.

The driver rejected the path in LightningFileSystemUtil.checkLocalFilePath.
Inspection of the installed method showed that it removes an optional file://
prefix, rejects system directories, then requires the path to start with
LightningEnv.zetarisLocalFileSystemRootPath.

Both API and driver have this existing configuration, with the variable name
spelled exactly as installed:

~~~text
ZETARIS_LOCAL_FILE_SYTEM_ROOT_PATH=/home/zetaris/customer-data/shared
~~~

The original CSV was at /home/zetaris/customer-data/meteo_precipitations_44_2024.csv,
outside that SQL root. API logs independently showed that NDP's virtual
/file-store maps to /home/zetaris/customer-data/<organisation>/file-store.
This browser path is separate from the configured SQL access root.
The virtual /file-store/... SQL attempt was also rejected with HTTP 400:
Invalid file path to access.

Thus Linux readability and a shared Docker volume were insufficient. The
driver's SQL path validation occurred before CSV reading. This was not evidence
of an invalid CSV delimiter, missing Docker mount, or required reinstallation.

The driver did not include javap. The relevant installed class methods were
read in memory using Python standard-library ZIP/class inspection; no runtime
file, library, package or configuration was changed. A library-name listing
took 82.159 seconds; it was not repeated.

## Minimal correction and exact registration

Copied the original file without overwriting into the already configured root:

~~~text
/home/zetaris/customer-data/shared/meteo_precipitations_44_2024.csv
~~~

Source and destination SHA-256 were identical:

~~~text
5fbffc154a7b04fbed8c696abbeb6bb2fc32dae8bb8f3d39c9239d8deb36ceaf
~~~

An earlier identical copy under the organisation file-store was retained but
was not used by the successful SQL table. No source file was moved or deleted.

The successful statement, dry-run first, was:

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

Executed through the unchanged getting-started scripts/run_sql.py using -e;
the dry-run used --dry-run, followed by a separately approved execution.
The existing flood_hydro database was reused. Hub'Eau tables/views and Docker
configuration were not modified.

## Actual SQL verification

The read-only preflight returned READY: credential presence checks, datasources
HTTP 200, SELECT 1 and the expected Lightning database listing passed.
Credential values were not displayed.

Before creation, a SELECT on the target returned TABLE_OR_VIEW_NOT_FOUND.
After successful registration, these statements passed:

~~~sql
SELECT * FROM flood_hydro.meteo_precipitations_raw LIMIT 5
~~~

~~~sql
DESCRIBE flood_hydro.meteo_precipitations_raw
~~~

~~~sql
SELECT COUNT(*) AS row_count, COUNT(DISTINCT NUM_POSTE) AS station_count,
       MIN(AAAAMMJJ) AS first_day, MAX(AAAAMMJJ) AS last_day,
       COUNT(RR) AS nonnull_rr
FROM flood_hydro.meteo_precipitations_raw
~~~

Observed schema:

| Column | Actual inferred type |
|---|---|
| NUM_POSTE | int |
| NOM_USUEL | string |
| LAT | double |
| LON | double |
| AAAAMMJJ | int |
| RR | double |
| QRR | int |

Observed coverage: 5490 rows, 15 distinct station codes, first day 20240101,
last day 20241231 and 5490 non-null RR values. The source file contained
5491 physical lines including the header, consistent with the SQL count.
Date bounds and aggregate counts do not prove completeness per station.

Five returned BLAIN rows had dates 20240101..20240105 and RR values
37.6, 19.9, 5.2, 4.0 and 0.6 respectively. No values were invented.

## Catalog and application access

Catalog version: loire-hydro-weather-discovery-2026-10-27-v5.

The catalog/allowlist now includes the exact raw table and its seven columns.
The same restricted read-only run_sql interface handles this table and the
three existing hydrometry views. Units and accumulation semantics for RR,
and the meaning of QRR, remain unconfirmed from source documentation.

The actual HydroSqlExecutor was also executed with the real Zetaris REST
transport and a distinct attempt query ID:

~~~sql
SELECT * FROM flood_hydro.meteo_precipitations_raw
ORDER BY NUM_POSTE ASC, AAAAMMJJ ASC LIMIT 5
~~~

It returned five correctly typed rows under the canonical tool envelope:

- operationId: ee3f3c48-c87a-481f-b3fa-4c4d205e876f.
- attemptId / REST queryId: 927b5666-693b-45b1-8925-980a4de5a9c1.
- evidenceId: 8169b8c3-4baa-4c0d-945d-88b344fd1c02.
- sourceKind: zetaris_rest.
- First row: [44015001, "BLAIN", 47.472833, -1.771667, 20240101, 37.6, 1].

Local full evidence: .cache/meteo-zetaris-tool-verified.json.
This is real SQL/tool evidence, not a newly generated Nemotron answer.

Five actual SQL-returned weather rows were added to the existing captured-data
snapshot for standalone replay. This is a five-row subset, not all 5490 rows.
The snapshot adapter was adjusted to recognize the flood_hydro namespace.

## Targeted tests

~~~bash
python3 -B -m unittest discover -s tests/unit -p 'test_*analysis*.py' -q
~~~

Final observed result: 56 tests in 0.730 seconds, OK.
The initial run failed because the SQLite snapshot adapter attached only
flood_analysis. Adding its flood_hydro namespace fixed that concrete issue.
The tests also cover the separately approved preservation of generated
hydrological text with backend provenance and explicit missing-citation flags.

## Boundaries and remaining work

- Verified precipitation coverage is 2024 only, not 1950-2024.
- Department 44 is the owner-supplied file scope; geographic compatibility with
  a hydrometric station and its catchment must not be assumed.
- This is an imported CSV, not a working Meteo-France API collector.
- Source download URL, redistribution terms, RR units/accumulation interval
  and QRR semantics need their own source confirmation.
- No Python rainfall calculation, correlation or forecast was added.
- No extra view is required for this verified access path.
- The separately approved workflow 1.3 incident increment is still in progress:
  its Python core and definition exist, but its bridge projection and tests
  remain pending. Do not claim its full CLI or retry/human workflow is validated.

## References

- [Project status](../../PROJECT_STATUS.md)
- [Hydrological tool contract](../../architecture/hydrological-analysis.md)
- [Prior hydrological evidence](0016-catalog-aware-hydro-analysis.md)

## History

- 2026-10-27: Recorded the configured-root diagnosis, successful real CSV registration, coverage, catalog/tool access and standalone checks.
