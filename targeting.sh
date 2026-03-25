#!/bin/bash
# Autoresearch entry point for MSP targeting model sweep
# Sweeps across model configurations and outputs METRIC lines

set -euo pipefail
cd "$(dirname "$0")"

python3 -m targeting.sweep "$@"
