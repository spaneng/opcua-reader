# Development and releases

## Branch policy

Use `master` for the fuel-additive reader and report generator. Create short-lived
feature branches from it. Preserve app IDs in both manifests. Do not publish
2.0 code to the historical GHCR `fuel_additive` or `dv1` tags.

Recovery tags document pre-consolidation history; see [LEGACY.md](LEGACY.md).
The old Alpine PR must not be merged: it includes vendored platform-specific
report dependencies. Container smoke testing is supplied by the shared workflow;
image signing is handled by Doover when an immutable release is created.

## Local checks

Run separately in the repository root and `report_generator/`:

```sh
uv sync --locked --all-extras --dev
uv run pytest tests
```

From the repository root:

```sh
doover app discover . --json
doover config-schema validate . --app-name fuel_additive_opcua_reader
doover ui-schema validate . --app-name fuel_additive_opcua_reader
doover config-schema validate report_generator --app-name fuel_additive_report_generator
doover ui-schema validate report_generator --app-name fuel_additive_report_generator
```

Schemas are generated from Python during publishing, not committed duplicates.
Build the report with `sh build.sh` from `report_generator/`; its native wheels
must be Linux ARM64, even when the build host uses another platform.

## Production

Push or merge tested changes to `master`. The Doover App workflow publishes both
apps through the shared `getdoover/workflows` workflow pinned in the caller.
Manual dispatch is available on `master` only. Production publishing is serialized.
There is no production release trigger on a feature branch or a pull request.

The shared workflow checks both apps' schemas and tests, smoke-tests the reader
container, builds its image, builds the report package and creates source-linked
releases. Lint remains advisory as in the previous workflow. Check both publish
jobs and the resulting Doover versions before deploying a selected installation.

Do not manually publish unpushed commits. Do not clear an app ID to fix a publish
failure: that can create another application. Both apps are owned by Span
Engineering; Solar Injection owns the current installations.

## Simulators

`doover app run` uses `simulators/docker-compose.yml` and the fuel-additive PLC
simulator. Review `simulators/app_config.json` before connecting to any server.
Keep simulation keys and configuration separate from real device installations.
