# Project status

Last updated: 2026-10-28.
Documentary baseline V1: not recorded as approved in the inspected material.
Git reference: not collected during this inspection.

## Current objective

Deliver a traceable Loire hydrological-analysis prototype with real observations
accessed through Zetaris and a useful Nemotron-backed analysis through Nightshift.
The prototype is exploratory, not an official flood-warning service or a
scientifically validated forecasting or safety-decision system.

This document is the lightweight session handover. Decisions remain in the
[decision register](decisions/README.md); test evidence remains in the
[validation register](validation/README.md). Do not duplicate their histories.

## Release verification checkpoint

The credential-free portable SAMPLE and its 15 targeted tests passed from a
clean local Git clone. Optional official World Model installation and SAMPLE
execution also passed in a short-path clone with 16 native events.
See [release report 0019](validation/reports/0019-release-readiness.md).
The final post-packaging rerun also passed all 15 tests and the isolated
manual-extractor safeguards; runtime code and captured measurement rows were unchanged.

The interface and portable command are implemented and tested; earlier
checkpoint statements that mark them pending are historical. Public GitHub
publication, final owner review and video submission remain owner actions.
No new LIVE platform call was made; report 0018 retains that evidence.
Data licenses/attribution and optional raw-weather restoration are recorded
in [data sources](data-sources.md). The raw archive is excluded, not deleted.
Keep optional-engine checkout paths short to avoid tsx IPC socket path limits.

## Analysis result presentation checkpoint

The local interface now presents **Analysis result** immediately after the
application control/agent-loop panel and before returned data. It shows the
run question, final response, execution outcome and a separate
**Scientific interpretation: NOT VALIDATED** badge. SAMPLE responses explicitly
state that they are scripted and involve no live Nemotron inference.
Incidents without a conclusion explain the stop or required human intervention;
starting a new run clears the previous conclusion.

Validation on 2026-10-27: all 15 targeted demonstration tests passed using
python3 -S -B -m unittest discover -s tests/unit -p test_demo.py -v
(3.872 seconds reported by unittest). Additional Node VM checks passed for
JavaScript syntax, SAMPLE/LIVE disclosure, human intervention, failure, reset,
network interruption and escaped response content. Calculated contrast ratios
for the new text/status pairs range from 5.12:1 to 13.14:1.
These are targeted rendering/state checks, not automated browser screenshots
or scientific validation. No orchestrator or integration code changed.
Packaging/clean-checkout verification remains a separate delivery task.

## Current verified workflow 1.3 checkpoint

[Report 0018](validation/reports/0018-workflow-13-and-live-weather-analysis.md)
records 103 distinct final targeted passes, the current local SAMPLE CLI and
the successful real weather round trip: two Nightshift completions, one
Zetaris SELECT, five rows and 16 matching native events/audits.
The reported model was Nemotron Lightning; requested route was meterless/auto.
This is generated, scientifically unverified interpretation with linked data.

The Python core, pinned 1.3 definition and bridge projection are now connected.
Tests cover a recovered first error, persistent failure to WAITING_HUMAN,
attempt identity, rejection of new dispatch while waiting and preserved legacy
profiles. There is no additional inference to manage SQL infrastructure failure.
Durable resume and production approval/authentication remain deferred.

An initial unknown native acknowledgement was not reproduced by an isolated
diagnostic or the isolated four-case suite. Its cause remains unestablished;
the original failure is not reclassified.

Next proposed delivery work, requiring owner validation: a small local judging
interface and portable credential-free sample command, then video capture and
publication. Keep generated text, actual rows, source coverage and trace visible.

## Weather import checkpoint

[Report 0017](validation/reports/0017-meteo-csv-zetaris-import.md) confirms
successful actual SQL registration and application-tool access for
flood_hydro.meteo_precipitations_raw: 5490 rows, 15 station codes, 2024 only.
The catalog/SQL allowlist includes its verified seven fields. A five-row real
weather subset is available in the standalone snapshot; 56 targeted tests pass.
No Python precipitation analysis or new weather inference was performed.

The configured SQL root is /home/zetaris/customer-data/shared. NDP's virtual
/file-store uses a separate organisation directory. Docker settings and the
Hub Eau resources were not changed.

The approved 1.3 incident increment was subsequently completed and tested in
report 0018, including a separately approved real weather inference. CSV-only
checks in report 0017 remain distinct from this later application evidence.

## Catalog-aware hydro checkpoint

Report [0016](validation/reports/0016-catalog-aware-hydro-analysis.md) records
55 passing standalone checks, two passing actual-engine checks and the final
captured-data CLI. The final SAMPLE run used the current catalog, five completed
tasks and 23 native events/audit entries; inference was explicitly scripted.

The latest live attempt made three Nightshift calls and two Zetaris SELECTs.
The correct recent-observation query returned zero Givry rows; the station
query returned one row. The generated final answer failed receipt citation.
This is partial live-chain evidence, not completed business acceptance.

Next required work from the owner: one bounded retry of transient SQL failures,
then application-orchestrator suspension and human intervention. No extra
Nemotron call is needed for that infrastructure incident. Empty-result
confirmation is a separate check; the current retry/approval mechanism is
not implemented or tested. Confirm source coverage before further live claims.

## Observed implementation and evidence

| Component | Current evidence | Remaining work |
|---|---|---|
| Application entry point | SELECT-one and catalog-aware hydro CLI tested; report 0016 | Final interface and clean judging setup |
| Model integration | Catalog/context-aware bounded loop implemented; latest real final answer failed receipt citation | Resolve final-result handling without claiming scientific or JUDGE validation |
| Application Zetaris integration | Admitted hydro SELECTs executed by the application and returned to Nemotron | Latest correct Givry read empty; confirm coverage and add required retry/human handling |
| World Model | Nominal application events/tasks and simultaneous-run isolation passed against the official reference; report 0014 | Durability, restart and advanced incident policies remain deferred |
| Workflow | Nominal orchestration/projection bound to 1.2.0 implemented; E1 remains pinned to 1.1.0 | Full JSON-policy interpretation and hydrological scenarios remain pending |
| Nightshift connectivity | Real two-call Nemotron tool round trip through the application passed; report 0009 | No JUDGE or hydrological validity claim |
| Weather and hydrometry sources | Three Hub Eau views plus 2024 weather CSV SQL-accessible; reports 0015/0017 | Historical overlap/pagination and weather units/source semantics remain open |
| Normalization, calculations and final interface | Typed rows and deterministic H/Q summaries tested against captured observations | Weather/lag analysis unsupported; final user interface pending |
| Complete credential-free SAMPLE | Prepared-environment CLI replay passes with scripted inference and real World Model | Clean setup, final presentation and delivery acceptance pending |

Prior evidence is recorded in [AGENTS.md](../AGENTS.md) and validation reports
[0004](validation/reports/0004-world-model-reference-execution.md),
[0005](validation/reports/0005-python-world-model-memory-bridge.md) and
[0006](validation/reports/0006-nightshift-live-api-smoke.md).
The earlier World Model tests and text-smoke calls were not rerun. A separate
structured-tool probe passed in Windows with a selected stub; see
[report 0007](validation/reports/0007-nightshift-structured-tool-round-trip.md).
Neither provider probe is a completed Analyzer application integration.

The SELECT-one application components subsequently passed 27 standalone
checks; see [report 0008](validation/reports/0008-select-one-application-standalone.md).
This probe explicitly does not execute World Model or workflow 1.2.0;
its trace is in memory. A subsequent real application round trip passed; see
[report 0009](validation/reports/0009-select-one-live-application.md).

Reports 0010 to 0012 describe the former adapted smoke and its redirect
diagnostic. The original guide script was subsequently restored with
formatting-only corrections and independently passed all three checks;
see [report 0013](validation/reports/0013-original-guide-smoke-live.md).
The process exited 0 and its source hash was unchanged. This is setup
evidence, not the full application or scientific validation.

The nominal application/official-engine integration passed 64 targeted checks
and the actual CLI; see
[report 0014](validation/reports/0014-world-model-nominal-application.md).
It is memory-only with stub inference/SQL, not a full hydrological workflow.

## Approved delivery cut

The owner approved a reduced scope for the seven-hour delivery window:
one useful bounded hydrological question, one coherent zone/period, real
Zetaris and Nightshift evidence, actual World Model, reproducible SAMPLE,
minimal restitution and submission artifacts.

Advanced crash recovery, full backtesting, production identity, public gateway,
JUDGE improvements and additional engines are deferred for this delivery.
Their earlier designs remain preserved, not silently implemented or revoked.
Use small approved code/test/documentation batches and do not repeat unrelated
platform smoke or upstream conformance checks.

## Required architecture

The application orchestrator owns the global workflow: qualification,
planning, authorized dispatch, run isolation, incidents and termination.
The Analyzer orchestrates its bounded internal Nemotron analysis loop.
The provider client remains a transport component.

The orchestrator invokes the Analyzer with the question, authorized source
catalog, geographical/time scope, context and limits. It does not require
Weather/Hydro collection to finish before analysis starts.

When Nemotron requests data, the Analyzer forwards a structured request to
the application orchestrator. The Planner evaluates requested coverage,
freshness, quality, temporal admissibility and reusable data. The orchestrator
controls any necessary Zetaris read or collection, then returns the result
through the Analyzer to Nemotron.

The orchestrator must service these requests while analysis is active, without
waiting for its final result. Data operations are activated on demand, not as
mandatory pre-analysis stages. Valid existing data can avoid a new collection.

Nemotron cannot rewrite the global workflow, grant authorization or dispatch
collectors directly. The Tracer records evidence throughout the workflow.
World Model represents supported state; it is not the scheduler.

Results must distinguish generated interpretation, observed measurements,
computed indicators, provenance, uncertainty, errors and validation status.
Requested routes and reported serving models are different evidence.
Lane outputs or verification outcomes are claimed only when observed.

[Decision 0011](decisions/0011-demand-driven-analysis.md) records this accepted
evolution. Its detailed contracts, final workflow and execution remain pending.

## Immediate sequence and dependencies

1. The Windows structured-tool stub round trip passed; report 0007 records
   the command and result. It did not run Zetaris or application components.
2. The minimal client, shared SQL interface, application orchestrator/Analyzer
   and CLI are implemented. Report 0008 records 27 passing standalone tests.
3. Report 0009 passed the real SELECT-one provider/SQL path. Report 0014
   separately passed the nominal application with actual World Model and
   provider/SQL stubs. The next business run must combine the real components
   with verified hydrological inputs, without conflating these proofs.
4. The original guide smoke passed all three checks in report 0013 using
   project .venv Python, with unchanged source. Earlier adapted-smoke
   failures remain historical; no redirect correction was implemented.
5. Hub Eau discovery is complete for the three current views in report 0015.
   The reference exposes 103 station codes; recent measurements only partly
   overlap it, and history has no matching code_station in exposed rows.
   The 2024 weather CSV subsequently passed SQL/tool qualification in report 0017; units/source semantics remain to confirm.
6. Report 0016 records shared normalization, deterministic summaries, catalog-aware
   data requests and the latest controlled live failure.
7. The provenance-preserving partial snapshot CLI passes. Clean SAMPLE setup,
   final interface and video evidence remain to be delivered.

The owner creates the external API access and Zetaris objects; do not duplicate
that work or modify neighboring repositories. SELECT 1 does not depend on the
weather/hydrometry source setup, but requires approved Zetaris connectivity.

The original setup smoke is complete within its three-check scope.
The minimal catalog-aware hydro path is implemented and locally tested.
Bounded retry/human handling and preservation of generated answers have now
passed in report 0018. The latest empty Givry read remains a source-coverage
issue; the real weather path is available for the vertical demonstration. Historical comparison is not justified by the current
station-code overlap; rainfall integration awaits the owner's source.
The nominal application/World Model connection is tested with stubs. No redirect patch is needed to claim
the observed original-script result. The nominal World Model increment has since passed 64 targeted tests and the
actual local CLI in report 0014. Further incident-handling changes and live tests still
require their exact scoped proposal and approval.
No command, code change, network request or test is authorized by this status
document. Each operation remains subject to the project approval policy.

## Priority checks and risks

- Data coverage: both exposed measurement aggregates contain 1000 rows,
  not a verified complete API archive. Recent H/Q cover only a subset of the
  reference. History has zero matching station codes; site matching was not tested.
- Givry sample: three H and three Q points over ten minutes, constant and
  labeled unqualified/raw. No predictive or rainfall-lag claim is supported.

- Guide smoke: the original script passed in report 0013. The old 307 failure
  belongs to the former adaptation; its proposed fix was not implemented.
- Legacy test migration: tests/unit/test_smoke_test.py imports the root module
  but targets the removed adaptation. Do not run it against the original's
  live import-time checks; approved retargeting is pending.

- Tool calling: reports 0007/0008 cover the protocol probe and standalone
  checks. Report 0009 passed SELECT-one; report 0016 records actual hydro
  requests with incomplete final acceptance. Full provider compatibility and
  advanced failure/recovery cases remain open.
- SQL safety: least-privilege read-only access, authorized sources, restrictive
  backend query validation, and strict row/time/size limits. Do not rely solely
  on keyword filtering or execute arbitrary model-generated SQL.
- Loop bounds: explicit iteration, tool-call, elapsed-time and output budgets;
  controlled failure, cancellation and no hidden retries.
- Traceability: link run/task/attempt, question, tool requests/results, source
  versions, calculations, invocation identifiers and final outcome. Exclude
  secrets and reconcile uncertain effects before retrying.
- Nightshift JUDGE: the owner reported an unparseable, undecided panel. This
  does not block generation, and must never be reported as positive validation.
- Source compatibility: choose the scenario after observing actual cadence,
  spatial coverage and units. Never invent measurements or correlations.
- Historical claims: observation time alone cannot establish information
  availability at the simulated date; disclose missing publication/revision
  history and model-knowledge limitations.
- SAMPLE: clean judging requires no accounts or live credentials, whereas
  newly generated Nemotron tool decisions require accessible inference.
  Agree on explicit offline versus live-backed behavior; never present a
  recorded or scripted exchange as a new model-generated analysis.
- Delivery: public deployment, a gateway and JUDGE improvements are outside
  the critical path unless explicitly reprioritized.

## Documentation follow-up

- README: preserves earlier milestones and adds original-guide smoke report
  0013 with its independent three-PASS result and current invocation.
  Source inventory and final sample/hydrological delivery remain pending.
- After approved connection checks, replace pending source-inventory values
  with verified sanitized endpoints, qualified tables/views, schemas, units,
  coverage, transformations and prerequisites.
- Technical contracts: demand-driven coordination, Analyzer request/result
  requirements, causal tracing and the bounded Nightshift tool loop are now
  documented and locally tested with hydro rows. Current limits are two SQL
  calls, three inference requests and 180 seconds. Retry/human handling remains pending.
- Workflow: the nominal application now projects its 1.2.0 qualification,
  analysis, delegated data and report tasks through the official engine.
  It does not implement every declared policy or durable finalization.
  E1 still records 1.1.0 and must not migrate silently.
- Decisions: preserve Accepted ADRs. Propose a new ADR only where a substantive
  decision is added or changed; do not retroactively rewrite accepted context.
- Scientific scope: precipitation, discharge and water levels, optionally
  compared with documented flood periods, are a limited exploratory basis.
  Soil sealing/saturation, basin topography and connectivity, calibrated
  hydrological/statistical models and other relevant factors are not
  comprehensively modeled or validated.
- Additional application-database storage of analysis results is deferred;
  this does not remove required operational traceability or approved
  durability/recovery requirements. H-MEM remains deferred.
- Permanent instructions link report 0016. Earlier setup evidence remains
  historical; the current real hydro attempt combines both platforms and
  World Model but fails final acceptance and has no returned Givry observations.

## Session handover

Start with applicable instructions, this status document, relevant ADRs and
the validation evidence. Inspect only the code/contracts needed for the task.
Distinguish requirements, implementation, tests and demonstrated behavior.
Maintain concise dated history; do not treat proposed next work as authorized.

## Change history

| Date | Change |
|---|---|
| 2026-10-27 | Created the handover with inspected placeholders, prior evidence, owner-managed Zetaris setup, nested Analyzer requirements, delivery risks and pending documentation. |
| 2026-10-27 | Linked the additive README delivery clarification and kept source verification, technical contracts and implementation explicitly pending. |
| 2026-10-27 | Recorded accepted decision 0011, removed mandatory pre-analysis collection from the target sequence and identified remaining technical-contract alignment. |
| 2026-10-27 | Aligned four architecture contracts and added documentary workflow 1.2.0; JSON/declared-dependency checks do not establish execution or Runtime tool support. |
| 2026-10-27 | Recorded report 0007 and prioritized a real Zetaris SELECT 1 application round trip before the guide smoke and hydrological queries. |
| 2026-10-27 | Recorded the minimal application probe, 27 passing standalone checks and README procedures; live, workflow and durability validation remain pending. |
| 2026-10-27 | Recorded the successful live application SELECT-one path, synchronized evidence summaries and prioritized guide-smoke inspection before domain scenarios. |
| 2026-10-27 | Copied the guide page-24 smoke over the hello placeholder, checked syntax only and recorded pending configuration/transport/security adaptation. |
| 2026-10-27 | Recorded the import-safe guide adaptation, optional configured web URL, 12 isolated and 27 affected tests; live smoke remains pending. |
| 2026-10-27 | Recorded the live guide-smoke exit 1, successful SQL/ready response and unresolved web HTTP error; diagnostic remains proposed. |
| 2026-10-27 | Recorded report 0012 confirming HTTP 307; proposed bounded web-only handling without changing code or retrying the smoke. |
| 2026-10-27 | Recorded the unchanged original guide smoke's independent three-PASS run, preserved adapted results, clarified optional web configuration and flagged legacy-test retargeting. |
| 2026-10-27 | Recorded the actual memory-engine nominal integration, 64 targeted passes and local CLI; next priority is source qualification and the reduced business demonstration. |
| 2026-10-27 | Recorded three verified Hub Eau schemas, actual coverage/matching and Givry sample; controlled hydrological tool integration and weather qualification remain pending. |

| 2026-10-27 | Recorded catalog-aware hydro tests, failed live outcomes and the pending bounded retry/human-intervention requirement. |

| 2026-10-27 | Recorded verified 2024 weather CSV access and catalog scope without Python precipitation analysis; kept workflow 1.3 in progress. |

| 2026-10-27 | Recorded completed workflow 1.3 checks and the real weather inference with explicit generation, coverage and durability limits. |

| 2026-10-27 | Promoted the analysis result with distinct execution/scientific status, explicit SAMPLE/incident disclosure, 15 passing tests and targeted contrast/state checks. |

| 2026-10-28 | Recorded clean-clone SAMPLE and actual-engine installation/execution, publication screening, attribution and retained LIVE/path limits. |
