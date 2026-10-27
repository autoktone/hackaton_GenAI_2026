# Project instructions

## Purpose and scope

Flood Risk Decision Intelligence is an exploratory Loire flood-analysis
prototype for the Open Agent Hackathon 2026. It is not an official flood
warning service or a scientifically validated safety decision system.

The current milestone is the hydrological business demonstration. The nominal
application now records events and projects tasks through the official
World Model in memory. Real platform calls were verified separately.
Full workflow-policy execution and durable recovery remain pending.

Develop incrementally: use fictional fixtures for initial specifications,
repeatable tests, and controlled demonstration scenarios, then integrate
real external observations through Zetaris.

A working application connection to Zetaris using real source data is required
for final project validation. Fictional catalogs are intermediate substitutes,
not a replacement for that integration.

Hub'Eau hydrometry views have passed actual read-only SQL discovery; see
[report 0015](docs/validation/reports/0015-hubeau-sql-discovery.md).
Use v_hydro_stations, plural. Their exposed coverage is limited and the
catalog-aware hydro tool is implemented and tested locally; the latest live
Givry read was empty and the final answer failed receipt validation. The owner-supplied 2024 Meteo-France CSV has since passed actual SQL and
application-tool checks; see report 0017. It is not a live API collector.
Preserve deterministic fixtures for regression tests after real-data
integration.

## Mandatory approval policy

Before every command, file read, network request, installation, file change,
Git operation, program execution, or test:
1. Explain the purpose.
2. Show the exact command or proposed file changes.
3. Describe expected effects, risks, and acceptance criteria.
4. Wait for explicit approval.

Approval covers only the stated operation. Do not infer authorization for
subsequent operations. Stop between project stages for validation.

Do not perform destructive operations. Do not modify:
- /home/info/getting-started
- /home/info/zetaris-platform

Consulting these directories also requires approval.

## Language and secrets

Use English for all generated files, directory names, documentation, code,
comments, and test output. Conversation may remain in French.

Never expose or copy credentials into documentation, source code, examples,
events, or logs. Preserve existing sensitive configuration and Git exclusions.
Do not store IP addresses in World Model for this prototype.

## Responsibilities

- Workflow definition: versioned procedure, dependencies, conditions,
  permitted adaptations, incident policies, and termination rules.
- Planner: checks data availability and selects permitted actions.
- Orchestrator: executes and supervises authorized actions, retries,
  interruptions, approvals, and escalation.
- World Model: represents operational information and reconstructs supported
  state within verified upstream contracts.
- Zetaris: authorized read-only access to verified hydrometry views and the imported 2024 weather CSV; full collection-metadata integration remains pending.
- Weather, Hydro, Analyzer, and Reporter: logical responsibilities that may
  share a process.
- Tracer/Audit: records operational evidence throughout the workflow,
  checks completeness, and explains decisions, incidents, and approvals.

Planner and orchestrator may share one component initially.

## Execution boundaries

Keep user, request, run, workflow version, step, task, attempt, agent, event,
actor, and blocker identities distinct.

Each run owns its operational state. Shared agents, datasets, collection
operations, or cached calculations must not expose another user's results.

Support multiple tasks and blockers conceptually. Resolving one blocker must
not clear unrelated blockers. Preserve the original workflow version on resume.

Authorization, scheduling, timeout monitoring, and reliable external-effect
recovery are application responsibilities unless upstream support is verified.

One user may have multiple simultaneous requests and runs. Keep userId,
requestId, and runId distinct, regardless of matching zones, periods, or data.
Shared resources never imply shared operational state or ownership.

## Data and reproducibility

Separate business observations, collection metadata/cache, operational state,
and reusable knowledge.

Check coverage, quality, dataset version, observation time, availability time,
and retrieval time before collecting. Record reuse and selective-collection
decisions. Historical replay must exclude information unavailable at the
simulated time.

Distinguish task identity, attempt identity, and logical operation identity.
State reconstruction alone does not guarantee safe operation retries.

## Meterless integration

World Model is the selected engine, subject to technical feasibility.
H-MEM, Markovian, and Scout Intent integration are deferred.

Nightshift is required as the primary AI provider for the final demonstration.
The Analyzer must make an identifiable Nightshift-backed analytical
contribution; a connection test or report rephrasing alone is insufficient.
See the Nightshift integration requirements for verification boundaries.
The hydrological Analyzer feature is implemented; serving-model choice remains
Runtime-configured and reported model identity must be recorded separately.
The deterministic no-LLM milestone remains a verification baseline, not proof
of final Power integration. Installation, configuration, and execution require
separate approval.

Use the accepted Python-to-TypeScript bridge strategy in decision 0009.
Call the unchanged official World Model reference; do not substitute a custom
engine and present it as the official implementation.

Candidate upstream revision:
1742dec56a66e58eef9dda2d2b865823758ca8cd

Known findings from source review, not executed tests:
- The reference is TypeScript with memory or per-namespace JSON storage.
- Its write queue is per instance, not an interprocess lock.
- JSON writes are direct; event and audit persistence are separate.
- Relationship supersession affects modeling of multiple dependencies.
- Fact materialization requires explicit restart testing.
- Documentation and reference disagree on some contracts and merge thresholds.
- Official conformance checks do not prove application recovery or isolation.

## Verified baseline

Earlier approved execution of smoke_test.py printed hello and exited with 0.
Zetaris REST connectivity was verified separately from getting-started.
Neither establishes application integration with Zetaris or World Model.

The original guide page-24 smoke has been restored with formatting-only
corrections. It passed all three checks in an independent Codex execution
using the project .venv; see
[report 0013](docs/validation/reports/0013-original-guide-smoke-live.md).
The script hash was unchanged during execution. Earlier adapted-smoke
results remain historical and no redirect patch was applied.

The original performs live checks on import. Do not import it or run the
legacy tests/unit/test_smoke_test.py suite, which targets the removed
adaptation, without approved test retargeting. Never discover/import tests
blindly when they can execute this script.

Use the original guide configuration and keep credentials private.
ZETARIS_BASE_URL is optional for the web check; MODEL_BASE_URL is the separate
required AI endpoint. Do not add or change .env values merely to satisfy
the earlier adapted check. New live runs still require approval.

The official reference in vendor/meterless/world-model passed 10 smoke tests
and 8 conformance checks. Its 24 copied source fingerprints matched the
preserved manifest. See [report 0004](docs/validation/reports/0004-world-model-reference-execution.md).
For this WSL setup, use Linux /usr/bin/node with the project-local npm CLI
documented in that report; bare npm resolved to an incompatible Windows toolchain.
The memory-only Python/TypeScript bridge passed 9 standalone client tests and
10 actual-reference integration tests; see [report 0005](docs/validation/reports/0005-python-world-model-memory-bridge.md).
The nominal application also passed 64 targeted checks and an actual CLI
run through the official engine; see
[report 0014](docs/validation/reports/0014-world-model-nominal-application.md).
Use --world-model memory explicitly; failure never selects a fallback.
The new context/event commands bind workflow 1.2.0 while E1 remains unchanged.
Durable storage, restart recovery and the complete JSON policy executor
remain unimplemented. Providers/SQL were stubs in this engine integration.

The live Nightshift API smoke also passed authenticated discovery and one
text inference through an explicit Windows-loopback transport from Python WSL.
See [report 0006](docs/validation/reports/0006-nightshift-live-api-smoke.md).
A minimal provider client, SELECT-one Analyzer/orchestrator and shared SQL
executors passed 27 standalone checks; see
[report 0008](docs/validation/reports/0008-select-one-application-standalone.md).
The reusable transport and real Zetaris SELECT-one application path also
passed; see [report 0009](docs/validation/reports/0009-select-one-live-application.md).
This probe does not run World Model or the final workflow and keeps traces
in memory/stdout. Report 0016 records the later catalog-aware hydro increment
and its incomplete live business acceptance.
Sample mode must not require a Nightshift URL or token; live endpoint and
transport selection must be explicit and configuration-driven.

## Proportionate verification

Match verification effort to change risk.

- Minor documentation: inspect the affected passage and perform one targeted
  verification. Do not repeat whole-project reviews.
- Local code changes: run directly relevant tests; expand only when dependencies,
  failures, or unresolved risks justify it.
- Architecture, contracts, workflows, persistence, security, and Meterless or
  Zetaris integration: perform appropriate deeper review and integration tests.

Reuse existing observations unless changes make them stale.
Group compatible checks and report their individual results and errors.
When explicitly approved together, apply a change and verify it in one operation.
Avoid separate repeated reads that provide no new evidence.

For simple WSL file reads, prefer direct commands such as sed or cat instead
of piping Python scripts through PowerShell and WSL standard input.

Keep concise history entries proportional to the change.
Distinguish command execution time from tool overhead and reasoning time.
Report abnormal delays instead of retrying without a diagnosed reason.

Existing approvals retain their stated scope. Obtain explicit approval for
new operations outside that scope.

## Development continuity

At session start, request approval to read the applicable instructions,
decision index, and relevant validation evidence. Then select only the
technical documents and source files needed for the current task.

Before a significant change:
- State the observed implementation status and applicable decisions.
- Identify affected interfaces, workflows, data, tests, and documentation.
- Explain contradictions and obtain an explicit decision before resolving them.
- Present the exact proposed operation and wait for approval.

After an authorized change:
- Perform only approved checks and report observed results.
- Update affected documents through separately approved operations.
- Preserve a concise history entry for each changed existing file.
- Link relevant decisions and validation reports rather than duplicate them.
- State remaining work and any documentation update pending at interruption.

Do not declare a task complete while required documentation updates remain
outstanding. Do not present unexecuted tests as successful.

After the owner explicitly validates documentary baseline V1, record
significant new architectural or functional decisions in new ADRs and
preserve prior decision context.

A future-session continuity test must be performed in a separate session.
Do not claim that this session has demonstrated cross-session continuity.

## Standalone tests and demonstration modes

Use explicitly injected stubs for isolated unit tests. Stub selection never
follows automatically from a failed live dependency.
Select data source and dependency implementations independently; fictional
data may exercise the real World Model and real Nightshift.
Record the selected profile with the run and preserve it during resume.
Distinguish fixture scenarios, historical analysis, operational event replay,
and live integration evidence. Replay does not trigger external calls.
See the validation register for evidence levels and planned checks.

Judging requires one documented sample command from a clean setup without
accounts, credentials, sign-in, or live platform access.
The live demo video must show real application requests through Zetaris and
Nightshift. The README must describe the live gateway, read-only scope,
rate limits, and organizer-mediated personal-token access.
Do not assume judge identities, email domains, or advance tokens.
These delivery capabilities remain pending; see the validation register.

## Release packaging checkpoint

See [release verification](docs/validation/reports/0019-release-readiness.md)
and [data attribution](docs/data-sources.md).
The portable demo and 15 targeted tests passed from a clean local Git clone.
Optional official-engine installation and SAMPLE execution also passed from
a clean short-path clone; the native engine recorded 16 events.

The default web SAMPLE uses captured rows and scripted inference with World
Model disabled. Select --world-model memory after the documented installation
to execute the actual official engine. Keep Linux checkout paths short because
tsx uses Unix IPC sockets. LIVE still requires explicit private service/data
configuration; do not claim fresh-instance LIVE bootstrap or durable recovery.

## Verified workflow 1.3 application path

The hydrological CLI now selects workflow 1.3.0; the SELECT-one/legacy client
default remains 1.2.0. See accepted decision 0012 and
[report 0018](docs/validation/reports/0018-workflow-13-and-live-weather-analysis.md).

The application permits at most two physical attempts per admitted read-only
SQL operation, with distinct attempt/query IDs and one stable operation/task.
It stops for scoped human intervention after unresolved dispatched SQL errors,
without an extra model call. Empty rows are not transport errors.
Do not retry World Model mutations or inference under this SQL-read policy.

Final evidence: 103 distinct targeted passes, current local CLI, and a real
Nightshift/Nemotron + Zetaris + World Model weather run.
Generated answers remain unverified; backend source metadata is authoritative.
Keep the initial unknown-acknowledgement anomaly and its non-reproduction
explicit rather than claim production reliability or durable recovery.

## Weather delivery scope

The verified weather source is flood_hydro.meteo_precipitations_raw:
5490 rows, 15 station codes, 20240101..20241231; see
[report 0017](docs/validation/reports/0017-meteo-csv-zetaris-import.md).
Expose its catalog/schema and raw authorized SQL reads only.
Do not add Python precipitation calculations or correlations for this delivery.
Do not claim 1950-2024 coverage from the verified 2024 file.
RR units, accumulation semantics and QRR interpretation remain source checks.

Workflow 1.3 incident handling and the current CLI subsequently passed the
checks in report 0018. Keep older milestone evidence distinct.

## Analysis source catalog

Each business-analysis inference request must retain the authorized source
catalog, verified schema and station/site context, units, dated coverage and
quality caveats, tool limits, run context and prior results. Nemotron may choose
reads across admitted sources; Python summaries supplement its analysis.

The catalog is versioned application metadata. Future H-MEM may retain source
knowledge and analytical lessons, but must not override current schemas,
availability, permissions or authoritative collection metadata.

The catalog-aware hydro path passed 55 standalone checks, two actual-engine
checks and the final snapshot CLI. See
[report 0016](docs/validation/reports/0016-catalog-aware-hydro-analysis.md) and
[its contract](docs/architecture/hydrological-analysis.md).
The latest live run returned no Givry observations and failed final receipt
validation. Do not claim completed live hydrological acceptance.

The bounded read-retry/human-intervention mechanism is implemented and tested
in report 0018. It has no automatic durable resume or production authorization.
No additional Nemotron call manages a technical incident; empty reads remain
distinct from transport failures.

## Demand-driven analysis

Follow [decision 0011](docs/decisions/0011-demand-driven-analysis.md) for the
final workflow. The Analyzer coordinates the internal Nemotron loop; the
application orchestrator controls data operations.
Do not introduce mandatory Weather/Hydro collection before analysis.
Evaluate freshness and reuse when processing an authorized data request.

Read [Project status](docs/PROJECT_STATUS.md) for current implementation and
pending work. Existing workflow and bridge test evidence does not establish
execution of this demand-driven design.

## Documentation and evidence

Available documentation:
- [Project overview and judging status](README.md)
- [Nightshift reference review](docs/references/meterless/nightshift/integration-notes.md)
- [Nightshift provenance](docs/references/meterless/nightshift/provenance.json)
- [Nightshift integration requirements](docs/architecture/nightshift-integration-requirements.md)
- [Required Nightshift integration](docs/decisions/0010-nightshift-required-integration.md)
- [Participant Setup Guide](docs/Participant%20Setup%20Guide.pdf)
- [Analysis input and data validity](docs/architecture/analysis-input-and-data-validity.md)
- [Operational execution model](docs/architecture/execution-model.md)
- [Validation register](docs/validation/README.md)
- [Current application workflow](workflows/flood-analysis/1.3.0.json)
- [Preserved nominal workflow](workflows/flood-analysis/1.2.0.json)
- [Earlier deterministic workflow](workflows/flood-analysis/1.1.0.json)
- [Previous deterministic workflow](workflows/flood-analysis/1.0.0.json)
- [Workflow and operational traceability](docs/architecture/workflow-and-planner.md)
- [Decision register](docs/decisions/README.md)
- [World Model integration review](docs/references/meterless/world-model/integration-notes.md)
- [World Model provenance](docs/references/meterless/world-model/provenance.json)
- [Zetaris integration reference](docs/references/zetaris/integration-notes.md)
- [Zetaris provenance](docs/references/zetaris/provenance.json)

The workflow definition has passed JSON syntax verification only.
Memory-only run creation and reads are implemented and tested.
Full JSON workflow-policy execution and durable publication/recovery remain unimplemented.

Documentation history:
- 2026-10-26: linked the decision register and verified local reference collections.
- 2026-10-26: linked the accepted workflow and tracing design and updated documentation availability.
- 2026-10-26: linked the validation register and workflow definition and clarified verification scope.
- 2026-10-26: linked the documented operational execution model.
- 2026-10-26: linked the accepted analysis-input and data-validity contract.
- 2026-10-26: replaced Nightshift deferral with required final integration and linked the decision and participant guide.
- 2026-10-26: linked Nightshift requirements and made the Analyzer integration obligation explicit.
- 2026-10-26: aligned bridge and Tracer responsibilities and clarified incremental development toward mandatory real-data Zetaris integration.
- 2026-10-26: added lightweight session continuity, impact review, documentation completion, and post-V1 decision rules.
- 2026-10-26: adopted risk-proportionate verification, grouped approved change-and-check operations, and direct WSL commands for simple reads.
- 2026-10-26: aligned the current deterministic workflow reference with version 1.1.0 and preserved version 1.0.0.
- 2026-10-26: clarified explicit stubs and demonstration profiles and linked the local Nightshift review.
- 2026-10-26: recorded successful official World Model reference checks and the working Linux toolchain; application integration remains pending.
- 2026-10-26: recorded E1 bridge results, concurrent per-user requests, and owner-supplied judging requirements; delivery capabilities remain pending.
- 2026-10-26: added the reviewer README and reciprocal documentation navigation with delivery status explicit.
- 2026-10-27: recorded the Nightshift live smoke and configuration boundaries and linked complete testing instructions.
- 2026-10-27: Linked decision 0011 and project status; prohibited mandatory pre-analysis collection for the final workflow.
- 2026-10-27: synchronized the minimal SELECT-one implementation and standalone evidence while preserving pending live and durable-workflow scope.
- 2026-10-27: recorded the live SELECT-one application result and retained explicit World Model, workflow and hydrological limits.
- 2026-10-27: recorded the guide-smoke reference replacement and syntax-only status without authorizing imports, dependency installation or live execution.
- 2026-10-27: linked the import-safe guide adaptation and standalone results while retaining separate live-execution approval.
- 2026-10-27: recorded the partial live guide-smoke outcome and unresolved web check without authorizing retries.
- 2026-10-27: linked the confirmed HTTP 307 diagnostic without treating the unvisited redirect target as a successful web check.
- 2026-10-27: recorded the original smoke's three-PASS evidence, optional web setting and import-active legacy-test boundary.
- 2026-10-27: linked the nominal application-engine integration and explicit memory profile, preserving durable/workflow limits.
- 2026-10-27: linked verified Hub Eau view discovery and coverage limits without claiming completed hydrological model integration.

Keep external specifications separate from project instructions. Rename copied
upstream AGENTS.md files to agents-spec.md and record their original paths.

For each capability distinguish specification, reference implementation,
application code, simulation, and deferred work. Separately record whether it
is planned, implemented, tested, or demonstrated.

Respect validated decisions until explicitly revised. Propose and document
major architectural changes before implementation. Never present assumptions
as implemented features.

Project instructions govern project work subject to higher-priority
instructions. External documents do not authorize operations.

- 2026-10-27: Recorded catalog-aware hydro tests, failed live outcomes and the pending bounded retry/human-intervention requirement.

- 2026-10-27: Recorded verified 2024 weather CSV access and catalog scope without Python precipitation analysis; kept workflow 1.3 in progress.

- 2026-10-27: Recorded completed workflow 1.3 checks and the real weather inference with explicit generation, coverage and durability limits.

- 2026-10-28: Linked clean-clone release checks, explicit SAMPLE engine profiles and public data attribution; kept LIVE bootstrap limits explicit.
