# Zetaris integration reference

## Status and provenance

These are selected references from zetaris/getting-started, not a complete
copy of the repository or a uniform set of vendor-authored specifications.

Pinned revision:
6a2fbaa47c32c9ac33f6584c64b43b146c621bed

See provenance.json for original paths, source URLs, copy timestamps,
sizes, and content fingerprints.

Upstream files are unchanged. AGENTS.md was renamed to agents-spec.md
to keep external reference material separate from active project instructions.

Some relative links point to omitted files. Refer to the pinned upstream
repository when a local target is unavailable.

## Role in this project

Zetaris is the planned access layer for business observations and persistent
collection metadata.

The writable storage, dataset versioning, metadata schema, and application
adapter remain to be verified and selected.

World Model records operational state and decisions. It does not replace
the business-data layer.

## Connection boundaries

The upstream guides distinguish:
- Direct REST API: ZETARIS_REST_URL.
- UI proxy helpers: ZETARIS_BASE_URL.
- JDBC: separate driver and runtime requirements.

The starter scripts use .env.local. The application's configuration convention
and loading mechanism remain undecided; do not change existing configuration
or copy credentials to resolve this difference.

Never execute a documented command automatically. Obtain explicit approval
before connection checks, queries, installations, or resource changes.

## Safety and permissions

Keep credentials out of documentation, examples, events, and logs.
Use least privilege and do not switch accounts to bypass permission failures.

Zetaris permissions govern data access through its credentials.
They do not replace application ownership checks or workflow approvals.

Read the SQL command reference and companion before writing new Lightning SQL.
Follow the approved preflight procedure before future instance work.
Do not contact local port 8889.

## Required real-data increment

The local fictional catalog is an intermediate implementation and test aid.

Final project validation requires a working application connection to Zetaris
that accesses real external observations used by the analysis.

Source registration, collection or ingestion, persistence, and metadata
management must follow verified Zetaris and source-specific contracts.
Do not assume that every external API can be registered directly as a table.

Hub'Eau and Meteo-France are candidates pending technical and usage review.

## Evidence and limitations

Earlier REST checks succeeded from getting-started.
They do not establish current availability or application integration.

This documentation-copy operation did not contact Zetaris, execute SQL,
copy credentials, or run the referenced scripts.

A local fictional catalog used in the demonstration must be identified as
a simulation, not as completed Zetaris integration.

## Reference map

- upstream/agents-spec.md
- upstream/docs/connections/codex-connection.md
- upstream/docs/connections/client-setup.md
- upstream/scripts/HOWTO.md
- upstream/docs/guides/permissions.md
- upstream/docs/guides/zetaris-lightning-sql-commands.md
- upstream/docs/guides/zetaris-lightning-sql-companion.md
- upstream/LICENSE

## Review history

| Date | Change |
|---|---|
| 2026-10-26 | Recorded reference scope and integration boundaries; application integration remains unimplemented. |
| 2026-10-26 | Clarified mandatory real-data application integration and the intermediate role of fictional catalogs. |
