# Nightshift integration review

## Status

Selected sources have been read locally after preservation.
One live text API smoke and authenticated discovery passed on 2026-10-27; see
[report 0006](../../../validation/reports/0006-nightshift-live-api-smoke.md).
The reusable provider client, full contract compatibility, and required
Analyzer feature remain unimplemented or unverified. Decision 0010 still
requires the final application integration.

## Sources and versions

- [Provenance](provenance.json): eleven preserved files with hashes and retrieval times.
- [Power prompt](upstream/website/engines.html): Runtime 1.4 / provider contract v4, selected target.
- [Repository provider guide](upstream/repository/docs/agent-ready/add-meterless-provider.md): Runtime 0.90.0.
- [Product overview](upstream/repository/docs/products/nightshift/README.md).
- [Hotspot](upstream/repository/docs/products/nightshift/hotspot.md).
- [Editions](upstream/repository/docs/products/nightshift/editions.md).
- [Setup guide](upstream/website/nightshift-getting-started.md).
- [CLI](upstream/website/cli.html).
- [Windows](upstream/website/windows.html).
- [Participant guide](../../../Participant%20Setup%20Guide.pdf).

Repository copies are pinned to 1742dec56a66e58eef9dda2d2b865823758ca8cd.
Website snapshots are dated copies, not immutable upstream releases.
The page mentions a provider v5 specification without supplying its content.
No v5 contract has been reviewed. Product, Runtime, and contract versions
must be recorded separately. Published benchmarks do not identify our host.

## Integration consequences

Use the separate Python provider client, not the World Model bridge.
The Windows host API and an explicit Windows-loopback transport from Python
WSL were verified. Native WSL loopback was refused. This does not select a
universal URL, implement a configurable client, or verify other deployments.
The CLI refuses non-loopback targets; it is not a presumed WSL networking workaround.
Some edition descriptions disagree about a Mac M1-M4 endpoint; verify the
chosen installed edition instead of generalizing from those descriptions.
The setup guide omits headers required by the provider contract; its snippets
do not make those headers optional.
A discovered route is not proof of successful inference or actual model identity.
A configured or rate-limited cloud key is not proof of a completed analytical call.
meterless-app separates application streams, not our users or run states.
Keep run, task, operation, input, response, and model-evidence references in
application tracing.
Examples of retries, cloud fallback, scans, or security changes do not override
project approvals. No automatic fallback is selected.
LAN hotspot documentation describes plain HTTP; topology and token handling
must be reviewed before enabling network sharing.
No overnight-job, media, 3D, or CLI integration is required by our text-first scope.

## Planned verification

Use explicitly selected stubs for unit tests, then controlled scenarios.
Verify actual Nightshift authentication, discovery, and analytical inference
separately after installation and approval.
Keep fictional inputs, stubbed services, and actual engine execution distinct.
The full Participant Guide requirement-to-evidence mapping remains pending.

## History

- 2026-10-26: Recorded local source findings, the v4 target, compatibility gaps, and scoped verification.

- 2026-10-27: Recorded successful live text smoke and the Windows/WSL endpoint distinction while retaining unverified application and panel capabilities.
