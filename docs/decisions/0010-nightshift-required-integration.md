# 0010 - Require Nightshift as the primary AI provider

- Status: Accepted
- Category: Architecture
- Recorded on: 2026-10-26
- Approval evidence: Ok.
- Supersedes: Decision 0001 only regarding deferred Nightshift integration.
- Superseded by: None

## Context

The project owner requires effective Nightshift integration for the final
hackathon demonstration.

The local Participant Setup Guide, last updated 21 October 2026, confirms
that the application must support Meterless Nightshift as a primary AI
provider.

World Model integration alone does not satisfy the Power requirement.

## Decision

Integrate Nightshift as the primary AI provider for the final demonstration.

The Analyzer must provide an identifiable Nightshift-backed analytical
contribution. Connection checks or report rephrasing alone are insufficient.
Detailed requirements are recorded in
../architecture/nightshift-integration-requirements.md.

Retain World Model for operational representation and reconstruction.
Retain the accepted Python-to-TypeScript bridge direction for that engine.

Keep the Nightshift provider client separate from the World Model bridge.

The deterministic fictional workflow remains a verification baseline.
It is not sufficient evidence of final Power integration.

Model selection and the exact AI-powered feature remain open.
Do not equate generative-model output with validated hydrological forecasting.

H-MEM, Markovian, and Scout Intent remain deferred.

## Guide evidence

Source: ../../Participant Setup Guide.pdf
Document date: 21 October 2026.

- Page 16: Nightshift must be supported as a primary AI provider.
- Page 17: use the live official Power Prompt as the implementation contract.
- Page 19: obtain Runtime connection details from Nightshift Console.
- Page 20: demonstrate a working application feature and a real request
  passing through Nightshift.

The Power verification checklist includes a responding Nemotron lane.
Visible Nemotron use is explicitly required for the NVIDIA award.

Pages 21 to 24 also contain direct-NVIDIA route examples. These do not replace
the explicit Nightshift requirement adopted for this project.

The guide also names Cursor as required Build tooling. Work performed through
Codex alone must not be presented as proof of meeting that tooling requirement.
Any eligibility ambiguity requires clarification with the organizers.

## Responsibilities and capability boundaries

Nightshift provides the configured AI Runtime route.
World Model records supported operational events and projections.
The application validates actions, data access, workflow progression, and
human approvals.

Model-generated proposals must not bypass deterministic workflow constraints
or authorization gates.

The initial fictional collectors remain simulations. Final demonstration
evidence must distinguish actual Nightshift calls, World Model execution,
and real or simulated data access.

## Security

Use Runtime credentials supplied by Nightshift Console.
Keep provider credentials, including NVIDIA keys, inside the appropriate
Nightshift provider configuration.

Never store secrets in source, documentation, events, or demonstration output.

Do not assume a default localhost address is reachable from WSL.
Verify the actual supported connection after separate approval.

## Required evidence

- Installed Nightshift Runtime reachable from the application.
- Successful authorization and model discovery.
- A real text request through the configured Runtime route.
- A useful application feature consuming the returned result.
- Trace references linking the invocation to its run, task, and attempt.
- Available Runtime evidence identifying the actual underlying model,
  particularly for Nemotron award claims.
- Explicit separation of simulated tests and live integration results.

A health response or a provider listed in documentation is insufficient.

## Verified live API smoke

On 2026-10-27, authenticated catalog reads and one real text inference
succeeded through an explicitly selected Windows-loopback transport called
from Python WSL. The catalog exposed 18 meterless routes including auto.
The Runtime reported nvidia/nemotron-3.5-lightning-30b-a3b and finish reason stop.
Native WSL loopback access was refused before HTTP.
See [report 0006](../validation/reports/0006-nightshift-live-api-smoke.md)
for the exact command, results, prerequisites, and limits.

This is provider API evidence, not a reusable project client or the required
Analyzer feature. The response was generated; no application content
verification or JUDGE-panel success was established.
Full provider-contract compatibility and the installed Runtime version
remain unverified.

## Open questions

- Compatibility of the installed Runtime with the target Runtime 1.4 /
  provider contract v4; local source snapshots are now preserved.
- Exact installed Runtime version beyond the observed working Windows installation.
- Implementation of a reusable explicitly configured transport beyond the verified Python WSL to Windows-loopback smoke.
- Final feature-specific model selection; the smoke's reported Nemotron model is evidence for that invocation only.
- Exact feature powered by Nightshift.
- Invocation validation, failures, timeouts, and uncertain outcomes.
- Workflow version changes and reproducibility metadata.

No installation, configuration, credential access, or model execution is
authorized by this decision.

## References

- Local source review: ../references/meterless/nightshift/integration-notes.md
- Source provenance: ../references/meterless/nightshift/provenance.json
- Project instructions: ../../AGENTS.md
- Previous decision: 0001-meterless-world-model.md
- World Model bridge: 0009-python-world-model-bridge.md
- Participant guide: ../../Participant Setup Guide.pdf

## Record history

| Date | Change |
|---|---|
| 2026-10-26 | Required Nightshift as the primary AI provider and partially superseded its earlier deferral using guide evidence. |
| 2026-10-26 | Made the Analyzer obligation explicit and updated the reviewed provider-contract status. |
| 2026-10-26 | Linked preserved Nightshift sources and separated the selected v4 target from unverified installed compatibility. |
| 2026-10-27 | Linked the successful API-smoke evidence while retaining the required live application feature and open configuration decisions. |
