# Fuel Additive Reconciliation Report

Daily reconciliation PDF report for fuel additive skids, generated from each
device's `ui_state` message history (the fuel additive device app logs a
snapshot of the Reconciliation widget values every 5 minutes).

This is a Doover 2.0 **report generator** app (`type: REP`). It runs as a
cloud processor on a cron schedule, iterates back through the last two hours
of `ui_state` messages to find the last injection of the day (the PLC clears
the data at midnight), and renders one PDF per device.

## Structure

```
doover_config.json                 Doover app definition (REP + lambda config)
pyproject.toml                     Dependencies (pydoover[reports], fpdf2)
build.sh                           Builds package.zip for the lambda runtime
src/fuel_additive_report/
  __init__.py                      Lambda handler entry point
  app_config.py                    Schedule / timezone / permissions config
  application.py                   Report generation (context from ui_state history)
  build_pdf.py                     PDF rendering (fpdf2)
  ZGH_logon.png.webp               Report logo
```

## Development

```bash
uv sync
uv run export-config   # regenerate config_schema in doover_config.json
uv run pytest          # includes a PDF render smoke test
sh build.sh            # build package.zip
```

## Publishing

```bash
doover app publish report_generator/
```

The CLI builds `package.zip` via `build.sh`, uploads it, and cuts a new lambda
version.

## Configuration

- **Schedule**: cron, default `cron(0 1 * * ?)` (1:00am) in the configured
  timezone (default `Asia/Riyadh`) — shortly after the PLC's midnight reset.
- **Extended permissions**: select the fuel additive skid devices the report
  should cover.
