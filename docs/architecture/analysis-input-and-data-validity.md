# Analysis input and data validity

## Status

Detailed contract accepted by the project owner.
Approval: Ok.

The first implementation increment is planned to use fictional observations
and a local test catalog. These components are not implemented yet.

A subsequent increment must integrate real external observations through
Zetaris. The local catalog is an intermediate test substitute.

Retain fictional fixtures for repeatable regression and demonstration
scenarios after real-data integration.
It does not establish real Zetaris integration or hydrological validity.

## Analysis request

Example:

{
  "userId": "USR-001",
  "requestId": "REQ-001",
  "zoneId": "LOIRE-DEMO",
  "analysisTime": "2026-10-25T12:00:00Z",
  "forecastHorizonHours": 24,
  "mode": "historical_replay",
  "dataWindowStart": "2026-10-24T12:00:00Z",
  "dataWindowEnd": "2026-10-25T12:00:00Z"
}

LOIRE-DEMO is a fictional zone, not a geographic coverage claim.

Required fields:
- userId: request owner.
- requestId: logical request identifier.
- zoneId: supported geographic scope.
- analysisTime: analysis reference time.
- forecastHorizonHours: positive integer defining the exploration horizon.
- mode: current or historical_replay.
- dataWindowStart and dataWindowEnd: required observation window.

Use normalized UTC timestamps.
Coverage intervals use inclusive start and exclusive end.

Require:
- dataWindowStart < dataWindowEnd.
- dataWindowEnd <= analysisTime.
- forecastHorizonHours > 0.
- Recognized mode, zone, and bounded identifier formats.

For this prototype, the input observation window excludes analysisTime itself.
Future target observations are not analysis inputs.

The application derives the exploration end from analysisTime and the horizon.
It does not claim to produce a validated forecast.

## Run binding and reproducibility

Assign runId when creating an execution.
Bind the run to:
- Validated request parameters.
- Owner and request identifiers.
- Exact workflow definition, version, and integrity identifier.
- Data-validity policy version.
- Method versions and dataset versions actually used.

Do not silently replace these values during resume.
A new execution may use a different configuration without changing the old run.

Operational recording time is separate from analysisTime.
An injected decision clock makes fictional scenarios reproducible.

## Catalog records

Represent coverage using segments with at least:
- sourceId, zoneId, variables, and relevant collection parameters.
- periodStart and periodEnd.
- datasetVersion and an immutable data reference.
- observation timestamps or an explicit observation-bound summary.
- availableAt: when that version became available from its source.
- lastFetchedAt: when this system retrieved it.
- qualityStatus.
- Metadata needed to verify actual coverage and expected observation cadence.

Use lastObservationAt for the latest observation represented by the segment.
A coverage interval alone does not prove that every expected sample exists.

Split segments where publication time, revision, quality, or coverage differs.
One timestamp must not hide later revisions within a segment.

The physical schema and Zetaris storage mapping remain undecided.

## Validity evaluation

Evaluate source, geographic scope, variables, parameters, coverage, quality,
dataset version, and temporal admissibility before collecting.

Return a structured decision with:
- Dataset references selected for reuse.
- Missing or invalid intervals.
- Excluded versions and reasons.
- Applicable policy version.
- Shared collection references, when relevant.
- Decision time and analysis time.

Reasons must be explicit, such as:
- DATA_REUSE_DECIDED.
- MISSING_COVERAGE.
- STALE_OBSERVATIONS.
- REFRESH_REQUIRED.
- QUALITY_REJECTED.
- NOT_AVAILABLE_AT_ANALYSIS_TIME.
- AVAILABILITY_UNKNOWN.
- COLLECTION_ALREADY_RUNNING.

These are application labels, not native World Model event kinds.

## Current-mode policy

Evaluate freshness against a recorded decision time.
Require an admissible analysisTime close enough to that decision time under
the configured policy; older situations use historical_replay.

Distinguish:
- Observation recency.
- Retrieval or refresh recency.
- Required window coverage.
- Quality and usability.

A recent retrieval cannot compensate for stale observations.
A recent observation cannot compensate for missing required history.

Accepted thresholds for the fictional demonstration only:
- Maximum analysis-time age: one hour; future analysis times are rejected.
- Maximum latest-observation age: two hours relative to analysisTime.
- Maximum retrieval age: one hour relative to decision time.
- qualityStatus must be VALID.
- Required coverage and expected samples must be complete.

These thresholds are test fixtures, not operational flood-monitoring advice.
Reject impossible negative ages rather than treating them as fresh.

## Historical replay policy

Use only observation versions available at or before analysisTime.
Observations must also fall inside the requested input window.

A revision published after analysisTime is ineligible even if it corrects an
older observation.

Retrieval performed today may supply an older version if evidence establishes
that this exact version was available at the simulated time.

Do not use lastFetchedAt as a substitute for historical availability.
Unknown availability blocks use in the strict historical demonstration.

Current retrieval-age rules do not invalidate historically admissible data.
Missing archive data must not be replaced by today's revised values silently.

Future observations may be used later as evaluation targets only.
Keep them separate from analysis inputs and record their evaluation role.

The Tracer records selected and excluded versions with reasons.

## Selective collection

Compute uncovered or invalid intervals after selecting reusable segments.
Request only the necessary source, zone, variables, intervals, and parameters.

Do not assume a source can deliver arbitrary intervals or historical versions.
The fictional collector supports the demonstration contract only.

Wait for an identical compatible collection already in progress.
A collection started for another run does not transfer ownership or approvals.

After collection, verify stored results and metadata before declaring coverage
usable. A successful collection command alone is insufficient.

## Estimates, evaluation targets, and experimental indicators

Keep each estimate as a versioned artifact linked to its run, issue time,
analysis time, target location and variable, target period or lead time,
units, input datasets, workflow, and method or model versions.
Retain the original estimate when observations or methods later change.
Observed outcomes used for evaluation are separate from analysis inputs;
record their provenance, availability, revisions, and matching rules.
Missing outcomes leave evaluation pending, not successful.
Error metrics, evaluation windows, and reference baselines remain to be
selected before making performance claims.
Risk indicators are versioned experimental derived values, separate from
raw measurements and official warnings; they are not validated safety advice.
H-MEM may later retain lessons and references to comparisons. Its integration
remains deferred and is not required to preserve evaluation artifacts.

## Model-assisted analysis

The Analyzer must use Nightshift for an identifiable analytical contribution
in the final demonstration.

For each invocation, preserve references to the admitted input datasets,
calculation results, prompt version, requested route, generation settings,
response artifact, and validation outcome.

Record client and Runtime versions and actual serving-model evidence when
available. Explicitly identify unavailable information.

Model outputs do not replace data-quality checks or calibrated uncertainty.

Historical input filtering does not exclude knowledge learned by the model
after the simulated date. Historical model-assisted analyses remain
exploratory unless evaluation addresses that contamination risk.

## Demonstration scenarios

- Missing observations trigger fictional collection.
- An identical compatible request reuses valid data.
- A wider input window triggers collection of missing coverage only.
- Recent retrieval with stale observations fails the recency check.
- Missing expected samples invalidate otherwise broad interval coverage.
- A late historical revision is excluded.
- A historically admissible version retrieved today remains eligible.
- Unknown historical availability prevents strict replay.
- Tracing explains reuse, exclusions, and collection decisions.

These scenarios are planned, not implemented or tested.

## Real-data integration increment

Final validation requires the application to retrieve and use real observations
through Zetaris, with verified source contracts and data provenance.

Hub'Eau and Meteo-France are candidates. Source selection, available variables,
coverage, access conditions, licensing, and collection mechanisms remain
to be verified.

Replace fictional freshness and quality policies with explicit source-appropriate
policies before applying them to real analysis.

Passing fixture-based tests does not establish source availability, real-data
quality, or scientific forecasting validity.

## Open questions

- Real sources, geographic definitions, variables, units, and sampling cadence.
- Real freshness and quality policies.
- Archive availability and revision provenance.
- Catalog storage, cache invalidation, and access enforcement.
- Limits on request size and supported horizon.
- Forecast method and scientific evaluation metrics.

## Final Analyzer contracts

These contracts extend the final application design, not the implemented
E1 create_run protocol.

The Analyzer request contains runId, taskId, question, fixed analysis inputs,
authorized source descriptions, execution profile and execution limits.

A data request contains a request identity, originating invocation and
tool-call identity, source references, requested operation and validated
arguments. Its scope must remain within the owning analysis request.

The orchestrator returns the matching request identity, status, dataset
references, provenance, units, coverage, validity findings and either a
bounded result or an explicit error.

Evaluate freshness, temporal admissibility, coverage and quality when
processing the request. Reuse valid data before requesting collection.
Existing historical-availability rules remain applicable.

The Analyzer result contains status, conclusions, computed indicators,
evidence references, uncertainties, tool-call references and errors.

See [decision 0011](../decisions/0011-demand-driven-analysis.md).
These are documented contract requirements, not implemented payload schemas.
Existing E1 request fields and validation remain unchanged.

## References

- Nightshift requirements: nightshift-integration-requirements.md
- Project instructions: ../../AGENTS.md
- Workflow: workflow-and-planner.md
- Execution model: execution-model.md
- Decisions: ../decisions/README.md
- Zetaris reference: ../references/zetaris/integration-notes.md

## Document history

| Date | Change |
|---|---|
| 2026-10-26 | Recorded accepted analysis inputs, data-validity rules, fictional thresholds, and historical availability boundaries. |
| 2026-10-26 | Added model-invocation reproducibility requirements and historical knowledge-contamination limits. |
| 2026-10-26 | Clarified fixture-based increments, required subsequent real-data integration, and the limited scope of fictional thresholds. |
| 2026-10-26 | Specified versioned estimates, separate evaluation targets, and experimental risk indicators without adding H-MEM. |
| 2026-10-27 | Added final Analyzer and data-request/result contract requirements without changing the implemented E1 protocol. |
