# 0016 - Catalog-aware hydrological analysis

- Date: 2026-10-27.
- Approval evidence: Ok; individual source/test/live operations were explicitly approved.
- Local result: passed 55 standalone checks, two actual-engine checks and the final snapshot CLI.
- Live result: partial integration evidence; all four business attempts terminated as FAILED.
- No hydrological forecast, JUDGE approval or complete delivery acceptance is established.

## Implemented scope

The application orchestrator owns dispatch and World Model state. The Analyzer
supplies the authorized three-view catalog, per-request context, previous results
and deterministic summaries on every inference request. Nemotron chooses reads.
The backend validates the complete restricted SQL grammar and controls volumes.
H-MEM remains deferred; authoritative schemas and permissions are not agent memory.

Source and model implementations are selected independently. Snapshot and live
share run_sql(sql), canonical typed result fields, calculations and orchestration.
Upstream World Model and smoke_test.py were not modified.

## Preconditions and exact commands

Commands ran from /home/info/flood-risk-intelligence in Ubuntu WSL.
The actual-engine profile uses the prepared Linux Node/locked reference setup.
Live used the already verified Windows-loopback Runtime, meterless/auto and the
existing explicit getting-started .env.local. No credential was copied or displayed.

Latest standalone command (also run through unittest's programmatic loader
as the gate before live attempt 4):

~~~bash
python3 -B -W error::ResourceWarning -m unittest discover -s tests/unit -p 'test_*analysis*.py' -q
~~~

Latest gate result: 55 tests, 0.422 seconds, OK. Earlier intermediate runs had
50, 52 and 54 tests as cases were added; they are not additional unique tests.

~~~bash
python3 -B -m unittest discover -s tests/integration -p test_hydro_world_model.py -q
~~~

Two actual-reference checks passed in 10.043 seconds after source-profile,
catalog-context and effective-SQL tracing integration. Later grammar/catalog
changes were covered by standalone checks and the final actual-engine CLI.
These checks cover five nominal tasks and concurrent same-user run isolation.

Final snapshot CLI:

~~~bash
python3 -B -m agent.main --analysis hydro --provider stub --sql-executor stub --world-model memory
~~~

Live CLI used for each separately approved attempt:

~~~bash
python3 -B -m agent.main --analysis hydro --provider nightshift --sql-executor zetaris --world-model memory --transport windows-loopback --nightshift-base-url http://127.0.0.1:8088/v1 --route meterless/auto --zetaris-env-file /home/info/getting-started/.env.local
~~~

The shell evidence wrappers invoked agent.main.main with exactly those CLI
arguments, captured its JSON output and saved separate artifacts under .cache/.
They printed selected fields instead of duplicating the complete World Model
snapshot. These local artifacts are not a durable recovery mechanism or a
published audit service.

## Final snapshot result

~~~json
{
  "status": "PASSED",
  "runId": "a9eadc5e-61e6-44d8-95ee-8ff0b63f74b1",
  "profile": {
    "providerKind": "standalone_stub",
    "sourceKind": "captured_real_snapshot"
  },
  "counts": {
    "inferenceDispatches": 3,
    "toolExecutions": 2
  },
  "catalogVersion": "hubeau-sql-discovery-2026-10-27-v4",
  "catalogDigest": "ca27006eb8af546a7c78d6fafcf84ed7d7bb899c0c100a206b76b2924f96c946",
  "events": 22,
  "nativeEventCount": 23,
  "nativeAuditCount": 23,
  "taskCount": 5,
  "workflowExecuted": false,
  "durableTrace": false,
  "summaries": [
    {
      "evidenceId": "4ad83e1b-6ae8-48be-a249-a215fec3d38a",
      "returnedRows": 1,
      "limitReached": true,
      "series": [],
      "warnings": [
        "Returned rows do not prove full source coverage.",
        "Correlation is not causation; this is not a validated flood forecast.",
        "No complete recent-observation columns in this result."
      ]
    },
    {
      "evidenceId": "1b76f7ed-76d6-4293-b6e9-4bc3b46fe59f",
      "returnedRows": 6,
      "limitReached": false,
      "series": [
        {
          "stationId": "K400001010",
          "variable": "H",
          "unit": "m",
          "returnedPoints": 3,
          "distinctTimes": 3,
          "firstObservationAt": "2026-10-27T17:50:00Z",
          "lastObservationAt": "2026-10-27T18:00:00Z",
          "windowMinutes": 10.0,
          "minimum": -1.46,
          "maximum": -1.46,
          "firstToLastChange": 0.0,
          "qualityLabels": [
            "Non qualifi\u00e9e"
          ],
          "statusLabels": [
            "Brute"
          ],
          "conflictingDuplicates": false
        },
        {
          "stationId": "K400001010",
          "variable": "Q",
          "unit": "m3/s",
          "returnedPoints": 3,
          "distinctTimes": 3,
          "firstObservationAt": "2026-10-27T17:50:00Z",
          "lastObservationAt": "2026-10-27T18:00:00Z",
          "windowMinutes": 10.0,
          "minimum": 50.6,
          "maximum": 50.6,
          "firstToLastChange": 0.0,
          "qualityLabels": [
            "Non qualifi\u00e9e"
          ],
          "statusLabels": [
            "Brute"
          ],
          "conflictingDuplicates": false
        }
      ],
      "warnings": [
        "Returned rows do not prove full source coverage.",
        "Correlation is not causation; this is not a validated flood forecast.",
        "No precipitation series is available in the verified catalog.",
        "No rainfall/discharge lag or predictive coefficient is computed.",
        "History station overlap and time-period compatibility must be checked before comparison.",
        "Water-level datum and station-specific flood thresholds are not established."
      ],
      "excludedInvalidRows": 0
    }
  ]
}
~~~

The replay contains one real Givry station, six real observations and one real
history row. It does not reproduce all 103 reference stations or the exposed
1000-row source sets. The provider output is explicitly scripted, not Nemotron.
Source Unicode labels were repaired after detecting PowerShell transfer damage;
the final replay preserves the actual captured labels.

Full Givry metadata was independently read after report 0015 using:

~~~sql
SELECT * FROM flood_analysis.v_hydro_stations WHERE code_station = 'K400001010' LIMIT 1
~~~

This additional statement passed with one 15-field row. It was run using the
unchanged getting-started SQL runner with --limit 1. The capture is non-atomic:
station and observation rows came from separate SQL statements.

## Actual live attempts

All Runtime responses in the recorded traces reported
nvidia/nemotron-3.5-lightning-30b-a3b for the requested meterless/auto route.
This is response metadata, not an independent serving-model attestation.

### Attempt 1

- Run: ac28f4c1-270a-404c-8f8b-da08a8c8c8ba.
- Outcome: FAILED; SQL_NOT_ALLOWED.
- Runtime completion dispatches: 1.
- SQL executions: 0.
- Native World Model events/audits: 6/6.
- Trace-derived elapsed seconds: 13.737.

The initial policy rejection did not retain its proposal. A separate
one-completion diagnostic captured an authorized station SELECT
without LIMIT, with zero SQL executions. No first-attempt raw SQL
is reconstructed or invented here.

### Attempt 2

- Run: deeb242a-ca56-41c8-80c5-83ef1b8f5235.
- Outcome: FAILED; SQL_NOT_ALLOWED.
- Runtime completion dispatches: 1.
- SQL executions: 0.
- Native World Model events/audits: 7/7.
- Trace-derived elapsed seconds: 6.985.

TOOL_REQUEST_RECEIVED:

~~~sql
SELECT code_station, code_site, libelle_station, libelle_site, libelle_commune, libelle_departement, libelle_cours_eau, en_service, latitude_station, longitude_station, date_ouverture_station, date_fermeture_station
FROM flood_analysis.v_hydro_stations
WHERE code_station = 'K400001010' OR code_site = 'K400001010'
LIMIT 1
~~~

The proposal used multiline layout and OR. It was rejected before
dispatch. Later strict-grammar support and regression tests address
that concrete form without authorizing arbitrary SQL.

### Attempt 3

- Run: 4a6d0210-d430-429c-abbf-8bff110d7353.
- Outcome: FAILED; SQL_NOT_ALLOWED.
- Runtime completion dispatches: 2.
- SQL executions: 1.
- Native World Model events/audits: 14/14.
- Trace-derived elapsed seconds: 16.09.

TOOL_REQUEST_RECEIVED:

~~~sql
SELECT * FROM flood_analysis.v_hydro_stations WHERE code_site = 'K400001010'
~~~

SQL_DISPATCHED:

~~~sql
SELECT * FROM flood_analysis.v_hydro_stations WHERE code_site = 'K400001010' LIMIT 50
~~~

- Returned rows: 0; receipt: 2f5870f0-2c9b-4824-8dca-aee6aae9ac5d.

TOOL_REQUEST_RECEIVED:

~~~sql
SELECT * FROM flood_analysis.v_hydro_stations WHERE libelle_commune LIKE '%Givry%' OR libelle_station LIKE '%Givry%'
~~~

Nemotron queried code_site using a station identifier and received
zero rows. Its subsequent LIKE search was rejected before dispatch.
The catalog was enriched with verified station/site identity and
bounded text search was added with a regression test.

### Attempt 4

- Run: 7eaed872-b90e-45ef-8973-0020f1c1215f.
- Outcome: FAILED; FINAL_RESULT_NOT_REFERENCED.
- Runtime completion dispatches: 3.
- SQL executions: 2.
- Native World Model events/audits: 20/20.
- Trace-derived elapsed seconds: 50.842.

TOOL_REQUEST_RECEIVED:

~~~sql
SELECT * FROM flood_analysis.v_hydro_observations WHERE code_station = 'K400001010' ORDER BY date_obs DESC LIMIT 50
~~~

SQL_DISPATCHED:

~~~sql
SELECT * FROM flood_analysis.v_hydro_observations WHERE code_station = 'K400001010' ORDER BY date_obs DESC LIMIT 50
~~~

- Returned rows: 0; receipt: ab643187-1e3e-40e1-ab34-a51283e29ae7.

TOOL_REQUEST_RECEIVED:

~~~sql
SELECT * FROM flood_analysis.v_hydro_stations WHERE code_station = 'K400001010' LIMIT 1
~~~

SQL_DISPATCHED:

~~~sql
SELECT * FROM flood_analysis.v_hydro_stations WHERE code_station = 'K400001010' LIMIT 1
~~~

- Returned rows: 1; receipt: ba4bb8d1-3b99-4554-9aea-589b4e5c5b06.

The recent-observation SELECT used the correct code_station and
returned zero rows. The station-reference SELECT returned one row.
Both results were returned to Nemotron before its final completion.
That final text failed the exact receipt-citation check; it is not
retained as a successful AnalysisResult. No positive result or
hydrological-data availability is inferred from this attempt.

### Separate diagnostic

~~~json
{
  "diagnosticOnly": true,
  "sqlExecutions": 0,
  "resultCode": "SQL_NOT_ALLOWED",
  "events": [
    {
      "eventType": "INFERENCE_DISPATCHED",
      "payload": {
        "invocationId": "9f5ec87c-b611-4e67-b495-6ebdb06d6c81",
        "requestedRoute": "meterless/auto",
        "providerKind": "nightshift"
      }
    },
    {
      "eventType": "INFERENCE_RESPONSE_RECEIVED",
      "payload": {
        "invocationId": "9f5ec87c-b611-4e67-b495-6ebdb06d6c81",
        "reportedModel": "nvidia/nemotron-3.5-lightning-30b-a3b",
        "verification": "not_established"
      }
    },
    {
      "eventType": "TOOL_REQUEST_RECEIVED",
      "payload": {
        "invocationId": "9f5ec87c-b611-4e67-b495-6ebdb06d6c81",
        "toolCallId": "call-b7303583-9047-4730-9cd9-986bfce1e806",
        "toolName": "run_sql",
        "sql": "SELECT * FROM flood_analysis.v_hydro_stations WHERE code_station = 'K400001010'"
      }
    }
  ]
}
~~~

## Corrections and test limits

The first standalone run had two failed assertions: damaged Unicode source
labels and an invalid expectation that a valid one-column numeric row should
be rejected. The fixture transfer and test were corrected. SQLite in-memory
connections were also closed explicitly after resource warnings.

Later tests cover missing-LIMIT capping, the actual multiline OR proposal,
quoted-value preservation, LIKE, unknown sources/columns, injection rejection,
shared live/snapshot envelopes, strict result types, missing values, duplicate
timestamps, loop budgets, source choice and context on every inference request.

Tests do not establish full SQL-language support, upstream pagination, database
read-only account privileges, forecast quality, restart recovery or a clean
judge installation. The source snapshot's redistribution conditions still
require verification before public publication.

## Current blockers and next required incident policy

- The latest correct Givry read is empty despite the earlier captured rows.
  The reason is unverified: source contents, filtering, paging or a transient
  platform issue require confirmation. An empty result alone proves none of them.
- Missing final-text receipt citations currently fail the Analyzer check.
  This is a protocol/presentation condition, not a JUDGE or scientific verdict.
- Failed generated final text is not currently retained in analysisResult;
  invocation IDs, SQL, row counts, receipts and failed closure remain traced.
- The owner requested a second bounded SQL attempt for transient failures,
  followed by orchestrator suspension and human intervention if unresolved.
  No additional Nemotron call is needed to handle that technical incident.
  This is required next work, not an implemented retry or approval mechanism.
- Empty-result confirmation must remain distinct from HTTP/transport errors.
- Weather, usable historical overlap, the final interface, clean SAMPLE setup,
  video, slides and GitHub publication remain separate delivery work.

## Files and source fingerprints

- agent/hydro_catalog.py: 04142c6ae1abc51c29a5d6c86ed7715b6b0f21ecc0570b98cdf36a3337f1fbd7
- agent/hydro.py: 9b5b690667a09265aa243488f31da4b1c87190a2118462c55f3a4daa30259e77
- agent/analyzer.py: 84a57ab6b14ccd23db4f2772d07956716906c6b6aac1ff26bab884320597395e
- agent/orchestrator.py: dc09a4a80cd377f4927e0c0a5a1715f363e1b6ba9689ebb5e98c0f75b8e18f58
- agent/tools_zetaris.py: 369f4efdad5b5f8f2274a3c96f4261e12c9d2e59664bbec99acec71c59ecfe5d
- agent/main.py: 75c8710e97eb2f298c94451a97580c2154ce695f5105d3a090949a611b76f16e
- bridge/world-model.mts: b533d172f4f5641d05e21b34401be1b01aed1785c86ade368229c9161003f3c7
- tests/unit/test_hydro_analysis.py: 20b38750d30425547d0ff76e865e449f29154bde8b8f139425432f2a9b59e777
- tests/integration/test_hydro_world_model.py: ac7331a960c3f3419c7d4b6c9c9d9da20c8ce6be96f58718cde74db26ec481dc
- data/snapshots/hubeau-givry-2026-10-27.json: c31e9af28ba6d2eb4574042b84145fb5c028bc84dce7b858f8c6c795875f7c3c
- smoke_test.py: 295c5e8e8be4c9f518dddfdceb183bfb956fe88faf95e89227f8378552dea22c

## References

- [Hydrological contract](../../architecture/hydrological-analysis.md)
- [SQL discovery](0015-hubeau-sql-discovery.md)
- [Prior actual-engine baseline](0014-world-model-nominal-application.md)
- [Demand-driven analysis](../../decisions/0011-demand-driven-analysis.md)

## History

- 2026-10-27: Recorded catalog-aware implementation, local passes, all failed live attempts and required human-escalation follow-up.
