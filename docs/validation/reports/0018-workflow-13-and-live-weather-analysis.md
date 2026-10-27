# 0018 - Workflow 1.3 reliability and live catalog-aware weather round trip

- Date: 2026-10-27.
- Approval evidence: Ok; owner-approved incident increment and separately approved real weather inference.
- Result: 103 distinct targeted checks passed in their final recorded runs, local CLI passed, real weather round trip passed.
- Domain validation: false. Runtime JUDGE verification: not established.

## Implementation

Added workflow 1.3.0 without rewriting 1.1.0 or 1.2.0. The hydrological CLI
selects 1.3.0; legacy state clients and SELECT-one retain 1.2.0 by default.
The application bridge still imports the unchanged official Meterless reference.

The orchestrator admits at most two physical attempts per logical SQL read.
Retryable codes are ZETARIS_TRANSIENT_HTTP_ERROR and ZETARIS_OUTCOME_UNKNOWN.
Backoff is 0.25 seconds within the remaining analysis budget. The exception
for an uncertain outcome is limited to admitted side-effect-free SELECTs.
It does not establish cancellation, exactly-once effects or write recovery.

Task and operation identities remain stable; attempt identities are distinct.
The live REST queryId is the attempt ID. Attempt history, retry intent and
result receipt are recorded through the actual engine.

Persistent or non-retryable dispatched SQL failures return WAITING_HUMAN with
run/user/task/operation/attempt context. No additional model call manages that
incident. The projection rejects new dispatch after suspension. Empty results
are not automatically retried. Durable resume and interactive approval UI
remain unimplemented; the operator may explicitly start another run.

The Analyzer now retains generated text with backend provenance when exact
receipt citations are incomplete. toolResultReferenced records the citation
condition; provenanceAttached does not imply factual or scientific correctness.
The original SELECT-one receipt condition remains unchanged.

No Python rainfall analysis was added. Weather remains catalog/raw SQL access.

## Executed targeted checks

| Suite | Final result | Scope |
|---|---|---|
| Existing application and execution-state units | 66 passed, 1.478 s | SELECT-one, hydro/weather contracts and state adapter |
| New incident units | 13 passed, 0.552 s | Recovery, exhausted/nonretryable failures, time, IDs, no inference retry, provenance |
| Existing actual-engine bridge | 18 passed, 97.316 s | E1 and previous application boundary compatibility |
| Existing actual-engine hydro | 2 passed, 16.444 s | Scoped tasks and overlapping same-user runs |
| New actual-engine incident checks, isolated final run | 4 passed, 15.604 s | Two recoveries, human wait, uncertain read, legacy-policy refusal |

These sum to 103 distinct checks; repeated runs are not counted as new tests.

Commands, executed from the project root:

~~~bash
python3 -B -m unittest discover -s tests/unit -p 'test_*analysis*.py' -q
python3 -B -m unittest discover -s tests/unit -p test_execution_state.py -q
python3 -B -m unittest discover -s tests/unit -p test_incident_handling.py -v
python3 -B -m unittest discover -s tests/integration -p test_world_model_bridge.py -q
python3 -B -m unittest discover -s tests/integration -p test_hydro_world_model.py -q
python3 -B -m unittest discover -s tests/integration -p test_incident_world_model.py -v
~~~

The first two unit patterns were run together through unittest's programmatic
TestSuite, yielding 66. The final four native checks were run through its
programmatic loader before the gated local CLI. All tests used explicit
dependency substitutes or the local actual engine; no live service was called
by those test suites. The original smoke was neither imported nor modified.

### Initial native anomaly

The initial four-scenario native run had one WORLD_MODEL_OUTCOME_UNKNOWN
failure in the two-recovery case, with the other three checks passing.
The failed run was not retroactively marked successful. An isolated diagnostic
started a new run, passed with 29 matching events/audits and valid revisions,
then the isolated complete four-check suite passed. No blind mutation retry
or timeout increase was introduced. The original anomaly's cause remains
unestablished and is a prototype limitation, not a proven resolved issue.

Diagnostic metadata: maximum response was below 15 KiB; startup exchange was
4.458 seconds and subsequent exchanges were below 0.1 seconds in that run.
Local evidence: .cache/incident-native-debug.json.

## Final local CLI

~~~bash
python3 -B -m agent.main --analysis hydro --provider stub --sql-executor stub --world-model memory
~~~

~~~json
{
  "status": "PASSED",
  "workflowVersion": "1.3.0",
  "profile": {
    "providerKind": "standalone_stub",
    "sourceKind": "captured_real_snapshot"
  },
  "counts": {
    "inferenceDispatches": 3,
    "toolExecutions": 2,
    "sqlAttempts": 2
  },
  "nativeEventCount": 23,
  "nativeAuditCount": 23,
  "runStatus": "SUCCEEDED",
  "durableTrace": false,
  "workflowExecuted": false
}
~~~

This is captured real data with scripted inference and the actual memory
engine. It is not a new generated analysis. Clean-setup judging remains pending.

## Real weather question and exact CLI

The evidence wrapper invoked agent.main.main with these arguments and saved
its complete output under .cache/meteo-agent-live-result.json. This command
is a reproduction record, not authorization for another paid live run.

~~~bash
python3 -B -m agent.main --analysis hydro --provider nightshift --sql-executor zetaris --world-model memory --transport windows-loopback --nightshift-base-url http://127.0.0.1:8088/v1 --route meterless/auto --zetaris-env-file /home/info/getting-started/.env.local --question "For department 44, retrieve five precipitation records from the verified 2024 CSV in Zetaris. Identify the station and dates, report the raw RR and QRR values, and explain coverage and unit uncertainties. Do not forecast flood risk."
~~~

Observed live path: application orchestrator -> Analyzer -> Nightshift ->
Nemotron structured run_sql -> orchestrator-controlled real Zetaris REST ->
typed result -> Nemotron -> structured result -> application report task.
Actual operational events/tasks were recorded in the official engine.

~~~json
{
  "status": "PASSED",
  "runId": "e0f0e7c7-b7d2-4270-a030-6ebf26e35cee",
  "workflowVersion": "1.3.0",
  "profile": {
    "providerKind": "nightshift",
    "sourceKind": "zetaris_rest"
  },
  "counts": {
    "inferenceDispatches": 2,
    "toolExecutions": 1,
    "sqlAttempts": 1
  },
  "nativeEventCount": 16,
  "nativeAuditCount": 16,
  "traceElapsedSeconds": 42.532,
  "requestedRoute": "meterless/auto",
  "reportedModels": [
    "nvidia/nemotron-3.5-lightning-30b-a3b",
    "nvidia/nemotron-3.5-lightning-30b-a3b"
  ],
  "toolCalls": [
    {
      "toolName": "run_sql",
      "toolCallId": "call-345a24e2-0c18-4ab1-97d9-7c5962fe0b37",
      "sql": "SELECT * FROM flood_hydro.meteo_precipitations_raw LIMIT 5",
      "operationId": "5dc66a9d-fbab-44a1-842b-b4c5a62f71d3",
      "evidenceId": "efced179-30f6-4189-a9d5-6cc000e3bd3c"
    }
  ],
  "datasets": [
    {
      "columns": [
        "NUM_POSTE",
        "NOM_USUEL",
        "LAT",
        "LON",
        "AAAAMMJJ",
        "RR",
        "QRR"
      ],
      "rows": [
        [
          44015001,
          "BLAIN",
          47.472833,
          -1.771667,
          20240101,
          37.6,
          1
        ],
        [
          44015001,
          "BLAIN",
          47.472833,
          -1.771667,
          20240102,
          19.9,
          1
        ],
        [
          44015001,
          "BLAIN",
          47.472833,
          -1.771667,
          20240103,
          5.2,
          1
        ],
        [
          44015001,
          "BLAIN",
          47.472833,
          -1.771667,
          20240104,
          4.0,
          1
        ],
        [
          44015001,
          "BLAIN",
          47.472833,
          -1.771667,
          20240105,
          0.6,
          1
        ]
      ],
      "rowCount": 5,
      "truncated": true,
      "sourceKind": "zetaris_rest",
      "operationId": "5dc66a9d-fbab-44a1-842b-b4c5a62f71d3",
      "evidenceId": "efced179-30f6-4189-a9d5-6cc000e3bd3c"
    }
  ],
  "validation": {
    "toolResultReferenced": true,
    "provenanceAttached": true,
    "domainValidated": false,
    "runtimeJudge": "not_established"
  }
}
~~~

The Runtime reported nvidia/nemotron-3.5-lightning-30b-a3b on both responses.
That is response metadata, not an independent model-serving attestation.
The route remained meterless/auto; no NVIDIA model ID was hardcoded.

### Generated answer, retained verbatim

**Five precipitation records from the verified 2024 CSV (department 44)**  

| # | Station (NUM_POSTE) | Station name (NOM_USUEL) | Date (AAAAMMJJ) | Raw RR (mm * ?) | QRR (source flag) |
|---|----------------------|--------------------------|-----------------|----------------|-------------------|
| 1 | 44015001 | BLAIN | 20240101 | 37.6 | 1 |
| 2 | 44015001 | BLAIN | 20240102 | 19.9 | 1 |
| 3 | 44015001 | BLAIN | 20240103 | 5.2  | 1 |
| 4 | 44015001 | BLAIN | 20240104 | 4.0  | 1 |
| 5 | 44015001 | BLAIN | 20240105 | 0.6  | 1 |

*All five rows were returned by the authorized Zetaris view* `flood_hydro.meteo_precipitations_raw` **(evidenceId: `efced179-30f6-4189-a9d5-6cc000e3bd3c`)**.  

### What the columns mean (per the catalog semantics)

| Column | Description (as documented) | Uncertainty / Caveat |
|--------|-----------------------------|----------------------|
| **NUM_POSTE** | Weather‑station code assigned by the data owner. | The code alone does not guarantee the station lies inside department 44; the catalog only notes “department 44, according to the owner‑supplied file scope”. |
| **AAAAMMJJ** | Integer date in `YYYYMMDD` format. | No explicit calendar‑day granularity guarantee; the source is a static CSV, not a live API. |
| **RR** | Raw precipitation value. The catalog notes “Units and accumulation‑window semantics require source documentation confirmation.” | The numeric value is reported without a guaranteed unit (most likely millimetres, but this has not been verified for this file). |
| **QRR** | Uninterpreted source flag (integer). The catalog states “QRR is an uninterpreted source flag.” | No defined meaning; it should not be used as a quality indicator without the original documentation. |

### Coverage & representativeness

* The verified 2024 CSV contains **15 stations** for department 44 (`verifiedStationCount: 15`).  
* The query returned only the first five rows of the view, all from **station 44015001 (BLAIN)**. Because the view is not ordered by station, these rows do **not** prove that the other 14 stations are represented, nor that the five rows span the full temporal range of the department.  
* **Temporal coverage**: the CSV spans `20240101` → `20241231`, but the five records shown are only the first five calendar days of the year.  
* **Spatial coverage**: without a department column in the view, we cannot confirm that BLAIN (code 44015001) is representative of the whole department; it may be just one of the 15 verified stations.

### Unit & flag uncertainties (re‑stated)

* **RR** – raw precipitation value; unit not explicitly confirmed. Treat as “mm” only if the original source documentation is consulted; otherwise the value is unit‑ambiguous.  
* **QRR** – an opaque flag; no defined interpretation in the catalog. Do not use it to infer quality or accumulation window.

### Bottom line

- The five records above are the only data presently exposed through the authorized Zetaris view for the 2024 verification period.  
- They illustrate the format of the raw precipitation CSV but **do not** constitute a complete or validated dataset for department 44.  
- Any further analysis (e.g., aggregation, trend detection, flood‑risk assessment) must acknowledge these coverage gaps and the unresolved unit/flag semantics.  

*No forecast or causal claim about flood risk is made or implied.*

### Review of the generated answer

The five values and matching evidence receipt agree with the returned rows.
However, the generated final section incorrectly suggests that these five
rows are the only exposed data. LIMIT 5 bounds this query; the separately
verified table has 5490 rows and 15 stations. It also calls the raw table a
view and speculates about mm in a heading despite unverified source units.
These statements were not silently edited or treated as validated facts.
Backend source metadata and report 0017 remain the authoritative observations.
domainValidated=false and runtimeJudge=not_established remain explicit.

No flood forecast, causal finding or rainfall/discharge correlation was
produced or validated. The request exercised real dynamic tool calling,
not a prewritten application answer.

## Remaining delivery work

- A simple final interface and clean one-command judging setup.
- Slides, video capture and GitHub publication.
- Source confirmation for precipitation units, accumulation and quality flags.
- Compatible hydrometric periods/stations before claiming a joined analysis.
- Durable recovery, production authorization and full JSON-policy execution
  remain outside this verified memory-only increment.

## Source fingerprints

- agent/hydro.py: 6f97500f30ead0765b5ba894868cbda39f41feef647b787b25100bd111c39d2a
- agent/hydro_catalog.py: f452c2bbd31bb9d44c30f24f7473cba6f812fe3cf8ae3bb67efccc08903897c3
- agent/orchestrator.py: 2bca0f9e8e0e6c15c491de3bc69c0e61334f24a8ed8166342836b1e693159e9e
- agent/tools_zetaris.py: 74ae699d2cd311e18b30a31274f8faee060a5f62f38c30e4bb293d29f43b59c9
- agent/execution_state.py: bb5dcc93dce1a37121c40a75b6a77bd63eebb941d21be0720d0653375a166082
- agent/main.py: 1f354d36bee748210028c38491396d90779e5e7d9ef427f5edcb9a143e0ad684
- bridge/world-model.mts: af8b82f2ae3f36400ee9ff2bff3ed858ca966bc9425df6ca7698617b45563bc9
- workflows/flood-analysis/1.3.0.json: f8c8f1a5e28f4ed907de12dcc73268cc19b92d6599908d34d145509e9190922f
- tests/unit/test_incident_handling.py: 6516b53e402256ac1666b44917fa5a3b01fe6c36bd84ef66db647c8733c0f4bc
- tests/integration/test_incident_world_model.py: 967475151403dbdf2c0c3d51b96e84f24011b2ccca37d192dd15ea0f08b5dbeb

## References

- [Bounded retry decision](../../decisions/0012-bounded-sql-retry-and-human-intervention.md)
- [CSV registration evidence](0017-meteo-csv-zetaris-import.md)
- [Prior hydro attempts](0016-catalog-aware-hydro-analysis.md)

## History

- 2026-10-27: Recorded scoped retry/human behavior, 103 final targeted passes, the initial native anomaly, local CLI and successful real weather inference.
