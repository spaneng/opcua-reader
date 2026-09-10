# Legacy preservation and consolidation record

The September 10, 2026 consolidation makes `master` the fuel-additive Doover 2.0
branch. It does not migrate, redeploy or restart Doover 1.0 installations.

## Existing application identities

| Platform | App | ID / key | Install records at audit |
| --- | --- | --- | --- |
| 2.0 | fuel_additive_opcua_reader | 215985129422634250 | 1 (SJBP) |
| 2.0 | fuel_additive_report_generator | 215991351634869518 | 1 (CRDD Reports) |
| 2.0 | opcua_reader (retired) | 215954311643970818 | 0 |
| 1.0 | fuel_additive_opcua_reader | d198f35f-c747-46c5-857b-b05243fa9364 | 11 |
| 1.0 | opcua_reader | b9a0e028-4868-4142-86f2-df41fedf39e5 | 2 |

Counts are installation records, not evidence that every container is running.
The 1.0 approximate installation counter incorrectly returns zero. Query actual
application installation lists before making retirement decisions.

NRBP, QSBP, SRBP and Saad BP have 2.0 legacy bridge installs and still read from
1.0 devices. CRDD Reports reads them together with SJBP. Preserve bridge config,
site schedules, email destinations, widgets and existing device deployments.

## Recovery references

- `archive/master-before-fuel-consolidation`: `5c6491f` (former generic master).
- `archive/fuel-additive-before-consolidation`: `ec408d8` (all local report fixes).
- `archive/report-tester`: `6dca970` (already incorporated in fuel-additive).
- `archive/alpine-base-migration`: `84210f2` (unmerged PR; do not restore wholesale).
- `legacy/fuel-additive-1.0`: `0a2c334` (last successful published legacy fuel code
  before the 2.0 migration; January 18, 2026).
- `dv1`: retained for the old generic OPCUA app.

These are historical references, not active publication branches. The obsolete
GitHub build/lint/test workflows are disabled; the new publisher runs only on
`master` and writes only to the Doover registry and report Lambda.

## Legacy image audit

Historical deployments reference `ghcr.io/spaneng/opcua-reader:fuel_additive` or
`:dv1`. The `fuel_additive` tag was also overwritten by 2.0 branch builds. Do not
assume its current digest contains compatible 1.0 code, and do not redeploy a
legacy installation from it without verifying the image.

The manual **Audit legacy images** workflow lists GHCR history using GitHub's
short-lived package credential. It is read-only and saves its inventory as an
artifact. Pin or restore an existing, verified compatible digest; do not rebuild
old source against today's mutable base image and call it the historical image.

An app record's image reference is not proof of the digest running on a device.
The old registry credential embedded in the inspected deployment could not
authenticate during this audit. Existing containers were left untouched.

## Other historical issues

The Alpine PR includes 1,238 vendored dependency files, including macOS binaries.
Its useful container smoke-test intent is covered by the shared release workflow;
its vendored files and dependency downgrades are excluded.

Report version 12 already used local commit `ec408d8` before GitHub had those
commits. All seven unpushed commits are retained by the consolidation merge.
