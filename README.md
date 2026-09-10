# Fuel Additive OPCUA Reader

This repository is dedicated to fuel-additive injection skids. `master` is the
only active development and Doover 2.0 release branch.

It contains two independently installed apps:

| App | Directory | Production application ID |
| --- | --- | --- |
| Fuel Additive OPCUA Reader | Repository root | `215985129422634250` |
| Fuel Additive Reconciliation Report | `report_generator/` | `215991351634869518` |

The reader subscribes to the skid PLC, records injector and tank readings,
raises alarms, and publishes the HMI and reconciliation state. The report app
reconstructs the previous Saudi calendar day's readings from `ui_state` history
and generates a separate PDF for each skid.

The generic OPCUA application formerly on `master` is retired from this repo.
Generic OPCUA development belongs in the separate OPCUA repositories.

## Reader configuration

| Setting | Purpose | Default |
| --- | --- | --- |
| OPCUA Address | PLC server URI | Required |
| Injectors | Unique injector names and PLC indices | Required |
| Skid Name | Skid identifier in reconciliation state | App display name |
| Number of Tanks | Tank readings to display (1–6) | 2 |
| Timezone | Skid timezone | Asia/Riyadh |
| Report Restart Time | Hour to reset reconciliation state | 10 |

Preserve each installation's existing settings; for example SJBP uses three
tanks and a restart hour of zero. Repository defaults do not replace site config.

## Releases

Pushes to `master` run `.github/workflows/doover-app.yml`, which discovers,
tests, validates and publishes both apps through GitHub OIDC trusted publishing.
Device images go to `registry.doover.com/apps/fuel_additive_opcua_reader`;
reports are built for the Python 3.13 ARM64 Lambda runtime. Releases record the
source commit. App IDs stay the same when branches change.

A release does not constitute an instruction to redeploy legacy devices.
See [development and release instructions](DEVELOPMENT.md), the
[report documentation](report_generator/README.md), and the
[legacy preservation record](LEGACY.md).

## Widget delivery

HMI and reconciliation bundles are in `assets/`. They are loaded from the agent's
`fuel_additive_hmi` and `fuel_additive_reconciliation` channels. Doover 2.0 does
not deploy these through the old `file_deployments` manifest field; channel-file
updates remain a separate commissioning step. Do not overwrite existing site
widgets merely because an app release was created.
