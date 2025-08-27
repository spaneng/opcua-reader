#!/usr/bin/env bash

# AGENT="73371656-03cb-419c-83a5-ea97e805d5ac" # No Methane Sensor
AGENT="d8fbeab0-1e72-485e-8f55-a4bee9af0ac4" # OPCUA Re

# Option 1: Add the include directory to PYTHONPATH and run as module
export PYTHONPATH="${PYTHONPATH}:$(pwd)/include:$(pwd)"

# Run pydoover as a module instead of trying to use the entry point
doover report compose --package-path "injector_report" --agent-ids=$AGENT --agent-names "Test" --profile solarinjection

# Option 2: Use the wrapper script (uncomment the line below if you prefer this approach)
# python include/pydoover_runner.py compose_report \
#     --package_path "report_generator" \
#     --agent_ids=$AGENT \
#     --agent_names "Test" \
#     --enable-traceback \
#     --profile solarinjection