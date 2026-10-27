# Validation register

## Evidence levels

- Planned: specified but not implemented.
- Implemented: code or configuration exists.
- Tested: an identified check was executed with an observed result.
- Demonstrated: a reproducible scenario was run and its evidence recorded.

These levels apply to individual capabilities, not automatically to the
whole prototype.

## Reporting rules

Each report records the scenario, preconditions, exact command, expected
and observed results, date, relevant versions, and limitations.

Distinguish upstream conformance, application tests, simulations, and
scientific validation. Never infer one from another.

Preserve previous results. Record later checks in new reports and link
corrections or superseding evidence explicitly.

Do not include credentials or unnecessary personal data.

## Reports

| Report | Result | Scope |
|---|---|---|
| [0001](reports/0001-workflow-json-syntax.md) | Passed | Workflow JSON syntax and visual content review |
| [0002](reports/0002-documentary-consistency.md) | Passed within checked scope | ADR index, local Markdown targets, and workflow dependencies |
| [0003](reports/0003-local-executable-prerequisites.md) | Partial readiness | Node available and Python smoke passed; reference dependencies absent |
| [0004](reports/0004-world-model-reference-execution.md) | Passed within reference scope | 10 smoke tests, 8 conformance checks, and 24 copied source fingerprints |
| [0005](reports/0005-python-world-model-memory-bridge.md) | Passed within memory scope | 9 standalone and 10 actual-engine bridge tests; concurrent request creation |
| [0006](reports/0006-nightshift-live-api-smoke.md) | Passed within API-smoke scope | Authenticated catalog and one real text inference via explicit Windows-loopback transport |
| [0007](reports/0007-nightshift-structured-tool-round-trip.md) | Passed within tool-protocol scope | Two Windows Runtime calls; Nemotron used a structured run_sql stub result; no Zetaris or application workflow |
| [0008](reports/0008-select-one-application-standalone.md) | Passed within standalone scope | 27 tests for the minimal orchestrator/Analyzer, shared SQL executors and client boundaries; no live calls or World Model execution |
| [0009](reports/0009-select-one-live-application.md) | Passed within live SELECT-one scope | Application orchestrator/Analyzer, two real Nemotron calls and one Zetaris SELECT 1; in-memory traces, no World Model/workflow execution |
| [0010](reports/0010-guide-smoke-adaptation-standalone.md) | Passed within standalone scope | Adapted three-check guide smoke: 12 isolated tests and 27 affected application checks; no live smoke requests |
| [0011](reports/0011-guide-smoke-live.md) | Partial; exit 1 | Real SQL and Nemotron ready passed; web HTTP check failed, numeric status/cause unknown; no retry |
| [0012](reports/0012-zetaris-web-redirect-diagnostic.md) | Diagnostic observation | One configured web GET returned 307 with Location; no target inspection/follow, no SQL or inference |
| [0013](reports/0013-original-guide-smoke-live.md) | Passed; three guide checks | Original script independently executed in project .venv, exit 0 and unchanged hash; previous adaptation results remain historical |
| [0014](reports/0014-world-model-nominal-application.md) | Passed; nominal memory scope | 64 targeted checks and actual CLI: official engine events/tasks, two isolated concurrent runs; stub provider/SQL, no durable workflow |
| [0015](reports/0015-hubeau-sql-discovery.md) | SQL discovery passed with coverage limits | Three real hydro view schemas, 103 reference stations, partial recent overlap and unmatched history; no hydro Nemotron call at that milestone |
| [0016](reports/0016-catalog-aware-hydro-analysis.md) | Local passes; live acceptance failed | 55 standalone checks, two actual-engine checks and final snapshot CLI; live Runtime/SQL round trip reached an empty Givry read and failed final receipt citation |
| [0017](reports/0017-meteo-csv-zetaris-import.md) | CSV import and tool access passed | Actual CREATE/SELECT, 5490 rows/15 stations in 2024, verified catalog access and 56 standalone tests; no new weather inference or Python analysis |

| [0018](reports/0018-workflow-13-and-live-weather-analysis.md) | Workflow subset and real weather path passed | 103 distinct final targeted passes, local CLI and real Nightshift/Nemotron + Zetaris + World Model weather run; scientific validation and durable resume absent |

| [0019](reports/0019-release-readiness.md) | Clean SAMPLE and optional engine passed | 15 tests, HTTP scenario, locked reference restoration/install and 16 native events; no fresh LIVE platform call |

## Standalone tests and demonstration profiles

Select stubs explicitly through dependency injection; a live failure never
activates a stub or another provider automatically.
Keep data-source choice separate from dependency choice.
A fixture scenario can use the real World Model and real Nightshift;
record the actual implementations and call types in its evidence.
Real-data demonstrations require application access through Zetaris.
Historical analysis uses admissible past inputs; operational replay uses
recorded events and artifacts without new external requests.

Planned checks include:
- Each isolated function against controlled success and failure responses.
- Provider v4 normalization, headers, discovery, errors, and timeout settings.
- Multiple blockers, scoped approval, restart, workflow version, and run isolation.
- Fresh-data reuse, missing intervals, and shared collection deduplication.
- Duplicate acknowledgement recovery, conflicting identity reuse, and scope checks.
- Conformance of the future application adapter and separately approved live integrations.

Standalone client stubs and the memory-only actual-engine integration profile
are implemented and tested. The bounded hydro profile and snapshot replay are
also implemented; report 0016 separates their local passes from incomplete live
business acceptance. Full workflow-policy execution remains unimplemented.

## Judging and delivery acceptance

The project owner relayed the following judging guidance on 2026-10-26.
This is supplied guidance, not a newly verified website claim.
At least three reviewers may assess a submission and any may run it;
their identities, email addresses, and domains are not available in advance.

Required delivery evidence:
- Sample mode is the judging baseline: one documented command from a clean
  setup, without accounts, credentials, sign-in, or live platform access.
- Dependency downloads needed for clean setup must be disclosed separately
  from calls to live platforms. Do not claim offline bootstrap without a test.
- Sample components and fixture or recorded outputs must be labeled.
  Sample execution must not silently discover or fall back to live services.
- The demo video must show the application making real requests through
  Zetaris and Meterless Nightshift and using their results, with secrets hidden.
- The project README must explain the live gateway's purpose, access process,
  read-only scope, and rate limits. Those controls require implementation and
  verification; documentation alone does not establish them.
- If live access is requested, organizers arrange a personal token through
  their own channel. Do not assume advance tokens, judge identities, or an
  email-domain allowlist. Never expose platform credentials to judges.
- The live gateway is distinct from the local NDJSON World Model bridge;
  this requirement does not replace the accepted local bridge architecture.

Current status: the E1 memory tests are not the one-command sample application.
Clean-setup sample validation, live video evidence, README delivery instructions,
and gateway implementation and verification remain outstanding.

## Required final integration evidence

- World Model: execute the official reference and verify application behavior.
- Nightshift: demonstrate a real analytical invocation by the Analyzer.
- Traceability: link inputs, invocation, response, validation, and analytical
  result to the owning run and task.
- Model identity: distinguish the requested route from available evidence
  of the actual serving model.
- Zetaris: demonstrate the application retrieving and using real external
  observations through Zetaris, with source and dataset provenance.
- Controlled fixtures: retain repeatable workflow and incident scenarios,
  explicitly separated from live integration evidence.

Connection checks, mocks, and report rephrasing alone do not establish the
required Nightshift-backed analytical contribution.

These are acceptance requirements, not recorded successful results.

## Required finalization and persistence checks

- Failure before report production still produces an execution summary.
- Cancellation prevents new dispatches; late results do not reactivate the run.
- Conflicting commands are checked against the expected run revision.
- Interruption during working-file writes preserves readable committed state.
- Interruption after publication but before acknowledgement is reconciled
  without duplicating the business event.
- Repeated finalization preserves one logical closure.
- Missing evidence is explicit and never fabricated.

These checks are planned, not executed.
The selected publication adapter does not establish universal storage safety.

## Current limits

The official World Model reference passed 10 smoke tests and 8 conformance checks.
Nominal application task/event projection now passed against the official
memory engine in report 0014. Full hydrological workflow scenarios have not run.
No hydrological forecasting accuracy has been established.
The Participant Setup Guide Power section has been reviewed.
Authenticated Nightshift discovery and one text inference passed via the
Windows-loopback transport; native WSL loopback was refused.
A structured run_sql stub round trip also passed in Windows; see report 0007.
A minimal provider client, SELECT-one Analyzer/orchestrator and SQL executors
passed standalone checks in report 0008 and a real application SELECT-one
round trip in report 0009. Full workflow and hydrological analysis remain
unverified; the live probe does not exercise World Model or durable tracing.
The former adapted smoke passed isolated checks but had a partial live run
in reports 0010/0011. The restored original independently passed all three
guide checks in report 0013, with unchanged source and exit 0. The old adapted
smoke unit suite must be retargeted before reuse because the original executes
checks on import. A complete guide requirement-to-evidence mapping remains pending.
Actual hydrometry SQL reads and schemas are verified in report 0015, with
limited coverage and unmatched historical station codes. Their application
transmission was subsequently exercised in report 0016; the latest correct
Givry read was empty and the final answer failed receipt citation. Meteorological
SQL/tool access subsequently passed in report 0017. The bounded retry/human mechanism and a real weather application round trip
subsequently passed in report 0018. Complete judging delivery and scientific
validation remain outstanding. The owner requires technical-incident escalation by the application
orchestrator, without an additional Nemotron call.

## History

| Date | Change |
|---|---|
| 2026-10-26 | Created validation conventions and indexed the workflow syntax report. |
| 2026-10-26 | Added final integration evidence requirements, including the Analyzer's actual Nightshift contribution. |
| 2026-10-26 | Required real-data Zetaris evidence while retaining controlled fixtures for repeatable verification. |
| 2026-10-26 | Indexed the scoped documentary consistency review and its recorded limitations. |
| 2026-10-26 | Specified report-independent finalization and staged publication with explicit verification limits. |
| 2026-10-26 | Added explicit test profiles and recorded observed executable prerequisites without claiming engine integration. |
| 2026-10-26 | Indexed official reference execution, retained failed tooling attempts, and distinguished application checks still pending. |
| 2026-10-26 | Recorded E1 results and owner-supplied sample/live/gateway delivery criteria with implementation gaps explicit. |
| 2026-10-27 | Indexed real Nightshift API evidence and separated generated text, verified content, and pending application delivery. |
| 2026-10-27 | Indexed structured-tool report 0007 and separated protocol success from pending Python, orchestration and real Zetaris integration. |
| 2026-10-27 | Indexed 27 standalone application tests and separated implemented probe components from pending live and hydrological validation. |
| 2026-10-27 | Indexed the successful live SELECT-one application evidence and retained full workflow, domain-data and durable-trace limits. |
| 2026-10-27 | Indexed the guide-smoke adaptation and its isolated/regression evidence without claiming a live smoke result. |
| 2026-10-27 | Indexed the partial live smoke and retained the unresolved web failure without claiming three PASS results. |
| 2026-10-27 | Indexed the HTTP 307 diagnostic while preserving the failed smoke result and unverified redirect target. |
| 2026-10-27 | Indexed independent original-guide three-PASS evidence without replacing earlier adapted results or extending its verification scope. |
| 2026-10-27 | Indexed real-engine nominal application evidence, preserving earlier E1 and live-platform results as separate scopes. |
| 2026-10-27 | Indexed actual Hub Eau SQL discovery and retained coverage, historical matching and model-integration gaps. |

| 2026-10-27 | Recorded catalog-aware hydro tests, failed live outcomes and the pending bounded retry/human-intervention requirement. |

| 2026-10-27 | Recorded verified 2024 weather CSV access and catalog scope without Python precipitation analysis; kept workflow 1.3 in progress. |

| 2026-10-27 | Recorded completed workflow 1.3 checks and the real weather inference with explicit generation, coverage and durability limits. |

| 2026-10-28 | Indexed final clone/packaging checks and official engine reinstallation while retaining source and live-service limits. |
