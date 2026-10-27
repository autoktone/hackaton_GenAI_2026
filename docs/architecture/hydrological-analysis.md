# Catalog-aware hydrological analysis

## Responsibilities

The application orchestrator owns qualification, scoped data dispatch, run/task/
attempt identities, termination and operational trace references. The Analyzer
owns a bounded inner model/tool loop. Nightshift remains a provider transport,
not a second global workflow engine.

Each hydrological inference request includes the initial question, an authorized
source catalog, per-request context, tool definitions, limits, prior tool results
and any application-computed summaries. Nemotron chooses useful reads across all
four admitted sources; it is not restricted to a preselected Givry query pair.

The application validates each request again before dispatching it. Model output
and source text cannot grant permissions or alter the global workflow.

## Source catalog

The catalog in agent/hydro_catalog.py contains the verified columns/types for:

- flood_analysis.v_hydro_stations
- flood_analysis.v_hydro_observations
- flood_analysis.v_hydro_history
- flood_hydro.meteo_precipitations_raw

It also describes units, observed coverage, quality limitations, unverified
historical matching, verified station/site identities, example reads and the
unavailable precipitation source. Coverage is an
inspection result dated 2026-10-27, not an automatically refreshed guarantee.

The catalog version and SHA-256 digest are associated with the execution context
and Analyzer result. Individual results retain receipt, operation and source-kind
identities. The current catalog is a versioned application configuration; it is
not a general live schema-discovery or authorization service.

Future H-MEM could retain source descriptions and lessons from previous analyses,
with provenance and validity conditions. It must not replace authoritative current
schemas, collection metadata, permissions or business data. No H-MEM integration
is implemented.

## Tool contract and SQL boundary

run_sql keeps one argument, sql, in both live and snapshot profiles. Its canonical
result fields are columns, rows, rowCount, truncated, sourceKind, operationId and
evidenceId. Rows are typed from the admitted projection, not guessed from values.

The backend accepts a deliberately limited SQL grammar:

- One SELECT from one explicitly authorized view.
- Known columns or *, or COUNT/MIN/MAX/AVG projections with optional aliases.
- Simple column comparisons, LIKE and IS NULL, combined with AND or OR.
- Optional ORDER BY known columns, and LIMIT 1..50.
- Optional OFFSET 0..100000 only with an explicit LIMIT.
- If LIMIT is omitted, full grammar validation precedes addition of LIMIT 50.
- Layout whitespace is normalized outside string literals; quoted values remain intact.
- No writes, joins, CTEs, subqueries, comments, semicolons, GROUP BY, unlisted
  functions, or parenthesized Boolean expressions.
- SQL is at most 480 ASCII bytes, including any added row cap.

This is a restricted grammar, not a general SQL parser. Supporting additional
syntax or a new view requires reviewed policy and tests. A blacklist alone does
not authorize a statement. Least-privilege database credentials remain an
independent deployment control; no grants or account changes are performed here.

TOOL_REQUEST_RECEIVED records a bounded proposal before policy rejection.
DATA_REQUEST_ACCEPTED links it to a child task and operation.
SQL_DISPATCHED records the effective SQL, including backend normalization.
DATA_OPERATION_COMPLETED links its receipt and row count.

Reaching the query LIMIT conservatively sets truncated=true; it does not prove
additional rows exist. Conversely, fewer rows cannot prove a paginated upstream
source was fully retrieved.

## Budgets and failure behavior

Workflow 1.3 permits at most two logical SQL reads, two physical attempts per
read, three Runtime completion dispatches and 180 seconds in the Analyzer loop.
Only admitted read-only SQL transient failures are retried by the application;
inference and World Model mutations are not retried under this policy. It accepts
one structured tool call at a time and rejects repeated tool IDs or identical
queries within the run. These limits may produce a controlled failure rather
than a complete analysis.

REST uses a 15-second client timeout, a 64-KiB response cap, no redirects, no
proxy discovery and no automatic retry. Client timeout does not prove database
query cancellation. Model transport uses the remaining analysis budget; Runtime
lanes can perform multiple underlying model operations per completion.

No automatic fallback to a stub follows a live failure. No JUDGE verdict is
required for generation. Receipt citation establishes protocol linkage only;
domainValidated=false and runtimeJudge=not_established remain explicit.
The hydro Analyzer retains a nonempty generated response and attaches backend
provenance. It flags missing exact tool-receipt citations rather than discarding
the response. toolResultReferenced records that condition, provenanceAttached
records the backend evidence, and domainValidated remains false. Prior report
0016 preserves the earlier stricter check; no new live answer was reclassified.

## Deterministic application context

Python summaries use only returned recent observations with valid units, finite
values and timezone-aware timestamps. They report station, variable, unit, point
count, bounds, min/max, first-to-last change, quality/status labels and anomalies.
Missing or invalid measurements are excluded and counted, not replaced by zero.
Conflicting duplicate timestamps suppress the first-to-last trend.

No precipitation correlation, rainfall-response lag, causal inference or validated
forecast is computed from the short constant Givry sample. A negative water level
does not establish a universal flood condition; the local datum and thresholds
are not established.

## Explicit dependency profiles

Live: Nightshift inference plus direct Zetaris REST, with private server-side
settings and an explicitly configured Meterless route. The route is not a
hardcoded NVIDIA model ID; the response's reported serving model is separate
evidence.

Snapshot: data/snapshots/hubeau-givry-2026-10-27.json replays one real station,
six real hydrometric observations, one history row and five weather rows captured
through separate SQL reads.
It is partial and not transactionally captured. A standard-library in-memory
SQLite adapter implements only admitted reads against these rows. It is not a
new persistent business database or evidence of live Zetaris.

The standalone provider scripts two tool requests and labeled output. It is
not generated Nemotron analysis. Source and inference implementations are
selected independently and use the same Analyzer/orchestrator/tool contracts.

World Model: --world-model memory invokes the unchanged official TypeScript
reference through the application bridge, with per-run state and catalog identity.
The application remains memory-only. Full workflow-policy execution, crash
recovery, durable audit and restart/resume are not claimed.

## Reproduction in the prepared environment

From the project root, no live credentials are needed for:

```bash
python3 -B -m agent.main --analysis hydro --provider stub --sql-executor stub --world-model memory
```

This command requires Python with sqlite3, Linux Node and the already prepared
locked World Model bridge dependencies. Clean-install bootstrap remains unverified.

Live uses explicit configuration, and may consume provider credits:

```bash
python3 -B -m agent.main --analysis hydro --provider nightshift --sql-executor zetaris --world-model memory --transport windows-loopback --nightshift-base-url http://127.0.0.1:8088/v1 --route meterless/auto --zetaris-env-file /home/info/getting-started/.env.local
```

The URL is the verified Windows Runtime endpoint for this environment, not a
portable judge default. It requires the matching private Windows token file,
an active route and reachable configured Zetaris REST. The getting-started
.env.local path is an explicit local integration choice, not a shipped credential.

## Latest executed evidence

[Report 0018](../validation/reports/0018-workflow-13-and-live-weather-analysis.md)
records the completed 1.3 subset, 103 distinct final targeted passes and a real
weather query through Nightshift/Nemotron, Zetaris and the actual World Model.
The generated answer contains a sample-versus-source coverage error, explicitly
retained in the report. Backend provenance is not factual/scientific validation.

## Evidence and remaining work

See [report 0015](../validation/reports/0015-hubeau-sql-discovery.md) for discovery
and [report 0016](../validation/reports/0016-catalog-aware-hydro-analysis.md) for
executed application checks, initial failures and live outcomes.

Weather qualification, compatible historical comparison, clean judging setup,
final presentation and delivery artifacts remain separate work. Full freshness/
reuse policy, concurrent collection deduplication and temporal availability checks
are not established by this bounded read path. Snapshot replay is not a leakage-
controlled historical forecast backtest.

## Weather scope

The 2024 CSV is catalog/raw SQL only: seven actual fields, 5490 source rows,
15 station codes and date bounds 20240101..20241231. The snapshot keeps only
five BLAIN rows. No Python rainfall analysis is added. RR units/accumulation
and QRR meaning remain unconfirmed. See
[report 0017](../validation/reports/0017-meteo-csv-zetaris-import.md).

## Next incident-handling requirement

The owner requires a bounded second SQL attempt for transient technical failures,
then application-orchestrator suspension and human intervention if unresolved.
No extra Nemotron call is required to manage that infrastructure incident.
A human-authorized partial continuation may later communicate usable-data limits.
The bounded policy and actual-engine projection passed in report 0018.
WAITING_HUMAN prevents new dispatch but does not provide durable resume.
Empty reads are distinct from transport failures and must not be silently
replaced with snapshot data.

- 2026-10-27: Recorded verified 2024 weather CSV access and catalog scope without Python precipitation analysis; kept workflow 1.3 in progress.

- 2026-10-27: Recorded completed workflow 1.3 checks and the real weather inference with explicit generation, coverage and durability limits.
