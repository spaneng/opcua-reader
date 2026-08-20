# Fuel Additive OPCUA Reader

<!-- ![Doover Logo](https://doover.com/wp-content/uploads/Doover-Logo-Landscape-Navy-padded-small.png) -->
<img src="https://doover.com/wp-content/uploads/Doover-Logo-Landscape-Navy-padded-small.png" alt="App Icon" style="max-width: 300px;">

**Read OPC UA values from fuel additive injectors and create alarms based on those values.**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/spaneng/opcua-reader)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/spaneng/opcua-reader/blob/main/LICENSE)

[Configuration](#configuration) | [Developer](https://github.com/spaneng/opcua-reader/blob/main/DEVELOPMENT.md) | [Need Help?](#need-help)

<br/>

## Overview

Read OPC UA values from fuel additive injectors and create alarms based on those values.

<br/>

## Configuration

| Setting | Description | Default |
|---------|-------------|---------|
| **OPCUA Address** | OPC UA server URI | `Required` |
| **Injectors** | List of injector configurations | `Required` |
| **Timezone** | Timezone for reports | `Asia/Riyadh` |

<br/>
## Integrations

This is a standalone app with no dependencies on other Doover apps.

<br/>

## Need Help?

- Email: support@doover.com
- [Community Forum](https://doover.com/community)
- [Full Documentation](https://docs.doover.com)
- [Developer Documentation](https://github.com/spaneng/opcua-reader/blob/main/DEVELOPMENT.md)

<br/>

## Version History

### v1.0.0 (Current)
- Initial release

<br/>

## License

This app is licensed under the [Apache License 2.0](https://github.com/spaneng/opcua-reader/blob/main/LICENSE).

## Doover 2.0 Deployment Notes

This branch is migrated to the Doover 2.0 API (pydoover 1.x). The app is registered
in Doover 2.0 as `fuel_additive_opcua_reader`.

### Widget files (per agent)

The HMI and Reconciliation widgets are loaded from agent channels. Doover 2.0 does
not process `file_deployments` from `doover_config.json`, so when commissioning a
device the two widget bundles must be published to the agent's channels manually:

```bash
doover channel publish-file fuel_additive_hmi assets/HMIComponent.js --agent <AGENT_ID>
doover channel publish-file fuel_additive_reconciliation assets/ReconciliationComponent.js --agent <AGENT_ID>
```

(Check `doover channel publish-file --help` for the exact argument order of your CLI version.)

### Reconciliation report

`report_generator/` is still built against the Doover 1.0 reports API
(`pydoover.reports.base`, removed in pydoover 1.x) and has NOT been migrated yet.
The device app logs a `ui_state` snapshot message every 5 minutes so the report's
data source (Reconciliation values in ui_state message history) is preserved for
when the report is ported to a 2.0 report-generator app.
