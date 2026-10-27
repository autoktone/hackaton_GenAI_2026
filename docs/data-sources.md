# Data sources, attribution and optional raw input

Reviewed: 2026-10-28 (Europe/Paris). This record describes the small captured
SAMPLE and the optional raw weather input; it does not establish scientific
validity, full source coverage or the availability of past revisions.

## Hub'Eau / Eaufrance hydrometry

Source: public French hydrometric observations and station information,
distributed by Hub'Eau / Eaufrance and its contributing hydrometry producers.
Captured through the project's Zetaris views on 2026-10-27; see
[discovery evidence](validation/reports/0015-hubeau-sql-discovery.md).

The [official Hub'Eau terms](https://hubeau.eaufrance.fr/page/conditions-generales)
state that datasets use the Etalab Open Licence and require attribution to
their authors. See the [hydrometry API](https://hubeau.eaufrance.fr/page/api-hydrometrie)
and the [Open Licence](https://www.etalab.gouv.fr/licence-ouverte-open-licence/).

Observed source endpoints:

- https://hubeau.eaufrance.fr/api/v2/hydrometrie/observations_tr
- https://hubeau.eaufrance.fr/api/v2/hydrometrie/obs_elab

The station reference's exact original registration/filter was not exported.
The repository keeps only a small SQL-captured subset, not all API pages or
stations. Project-selected normalized H/Q values and other transformations
are described in the validation reports; do not attribute these project
transformations to the upstream provider.

## Meteo-France daily climate data

Author: Meteo-France. The
[official daily dataset](https://www.data.gouv.fr/datasets/donnees-climatologiques-de-base-quotidiennes)
identifies Meteo-France as publisher and Open Licence 2.0 as its license
(metadata value lov2). Dataset identifier: 6569b51ae64326786e4e8e1a.
This metadata was checked through the public data.gouv.fr API on 2026-10-28.

Published department-44 resource:
https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/BASE/QUOT/Q_44_previous-1950-2024_RR-T-Vent.csv.gz

Local archive SHA-256: 317d6d972e1a6287efac9842ee3b6b70b812ee181b1a43d8030b2ae4bf15d375.

The published resource was identified by its exact filename in the official
metadata. This audit did not download a second archive or verify that today's
remote bytes equal the operator's local copy. Upstream resources can change;
compare the checksum and requalify any different input.

The operator's extraction selected non-empty RR records for 2024 and retained
NUM_POSTE, NOM_USUEL, LAT, LON, AAAAMMJJ, RR and QRR. The imported CSV exposed
5490 records and 15 station codes. The SAMPLE contains five SQL-captured BLAIN
rows, not the full archive or CSV. The snapshot capture date is 2026-10-27.
See [CSV import evidence](validation/reports/0017-meteo-csv-zetaris-import.md).
The original source values are preserved; units, accumulation semantics and
QRR interpretation remain unverified in the application.

## Optional raw-input restoration

Not required for SAMPLE. The compressed archive and generated full CSV are
ignored by Git; no local files were deleted. From the repository root:

~~~bash
mkdir -p data/meteo
curl --fail --location --output data/meteo/Q_44_previous-1950-2024_RR-T-Vent.csv.gz https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/BASE/QUOT/Q_44_previous-1950-2024_RR-T-Vent.csv.gz
sha256sum data/meteo/Q_44_previous-1950-2024_RR-T-Vent.csv.gz
python3 -B data/meteo/extract_meteo_CSV.py
~~~

Download only if the archive is absent: curl's output option replaces its
target. The extraction helper refuses to overwrite an existing output CSV.
These commands are documented, not executed by this audit. Recheck upstream
metadata before downloading. Register the resulting CSV using the
[LIVE setup instructions](setup/live-data.md), then verify the actual SQL
schema and coverage. This is manual source preparation, not an API collector.

## Reference material

World Model reference sources, their Apache-2.0 license, pinned hashes and
package lock remain in docs/references/meterless/world-model. Installed
vendor/node_modules directories are excluded and separately reconstructible.
The Participant Setup Guide PDF remains included as the requested project
reference; its presence does not license third-party platforms or credentials.

## History

- 2026-10-28: Recorded verified public dataset licensing, attribution, source URLs, archive provenance and optional restoration.
