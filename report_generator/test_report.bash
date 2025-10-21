#!/usr/bin/env bash

# AGENT="73371656-03cb-419c-83a5-ea97e805d5ac" # No Methane Sensor
# AGENT="d8fbeab0-1e72-485e-8f55-a4bee9af0ac4" # OPCUA Re
AGENT="c408e9db-84b9-4a41-ab6f-f5d438313973"

# Option 1: Add the include directory to PYTHONPATH and run as module
export PYTHONPATH="${PYTHONPATH}:$(pwd)/include:$(pwd)"

# Run pydoover as a module instead of trying to use the entry point
# doover report compose --package-path "injector_report" --agent-ids=$AGENT --agent-names "Test" --profile solarinjection 
# python3.11doover report compose --package-path "injector_report" --agent-ids=$AGENT --agent-names "Test" --profile solarinjection 
doover report compose 2025-08-20 2025-08-21 $AGENT Test injector_report