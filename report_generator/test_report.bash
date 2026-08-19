#!/usr/bin/env bash

#NRBP
# AGENTS="c408e9db-84b9-4a41-ab6f-f5d438313973"
# AGENT_NAMES="NRBP"

#QSBP
# AGENTS="33b218a5-05eb-4a78-bbd6-23604664f778"
# AGENT_NAMES="QSBP"

# #SRBP
# AGENTS="369c8a41-2329-46c6-950f-cb18ab1a5efc"
# AGENT_NAMES="SRBP"

# #SAAD BP
# AGENTS="50d86305-de25-477b-ac3d-21017e587286"
# AGENT_NAMES="SAAD BP"

## All Fuel Additive Injectors
AGENTS="c408e9db-84b9-4a41-ab6f-f5d438313973,33b218a5-05eb-4a78-bbd6-23604664f778,369c8a41-2329-46c6-950f-cb18ab1a5efc,50d86305-de25-477b-ac3d-21017e587286"
AGENT_NAMES="NRBP,QSBP,SRBP,SAADBP"




# Option 1: Add the include directory to PYTHONPATH and run as module
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
## Don't include the include because only for the lambda function
# export PYTHONPATH="${PYTHONPATH}:$(pwd)/include:$(pwd)"

# Run pydoover as a module instead of trying to use the entry point
# doover report compose --package-path "injector_report" --agent-ids=$AGENT --agent-names "Test" --profile solarinjection 
# python3.11doover report compose --package-path "injector_report" --agent-ids=$AGENT --agent-names "Test" --profile solarinjection 
/Users/jarrod/Documents/getdoover/doover-cli/.venv/bin/doover report compose --period-from 2025-12-4T07:55:00 --period-to 2025-12-5T07:55:00 --agent-ids $AGENTS --agent-names $AGENT_NAMES --package-path "injector_report" --local-tz-name "Asia/Riyadh" --profile solarinjection