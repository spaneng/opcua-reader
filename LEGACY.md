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

## Preserved legacy images

Both historical image indexes were verified against embedded source-commit labels
for Linux ARM64 and AMD64. They were copied without rebuilding any layers.

| App | Source commit | Preserved GHCR tag |
| --- | --- | --- |
| Fuel additive 1.0 | `0a2c3340255f738b957cda29ebdfa9f104848902` | `legacy-fuel-additive-0a2c334` |
| Generic OPCUA 1.0 | `e6f7e6571f503b3cc7d29792dfb1428b28fd8c2b` | `legacy-dv1-e6f7e65` |

Both tags are in `ghcr.io/spaneng/opcua-reader`. The legacy application records
are now pinned to these immutable references:

```text
fuel_additive_opcua_reader:
ghcr.io/spaneng/opcua-reader@sha256:10dda843ac2e5b62ec208abc0ba321b3ad91ac092123305b3d2fb5937cc77452

opcua_reader:
ghcr.io/spaneng/opcua-reader@sha256:6a88f7e6ffd5ec698c584eeba1653f0a77120e7c6c05a13bf125836376564b01
```

Existing deployment compose files still refer to `:fuel_additive` or `:dv1`.
The former was restored to the verified 1.0 digest above; `:dv1` already matched.
The displaced 2.0 image is preserved as `:archive-fuel-additive-cf0e6dd5a28c`.
No current workflow writes these tags. Do not delete the legacy images while
1.0 installations remain in service.

The [preservation run](https://github.com/spaneng/opcua-reader/actions/runs/34430164248)
verified the tags again after copying. Its one-time audit/repair workflow and
script were removed afterward; they remain available in commit `91c1071`.

No device was redeployed or restarted, and no site configuration, bridge,
widget, email destination or schedule was changed. Image provenance establishes
the historical published version, not the exact container digest or possible
live edits on every device. Verify those before a future migration.

The old registry credential embedded in the inspected deployment did not
authenticate. Before any future legacy reinstall, validate its registry access;
this consolidation did not replace device credentials.

## Other historical issues

The Alpine PR includes 1,238 vendored dependency files, including macOS binaries.
Its useful container smoke-test intent is covered by the shared release workflow;
its vendored files and dependency downgrades are excluded.

Report version 12 already used local commit `ec408d8` before GitHub had those
commits. All seven unpushed commits are retained by the consolidation merge.
