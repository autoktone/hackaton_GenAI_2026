# 0015 - Hub'Eau hydrometry SQL discovery

- Date recorded: 2026-10-27.
- Result: three views accessible by actual SQL; application hydro tool integration pending.
- Approval evidence: Ok.
- Access: existing getting-started direct REST runner and private .env.local.
- Resources created, modified or dropped: none.
- Nightshift/Nemotron requests during discovery: none.
- Upstream API calls directly made by Codex: none; Zetaris REST tables may fetch
  their configured public source for SQL execution.

## Source and execution path

Owner-provided hydrometry source: Hub'Eau v2.
Registered REST database flood_hydro was confirmed by SHOW LIGHTNING DATABASES.
The real queryable reference is flood_analysis.v_hydro_stations, plural.
The initially provided singular name did not resolve.

The runtime application path remains Analyzer -> orchestrator request_data ->
SqlExecutor.execute -> ZetarisHttpTransport.post_query ->
POST /sql-editor/sqls/run. The current allowlist and result checks accept
SELECT 1 AS one only, and limit its result to one row. Discovery used the
existing onboarding runner; no application guard was bypassed or removed.

The app transport uses Bearer authentication, configured X-Org-ID, fresh UUID
X-Request-ID and UUID queryId. Credentials were not printed or copied.

DESCRIBE DATASOURCE TABLE does not describe this accessible SchemaStore view
in the tested form. Plain DESCRIBE worked. These observed errors are retained
below rather than interpreted as missing credentials or a need to recreate objects.

## Verified schemas

### flood_analysis.v_hydro_stations

15 columns: code_station string; code_site string; libelle_station string;
libelle_site string; libelle_commune string; libelle_departement string;
libelle_cours_eau string; en_service boolean; latitude_station double;
longitude_station double; date_ouverture_station string;
date_fermeture_station string; influence_locale_station bigint;
commentaire_influence_locale_station string; commentaire_station string.

SQL exposed 103 rows, 103 distinct station codes, 68 site codes and 75 rows
with en_service=true. These counts do not independently establish exhaustive
Hub'Eau or Loire-basin coverage.

### flood_analysis.v_hydro_observations

9 columns: code_station string; code_site string; date_obs string;
grandeur_hydro string; valeur_brute double; valeur_normalisee double;
unite_normalisee string; libelle_qualification_obs string; libelle_statut string.

Owner-reported upstream endpoint:
https://hubeau.eaufrance.fr/api/v2/hydrometrie/observations_tr

Observed aggregate:
- H: 381 rows, 120 distinct station codes, 12 matching the reference.
- Q: 619 rows, 97 distinct station codes, 10 matching the reference.
- Exposed time bounds for both groups: 2026-10-27T17:40:00Z to
  2026-10-27T18:00:00Z.
- Exposed unit labels: H=m, Q=m3/s.

Station counts are per variable; they must not be summed as unique coverage.
Normalization labels and values were observed through the views; the view SQL
and raw upstream unit specification were not independently audited here.

### flood_analysis.v_hydro_history

7 columns: code_station string; code_site string; date_obs_elab string;
grandeur_hydro_elab string; valeur_brute double; debit_m3_s double;
libelle_statut string.

Owner-reported upstream endpoint:
https://hubeau.eaufrance.fr/api/v2/hydrometrie/obs_elab

The exposed QmnJ result has 1000 rows and 3 distinct station codes, with date
bounds 2024-01-01 to 2024-12-31. No code_station matched the supplied reference.
Matching by code_site was not tested.

The date bounds do not establish complete daily coverage, all 103 stations
or the full upstream history. No recent/historical numerical comparison
was performed across unmatched station identities.

## Pagination, time and source limits

Both measurement views exposed 1000 rows in these aggregate queries.
This is a coverage limit to investigate, not proof of complete retrieval
or independently confirmed upstream pagination settings.

The source was queried at different times. A candidate query initially saw
five H and five Q points for Givry; a later selected-series query returned
three points of each variable over a shorter window. These are separate
observations, not a frozen transactional snapshot or an invented interpolation.

The reference includes replaced stations and comments about reconstructed
discharge. Station/site identity, instrumentation and method must be retained.
A matching site code alone would not prove methodological comparability.

## Selected real demonstration candidate

Station K400001010, site K4000010:
La Loire ? Cours-les-Barres - Givry, COURS-LES-BARRES.
The reference marks it en_service=true and exposes influence_locale_station=3.
The meaning of that influence code was not inferred.

Selected-series columns are ordered as the nine observation fields above.

```json
[
  [
    "K400001010",
    "K4000010",
    "2026-10-27T17:50:00Z",
    "H",
    "-1460.0",
    "-1.46",
    "m",
    "Non qualifi?e",
    "Brute"
  ],
  [
    "K400001010",
    "K4000010",
    "2026-10-27T17:50:00Z",
    "Q",
    "50600.0",
    "50.6",
    "m3/s",
    "Non qualifi?e",
    "Brute"
  ],
  [
    "K400001010",
    "K4000010",
    "2026-10-27T17:55:00Z",
    "H",
    "-1460.0",
    "-1.46",
    "m",
    "Non qualifi?e",
    "Brute"
  ],
  [
    "K400001010",
    "K4000010",
    "2026-10-27T17:55:00Z",
    "Q",
    "50600.0",
    "50.6",
    "m3/s",
    "Non qualifi?e",
    "Brute"
  ],
  [
    "K400001010",
    "K4000010",
    "2026-10-27T18:00:00Z",
    "H",
    "-1460.0",
    "-1.46",
    "m",
    "Non qualifi?e",
    "Brute"
  ],
  [
    "K400001010",
    "K4000010",
    "2026-10-27T18:00:00Z",
    "Q",
    "50600.0",
    "50.6",
    "m3/s",
    "Non qualifi?e",
    "Brute"
  ]
]
```

Across this captured 17:50 to 18:00 UTC window:
- H: three points, all -1.46 m; observed end-minus-start change 0 m.
- Q: three points, all 50.6 m3/s; observed end-minus-start change 0 m3/s.
- All returned quality/status labels are Non qualifi?e / Brute.

These are descriptive facts for this sample only. A negative H is retained as
reported; no universal danger threshold or datum interpretation was inferred.
The ten-minute constant sample cannot establish a forecast, causal relation,
rainfall lag, calibrated flood probability or safety decision.

## Exact executed SQL and observed results

Each statement was executed independently through:
python3 -B scripts/run_sql.py -e SQL --limit N.
Explicit SQL LIMIT bounds sample retrieval; aggregate values describe the
rows exposed to the engine, not the client display limit.

### Check 1

```sql
DESCRIBE DATASOURCE TABLE flood_analysis.v_hydro_station
```

Process exit: 1.

```text
     ERROR HTTP 400: {"msg":"`flood_analysis`.`v_hydro_station` does not exist"}
```

### Check 2

```sql
SELECT * FROM flood_analysis.v_hydro_station LIMIT 5
```

Process exit: 1.

```text
     ERROR HTTP 400: {"msg":"[TABLE_OR_VIEW_NOT_FOUND] The table or view `flood_analysis`.`v_hydro_station` cannot be found. Verify the spelling and correctness of the schema and catalog.\nIf you did not qualify the name with a schema, verify the current_schema() output, or qualify the name with the correct schema and catalog.\nTo tolerate the error on drop use DROP VIEW IF EXISTS or DROP TABLE IF EXISTS.; line 1 pos ...
```

### Check 3

```sql
SHOW LIGHTNING DATABASES
```

Process exit: 0.

```text
The accessible database list includes flood_hydro, plus the earlier sample databases.
```

### Check 4

```sql
SELECT * FROM flood_analysis.v_hydro_stations LIMIT 5
```

Process exit: 0.

```text
Five rows returned; source comments mention replaced stations and reconstructed discharge. Full descriptive comments are not duplicated here.
```

### Check 5

```sql
DESCRIBE DATASOURCE TABLE flood_analysis.v_hydro_stations
```

Process exit: 1.

```text
     ERROR HTTP 400: {"msg":"`flood_analysis`.`v_hydro_stations` does not exist"}
```

### Check 6

```sql
DESCRIBE flood_analysis.v_hydro_stations
```

Process exit: 0.

```text
['code_station', 'string', None]
      ['code_site', 'string', None]
      ['libelle_station', 'string', None]
      ['libelle_site', 'string', None]
      ['libelle_commune', 'string', None]
      ['libelle_departement', 'string', None]
      ['libelle_cours_eau', 'string', None]
      ['en_service', 'boolean', None]
      ['latitude_station', 'double', None]
      ['longitude_station', 'double', None]
      ['date_ouverture_station', 'string', None]
      ['date_fermeture_station', 'string', None]
      ['influence_locale_station', 'bigint', None]
      ['commentaire_influence_locale_station', 'string', None]
      ['commentaire_station', 'string', None]
```

### Check 7

```sql
SELECT COUNT(*) AS exposed_rows FROM flood_analysis.v_hydro_stations
```

Process exit: 0.

```text
['103']
```

### Check 8

```sql
SELECT * FROM flood_analysis.v_hydro_observations LIMIT 1
```

Process exit: 0.

```text
['K132181010', 'K1321810', '2026-10-27T17:45:00Z', 'H', '234.0', '0.234', 'm', 'Non qualifi?e', 'Brute']
```

### Check 9

```sql
SELECT * FROM flood_analysis.v_hydro_history LIMIT 1
```

Process exit: 0.

```text
['F128000101', 'F1280001', '2024-01-01', 'QmnJ', '0.0', '0.0', 'Donn?e brute']
```

### Check 10

```sql
DESCRIBE flood_analysis.v_hydro_observations
```

Process exit: 0.

```text
['code_station', 'string', None]
      ['code_site', 'string', None]
      ['date_obs', 'string', None]
      ['grandeur_hydro', 'string', None]
      ['valeur_brute', 'double', None]
      ['valeur_normalisee', 'double', None]
      ['unite_normalisee', 'string', None]
      ['libelle_qualification_obs', 'string', None]
      ['libelle_statut', 'string', None]
```

### Check 11

```sql
DESCRIBE flood_analysis.v_hydro_history
```

Process exit: 0.

```text
['code_station', 'string', None]
      ['code_site', 'string', None]
      ['date_obs_elab', 'string', None]
      ['grandeur_hydro_elab', 'string', None]
      ['valeur_brute', 'double', None]
      ['debit_m3_s', 'double', None]
      ['libelle_statut', 'string', None]
```

### Check 12

```sql
SELECT COUNT(*) AS exposed_rows, COUNT(DISTINCT code_station) AS distinct_stations, COUNT(DISTINCT code_site) AS distinct_sites, SUM(CASE WHEN en_service = true THEN 1 ELSE 0 END) AS active_rows FROM flood_analysis.v_hydro_stations
```

Process exit: 0.

```text
['103', '103', '68', '75']
```

### Check 13

```sql
SELECT o.grandeur_hydro, o.unite_normalisee, COUNT(*) AS exposed_rows, COUNT(DISTINCT o.code_station) AS exposed_stations, COUNT(DISTINCT s.code_station) AS reference_stations, MIN(o.date_obs) AS first_obs, MAX(o.date_obs) AS last_obs FROM flood_analysis.v_hydro_observations o LEFT JOIN (SELECT DISTINCT code_station FROM flood_analysis.v_hydro_stations) s ON o.code_station = s.code_station GROUP BY o.grandeur_hydro, o.unite_normalisee
```

Process exit: 0.

```text
['H', 'm', '381', '120', '12', '2026-10-27T17:40:00Z', '2026-10-27T18:00:00Z']
      ['Q', 'm3/s', '619', '97', '10', '2026-10-27T17:40:00Z', '2026-10-27T18:00:00Z']
```

### Check 14

```sql
SELECT h.grandeur_hydro_elab, COUNT(*) AS exposed_rows, COUNT(DISTINCT h.code_station) AS exposed_stations, COUNT(DISTINCT s.code_station) AS reference_stations, MIN(h.date_obs_elab) AS first_obs, MAX(h.date_obs_elab) AS last_obs FROM flood_analysis.v_hydro_history h LEFT JOIN (SELECT DISTINCT code_station FROM flood_analysis.v_hydro_stations) s ON h.code_station = s.code_station GROUP BY h.grandeur_hydro_elab
```

Process exit: 0.

```text
['QmnJ', '1000', '3', '0', '2024-01-01', '2024-12-31']
```

### Check 15

```sql
SELECT o.code_station, s.libelle_station, o.grandeur_hydro, COUNT(*) AS exposed_rows, MIN(o.date_obs) AS first_obs, MAX(o.date_obs) AS last_obs FROM flood_analysis.v_hydro_observations o JOIN flood_analysis.v_hydro_stations s ON o.code_station = s.code_station GROUP BY o.code_station, s.libelle_station, o.grandeur_hydro ORDER BY exposed_rows DESC LIMIT 5
```

Process exit: 0.

```text
['K400001010', 'La Loire ? Cours-les-Barres - Givry', 'H', '5', '2026-10-27T17:40:00Z', '2026-10-27T18:00:00Z']
      ['K400001010', 'La Loire ? Cours-les-Barres - Givry', 'Q', '5', '2026-10-27T17:40:00Z', '2026-10-27T18:00:00Z']
      ['K170001010', 'La Loire ? Decize', 'H', '4', '2026-10-27T17:40:00Z', '2026-10-27T17:55:00Z']
      ['K190001001', "La Loire ? Imphy - Pont d'Imphy", 'H', '4', '2026-10-27T17:40:00Z', '2026-10-27T17:55:00Z']
      ['K190001001', "La Loire ? Imphy - Pont d'Imphy", 'Q', '4', '2026-10-27T17:40:00Z', '2026-10-27T17:55:00Z']
```

### Check 16

```sql
SELECT code_station, code_site, libelle_station, libelle_commune, en_service, libelle_cours_eau, influence_locale_station, commentaire_influence_locale_station, commentaire_station FROM flood_analysis.v_hydro_stations WHERE code_station = 'K400001010' LIMIT 1
```

Process exit: 0.

```text
['K400001010', 'K4000010', 'La Loire ? Cours-les-Barres - Givry', 'COURS-LES-BARRES', 'true', 'la Loire', '3', None, None]
```

### Check 17

```sql
SELECT code_station, code_site, date_obs, grandeur_hydro, valeur_brute, valeur_normalisee, unite_normalisee, libelle_qualification_obs, libelle_statut FROM flood_analysis.v_hydro_observations WHERE code_station = 'K400001010' ORDER BY date_obs ASC, grandeur_hydro ASC LIMIT 50
```

Process exit: 0.

```text
['K400001010', 'K4000010', '2026-10-27T17:50:00Z', 'H', '-1460.0', '-1.46', 'm', 'Non qualifi?e', 'Brute']
      ['K400001010', 'K4000010', '2026-10-27T17:50:00Z', 'Q', '50600.0', '50.6', 'm3/s', 'Non qualifi?e', 'Brute']
      ['K400001010', 'K4000010', '2026-10-27T17:55:00Z', 'H', '-1460.0', '-1.46', 'm', 'Non qualifi?e', 'Brute']
      ['K400001010', 'K4000010', '2026-10-27T17:55:00Z', 'Q', '50600.0', '50.6', 'm3/s', 'Non qualifi?e', 'Brute']
      ['K400001010', 'K4000010', '2026-10-27T18:00:00Z', 'H', '-1460.0', '-1.46', 'm', 'Non qualifi?e', 'Brute']
      ['K400001010', 'K4000010', '2026-10-27T18:00:00Z', 'Q', '50600.0', '50.6', 'm3/s', 'Non qualifi?e', 'Brute']
```


## Current integration gaps and next increment

The SQL reads are verified. No hydrological result was sent to Nemotron in
this discovery phase. The application still rejects these source queries.

Proposed minimum: preserve run_sql(sql) and the same canonical result envelope
for stub/live executors; introduce an exact, read-only allowlist for the verified
views; normalize typed rows; compute descriptive metrics in Python; feed the
actual result to Nemotron through the existing orchestrator and World Model.

A Givry observational question is possible without claiming forecasting.
Historical comparison remains blocked for the exposed station identities.
The owner is preparing precipitation data; v_meteo_precipitations was not
queried, and its availability/schema/units/cumulative interval are unverified.

Keep measurements, derived values and any later fixtures explicitly labeled.
Do not publish a snapshot as complete or licensing-verified on this evidence.

## References

- [Project status](../../PROJECT_STATUS.md)
- [README](../../../README.md)
- [Validation register](../README.md)
- [Nominal World Model integration](0014-world-model-nominal-application.md)
- [Earlier real SELECT-one path](0009-select-one-live-application.md)

## Report history

| Date | Change |
|---|---|
| 2026-10-27 | Recorded real Hub'Eau view reads, actual schemas, coverage/matching limits, discovery errors and the captured Givry series; Nemotron integration remains pending. |
