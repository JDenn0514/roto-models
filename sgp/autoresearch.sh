#!/bin/bash
# Autoresearch entry point for SGP model benchmarking
# Sweeps across model configurations and outputs METRIC lines

set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m sgp.run_pipeline "$@"
